import sys
import types
import unittest

from fastapi.testclient import TestClient

ultralytics_stub = types.ModuleType("ultralytics")


class _FakeYOLO:
    def __init__(self, *args, **kwargs):
        pass


ultralytics_stub.YOLO = _FakeYOLO
sys.modules.setdefault("ultralytics", ultralytics_stub)

from app.main import app
from app.services.water_quality_dashboard import (
    evaluate_metric_status,
    format_trend_text,
    get_threshold_config,
)


class WaterQualityThresholdServiceTestCase(unittest.TestCase):
    def test_evaluate_metric_status_returns_chinese_levels(self):
        self.assertEqual(evaluate_metric_status("temperature", 27.0), "正常")
        self.assertEqual(evaluate_metric_status("temperature", 31.0), "警戒")
        self.assertEqual(evaluate_metric_status("temperature", 34.0), "危险")
        self.assertEqual(evaluate_metric_status("dissolved_oxygen", 5.8), "正常")
        self.assertEqual(evaluate_metric_status("dissolved_oxygen", 3.5), "警戒")
        self.assertEqual(evaluate_metric_status("dissolved_oxygen", 2.5), "危险")

    def test_threshold_config_contains_ideal_warning_and_critical_ranges(self):
        thresholds = get_threshold_config()

        self.assertIn("temperature", thresholds)
        self.assertIn("ideal", thresholds["temperature"])
        self.assertIn("warning", thresholds["temperature"])
        self.assertIn("critical", thresholds["temperature"])

    def test_format_trend_text_uses_expected_copy(self):
        self.assertEqual(format_trend_text(None, 1.23), "趋势 --")
        self.assertEqual(format_trend_text(1.0, 1.0), "趋势 持平")
        self.assertEqual(format_trend_text(1.0, 1.2), "趋势 +0.2")
        self.assertEqual(format_trend_text(1.2, 1.0), "趋势 -0.2")


class WaterQualityDashboardFrameApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_dashboard_frame_starts_from_first_record(self):
        response = self.client.get("/api/water-quality/dashboard-frame", params={"index": 0})

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]

        self.assertEqual(payload["index"], 0)
        self.assertEqual(payload["nextIndex"], 1)
        self.assertGreater(payload["total"], 0)
        self.assertIsNone(payload["previousWaterQuality"])
        self.assertEqual(payload["collectTime"], "2026-02-10 08:00:00")
        self.assertEqual(payload["waterQuality"]["temperature"], 27.2)
        self.assertEqual(payload["metrics"]["temperature"]["statusText"], "正常")
        self.assertEqual(len(payload["devices"]), 5)
        self.assertTrue(all(device["status"] == "online" for device in payload["devices"]))

    def test_dashboard_frame_wraps_back_to_first_record(self):
        first_response = self.client.get("/api/water-quality/dashboard-frame", params={"index": 0})
        first_payload = first_response.json()["data"]
        wrapped_response = self.client.get("/api/water-quality/dashboard-frame", params={"index": 39})

        self.assertEqual(wrapped_response.status_code, 200)
        wrapped_payload = wrapped_response.json()["data"]

        self.assertEqual(wrapped_payload["index"], 0)
        self.assertEqual(wrapped_payload["collectTime"], first_payload["collectTime"])
        self.assertEqual(
            wrapped_payload["waterQuality"]["temperature"], first_payload["waterQuality"]["temperature"]
        )

    def test_dashboard_frame_exposes_previous_record_and_alerts(self):
        response = self.client.get("/api/water-quality/dashboard-frame", params={"index": 6})

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]

        self.assertEqual(payload["index"], 6)
        self.assertIsNotNone(payload["previousWaterQuality"])
        self.assertEqual(payload["collectTime"], "2026-02-10 14:00:00")
        self.assertEqual(payload["metrics"]["dissolvedOxygen"]["statusText"], "危险")
        self.assertTrue(all(device["status"] == "online" for device in payload["devices"]))
        self.assertGreaterEqual(len(payload["alerts"]), 1)
        self.assertTrue(any("溶氧" in alert["title"] for alert in payload["alerts"]))


if __name__ == "__main__":
    unittest.main()
