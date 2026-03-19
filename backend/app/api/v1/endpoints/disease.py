# 修改 backend/app/api/v1/endpoints/disease.py
from fastapi import APIRouter
from app.schemas.base import BaseResponse
from pydantic import BaseModel
from typing import List, Optional
from app.models.ai.yolo_detector import YOLODetector
import os

# 确保 router 变量被正确定义
router = APIRouter()

# 使用绝对路径加载模型
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, '..', '..', '..', 'models', 'ai', 'best.pt')

print(f"Model path: {model_path}")
print(f"File exists: {os.path.exists(model_path)}")

detector = YOLODetector(model_path)


class DetectionRequest(BaseModel):
    """鱼长检测请求模型"""
    image: str  # base64 编码的图片数据


class DetectionItem(BaseModel):
    """检测结果项"""
    class_name: str  # 类别
    confidence: float  # 置信度
    bbox: List[float]  # 边界框坐标 [x, y, width, height]
    length: float  # 鱼的长度（像素）


class DetectionResponse(BaseModel):
    """鱼长检测响应模型"""
    detections: List[DetectionItem]


@router.post("/detect", response_model=BaseResponse[DetectionResponse])
def detect_fish(request: DetectionRequest):
    """鱼长检测接口"""
    # 使用 AI 模型进行检测
    try:
        detections = detector.detect(request.image)
        return BaseResponse[DetectionResponse](
            code=200,
            msg="检测成功",
            data=DetectionResponse(detections=detections)
        )
    except Exception as e:
        return BaseResponse[DetectionResponse](
            code=500,
            msg=f"检测失败: {str(e)}",
            data=DetectionResponse(detections=[])
        )


@router.get("/camera/stream", response_model=BaseResponse[str])
def get_camera_stream():
    """获取摄像头视频流"""
    # 返回一个公共的 HLS 测试流，用于前端展示
    return BaseResponse[str](
        code=200,
        msg="获取成功",
        data="http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8"
    )