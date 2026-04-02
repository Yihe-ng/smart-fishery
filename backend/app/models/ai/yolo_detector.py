import base64
import io
from typing import Any, Dict, List

from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 12_000_000
DEFAULT_CONFIDENCE = 0.1
MIME_BY_FORMAT = {
    "JPEG": "image/jpeg",
    "JPG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "BMP": "image/bmp",
}


class YOLODetector:
    """Wraps YOLO image inference for growth detection."""

    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        self.model.conf = DEFAULT_CONFIDENCE

    def detect(self, image_base64: str) -> Dict[str, Any]:
        image_data = self._decode_image_data(image_base64)
        image = self._load_image(image_data)

        if image.mode != "RGB":
            image = image.convert("RGB")

        results = self.model(image, conf=DEFAULT_CONFIDENCE)
        detections: List[Dict[str, Any]] = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                width = float(x2 - x1)
                height = float(y2 - y1)
                detections.append(
                    {
                        "class_name": result.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "bbox": [float(x1), float(y1), width, height],
                        "length": width,
                    }
                )

        return {
            "image": {
                "src": self._build_data_url(image_base64, image.format),
                "width": image.width,
                "height": image.height,
            },
            "detections": detections,
        }

    def _decode_image_data(self, image_base64: str) -> bytes:
        try:
            image_data = base64.b64decode(image_base64, validate=True)
        except Exception as exc:
            raise ValueError("IMAGE_DECODE_FAILED") from exc

        if not image_data:
            raise ValueError("INVALID_IMAGE")
        if len(image_data) > MAX_IMAGE_BYTES:
            raise ValueError("IMAGE_TOO_LARGE")
        return image_data

    def _load_image(self, image_data: bytes) -> Image.Image:
        try:
            image = Image.open(io.BytesIO(image_data))
            image.load()
        except UnidentifiedImageError as exc:
            raise ValueError("INVALID_IMAGE") from exc
        except Exception as exc:
            raise ValueError("IMAGE_DECODE_FAILED") from exc

        if image.width <= 0 or image.height <= 0:
            raise ValueError("INVALID_IMAGE")
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise ValueError("IMAGE_TOO_LARGE")
        return image

    def _build_data_url(self, image_base64: str, image_format: str | None) -> str:
        mime_type = MIME_BY_FORMAT.get((image_format or "").upper(), "image/png")
        return f"data:{mime_type};base64,{image_base64}"
