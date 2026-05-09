import base64
import io

from PIL import Image

from app.api.v1.endpoints import growth


def _make_image_base64(size=(32, 24), color=(0, 128, 255)) -> str:
    image = Image.new("RGB", size, color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


class _StubDetector:
    def __init__(self, detections):
        self._detections = detections

    def detect(self, image_base64: str):
        filled = []
        for d in self._detections:
            detection = dict(d)
            if "mask_polygons" not in detection:
                detection["mask_polygons"] = None
            filled.append(detection)
        return {
            "image": {
                "src": f"data:image/png;base64,{image_base64}",
                "width": 32,
                "height": 24,
            },
            "detections": filled,
        }


def test_detect_fish_returns_ranked_display_payload(monkeypatch):
    image_base64 = _make_image_base64()
    stub_detections = [
        {
            "class_name": "fish",
            "confidence": 0.91,
            "bbox": [2, 3, 18, 8],
            "length": 300,
            "mask_polygons": None,
        },
        {
            "class_name": "fish",
            "confidence": 0.82,
            "bbox": [10, 10, 9, 5],
            "length": 100,
            "mask_polygons": None,
        },
    ]
    monkeypatch.setattr(growth, "get_detector", lambda: _StubDetector(stub_detections))

    response = growth.detect_fish(growth.DetectionRequest(image=image_base64))

    assert response.code == 200
    assert response.data.taskStatus == "success"
    assert response.data.image.width == 32
    assert response.data.selectedDetectionId == "fish-1"
    assert len(response.data.detections) == 2
    assert response.data.detections[0].id == "fish-1"
    assert response.data.detections[0].index == 1
    assert response.data.detections[0].status == "large"
    assert response.data.detections[0].statusText
    assert response.data.detections[0].labelText.endswith("cm")
    assert response.data.stats.large == 1
    assert response.data.stats.small == 1
    assert response.data.stats.detectedCount == 2
    assert response.data.summary.avgBodyLengthCm > 0
    assert response.data.summary.avgWeightG > 0
    assert response.data.errorCode is None


def test_detect_fish_returns_success_for_no_fish(monkeypatch):
    image_base64 = _make_image_base64()
    monkeypatch.setattr(growth, "get_detector", lambda: _StubDetector([]))

    response = growth.detect_fish(growth.DetectionRequest(image=image_base64))

    assert response.code == 200
    assert response.data.taskStatus == "success"
    assert response.data.errorCode == "NO_FISH_DETECTED"
    assert response.data.selectedDetectionId is None
    assert len(response.data.detections) == 0
    assert response.data.stats.detectedCount == 0


def test_detect_fish_returns_failed_payload_on_invalid_image(monkeypatch):
    class _FailingDetector:
        def detect(self, image_base64: str):
            raise ValueError("IMAGE_DECODE_FAILED")

    monkeypatch.setattr(growth, "get_detector", lambda: _FailingDetector())

    response = growth.detect_fish(growth.DetectionRequest(image="bad-image"))

    assert response.code == 500
    assert response.data.taskStatus == "failed"
    assert response.data.errorCode == "IMAGE_DECODE_FAILED"
    assert len(response.data.detections) == 0


def test_sample_timestamps_limits_growth_video_frames():
    timestamps = growth._sample_timestamps(30.4)

    assert timestamps == list(range(12))


def test_build_video_result_aggregates_frame_detections(monkeypatch):
    image_base64 = _make_image_base64()
    monkeypatch.setattr(
        growth,
        "get_detector",
        lambda: _StubDetector(
            [
                {
                    "class_name": "fish",
                    "confidence": 0.85,
                    "bbox": [2, 3, 18, 8],
                    "length": 200,
                    "mask_polygons": None,
                }
            ]
        ),
    )

    frame_with_fish = growth._build_frame_item(
        "frame-1",
        0,
        {
            "image": {
                "src": f"data:image/png;base64,{image_base64}",
                "width": 32,
                "height": 24,
            },
            "detections": [
                {
                    "class_name": "fish",
                    "confidence": 0.85,
                    "bbox": [2, 3, 18, 8],
                    "length": 200,
                    "mask_polygons": None,
                }
            ],
        },
    )
    empty_frame = growth.GrowthVideoFrameItem(
        frameId="frame-2",
        timestampSec=1,
        image=frame_with_fish.image,
        detections=[],
        selectedDetectionId=None,
        stats=growth.GrowthStats(),
        summary=growth.GrowthSummary(),
    )

    result = growth._build_video_result(
        "task-1",
        "success",
        progress=100,
        video=growth.GrowthVideoMeta(filename="demo.mp4", durationSec=3.0),
        frames=[frame_with_fish, empty_frame],
        selected_frame_id="frame-1",
    )

    assert result.taskId == "task-1"
    assert result.taskStatus == "success"
    assert result.selectedFrameId == "frame-1"
    assert len(result.frames) == 2
    assert result.aggregateStats.detectedCount == 1
    assert result.aggregateStats.normal == 1
    assert result.aggregateSummary.avgBodyLengthCm > 0


def test_detect_fish_passes_mask_polygons_in_response(monkeypatch):
    image_base64 = _make_image_base64()
    sample_polygon = [[0.1, 0.2], [0.3, 0.2], [0.3, 0.4], [0.1, 0.4]]
    stub_detections = [
        {
            "class_name": "fish",
            "confidence": 0.88,
            "bbox": [2, 3, 18, 8],
            "length": 200,
            "mask_polygons": sample_polygon,
        },
    ]
    monkeypatch.setattr(growth, "get_detector", lambda: _StubDetector(stub_detections))

    response = growth.detect_fish(growth.DetectionRequest(image=image_base64))

    assert response.code == 200
    assert len(response.data.detections) == 1
    detection = response.data.detections[0]
    assert len(detection.maskPolygons) == 4
    assert detection.maskPolygons[0][0] == 0.1
    assert detection.maskPolygons[0][1] == 0.2


def test_build_frame_item_preserves_mask_polygons(monkeypatch):
    image_base64 = _make_image_base64()
    sample_polygon = [[0.5, 0.6], [0.7, 0.6], [0.7, 0.8], [0.5, 0.8]]
    monkeypatch.setattr(
        growth, "get_detector",
        lambda: _StubDetector([{
            "class_name": "fish",
            "confidence": 0.9,
            "bbox": [5, 5, 20, 10],
            "length": 200,
            "mask_polygons": sample_polygon,
        }]),
    )
    detection_result = {
        "image": {"src": f"data:image/png;base64,{image_base64}", "width": 32, "height": 24},
        "detections": [{
            "class_name": "fish",
            "confidence": 0.9,
            "bbox": [5, 5, 20, 10],
            "length": 200,
            "mask_polygons": sample_polygon,
        }],
    }

    frame = growth._build_frame_item("f1", 3, detection_result)

    assert len(frame.detections) == 1
    assert len(frame.detections[0].maskPolygons) == 4
    assert frame.detections[0].maskPolygons == sample_polygon


def test_video_task_store_cleans_expired_tasks(monkeypatch):
    monkeypatch.setattr(growth, "VIDEO_TASK_TTL_SECONDS", 60)
    monkeypatch.setattr(growth.time, "time", lambda: 1_000.0)
    growth._video_tasks.clear()

    expired_task = growth._build_video_result(
        "expired-task",
        "success",
        progress=100,
        video=growth.GrowthVideoMeta(filename="old.mp4", durationSec=2.0),
        started_at=900.0,
    )
    current_task = growth._build_video_result(
        "current-task",
        "queued",
        progress=0,
        video=growth.GrowthVideoMeta(filename="new.mp4", durationSec=0),
        started_at=990.0,
    )

    try:
        growth._set_video_task("expired-task", expired_task)
        growth._set_video_task("current-task", current_task)

        assert growth._get_video_task("expired-task") is None
        assert growth._get_video_task("current-task") is not None
    finally:
        growth._video_tasks.clear()
