from fastapi import APIRouter
from app.schemas.base import BaseResponse
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class DetectionRequest(BaseModel):
    """病害检测请求模型"""
    image: str  # base64 编码的图片数据


class DetectionItem(BaseModel):
    """检测结果项"""
    class_name: str  # 病害类型
    confidence: float  # 置信度
    bbox: List[float]  # 边界框坐标 [x, y, width, height]


class DetectionResponse(BaseModel):
    """病害检测响应模型"""
    detections: List[DetectionItem]


# 模拟检测结果
mock_detection_result = {
    "detections": [
        {
            "class_name": "烂鳃",
            "confidence": 0.94,
            "bbox": [100, 100, 200, 200]
        }
    ]
}


@router.post("/detect", response_model=BaseResponse[DetectionResponse])
def detect_disease(request: DetectionRequest):
    """病害检测接口"""
    # TODO: 实际项目中，这里应该调用 AI 模型进行检测
    # 例如：result = ai_model.detect(request.image)
    
    return BaseResponse[DetectionResponse](
        code=200,
        msg="检测成功",
        data=DetectionResponse(**mock_detection_result)
    )


@router.get("/camera/stream", response_model=BaseResponse[str])
def get_camera_stream():
    """获取摄像头视频流"""
    # TODO: 实际项目中，这里应该返回真实的摄像头流地址
    # 例如：从摄像头厂商提供的 RTSP 流转码为 HLS 流
    # 或者使用流媒体服务器（如 Nginx-RTMP、SRS、ZLMediaKit）
    
    # 返回一个公共的 HLS 测试流，用于前端展示
    return BaseResponse[str](
        code=200,
        msg="获取成功",
        data="http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8"
    )
