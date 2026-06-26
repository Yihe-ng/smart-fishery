import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

ultralytics_stub = types.ModuleType("ultralytics")


class _FakeYOLO:
    def __init__(self, *args, **kwargs):
        pass


ultralytics_stub.YOLO = _FakeYOLO
sys.modules.setdefault("ultralytics", ultralytics_stub)

from app.main import app


class ManualFeedingSecurityTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_preview_returns_structured_fields_for_execute(self):
        response = self.client.post(
            "/api/agent/actions/manual-feeding/preview",
            json={"pondId": "pond-001", "amount": 600},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["actionType"], "manual_feeding_preview")
        self.assertEqual(payload["amount"], 600)
        self.assertEqual(payload["feederId"], "feeder-001")
        self.assertEqual(payload["duration"], 10)
        self.assertEqual(payload["pondId"], "pond-001")
        self.assertIn("confirmToken", payload)
        self.assertIn("expiresAt", payload)
        self.assertIn("previewText", payload)

    def test_execute_rejects_missing_confirm_token(self):
        response = self.client.post(
            "/api/feeding/execute",
            json={"feederId": "feeder-001", "amount": 600, "duration": 10},
        )

        self.assertEqual(response.status_code, 422)

    def test_execute_rejects_invalid_confirm_token(self):
        response = self.client.post(
            "/api/feeding/execute",
            json={
                "confirmToken": "preview-invalid",
                "feederId": "feeder-001",
                "amount": 600,
                "duration": 10,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("无效", response.json()["detail"])

    def test_execute_rejects_tampered_amount(self):
        preview_response = self.client.post(
            "/api/agent/actions/manual-feeding/preview",
            json={"pondId": "pond-001", "amount": 600},
        )
        preview = preview_response.json()["data"]

        response = self.client.post(
            "/api/feeding/execute",
            json={
                "confirmToken": preview["confirmToken"],
                "feederId": preview["feederId"],
                "amount": 700,
                "duration": preview["duration"],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("参数", response.json()["detail"])

    def test_execute_uses_preview_snapshot_and_prevents_replay(self):
        preview_response = self.client.post(
            "/api/agent/actions/manual-feeding/preview",
            json={"pondId": "pond-001", "amount": 600},
        )
        preview = preview_response.json()["data"]

        with patch(
            "app.api.v1.endpoints.feeding.smart_feeding_service.execute_feeding",
            new=AsyncMock(
                return_value={
                    "success": True,
                    "feeder_id": "feeder-001",
                    "amount": 600,
                    "duration": 10,
                    "status": "command_sent",
                }
            ),
        ) as execute_mock:
            response = self.client.post(
                "/api/feeding/execute",
                json={
                    "confirmToken": preview["confirmToken"],
                    "feederId": preview["feederId"],
                    "amount": preview["amount"],
                    "duration": preview["duration"],
                },
            )

            self.assertEqual(response.status_code, 200)
            execute_mock.assert_awaited_once_with(
                feeder_id="feeder-001",
                amount=600,
                duration=10,
            )

            replay_response = self.client.post(
                "/api/feeding/execute",
                json={
                    "confirmToken": preview["confirmToken"],
                    "feederId": preview["feederId"],
                    "amount": preview["amount"],
                    "duration": preview["duration"],
                },
            )

        self.assertEqual(replay_response.status_code, 400)
        self.assertIn("已执行", replay_response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
