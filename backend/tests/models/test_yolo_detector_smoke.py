import base64
from pathlib import Path

import numpy as np
import pytest

from app.models.ai.yolo_detector import YOLODetector


MODEL_PATH = Path(__file__).resolve().parents[2] / "app" / "models" / "ai" / "best.pt"
ANNOTATED_IMAGE_PATH = Path(
    r"D:\文件\易找的文件\智慧渔业\图片标注\41-80\00041.jpg"
)


@pytest.mark.slow
def test_real_segmentation_model_returns_mask_polygons_for_annotated_image():
    if not MODEL_PATH.exists():
        pytest.skip(f"Model file not found: {MODEL_PATH}")
    if not ANNOTATED_IMAGE_PATH.exists():
        pytest.skip(f"Annotated smoke-test image not found: {ANNOTATED_IMAGE_PATH}")

    image_base64 = base64.b64encode(ANNOTATED_IMAGE_PATH.read_bytes()).decode("utf-8")
    result = YOLODetector(str(MODEL_PATH)).detect(image_base64)

    detections = result["detections"]
    assert detections
    assert any(detection.get("mask_polygons") for detection in detections)

    first_detection = detections[0]
    assert len(first_detection["bbox"]) == 4
    assert first_detection["confidence"] > 0
    assert first_detection["length"] > 0

    polygon = next(
        detection["mask_polygons"]
        for detection in detections
        if detection.get("mask_polygons")
    )
    assert polygon
    assert all(0 <= point[0] <= 1 and 0 <= point[1] <= 1 for point in polygon)


def test_clean_mask_polygon_keeps_largest_external_contour():
    mask = np.zeros((24, 32), dtype=np.uint8)
    mask[4:18, 5:24] = 1
    mask[1:4, 27:30] = 1

    normalized, pixel = YOLODetector._extract_clean_mask_polygon(mask, 32, 24)

    assert normalized is not None
    assert pixel is not None
    assert len(normalized) >= 4
    assert all(0 <= point[0] <= 1 and 0 <= point[1] <= 1 for point in normalized)
    x_values = [point[0] for point in pixel]
    y_values = [point[1] for point in pixel]
    assert min(x_values) == 5
    assert max(x_values) == 23
    assert min(y_values) == 4
    assert max(y_values) == 17
