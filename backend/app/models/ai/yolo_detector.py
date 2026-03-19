# 修改 backend/app/models/ai/yolo_detector.py
from ultralytics import YOLO
from PIL import Image
import numpy as np
import base64
import io
from typing import List, Dict, Any

class YOLODetector:
    """鱼长检测模型"""
    
    def __init__(self, model_path: str):
        """初始化模型"""
        # 使用本地 ultralytics 库加载模型
        self.model = YOLO(model_path)
        # 设置置信度阈值
        self.model.conf = 0.25
    
    def detect(self, image_base64: str) -> List[Dict[str, Any]]:
        """检测鱼并测量长度"""
        # 解码 base64 图片
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # 转换为 RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 进行检测
        results = self.model(image)
        
        # 处理检测结果
        detections = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                conf = box.conf[0]
                cls = box.cls[0]
                class_name = result.names[int(cls)]
                
                # 计算鱼的长度（像素）
                length = float(x2 - x1)
                
                detections.append({
                    "class_name": class_name,
                    "confidence": float(conf),
                    "bbox": [float(x1), float(y1), float(x2 - x1), float(y2 - y1)],
                    "length": length
                })
        
        return detections