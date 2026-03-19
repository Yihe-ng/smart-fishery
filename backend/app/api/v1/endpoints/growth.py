from fastapi import APIRouter
from app.schemas.base import BaseResponse
from pydantic import BaseModel
from typing import List, Optional
from app.models.ai.yolo_detector import YOLODetector
import os

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

_detector: Optional[YOLODetector] = None


def get_detector() -> YOLODetector:
    global _detector
    if _detector is None:
        print(f"[Growth] Loading model from: {MODEL_PATH}")
        _detector = YOLODetector(MODEL_PATH)
    return _detector


class DetectionRequest(BaseModel):
    image: str


class DetectionItem(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]
    length: float


class DetectionResponse(BaseModel):
    detections: List[DetectionItem]


@router.post("/detect", response_model=BaseResponse[DetectionResponse])
def detect_fish(request: DetectionRequest):
    try:
        detector = get_detector()
        raw_detections = detector.detect(request.image)
        detections = [DetectionItem(**d) for d in raw_detections]
        return BaseResponse[DetectionResponse](
            code=200, msg="检测成功", data=DetectionResponse(detections=detections)
        )
    except Exception as e:
        return BaseResponse[DetectionResponse](
            code=500, msg=f"检测失败: {str(e)}", data=DetectionResponse(detections=[])
        )


@router.get("/camera/stream", response_model=BaseResponse[str])
def get_camera_stream():
    return BaseResponse[str](
        code=200,
        msg="获取成功",
        data="http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8",
    )
