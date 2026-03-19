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
        self.model = YOLO(model_path)
        self.model.conf = 0.1

    def detect(self, image_base64: str) -> List[Dict[str, Any]]:
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))

        print(f"[Detector] Image size: {image.size}, mode: {image.mode}")

        if image.mode != "RGB":
            image = image.convert("RGB")

        results = self.model(image, conf=0.1)

        print(f"[Detector] Results count: {len(results)}")
        print(f"[Detector] Boxes in result[0]: {len(results[0].boxes)}")

        detections = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                conf = box.conf[0]
                cls = box.cls[0]
                class_name = result.names[int(cls)]

                # 计算鱼的长度（像素）
                length = float(x2 - x1)

                detections.append(
                    {
                        "class_name": class_name,
                        "confidence": float(conf),
                        "bbox": [float(x1), float(y1), float(x2 - x1), float(y2 - y1)],
                        "length": length,
                    }
                )

        return detections
