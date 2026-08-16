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
from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile
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
    GrowthEvaluateVideoRequest,
    GrowthEvaluateVideoResponse,
    GrowthEvaluatedFishItem,
    GrowthImageMeta,
    GrowthStats,
    GrowthStatus,
    GrowthSummary,
    GrowthVideoDetectCreateResponse,
    GrowthVideoDetectResultResponse,
    GrowthVideoFrameItem,
    GrowthVideoFrameEvaluationResponse,
    GrowthVideoMeta,
)
from app.services.growth_standard import (
    STATUS_TEXTS,
    AssessmentContext,
    FishMeasurement,
    GrowthEvaluation,
    GrowthStandardError,
    ReferenceRange,
    VideoGrowthEvaluation,
    calculate_reference_range,
    classify_growth_length,
    estimate_weight,
    evaluate_growth_measurements,
    evaluate_video_measurements,
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
VIDEO_MAX_BYTES = 50 * 1024 * 1024
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
_video_cancel_requested: Dict[str, bool] = {}
_growth_inference_lock = threading.Lock()


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
    养殖月数/投苗体长或评价配置不可用，此时返回"未评估"。判断本身使用未四舍五入的
    原始值。
    """
    status = classify_growth_length(body_length_cm, reference_range)
    return status, STATUS_TEXTS[status]


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
) -> List[GrowthDetectionItem]:
    """把模型原始检测转成前端检测项，并给可测鱼附加生长状态。

    图片和视频都使用共享的 reference_range；缺参数时可测鱼记为"未评估"。
    不可测鱼一律为"不可测"、体长与体重记 0，不参与任何平均值。本函数只做
    换算与映射，不运行模型。
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
) -> GrowthDetectResponse:
    """组装图片识别响应：测量结果 + 可选月度生长评价。

    context 是养殖参数（养殖月数、投苗时平均全长）；参数不全时可测鱼为"未评估"，
    但体长、体重和平均值照常返回。养殖标准加载或校验失败时同样保留全部测量结果，
    assessment 置 None、可测鱼置"未评估"，不使用任何固定阈值回退。
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
    reference_range = None if context is None else _safe_reference_range(context)
    detections = _build_detection_items(
        raw_detections,
        image_meta_dict,
        reference_range=reference_range,
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
    if context is not None:
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


def _build_frame_item(
    frame_id: str,
    timestamp_sec: float,
    detection_result: Dict[str, object],
    context: AssessmentContext,
) -> GrowthVideoFrameItem:
    """组装一个关键帧结果，并复用图片评价函数得到帧级状态。"""
    frame_response = _build_detect_response(
        detection_result,
        context=context,
    )
    if not frame_response.detections:
        frame_status = "no_valid_detection"
    elif frame_response.assessment and frame_response.assessment.trimmedMeanLengthCm is not None:
        frame_status = "evaluable"
    else:
        frame_status = "insufficient_sample"
    return GrowthVideoFrameItem(
        frameId=frame_id,
        timestampSec=timestamp_sec,
        image=frame_response.image,
        detections=frame_response.detections,
        selectedDetectionId=frame_response.selectedDetectionId,
        stats=frame_response.stats,
        summary=frame_response.summary,
        assessment=frame_response.assessment,
        frameStatus=frame_status,
    )


def _sample_timestamps(duration_sec: float) -> List[float]:
    """按完整视频时长生成 3–8 个等分区间中点（单位：秒）。"""
    if duration_sec < settings.VIDEO_MIN_DURATION_SECONDS:
        return []
    sample_count = min(
        settings.VIDEO_MAX_FRAMES,
        max(settings.VIDEO_MIN_FRAMES, math.ceil(duration_sec / settings.VIDEO_TARGET_INTERVAL_SECONDS)),
    )
    segment_width = duration_sec / sample_count
    timestamps = [
        min(duration_sec - 0.001, (index + 0.5) * segment_width)
        for index in range(sample_count)
    ]
    return list(dict.fromkeys(round(max(0.0, timestamp), 3) for timestamp in timestamps))


def _prioritized_indices(count: int) -> List[int]:
    """返回覆盖视频前、中、后的分散处理顺序，最终展示仍按时间排序。"""
    if count <= 0:
        return []
    preferred = [0, count - 1, count // 2, count // 4, (count * 3) // 4]
    return list(dict.fromkeys(preferred + list(range(count))))


def _encode_frame_to_base64(frame, *, for_display: bool = False) -> str:
    """编码关键帧展示副本；推理路径可选择保留原始分辨率。"""
    output = frame
    if for_display:
        height, width = frame.shape[:2]
        max_edge = max(height, width)
        if max_edge > settings.VIDEO_DISPLAY_MAX_EDGE:
            scale = settings.VIDEO_DISPLAY_MAX_EDGE / max_edge
            output = cv2.resize(frame, (round(width * scale), round(height * scale)))
    success, encoded = cv2.imencode(
        ".jpg",
        output,
        [cv2.IMWRITE_JPEG_QUALITY, settings.VIDEO_DISPLAY_JPEG_QUALITY],
    )
    if not success:
        raise ValueError("VIDEO_DECODE_FAILED")
    return base64.b64encode(encoded.tobytes()).decode("utf-8")


def _detect_frame_payload(
    frame,
    *,
    stream_id: str,
    frame_index: int,
    timestamp_sec: float,
) -> Dict[str, object]:
    """把原始 OpenCV 帧直接送入两阶段管线，兼容 legacy 路径再编码。"""
    if settings.GROWTH_PIPELINE != "two_stage":
        return _detect_payload(
            _encode_frame_to_base64(frame),
            stream_id=stream_id,
            frame_index=frame_index,
            timestamp_sec=timestamp_sec,
            temporal_enabled=False,
        )

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    height, width = image_rgb.shape[:2]
    pipeline = get_pipeline()
    output = pipeline.analyze_frame(
        image_rgb,
        {"width": width, "height": height},
        stream_id=stream_id,
        frame_index=frame_index,
        timestamp_sec=timestamp_sec,
        temporal_enabled_override=False,
    )
    return {
        "image": {"src": "", "width": width, "height": height},
        "detections": pipeline.to_legacy_detections(output),
        "debug": output.debug,
    }


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
    created_at: Optional[float] = None,
    finished_at: Optional[float] = None,
    stage: str = "queued",
    culture_month: Optional[int] = None,
    stocking_avg_length_cm: Optional[float] = None,
    planned_frame_count: int = 0,
    is_partial: bool = False,
    warning_code: Optional[str] = None,
) -> GrowthVideoDetectResultResponse:
    safe_frames = frames or []
    safe_frames = sorted(safe_frames, key=lambda frame: frame.timestampSec)
    flattened_detections = [
        detection for frame in safe_frames for detection in frame.detections
    ]
    context = AssessmentContext(
        culture_month=culture_month,
        stocking_avg_length_cm=stocking_avg_length_cm,
    )
    video_evaluation: Optional[VideoGrowthEvaluation] = None
    if task_status != "cancelled":
        try:
            video_evaluation = evaluate_video_measurements(
                [
                    _to_fish_measurements(frame.detections)
                    for frame in safe_frames
                ],
                context,
            )
        except GrowthStandardError as exc:
            print(f"[Growth] 视频评价配置不可用，保留测量结果并降级为未评估：{exc}")

    video_assessment = _to_video_assessment(video_evaluation)
    video_length = video_evaluation.video_length_cm if video_evaluation else None
    video_summary = GrowthSummary()
    if task_status != "cancelled":
        video_summary = (
            GrowthSummary(
                avgBodyLengthCm=_round_optional(video_length) or 0,
                avgWeightG=round(_estimate_weight(video_length or 0), 1),
            )
            if video_length is not None
            else _build_summary(flattened_detections)
        )
    evaluable_count = (
        video_evaluation.evaluable_frame_count
        if video_evaluation
        else sum(frame.frameStatus == "evaluable" for frame in safe_frames)
    )
    return GrowthVideoDetectResultResponse(
        taskId=task_id,
        taskStatus=task_status,
        stage=stage,
        progress=progress,
        video=video,
        cultureMonth=culture_month,
        stockingAvgLengthCm=stocking_avg_length_cm,
        selectedFrameId=selected_frame_id,
        frames=safe_frames,
        aggregateStats=_build_stats(flattened_detections),
        aggregateSummary=video_summary,
        assessment=video_assessment,
        plannedFrameCount=planned_frame_count,
        completedFrameCount=len(safe_frames),
        evaluableFrameCount=evaluable_count,
        detectionOccurrenceCount=len(flattened_detections),
        measurableOccurrenceCount=sum(1 for item in flattened_detections if item.isMeasurable),
        isPartial=is_partial,
        warningCode=warning_code,
        errorCode=error_code,
        startedAt=started_at,
        createdAt=created_at,
        finishedAt=finished_at,
    )


def _to_video_assessment(
    evaluation: Optional[VideoGrowthEvaluation],
) -> Optional[GrowthAssessment]:
    """把视频级中位数评价映射为页面复用的群体评价模型。"""
    if evaluation is None:
        return None
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
        trimmedMeanLengthCm=_round_optional(evaluation.video_length_cm),
        allMeasurableAvgLengthCm=_round_optional(evaluation.all_measurable_avg_length_cm),
        cohortStatus=evaluation.cohort_status,
        sampleSufficient=evaluation.sample_sufficient,
        advice=evaluation.advice,
    )


def _set_video_task(task_id: str, payload: GrowthVideoDetectResultResponse) -> None:
    with _video_task_lock:
        _cleanup_expired_video_tasks_locked(time.time())
        if (
            payload.taskStatus == "success"
            and _video_cancel_requested.get(task_id, False)
        ):
            payload = payload.model_copy(
                update={
                    "taskStatus": "cancelled",
                    "assessment": None,
                    "aggregateSummary": GrowthSummary(),
                    "warningCode": "USER_CANCELLED",
                }
            )
        _video_tasks[task_id] = payload
        if payload.taskStatus in {"success", "failed"}:
            _video_cancel_requested.pop(task_id, None)
        _trim_terminal_video_tasks_locked()


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
        if task.finishedAt is not None
        and now - task.finishedAt > settings.VIDEO_TASK_TTL_SECONDS
    ]
    for task_id in expired_task_ids:
        del _video_tasks[task_id]
        _video_cancel_requested.pop(task_id, None)


def _trim_terminal_video_tasks_locked() -> None:
    terminal = [
        (task.finishedAt or 0.0, task_id)
        for task_id, task in _video_tasks.items()
        if task.taskStatus in {"success", "failed", "cancelled"}
    ]
    terminal.sort()
    for _, task_id in terminal[: -settings.VIDEO_MAX_TERMINAL_TASKS]:
        del _video_tasks[task_id]
        _video_cancel_requested.pop(task_id, None)


def _is_video_cancel_requested(task_id: str) -> bool:
    with _video_task_lock:
        return _video_cancel_requested.get(task_id, False)


def _select_default_video_frame(frames: List[GrowthVideoFrameItem]) -> Optional[GrowthVideoFrameItem]:
    """按可评价优先、可测数最多、时间最早的规则选择默认关键帧。"""
    if not frames:
        return None
    evaluable = [frame for frame in frames if frame.frameStatus == "evaluable"]
    if evaluable:
        return max(evaluable, key=lambda frame: (frame.stats.measurableCount, -frame.timestampSec))
    with_measurable = [frame for frame in frames if frame.stats.measurableCount > 0]
    if with_measurable:
        return max(with_measurable, key=lambda frame: (frame.stats.measurableCount, -frame.timestampSec))
    with_detection = [frame for frame in frames if frame.stats.detectedCount > 0]
    return max(with_detection, key=lambda frame: (frame.stats.detectedCount, -frame.timestampSec)) if with_detection else frames[0]


def _cleanup_video_file(temp_path: str) -> None:
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass


def _process_video_task(task_id: str, temp_path: str, filename: str) -> None:
    """串行处理视频任务，保留已完成帧并把阶段/预算映射到查询响应。"""
    capture = None
    inference_acquired = False
    started_at: Optional[float] = None
    created_at = (_get_video_task(task_id).createdAt if _get_video_task(task_id) else time.time())
    try:
        while not inference_acquired:
            if _is_video_cancel_requested(task_id):
                current = _get_video_task(task_id)
                if current:
                    _set_video_task(
                        task_id,
                        current.model_copy(
                            update={
                                "taskStatus": "cancelled",
                                "progress": 100,
                                "warningCode": "USER_CANCELLED",
                                "finishedAt": time.time(),
                            }
                        ),
                    )
                return
            inference_acquired = _growth_inference_lock.acquire(timeout=0.2)

        current = _get_video_task(task_id)
        if current is None or current.taskStatus == "cancelled":
            return
        if _is_video_cancel_requested(task_id):
            _set_video_task(
                task_id,
                current.model_copy(
                    update={
                        "taskStatus": "cancelled",
                        "progress": 100,
                        "warningCode": "USER_CANCELLED",
                        "finishedAt": time.time(),
                    }
                ),
            )
            return

        started_at = time.time()
        context = AssessmentContext(
            culture_month=current.cultureMonth if current else None,
            stocking_avg_length_cm=current.stockingAvgLengthCm if current else None,
        )
        _update_video_task(
            task_id,
            taskStatus="processing",
            stage="preparing",
            progress=2,
            startedAt=started_at,
        )
        if settings.GROWTH_PIPELINE == "two_stage":
            get_pipeline().reset_temporal_state(task_id)
        frame_budget_started_at = time.time()

        capture = cv2.VideoCapture(temp_path)
        if not capture.isOpened():
            raise ValueError("VIDEO_DECODE_FAILED")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if fps <= 0 or total_frames <= 0:
            raise ValueError("VIDEO_DECODE_FAILED")

        duration_sec = total_frames / fps
        if duration_sec < settings.VIDEO_MIN_DURATION_SECONDS:
            raise ValueError("VIDEO_TOO_SHORT")
        video_meta = GrowthVideoMeta(filename=filename, durationSec=round(duration_sec, 2))
        timestamps = _sample_timestamps(duration_sec)
        if not timestamps:
            raise ValueError("VIDEO_TOO_SHORT")
        planned_count = len(timestamps)
        _update_video_task(
            task_id,
            video=video_meta,
            stage="analyzing",
            plannedFrameCount=planned_count,
            progress=5,
        )

        frames: List[GrowthVideoFrameItem] = []
        partial = False
        warning_code: Optional[str] = None
        for processed_index, timestamp_index in enumerate(
            _prioritized_indices(planned_count), start=1
        ):
            if _is_video_cancel_requested(task_id):
                partial = True
                warning_code = "USER_CANCELLED"
                break

            elapsed = time.time() - frame_budget_started_at
            if elapsed >= settings.VIDEO_PROCESS_SOFT_LIMIT_SECONDS:
                partial = True
                warning_code = "PROCESS_TIMEOUT"
                break

            timestamp_sec = timestamps[timestamp_index]
            _update_video_task(
                task_id,
                stage="analyzing",
                progress=min(95, max(5, int((processed_index - 1) / planned_count * 100))),
            )
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
            success, frame = capture.read()
            if not success:
                print(f"[Growth][Video {task_id}] 关键帧解码失败 timestamp={timestamp_sec:.3f}")
                continue

            try:
                frame_detection_result = _detect_frame_payload(
                    frame,
                    stream_id=task_id,
                    frame_index=timestamp_index,
                    timestamp_sec=timestamp_sec,
                )
                display_base64 = _encode_frame_to_base64(frame, for_display=True)
                image_payload = frame_detection_result.get("image")
                if isinstance(image_payload, dict):
                    image_payload["src"] = f"data:image/jpeg;base64,{display_base64}"
                frame_item = _build_frame_item(
                    frame_id=f"frame-{timestamp_index + 1}",
                    timestamp_sec=timestamp_sec,
                    detection_result=frame_detection_result,
                    context=context,
                )
                frames.append(frame_item)
            except Exception as exc:
                print(
                    f"[Growth][Video {task_id}] 关键帧分析失败 "
                    f"timestamp={timestamp_sec:.3f}: {type(exc).__name__}: {exc}"
                )
            else:
                _update_video_task(
                    task_id,
                    completedFrameCount=len(frames),
                    evaluableFrameCount=sum(
                        frame.frameStatus == "evaluable" for frame in frames
                    ),
                    detectionOccurrenceCount=sum(
                        frame.stats.detectedCount for frame in frames
                    ),
                    measurableOccurrenceCount=sum(
                        frame.stats.measurableCount for frame in frames
                    ),
                    progress=min(
                        95, max(10, int(processed_index / planned_count * 100))
                    ),
                )

            # 单帧推理是同步调用，不能在不隔离模型进程的前提下安全强杀；
            # 因此最大时限在每次帧尝试返回后统一判定，且绝不再启动下一帧。
            if (
                time.time() - frame_budget_started_at
                >= settings.VIDEO_PROCESS_MAX_SECONDS
            ):
                partial = True
                warning_code = "PROCESS_TIMEOUT"
                break

        if not frames and warning_code == "USER_CANCELLED":
            _set_video_task(
                task_id,
                _build_video_result(
                    task_id,
                    "cancelled",
                    progress=100,
                    video=video_meta,
                    frames=[],
                    selected_frame_id=None,
                    error_code=None,
                    started_at=started_at,
                    created_at=created_at,
                    finished_at=time.time(),
                    stage="finalizing",
                    culture_month=context.culture_month,
                    stocking_avg_length_cm=context.stocking_avg_length_cm,
                    planned_frame_count=planned_count,
                    is_partial=False,
                    warning_code=warning_code,
                ),
            )
            return
        if not frames:
            raise ValueError("NO_VALID_FRAMES")

        frames.sort(key=lambda frame: frame.timestampSec)
        selected_frame = _select_default_video_frame(frames)
        is_cancelled = warning_code == "USER_CANCELLED"
        is_partial = partial or len(frames) < planned_count
        if len(frames) < planned_count and warning_code is None:
            warning_code = "PARTIAL_FRAME_FAILURE"
        _update_video_task(task_id, stage="finalizing", progress=98)
        _set_video_task(
            task_id,
            _build_video_result(
                task_id,
                "cancelled" if is_cancelled else "success",
                progress=100,
                video=video_meta,
                frames=frames,
                selected_frame_id=selected_frame.frameId if selected_frame else None,
                error_code=None,
                started_at=started_at,
                created_at=created_at,
                finished_at=time.time(),
                stage="finalizing",
                culture_month=context.culture_month,
                stocking_avg_length_cm=context.stocking_avg_length_cm,
                planned_frame_count=planned_count,
                is_partial=is_partial,
                warning_code=warning_code,
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
                frames=current.frames if current else [],
                selected_frame_id=current.selectedFrameId if current else None,
                error_code=str(exc) or "VIDEO_DECODE_FAILED",
                started_at=started_at,
                created_at=created_at,
                finished_at=time.time(),
                stage="finalizing",
                culture_month=current.cultureMonth if current else None,
                stocking_avg_length_cm=current.stockingAvgLengthCm if current else None,
                planned_frame_count=current.plannedFrameCount if current else 0,
                warning_code=str(exc) if str(exc) == "PROCESS_TIMEOUT" else None,
            ),
        )
    except Exception as exc:
        print(f"[Growth][Video {task_id}] 任务失败: {type(exc).__name__}: {exc}")
        current = _get_video_task(task_id)
        _set_video_task(
            task_id,
            _build_video_result(
                task_id,
                "failed",
                progress=100,
                video=current.video if current else None,
                frames=current.frames if current else [],
                selected_frame_id=current.selectedFrameId if current else None,
                error_code="INTERNAL_ERROR",
                started_at=started_at,
                created_at=created_at,
                finished_at=time.time(),
                stage="finalizing",
                culture_month=current.cultureMonth if current else None,
                stocking_avg_length_cm=current.stockingAvgLengthCm if current else None,
                planned_frame_count=current.plannedFrameCount if current else 0,
            ),
        )
    finally:
        if capture is not None:
            capture.release()
        if inference_acquired:
            _growth_inference_lock.release()
        with _video_task_lock:
            _video_cancel_requested.pop(task_id, None)
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
    if not _growth_inference_lock.acquire(blocking=False):
        return BaseResponse[GrowthDetectResponse](
            code=ERROR_CODE,
            msg="检测忙碌: GROWTH_INFERENCE_BUSY",
            data=_empty_detect_response(
                task_status="failed", error_code="GROWTH_INFERENCE_BUSY"
            ),
        )
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
    finally:
        _growth_inference_lock.release()


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


@router.post("/evaluate/video", response_model=BaseResponse[GrowthEvaluateVideoResponse])
def evaluate_growth_video(request: GrowthEvaluateVideoRequest):
    """轻量重评视频所有关键帧，不读取媒体、不运行模型。"""
    context = AssessmentContext(
        culture_month=request.cultureMonth,
        stocking_avg_length_cm=request.stockingAvgLengthCm,
    )
    frame_measurements = [
        [
            FishMeasurement(
                id=item.id,
                is_measurable=item.isMeasurable,
                body_length_cm=item.bodyLengthCm,
            )
            for item in frame.fishMeasurements
        ]
        for frame in request.frames
    ]
    try:
        evaluation = evaluate_video_measurements(frame_measurements, context)
    except GrowthStandardError as exc:
        print(f"[Growth] 视频轻量重评失败（保留前端上一次成功结果）：{exc}")
        return BaseResponse[GrowthEvaluateVideoResponse](
            code=ERROR_CODE,
            msg="生长评价配置暂时不可用",
            data=GrowthEvaluateVideoResponse(errorCode="EVALUATION_CONFIG_UNAVAILABLE"),
        )

    frame_results: List[GrowthVideoFrameEvaluationResponse] = []
    for frame_input, frame_evaluation in zip(
        request.frames, evaluation.frame_evaluations
    ):
        counts = frame_evaluation.status_counts
        stats = GrowthStats(
            small=counts.get("small", 0),
            normal=counts.get("normal", 0),
            large=counts.get("large", 0),
            unassessed=counts.get("unassessed", 0),
            detectedCount=len(frame_evaluation.fish),
            measurableCount=frame_evaluation.measurable_count,
            unmeasurableCount=frame_evaluation.unmeasurable_count,
        )
        frame_results.append(
            GrowthVideoFrameEvaluationResponse(
                frameId=frame_input.frameId,
                detections=[
                    GrowthEvaluatedFishItem(
                        id=item.id,
                        status=cast(GrowthStatus, item.status),
                        statusText=item.status_text,
                    )
                    for item in frame_evaluation.fish
                ],
                stats=stats,
                summary=GrowthSummary(
                    avgBodyLengthCm=round(
                        frame_evaluation.all_measurable_avg_length_cm or 0, 1
                    ),
                    avgWeightG=0,
                ),
                assessment=_to_assessment(frame_evaluation),
                frameStatus=(
                    "evaluable"
                    if frame_evaluation.trimmed_mean_length_cm is not None
                    else (
                        "insufficient_sample"
                        if stats.detectedCount > 0
                        else "no_valid_detection"
                    )
                ),
            )
        )

    return BaseResponse[GrowthEvaluateVideoResponse](
        code=SUCCESS_CODE,
        msg="视频评价已更新",
        data=GrowthEvaluateVideoResponse(
            frames=frame_results,
            assessment=_to_video_assessment(evaluation),
            summary=GrowthSummary(
                avgBodyLengthCm=round(evaluation.video_length_cm or 0, 1),
                avgWeightG=round(_estimate_weight(evaluation.video_length_cm or 0), 1),
            ),
            errorCode=None,
        ),
    )


@router.post("/detect/video", response_model=BaseResponse[GrowthVideoDetectCreateResponse])
async def create_growth_video_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    cultureMonth: Optional[int] = Form(None),
    stockingAvgLengthCm: Optional[float] = Form(None),
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
    created_at = time.time()
    initial_video = GrowthVideoMeta(filename=filename, durationSec=0)
    with _video_task_lock:
        _video_cancel_requested[task_id] = False
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
            created_at=created_at,
            culture_month=cultureMonth,
            stocking_avg_length_cm=stockingAvgLengthCm,
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
        "cancelled": "视频识别已取消",
    }[task.taskStatus]
    return BaseResponse[GrowthVideoDetectResultResponse](
        code=SUCCESS_CODE,
        msg=status_message,
        data=task,
    )


@router.post(
    "/detect/video/{task_id}/cancel",
    response_model=BaseResponse[GrowthVideoDetectResultResponse],
)
def cancel_growth_video_task(task_id: str):
    """请求协作式取消：当前帧完成后不再启动下一帧。"""
    task = _get_video_task(task_id)
    if task is None:
        return BaseResponse[GrowthVideoDetectResultResponse](
            code=ERROR_CODE,
            msg="视频任务不存在: INTERNAL_ERROR",
            data=_build_video_result(task_id, "failed", error_code="INTERNAL_ERROR"),
        )
    if task.taskStatus in {"success", "failed", "cancelled"}:
        return BaseResponse[GrowthVideoDetectResultResponse](
            code=SUCCESS_CODE,
            msg="视频任务已结束",
            data=task,
        )
    with _video_task_lock:
        _video_cancel_requested[task_id] = True
    if task.taskStatus == "queued":
        cancelled = task.model_copy(
            update={
                "taskStatus": "cancelled",
                "progress": 100,
                "warningCode": "USER_CANCELLED",
                "finishedAt": time.time(),
            }
        )
        _set_video_task(task_id, cancelled)
    return BaseResponse[GrowthVideoDetectResultResponse](
        code=SUCCESS_CODE,
        msg="已请求取消视频识别",
        data=_get_video_task(task_id) or task,
    )


@router.delete(
    "/detect/video/{task_id}",
    response_model=BaseResponse[GrowthVideoDetectResultResponse],
)
def delete_growth_video_task(task_id: str):
    """只释放终态任务的内存结果，活动任务必须先取消。"""
    with _video_task_lock:
        task = _video_tasks.get(task_id)
        if task is None:
            return BaseResponse[GrowthVideoDetectResultResponse](
                code=ERROR_CODE,
                msg="视频任务不存在: INTERNAL_ERROR",
                data=_build_video_result(task_id, "failed", error_code="INTERNAL_ERROR"),
            )
        if task.taskStatus not in {"success", "failed", "cancelled"}:
            return BaseResponse[GrowthVideoDetectResultResponse](
                code=ERROR_CODE,
                msg="活动视频任务需先取消",
                data=task,
            )
        del _video_tasks[task_id]
        _video_cancel_requested.pop(task_id, None)
        print(f"[Growth] 清理视频任务 {task_id}：用户主动释放终态结果")
    return BaseResponse[GrowthVideoDetectResultResponse](
        code=SUCCESS_CODE,
        msg="视频任务已释放",
        data=task,
    )


@router.get("/camera/stream", response_model=BaseResponse[str])
def get_camera_stream():
    return BaseResponse[str](
        code=SUCCESS_CODE,
        msg="获取成功",
        data="http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8",
    )
