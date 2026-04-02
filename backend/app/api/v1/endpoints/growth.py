import base64
import math
import os
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from pydantic import BaseModel

from app.models.ai.yolo_detector import YOLODetector
from app.schemas.base import BaseResponse
from app.schemas.growth import (
    GrowthDetectResponse,
    GrowthDetectionBBox,
    GrowthDetectionItem,
    GrowthImageMeta,
    GrowthStats,
    GrowthSummary,
    GrowthVideoDetectCreateResponse,
    GrowthVideoDetectResultResponse,
    GrowthVideoFrameItem,
    GrowthVideoMeta,
)

router = APIRouter()

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
_video_task_lock = threading.Lock()
_video_tasks: Dict[str, GrowthVideoDetectResultResponse] = {}


class DetectionRequest(BaseModel):
    image: str


def get_detector() -> YOLODetector:
    global _detector
    if _detector is None:
        print(f"[Growth] Loading model from: {MODEL_PATH}")
        _detector = YOLODetector(MODEL_PATH)
    return _detector


def _detect_payload(image_base64: str) -> Dict[str, object]:
    with _detector_lock:
        return get_detector().detect(image_base64)


def _map_status(class_name: str) -> Tuple[str, str]:
    normalized = class_name.lower()
    if normalized == "small":
        return "small", "偏小"
    if normalized in {"medium", "normal"}:
        return "normal", "正常"
    if normalized == "large":
        return "large", "偏大"
    return "normal", "正常"


def _estimate_weight(length_cm: float) -> float:
    if length_cm <= 0:
        return 0
    weight = GROUPER_WEIGHT_COEF_A * math.pow(length_cm, GROUPER_WEIGHT_COEF_B)
    return round(weight, 1)


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
) -> List[GrowthDetectionItem]:
    center_x = image_meta["width"] / 2
    center_y = image_meta["height"] / 2
    sortable_items = []

    for detection in raw_detections:
        bbox = detection.get("bbox")
        if not isinstance(bbox, list) or not _is_valid_detection(bbox, image_meta):
            continue

        x, y, width, height = [float(value) for value in bbox]
        status, status_text = _map_status(str(detection.get("class_name", "")))
        body_length_cm = round(float(detection.get("length", 0)) * CM_PER_PIXEL, 1)
        weight_g = _estimate_weight(body_length_cm)
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
                "label_text": f"{status_text} | {body_length_cm}cm",
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
        )
        for index, item in enumerate(sortable_items, start=1)
    ]


def _build_stats(detections: List[GrowthDetectionItem]) -> GrowthStats:
    stats = GrowthStats(detectedCount=len(detections))
    for detection in detections:
        setattr(stats, detection.status, getattr(stats, detection.status) + 1)
    return stats


def _build_summary(detections: List[GrowthDetectionItem]) -> GrowthSummary:
    if not detections:
        return GrowthSummary()
    avg_length = round(
        sum(detection.bodyLengthCm for detection in detections) / len(detections), 1
    )
    avg_weight = round(sum(detection.weightG for detection in detections) / len(detections), 1)
    return GrowthSummary(avgBodyLengthCm=avg_length, avgWeightG=avg_weight)


def _build_detect_response(
    detection_result: Dict[str, object],
    task_status: str = "success",
    error_code: Optional[str] = None,
) -> GrowthDetectResponse:
    image_payload = detection_result["image"]
    raw_detections = detection_result["detections"]
    image_meta_dict = {
        "src": str(image_payload["src"]),
        "width": int(image_payload["width"]),
        "height": int(image_payload["height"]),
    }
    image = GrowthImageMeta(**image_meta_dict)
    detections = _build_detection_items(raw_detections, image_meta_dict)

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

    return GrowthDetectResponse(
        taskStatus=task_status,
        image=image,
        detections=detections,
        selectedDetectionId=detections[0].id,
        stats=_build_stats(detections),
        summary=_build_summary(detections),
        errorCode=error_code,
    )


def _build_frame_item(
    frame_id: str,
    timestamp_sec: int,
    detection_result: Dict[str, object],
) -> GrowthVideoFrameItem:
    frame_response = _build_detect_response(detection_result)
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
        _video_tasks[task_id] = payload


def _get_video_task(task_id: str) -> Optional[GrowthVideoDetectResultResponse]:
    with _video_task_lock:
        return _video_tasks.get(task_id)


def _update_video_task(task_id: str, **updates) -> None:
    with _video_task_lock:
        current = _video_tasks.get(task_id)
        if current is None:
            return
        _video_tasks[task_id] = current.model_copy(update=updates)


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
            frame_detection_result = _detect_payload(frame_base64)
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
        response_data = _build_detect_response(detection_result)

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
