import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


class TestMoodHistoryController(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.auth_headers = {
            "x-user-id": "patient-1",
            "x-user-role": "patient",
        }

    def test_history_empty(self):
        # Unit test: controller behavior with mocked service output.
        with patch("app.routes.mood.get_mood_history", new=AsyncMock(return_value=[])):
            response = self.client.get("/api/mood/history", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"entries": []})

    def test_history_single_entry(self):
        point = {
            "date": "2026-04-10T10:00:00Z",
            "sentiment_label": "positive",
            "confidence_score": 0.91,
        }
        with patch("app.routes.mood.get_mood_history", new=AsyncMock(return_value=[point])):
            response = self.client.get("/api/mood/history", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 1)
        self.assertEqual(payload["entries"][0]["sentiment_label"], "positive")

    def test_history_multiple_entries(self):
        points = [
            {
                "date": "2026-04-10T10:00:00Z",
                "sentiment_label": "positive",
                "confidence_score": 0.91,
            },
            {
                "date": "2026-04-11T10:00:00Z",
                "sentiment_label": "negative",
                "confidence_score": 0.72,
            },
        ]
        with patch("app.routes.mood.get_mood_history", new=AsyncMock(return_value=points)):
            response = self.client.get("/api/mood/history", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 2)
        self.assertEqual(payload["entries"][1]["sentiment_label"], "negative")

    def test_history_unauthenticated_returns_401(self):
        response = self.client.get("/api/mood/history")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
