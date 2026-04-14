import sys
import types
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.modules.setdefault("ultralytics", types.SimpleNamespace(YOLO=object))

from app.main import app


class AIRoutesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_bootstrap_returns_environment_mode_and_allowed_tools(self):
        response = self.client.post(
            "/api/agent/agent/bootstrap",
            json={
                "pageId": "feeding",
                "routePath": "/fishery/feeding",
                "pondId": "pond-001",
                "selection": {"tab": "overview"},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["environmentMode"], "real")
        self.assertIn("systemInstructions", payload)
        self.assertIn("pageInstructions", payload)
        self.assertIn("preview_manual_feeding_action", payload["allowedTools"])
        self.assertTrue(payload["uiCapabilities"]["showSuggestionPanel"])
        self.assertTrue(payload["uiCapabilities"]["canExecute"])

    def test_context_changes_when_page_changes(self):
        response = self.client.post(
            "/api/agent/agent/context",
            json={
                "pageId": "water-quality",
                "routePath": "/fishery/water-quality",
                "pondId": "pond-002",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["currentPage"]["pageId"], "water-quality")
        self.assertEqual(payload["pond"]["pondId"], "pond-002")
        self.assertEqual(payload["sourceMode"], "real")
        self.assertIn("contextVersion", payload)

    def test_feeding_suggestions_include_metadata(self):
        response = self.client.post(
            "/api/agent/suggestions/feeding",
            json={"pageId": "feeding", "routePath": "/fishery/feeding", "pondId": "pond-001"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertGreaterEqual(len(payload["cards"]), 1)
        first_card = payload["cards"][0]
        self.assertEqual(first_card["sourceMode"], "real")
        self.assertIn("updatedAt", first_card)
        self.assertIn("panelState", payload)

    def test_manual_feeding_preview_returns_preview_payload(self):
        response = self.client.post(
            "/api/agent/actions/manual-feeding/preview",
            json={"pondId": "pond-001", "amount": 600},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["mode"], "real")
        self.assertEqual(payload["actionType"], "manual_feeding_preview")
        self.assertIn("confirmToken", payload)
        self.assertIn("previewText", payload)

    def test_invoke_returns_warning_and_never_executes_in_mock_mode(self):
        response = self.client.post(
            "/api/agent/agent/invoke",
            json={
                "pageId": "feeding",
                "messages": [{"role": "user", "content": "Please generate a manual feeding preview for 600g."}],
                "contextVersion": "ctx-test",
                "pageContextSummary": {"sourceMode": "mock"},
                "allowedTools": ["preview_manual_feeding_action"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertIn("assistantMessage", payload)
        self.assertIn("warnings", payload)
        self.assertEqual(payload["toolCalls"][0]["name"], "preview_manual_feeding_action")
        self.assertIsNotNone(payload["toolResults"])
        self.assertIsNotNone(payload["confirmPreview"])
        self.assertEqual(payload["confirmPreview"]["mode"], "real")

    def test_invoke_can_complete_query_tool_loop_with_structured_response(self):
        response = self.client.post(
            "/api/agent/agent/invoke",
            json={
                "pageId": "water-quality",
                "messages": [{"role": "user", "content": "现在水质怎么样？"}],
                "contextVersion": "ctx-test",
                "pageContextSummary": {
                    "pond": {"pondId": "pond-001"},
                    "sourceMode": "mock",
                },
                "allowedTools": ["get_water_quality_summary"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertIn("assistantMessage", payload)
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["toolCalls"][0]["name"], "get_water_quality_summary")
        self.assertEqual(payload["toolResults"][0]["tool"], "get_water_quality_summary")
        self.assertIsNone(payload["confirmPreview"])

    def test_invoke_blocks_tool_outside_whitelist(self):
        with patch(
            "app.agent.llm_service._decide_next_step",
            return_value={
                "type": "tool",
                "toolName": "preview_manual_feeding_action",
                "arguments": {"pondId": "pond-001", "amount": 500},
            },
        ):
            response = self.client.post(
                "/api/agent/agent/invoke",
                json={
                    "pageId": "feeding",
                    "messages": [{"role": "user", "content": "帮我预览投喂 500g"}],
                    "contextVersion": "ctx-test",
                    "pageContextSummary": {
                        "pond": {"pondId": "pond-001"},
                        "sourceMode": "mock",
                    },
                    "allowedTools": ["get_water_quality_summary"],
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["status"], "degraded")
        self.assertIsNone(payload["confirmPreview"])
        self.assertTrue(any("not allowed" in item.lower() for item in payload["warnings"]))

    def test_invoke_stops_when_tool_calls_exceed_limit(self):
        scripted_steps = iter(
            [
                {"type": "tool", "toolName": "get_water_quality_summary", "arguments": {}},
                {"type": "tool", "toolName": "get_alert_digest", "arguments": {}},
                {"type": "tool", "toolName": "get_device_status", "arguments": {}},
            ]
        )

        with patch(
            "app.agent.llm_service._decide_next_step",
            side_effect=lambda *args, **kwargs: next(scripted_steps),
        ):
            response = self.client.post(
                "/api/agent/agent/invoke",
                json={
                    "pageId": "feeding",
                    "messages": [{"role": "user", "content": "请连续检查水质、告警和设备"}],
                    "contextVersion": "ctx-test",
                    "pageContextSummary": {
                        "pond": {"pondId": "pond-001"},
                        "sourceMode": "mock",
                    },
                    "allowedTools": [
                        "get_water_quality_summary",
                        "get_alert_digest",
                        "get_device_status",
                    ],
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(len(payload["toolCalls"]), 2)
        self.assertTrue(any("limit" in item.lower() for item in payload["warnings"]))


if __name__ == "__main__":
    unittest.main()
