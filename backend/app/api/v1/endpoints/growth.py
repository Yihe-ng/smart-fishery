import base64
import math
import os
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, cast

import cv2
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.models.ai.yolo_detector import YOLODetector
from app.schemas.base import BaseResponse
from app.schemas.growth import (
    GrowthAssessment,
    GrowthDetectResponse,
    GrowthDetectionBBox,
    GrowthDetectionItem,
    GrowthEvaluateRequest,
    GrowthEvaluateResponse,
    GrowthEvaluatedFishItem,
    GrowthImageMeta,
    GrowthStats,
    GrowthStatus,
    GrowthSummary,
    GrowthVideoDetectCreateResponse,
    GrowthVideoDetectResultResponse,
    GrowthVideoFrameItem,
    GrowthVideoMeta,
)
from app.services.growth_standard import (
    STATUS_TEXTS,
    AssessmentContext,
    FishMeasurement,
    GrowthEvaluation,
    GrowthStandardError,
    LegacyVideoRule,
    ReferenceRange,
    calculate_reference_range,
    classify_growth_length,
    estimate_weight,
    evaluate_growth_measurements,
    load_legacy_video_rule,
)

router = APIRouter()

# backend 根目录（本文件位于 backend/app/api/v1/endpoints/ 下）
_BACKEND_ROOT = Path(__file__).resolve().parents[4]

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "models",
    "ai",
    "best.pt",
)

CM_PER_PIXEL = 0.1
GROUPER_WEIGHT_COEF_A = 0.0285
GROUPER_WEIGHT_COEF_B = 2.937
SUCCESS_CODE = 200
ERROR_CODE = 500
CENTER_WEIGHT = 0.01
VIDEO_SAMPLE_INTERVAL_SECONDS = 1
VIDEO_MAX_FRAMES = 12
VIDEO_MAX_BYTES = 50 * 1024 * 1024
VIDEO_PROCESS_TIMEOUT_SECONDS = 60
VIDEO_TASK_TTL_SECONDS = 60 * 60
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}
ALLOWED_VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "video/x-msvideo",
    "video/x-matroska",
    "application/octet-stream",
}

_detector: Optional[YOLODetector] = None
_detector_lock = threading.Lock()
_pipeline = None
_pipeline_lock = threading.Lock()
_growth_manifest = None
_growth_manifest_lock = threading.Lock()
_video_task_lock = threading.Lock()
_video_tasks: Dict[str, GrowthVideoDetectResultResponse] = {}


class DetectionRequest(BaseModel):
    image: str
    # 养殖月数（从投苗日起，3–15）与投苗时平均全长（cm），均为可选。
    # 不传时仍可测量体长，但可测鱼状态为"未评估"（向后兼容，方案 §9.2）。
    cultureMonth: Optional[int] = None
    stockingAvgLengthCm: Optional[float] = None


def get_detector() -> YOLODetector:
    global _detector
    if _detector is None:
        print(f"[Growth] Loading model from: {MODEL_PATH}")
        _detector = YOLODetector(MODEL_PATH)
    return _detector


def _default_manifest_path() -> str:
    """新管线默认模型清单路径（backend/config/growth/pipeline.final.json，正式冻结清单）。

    模型清单只负责"怎么测"（模型/裁剪/时序/测长算法/厘米换算/准入策略）；
    月度分档与估重等业务参数在同目录 grouper_growth_standard.json，见 config.py 注释。
    """
    return str(_BACKEND_ROOT / "config" / "growth" / "pipeline.final.json")


def get_pipeline():
    """懒加载 FishAnalysisPipeline 单例（feature flag=two_stage 时使用）。"""
    global _pipeline
    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:
                from app.models.ai.pipeline.manifest import load_manifest
                from app.models.ai.pipeline.pipeline import FishAnalysisPipeline

                manifest_path = settings.GROWTH_MANIFEST_PATH or _default_manifest_path()
                print(f"[Growth] Loading two_stage pipeline manifest: {manifest_path}")
                manifest = load_manifest(manifest_path)
                _pipeline = FishAnalysisPipeline.from_manifest(
                    manifest,
                    device=settings.GROWTH_PIPELINE_DEVICE,
                )
    return _pipeline


def get_growth_manifest():
    """读取当前正式 manifest，统一提供换算、分档和估重业务参数。"""
    global _growth_manifest
    if _pipeline is not None:
        return _pipeline.manifest
    if _growth_manifest is None:
        with _growth_manifest_lock:
            if _growth_manifest is None:
                from app.models.ai.pipeline.manifest import load_manifest

                _growth_manifest = load_manifest(
                    settings.GROWTH_MANIFEST_PATH or _default_manifest_path()
                )
    return _growth_manifest


def _detect_payload_two_stage(
    image_base64: str,
    *,
    stream_id: Optional[str] = None,
    frame_index: Optional[int] = None,
    timestamp_sec: Optional[float] = None,
    temporal_enabled: Optional[bool] = None,
) -> Dict[str, object]:
    """新管线推理入口：图片（时序强制关闭）或视频帧（由 manifest 决定）。"""
    from app.models.ai.pipeline.image_io import decode_base64_to_rgb

    pipeline = get_pipeline()
    image_rgb, image_meta = decode_base64_to_rgb(image_base64)
    if stream_id is None:
        output = pipeline.analyze_image(image_rgb, image_meta)
    else:
        output = pipeline.analyze_frame(
            image_rgb,
            image_meta,
            stream_id=stream_id,
            frame_index=int(frame_index or 0),
            timestamp_sec=timestamp_sec,
            temporal_enabled_override=temporal_enabled,
        )
    return {
        "image": {
            "src": image_meta["src"],
            "width": image_meta["width"],
            "height": image_meta["height"],
        },
        "detections": pipeline.to_legacy_detections(output),
        "debug": output.debug,
    }


def _detect_payload(
    image_base64: str,
    *,
    stream_id: Optional[str] = None,
    frame_index: Optional[int] = None,
    timestamp_sec: Optional[float] = None,
    temporal_enabled: Optional[bool] = None,
) -> Dict[str, object]:
    """按 feature flag 分发推理路径：legacy（默认）| two_stage。"""
    if settings.GROWTH_PIPELINE == "two_stage":
        return _detect_payload_two_stage(
            image_base64,
            stream_id=stream_id,
            frame_index=frame_index,
            timestamp_sec=timestamp_sec,
            temporal_enabled=temporal_enabled,
        )
    with _detector_lock:
        return get_detector().detect(image_base64)


def _map_status(
    body_length_cm: float,
    reference_range: Optional[ReferenceRange] = None,
) -> Tuple[str, str]:
    """把单条可测鱼的估算全长映射为月度生长状态与中文文案。

    reference_range 由养殖标准算出（当月综合参考全长及上下限）；为 None 表示未提供
    养殖月数/投苗体长或评价配置不可用，此时返回"未评估"——图片路径绝不回退到旧的
    固定 15/25 cm 分档（方案 §9.4）。判断本身使用未四舍五入的原始值。
    """
    status = classify_growth_length(body_length_cm, reference_range)
    return status, STATUS_TEXTS[status]


def _map_status_legacy_video(
    body_length_cm: float,
    rule: LegacyVideoRule,
) -> Tuple[str, str]:
    """⚠️ 临时兼容：视频逐帧分档沿用配置拆分前的固定 15/25 cm 阈值。

    视频本期不做月度评价，为保证行为不变而显式读取 legacy_video_rule；图片路径
    禁止调用本函数。视频完成月度改造后应删除本函数及对应 JSON 段（方案 §11）。
    """
    if body_length_cm < rule.small_threshold_cm:
        return "small", "偏小"
    if body_length_cm <= rule.large_threshold_cm:
        return "normal", "正常"
    return "large", "偏大"


def _is_measurable_detection(detection: Dict[str, object]) -> bool:
    explicit = detection.get("is_measurable")
    if explicit is not None:
        return bool(explicit)

    class_name = str(detection.get("class_name") or "")
    if class_name == "fish_unmeasurable":
        return False
    return True


def _estimate_weight(length_cm: float) -> float:
    """按养殖标准的经验公式由估算全长换算估算体重（g）。

    公式系数来自 grouper_growth_standard.json 的 weight_estimation 段（不再读模型清单）。
    养殖标准不可用时返回 0，让接口保留体长结果而不是整体失败。
    """
    if length_cm <= 0:
        return 0
    try:
        return estimate_weight(length_cm)
    except GrowthStandardError as exc:
        print(f"[Growth] 养殖标准不可用，估重降级为 0：{exc}")
        return 0


def _safe_cm(value: object, cm_per_pixel: Optional[float] = None) -> float | None:
    """按 manifest 场景先验把像素长度转为原始厘米值，拒绝无效输入。"""
    if value is None:
        return None
    try:
        v = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if v <= 0:
        return None
    scale = cm_per_pixel if cm_per_pixel is not None else get_growth_manifest().measurement.cm_per_pixel
    return v * scale


def _is_valid_detection(bbox: List[float], image_meta: Dict[str, int]) -> bool:
    if len(bbox) != 4:
        return False
    x, y, width, height = bbox
    if width <= 1 or height <= 1:
        return False
    if image_meta["width"] <= 0 or image_meta["height"] <= 0:
        return False
    if x + width <= 0 or y + height <= 0:
        return False
    if x >= image_meta["width"] or y >= image_meta["height"]:
        return False
    return True


def _build_detection_items(
    raw_detections: List[Dict[str, object]],
    image_meta: Dict[str, int],
    *,
    reference_range: Optional[ReferenceRange] = None,
    legacy_video_rule: Optional[LegacyVideoRule] = None,
) -> List[GrowthDetectionItem]:
    """把模型原始检测转成前端检测项，并给可测鱼附加生长状态。

    分档来源二选一，互斥：图片路径传 reference_range（养殖标准算出的当月参考范围，
    缺参数时为 None → 可测鱼记为"未评估"）；视频路径传 legacy_video_rule
    （⚠️ 临时兼容的固定 15/25 cm 阈值）。不可测鱼一律为"不可测"、体长与体重记 0，
    不参与任何平均值。本函数只做换算与映射，不运行模型。
    """
    center_x = image_meta["width"] / 2
    center_y = image_meta["height"] / 2
    cm_per_pixel = get_growth_manifest().measurement.cm_per_pixel
    sortable_items = []

    for detection in raw_detections:
        bbox = detection.get("bbox")
        if not isinstance(bbox, list) or not _is_valid_detection(bbox, image_meta):
            continue

        x, y, width, height = [float(value) for value in bbox]
        class_name = str(detection.get("class_name") or "")
        is_measurable = _is_measurable_detection(detection)
        if is_measurable:
            body_length_cm = _safe_cm(detection.get("length", 0), cm_per_pixel) or 0.0
            if legacy_video_rule is not None:
                status, status_text = _map_status_legacy_video(
                    body_length_cm, legacy_video_rule
                )
            else:
                status, status_text = _map_status(body_length_cm, reference_range)
            weight_g = _estimate_weight(body_length_cm)
            label_text = f"{status_text} | {body_length_cm:.1f}cm"
            measurability_label = "可测"
        else:
            body_length_cm = 0
            status, status_text = "unmeasurable", "不可测"
            weight_g = 0
            label_text = "不可测"
            measurability_label = "不可测"
        bbox_center_x = x + (width / 2)
        bbox_center_y = y + (height / 2)
        center_distance = math.sqrt(
            math.pow(bbox_center_x - center_x, 2) + math.pow(bbox_center_y - center_y, 2)
        )

        sortable_items.append(
            {
                "status": status,
                "status_text": status_text,
                "confidence": round(float(detection.get("confidence", 0)), 2),
                "bbox": GrowthDetectionBBox(x=x, y=y, width=width, height=height),
                "body_length_cm": body_length_cm,
                "weight_g": weight_g,
                "area": width * height,
                "center_distance": center_distance,
                "label_text": label_text,
                "mask_polygons": detection.get("mask_polygons"),
                "measurement_method": detection.get("measurement_method"),
                "measurement_confidence": detection.get("measurement_confidence"),
                "measurement_reasons": detection.get("measurement_reasons"),
                "visible_mask_length_px": detection.get("visible_mask_length_px"),
                "class_name": class_name,
                "is_measurable": is_measurable,
                "measurability_label": measurability_label,
                # two_stage 可选 debug 字段（legacy 恒为 None，API 兼容）
                "instance_id": detection.get("instance_id"),
                "seg_confidence": detection.get("seg_confidence"),
                "single_measurable_probability": detection.get(
                    "single_measurable_probability"
                ),
                "final_measurable_probability": detection.get(
                    "final_measurable_probability"
                ),
                "temporal_applied": detection.get("temporal_applied"),
                "temporal_policy": detection.get("temporal_policy"),
                "temporal_fallback_reason": detection.get("temporal_fallback_reason"),
                "temporal_history_count": detection.get("temporal_history_count"),
            }
        )

    sortable_items.sort(
        key=lambda item: (
            -item["confidence"],
            -item["area"],
            item["center_distance"] * CENTER_WEIGHT,
        )
    )

    return [
        GrowthDetectionItem(
            id=f"fish-{index}",
            index=index,
            status=item["status"],
            statusText=item["status_text"],
            confidence=item["confidence"],
            bbox=item["bbox"],
            bodyLengthCm=item["body_length_cm"],
            weightG=item["weight_g"],
            labelText=item["label_text"],
            maskPolygons=item.get("mask_polygons") or [],
            measurementMethod=item.get("measurement_method"),
            measurementConfidence=item.get("measurement_confidence"),
            visibleMaskLengthCm=_safe_cm(item.get("visible_mask_length_px"), cm_per_pixel),
            measurementReasons=item.get("measurement_reasons"),
            className=item.get("class_name"),
            isMeasurable=bool(item.get("is_measurable")),
            measurabilityLabel=str(item.get("measurability_label")),
            instanceId=item.get("instance_id"),
            segmentationConfidence=item.get("seg_confidence"),
            singleMeasurableProbability=item.get("single_measurable_probability"),
            finalMeasurableProbability=item.get("final_measurable_probability"),
            temporalApplied=item.get("temporal_applied"),
            temporalPolicy=item.get("temporal_policy"),
            temporalFallbackReason=item.get("temporal_fallback_reason"),
            temporalHistoryCount=item.get("temporal_history_count"),
        )
        for index, item in enumerate(sortable_items, start=1)
    ]


def _build_stats(detections: List[GrowthDetectionItem]) -> GrowthStats:
    stats = GrowthStats(detectedCount=len(detections))
    for detection in detections:
        if detection.isMeasurable:
            stats.measurableCount += 1
            setattr(stats, detection.status, getattr(stats, detection.status) + 1)
        else:
            stats.unmeasurableCount += 1
    return stats


def _build_summary(detections: List[GrowthDetectionItem]) -> GrowthSummary:
    measurable_detections = [
        detection for detection in detections if detection.isMeasurable
    ]
    if not measurable_detections:
        return GrowthSummary()
    avg_length = round(
        sum(detection.bodyLengthCm for detection in measurable_detections)
        / len(measurable_detections),
        1,
    )
    avg_weight = round(
        sum(detection.weightG for detection in measurable_detections)
        / len(measurable_detections),
        1,
    )
    return GrowthSummary(avgBodyLengthCm=avg_length, avgWeightG=avg_weight)


def _round_optional(value: Optional[float]) -> Optional[float]:
    """展示口径：接口统一输出一位小数；判断用的原始值不经过这里。"""
    return None if value is None else round(value, 1)


def _to_assessment(evaluation: GrowthEvaluation) -> GrowthAssessment:
    """把评价服务结果转成接口 assessment（长度字段按展示口径保留一位小数）。"""
    reference = evaluation.reference_range
    return GrowthAssessment(
        cultureMonth=reference.culture_month if reference else None,
        stockingAvgLengthCm=(
            _round_optional(reference.stocking_avg_length_cm) if reference else None
        ),
        referenceLengthCm=(
            _round_optional(reference.reference_length_cm) if reference else None
        ),
        smallThresholdCm=_round_optional(reference.small_lower_cm) if reference else None,
        largeThresholdCm=_round_optional(reference.large_upper_cm) if reference else None,
        trimmedMeanLengthCm=_round_optional(evaluation.trimmed_mean_length_cm),
        allMeasurableAvgLengthCm=_round_optional(
            evaluation.all_measurable_avg_length_cm
        ),
        cohortStatus=evaluation.cohort_status,
        sampleSufficient=evaluation.sample_sufficient,
        advice=evaluation.advice,
    )


def _to_fish_measurements(
    detections: List[GrowthDetectionItem],
) -> List[FishMeasurement]:
    return [
        FishMeasurement(
            id=detection.id,
            is_measurable=detection.isMeasurable,
            body_length_cm=detection.bodyLengthCm,
        )
        for detection in detections
    ]


def _safe_reference_range(context: AssessmentContext) -> Optional[ReferenceRange]:
    """算当月参考范围；养殖标准不可用或参数非法时返回 None（降级为未评估）。

    错误只记后端终端日志，不把文件路径和堆栈带进接口响应（方案 §9.4）。
    """
    try:
        return calculate_reference_range(context)
    except GrowthStandardError as exc:
        print(f"[Growth] 生长评价配置不可用，本次降级为未评估：{exc}")
        return None


def _build_detect_response(
    detection_result: Dict[str, object],
    task_status: str = "success",
    error_code: Optional[str] = None,
    *,
    context: Optional[AssessmentContext] = None,
    legacy_video_rule: Optional[LegacyVideoRule] = None,
) -> GrowthDetectResponse:
    """组装图片识别响应：测量结果 + 可选月度生长评价。

    context 是图片路径的养殖参数（养殖月数、投苗时平均全长）；参数不全时可测鱼为
    "未评估"，但体长、体重和平均值照常返回。养殖标准加载或校验失败时同样保留全部
    测量结果，assessment 置 None、可测鱼置"未评估"，**不回退到视频旧的 15/25 分档**
    （方案 §9.4）。legacy_video_rule 仅供视频逐帧调用（⚠️ 临时兼容）。
    本函数不运行模型，只消费已有的推理结果。
    """
    image_payload = detection_result["image"]
    raw_detections = detection_result["detections"]
    image_meta_dict = {
        "src": str(image_payload["src"]),
        "width": int(image_payload["width"]),
        "height": int(image_payload["height"]),
    }
    image = GrowthImageMeta(**image_meta_dict)
    reference_range = (
        None
        if legacy_video_rule is not None or context is None
        else _safe_reference_range(context)
    )
    detections = _build_detection_items(
        raw_detections,
        image_meta_dict,
        reference_range=reference_range,
        legacy_video_rule=legacy_video_rule,
    )

    if not detections:
        return GrowthDetectResponse(
            taskStatus=task_status,
            image=image,
            detections=[],
            selectedDetectionId=None,
            stats=GrowthStats(),
            summary=GrowthSummary(),
            errorCode=error_code or "NO_FISH_DETECTED",
        )

    assessment: Optional[GrowthAssessment] = None
    if legacy_video_rule is None and context is not None:
        try:
            assessment = _to_assessment(
                evaluate_growth_measurements(_to_fish_measurements(detections), context)
            )
        except GrowthStandardError as exc:
            print(f"[Growth] 生长评价失败，仅返回测量结果：{exc}")

    return GrowthDetectResponse(
        taskStatus=task_status,
        image=image,
        detections=detections,
        selectedDetectionId=detections[0].id,
        stats=_build_stats(detections),
        summary=_build_summary(detections),
        errorCode=error_code,
        assessment=assessment,
    )


def _safe_legacy_video_rule() -> Optional[LegacyVideoRule]:
    """⚠️ 临时兼容：读取视频专用的固定 15/25 cm 分档规则。

    仅视频路径调用；养殖标准不可用时返回 None，视频帧退回"未评估"而不是内置阈值。
    视频完成月度评价改造后删除本函数（方案 §11）。
    """
    try:
        return load_legacy_video_rule()
    except GrowthStandardError as exc:
        print(f"[Growth] 视频临时分档规则不可用，本帧降级为未评估：{exc}")
        return None


def _build_frame_item(
    frame_id: str,
    timestamp_sec: int,
    detection_result: Dict[str, object],
    legacy_video_rule: Optional[LegacyVideoRule] = None,
) -> GrowthVideoFrameItem:
    """组装视频关键帧结果。

    ⚠️ 临时兼容：视频本期不做月度评价，逐帧分档显式使用 legacy_video_rule
    （固定 15/25 cm），不产出 assessment，行为与配置拆分前保持一致。
    """
    frame_response = _build_detect_response(
        detection_result,
        legacy_video_rule=legacy_video_rule or _safe_legacy_video_rule(),
    )
    return GrowthVideoFrameItem(
        frameId=frame_id,
        timestampSec=timestamp_sec,
        image=frame_response.image,
        detections=frame_response.detections,
        selectedDetectionId=frame_response.selectedDetectionId,
        stats=frame_response.stats,
        summary=frame_response.summary,
    )


def _sample_timestamps(duration_sec: float) -> List[int]:
    if duration_sec <= 0:
        return [0]
    sample_count = min(VIDEO_MAX_FRAMES, max(1, math.ceil(duration_sec)))
    return [index * VIDEO_SAMPLE_INTERVAL_SECONDS for index in range(sample_count)]


def _encode_frame_to_base64(frame) -> str:
    success, encoded = cv2.imencode(".jpg", frame)
    if not success:
        raise ValueError("VIDEO_DECODE_FAILED")
    return base64.b64encode(encoded.tobytes()).decode("utf-8")


def _build_video_result(
    task_id: str,
    task_status: str,
    *,
    progress: int = 0,
    video: Optional[GrowthVideoMeta] = None,
    frames: Optional[List[GrowthVideoFrameItem]] = None,
    selected_frame_id: Optional[str] = None,
    error_code: Optional[str] = None,
    started_at: Optional[float] = None,
) -> GrowthVideoDetectResultResponse:
    safe_frames = frames or []
    flattened_detections = [
        detection for frame in safe_frames for detection in frame.detections
    ]
    return GrowthVideoDetectResultResponse(
        taskId=task_id,
        taskStatus=task_status,
        progress=progress,
        video=video,
        selectedFrameId=selected_frame_id,
        frames=safe_frames,
        aggregateStats=_build_stats(flattened_detections),
        aggregateSummary=_build_summary(flattened_detections),
        errorCode=error_code,
        startedAt=started_at,
    )


def _set_video_task(task_id: str, payload: GrowthVideoDetectResultResponse) -> None:
    with _video_task_lock:
        _cleanup_expired_video_tasks_locked(time.time())
        _video_tasks[task_id] = payload


def _get_video_task(task_id: str) -> Optional[GrowthVideoDetectResultResponse]:
    with _video_task_lock:
        _cleanup_expired_video_tasks_locked(time.time())
        return _video_tasks.get(task_id)


def _update_video_task(task_id: str, **updates) -> None:
    with _video_task_lock:
        _cleanup_expired_video_tasks_locked(time.time())
        current = _video_tasks.get(task_id)
        if current is None:
            return
        _video_tasks[task_id] = current.model_copy(update=updates)


def _cleanup_expired_video_tasks_locked(now: float) -> None:
    expired_task_ids = [
        task_id
        for task_id, task in _video_tasks.items()
        if task.startedAt is not None and now - task.startedAt > VIDEO_TASK_TTL_SECONDS
    ]
    for task_id in expired_task_ids:
        del _video_tasks[task_id]


def _cleanup_video_file(temp_path: str) -> None:
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass


def _process_video_task(task_id: str, temp_path: str, filename: str) -> None:
    capture = None
    started_at = time.time()
    try:
        # 两阶段管线：每个视频任务独立 stream_id，重置时序状态防止串线
        if settings.GROWTH_PIPELINE == "two_stage":
            get_pipeline().reset_temporal_state(task_id)
        _update_video_task(task_id, taskStatus="processing", progress=5, startedAt=started_at)

        capture = cv2.VideoCapture(temp_path)
        if not capture.isOpened():
            raise ValueError("VIDEO_DECODE_FAILED")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if fps <= 0 and total_frames <= 0:
            raise ValueError("VIDEO_DECODE_FAILED")

        duration_sec = round(total_frames / fps, 1) if fps > 0 and total_frames > 0 else 0.0
        video_meta = GrowthVideoMeta(filename=filename, durationSec=duration_sec)
        _update_video_task(task_id, video=video_meta)

        timestamps = _sample_timestamps(duration_sec)
        frames: List[GrowthVideoFrameItem] = []

        for index, timestamp_sec in enumerate(timestamps, start=1):
            if time.time() - started_at > VIDEO_PROCESS_TIMEOUT_SECONDS:
                raise ValueError("PROCESS_TIMEOUT")

            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
            success, frame = capture.read()

            if not success and fps > 0:
                target_index = min(total_frames - 1, int(timestamp_sec * fps))
                if target_index >= 0:
                    capture.set(cv2.CAP_PROP_POS_FRAMES, target_index)
                    success, frame = capture.read()

            if not success:
                continue

            frame_base64 = _encode_frame_to_base64(frame)
            frame_detection_result = _detect_payload(
                frame_base64,
                stream_id=task_id,
                frame_index=timestamp_sec,
                timestamp_sec=float(timestamp_sec),
                temporal_enabled=settings.GROWTH_VIDEO_TEMPORAL_ENABLED,
            )
            frames.append(
                _build_frame_item(
                    frame_id=f"frame-{len(frames) + 1}",
                    timestamp_sec=timestamp_sec,
                    detection_result=frame_detection_result,
                )
            )

            progress = min(95, max(10, int(index / len(timestamps) * 100)))
            _update_video_task(task_id, progress=progress)

        if not frames:
            raise ValueError("NO_VALID_FRAMES")

        selected_frame = next((frame for frame in frames if frame.detections), frames[0])
        _set_video_task(
            task_id,
            _build_video_result(
                task_id,
                "success",
                progress=100,
                video=video_meta,
                frames=frames,
                selected_frame_id=selected_frame.frameId,
                error_code=None,
                started_at=started_at,
            ),
        )
    except ValueError as exc:
        current = _get_video_task(task_id)
        _set_video_task(
            task_id,
            _build_video_result(
                task_id,
                "failed",
                progress=100,
                video=current.video if current else None,
                frames=[],
                selected_frame_id=None,
                error_code=str(exc) or "VIDEO_DECODE_FAILED",
                started_at=started_at,
            ),
        )
    except Exception:
        current = _get_video_task(task_id)
        _set_video_task(
            task_id,
            _build_video_result(
                task_id,
                "failed",
                progress=100,
                video=current.video if current else None,
                frames=[],
                selected_frame_id=None,
                error_code="INTERNAL_ERROR",
                started_at=started_at,
            ),
        )
    finally:
        if capture is not None:
            capture.release()
        _cleanup_video_file(temp_path)


def _empty_detect_response(task_status: str, error_code: Optional[str] = None):
    return GrowthDetectResponse(
        taskStatus=task_status,
        image=None,
        detections=[],
        selectedDetectionId=None,
        stats=GrowthStats(),
        summary=GrowthSummary(),
        errorCode=error_code,
    )


def _invalid_video_create_response(error_code: str):
    return BaseResponse[GrowthVideoDetectCreateResponse](
        code=ERROR_CODE,
        msg=f"视频任务创建失败: {error_code}",
        data=GrowthVideoDetectCreateResponse(taskId="", taskStatus="queued"),
    )


@router.post("/detect", response_model=BaseResponse[GrowthDetectResponse])
def detect_fish(request: DetectionRequest):
    try:
        detection_result = _detect_payload(request.image)
        # 图片路径把养殖参数传给统一评价入口；不传时 assessment 为 None、可测鱼"未评估"
        context = (
            AssessmentContext(
                culture_month=request.cultureMonth,
                stocking_avg_length_cm=request.stockingAvgLengthCm,
            )
            if request.cultureMonth is not None or request.stockingAvgLengthCm is not None
            else None
        )
        response_data = _build_detect_response(
            detection_result,
            context=context,
        )

        if response_data.errorCode == "NO_FISH_DETECTED":
            return BaseResponse[GrowthDetectResponse](
                code=SUCCESS_CODE,
                msg="未识别到石斑鱼",
                data=response_data,
            )

        return BaseResponse[GrowthDetectResponse](
            code=SUCCESS_CODE,
            msg="检测成功",
            data=response_data,
        )
    except ValueError as exc:
        error_code = str(exc) or "INVALID_IMAGE"
        return BaseResponse[GrowthDetectResponse](
            code=ERROR_CODE,
            msg=f"检测失败: {error_code}",
            data=_empty_detect_response(task_status="failed", error_code=error_code),
        )
    except Exception:
        return BaseResponse[GrowthDetectResponse](
            code=ERROR_CODE,
            msg="检测失败: INTERNAL_ERROR",
            data=_empty_detect_response(task_status="failed", error_code="INTERNAL_ERROR"),
        )


@router.post("/evaluate", response_model=BaseResponse[GrowthEvaluateResponse])
def evaluate_growth(request: GrowthEvaluateRequest):
    """轻量重评：修改养殖参数后重算业务状态。

    本端点只接收前端已完成的检测项（标识/可测性/个体全长）与新的养殖参数，
    **不调用检测器、不加载模型、不读取图片、不重复测长**（方案 §9.3、§13）。
    它与图片首次识别共用 evaluate_growth_measurements 唯一业务入口，保证两套
    结果口径一致。养殖参数不全时按"未评估"返回；养殖标准不可用时返回结构化
    错误码，由前端保留上一次成功结果，不泄露本机路径与堆栈（方案 §9.4）。
    """
    context = AssessmentContext(
        culture_month=request.cultureMonth,
        stocking_avg_length_cm=request.stockingAvgLengthCm,
    )
    try:
        measurements = [
            FishMeasurement(
                id=item.id,
                is_measurable=item.isMeasurable,
                body_length_cm=item.bodyLengthCm,
            )
            for item in request.fishMeasurements
        ]
        evaluation = evaluate_growth_measurements(measurements, context)
    except GrowthStandardError as exc:
        print(f"[Growth] 轻量重评失败（保留前端上一次成功结果）：{exc}")
        return BaseResponse[GrowthEvaluateResponse](
            code=ERROR_CODE,
            msg="生长评价配置暂时不可用",
            data=GrowthEvaluateResponse(errorCode="EVALUATION_CONFIG_UNAVAILABLE"),
        )

    status_counts = evaluation.status_counts
    stats = GrowthStats(
        small=status_counts.get("small", 0),
        normal=status_counts.get("normal", 0),
        large=status_counts.get("large", 0),
        unassessed=status_counts.get("unassessed", 0),
        detectedCount=len(evaluation.fish),
        measurableCount=evaluation.measurable_count,
        unmeasurableCount=evaluation.unmeasurable_count,
    )
    return BaseResponse[GrowthEvaluateResponse](
        code=SUCCESS_CODE,
        msg="重新评价完成",
        data=GrowthEvaluateResponse(
            detections=[
                GrowthEvaluatedFishItem(
                    id=item.id,
                    status=cast(GrowthStatus, item.status),
                    statusText=item.status_text,
                )
                for item in evaluation.fish
            ],
            stats=stats,
            summary=GrowthSummary(
                avgBodyLengthCm=(
                    round(evaluation.all_measurable_avg_length_cm, 1)
                    if evaluation.all_measurable_avg_length_cm is not None
                    else 0
                ),
                avgWeightG=0,
            ),
            assessment=_to_assessment(evaluation),
            errorCode=None,
        ),
    )


@router.post("/detect/video", response_model=BaseResponse[GrowthVideoDetectCreateResponse])
async def create_growth_video_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    filename = file.filename or "growth-video.mp4"
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        return _invalid_video_create_response("INVALID_VIDEO")

    if file.content_type and file.content_type not in ALLOWED_VIDEO_CONTENT_TYPES:
        return _invalid_video_create_response("INVALID_VIDEO")

    content = await file.read()
    if not content:
        return _invalid_video_create_response("INVALID_VIDEO")
    if len(content) > VIDEO_MAX_BYTES:
        return _invalid_video_create_response("VIDEO_TOO_LARGE")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp_file.write(content)
        temp_path = temp_file.name
    finally:
        temp_file.close()

    task_id = uuid.uuid4().hex
    initial_video = GrowthVideoMeta(filename=filename, durationSec=0)
    _set_video_task(
        task_id,
        _build_video_result(
            task_id,
            "queued",
            progress=0,
            video=initial_video,
            frames=[],
            selected_frame_id=None,
            error_code=None,
            started_at=time.time(),
        ),
    )
    background_tasks.add_task(_process_video_task, task_id, temp_path, filename)

    return BaseResponse[GrowthVideoDetectCreateResponse](
        code=SUCCESS_CODE,
        msg="视频任务已创建",
        data=GrowthVideoDetectCreateResponse(taskId=task_id, taskStatus="queued"),
    )


@router.get("/detect/video/{task_id}", response_model=BaseResponse[GrowthVideoDetectResultResponse])
def get_growth_video_task(task_id: str):
    task = _get_video_task(task_id)
    if task is None:
        return BaseResponse[GrowthVideoDetectResultResponse](
            code=ERROR_CODE,
            msg="视频任务不存在: INTERNAL_ERROR",
            data=_build_video_result(
                task_id,
                "failed",
                progress=100,
                video=None,
                frames=[],
                selected_frame_id=None,
                error_code="INTERNAL_ERROR",
            ),
        )

    status_message = {
        "queued": "视频任务排队中",
        "processing": "视频关键帧识别中",
        "success": "视频识别完成",
        "failed": "视频识别失败",
    }[task.taskStatus]
    return BaseResponse[GrowthVideoDetectResultResponse](
        code=SUCCESS_CODE,
        msg=status_message,
        data=task,
    )


@router.get("/camera/stream", response_model=BaseResponse[str])
def get_camera_stream():
    return BaseResponse[str](
        code=SUCCESS_CODE,
        msg="获取成功",
        data="http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8",
    )
