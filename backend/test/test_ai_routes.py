import unittest

from fastapi.testclient import TestClient

from app.main import app


class AIRoutesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_bootstrap_returns_mock_mode_and_allowed_tools(self):
        response = self.client.post(
            "/api/ai/agent/bootstrap",
            json={
                "pageId": "feeding",
                "routePath": "/fishery/feeding",
                "pondId": "pond-001",
                "selection": {"tab": "overview"},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["environmentMode"], "mock")
        self.assertIn("systemInstructions", payload)
        self.assertIn("pageInstructions", payload)
        self.assertIn("preview_manual_feeding_action", payload["allowedTools"])
        self.assertTrue(payload["uiCapabilities"]["showSuggestionPanel"])
        self.assertFalse(payload["uiCapabilities"]["canExecute"])

    def test_context_changes_when_page_changes(self):
        response = self.client.post(
            "/api/ai/agent/context",
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
        self.assertEqual(payload["sourceMode"], "mock")
        self.assertIn("contextVersion", payload)

    def test_feeding_suggestions_include_mock_metadata(self):
        response = self.client.post(
            "/api/ai/suggestions/feeding",
            json={"pageId": "feeding", "routePath": "/fishery/feeding", "pondId": "pond-001"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertGreaterEqual(len(payload["cards"]), 1)
        first_card = payload["cards"][0]
        self.assertEqual(first_card["sourceMode"], "mock")
        self.assertIn("updatedAt", first_card)
        self.assertIn("panelState", payload)

    def test_manual_feeding_preview_returns_mock_preview(self):
        response = self.client.post(
            "/api/ai/actions/manual-feeding/preview",
            json={"pondId": "pond-001", "amount": 600},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["mode"], "mock")
        self.assertEqual(payload["actionType"], "manual_feeding_preview")
        self.assertIn("confirmToken", payload)
        self.assertIn("previewText", payload)

    def test_invoke_returns_warning_and_never_executes_in_mock_mode(self):
        response = self.client.post(
            "/api/ai/agent/invoke",
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
        self.assertIsNone(payload["toolResults"])
        self.assertIsNotNone(payload["confirmPreview"])
        self.assertEqual(payload["confirmPreview"]["mode"], "mock")


if __name__ == "__main__":
    unittest.main()
