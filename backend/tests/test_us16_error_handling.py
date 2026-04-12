import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
import app.services.checkin as checkin_service


class TestUs16ErrorHandling(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(os.environ, {}, clear=False)
        self.connect_patch = patch("app.main.connect_to_mongo", new=AsyncMock())
        self.close_patch = patch("app.main.close_mongo_connection", new=AsyncMock())
        self.load_models_patch = patch("app.main.load_models")

        self.env_patch.start()
        self.connect_patch.start()
        self.close_patch.start()
        self.load_models_patch.start()

        self.client = TestClient(app, raise_server_exceptions=False)
        checkin_service._memory_store.clear()
        checkin_service._db_unavailable_until = 0.0
        self.headers = {
            "x-user-id": "patient-demo-1",
            "x-user-role": "patient",
        }

    def tearDown(self):
        checkin_service._memory_store.clear()
        self.load_models_patch.stop()
        self.close_patch.stop()
        self.connect_patch.stop()
        self.env_patch.stop()

    def test_validation_errors_use_consistent_json_shape(self):
        response = self.client.post(
            "/api/checkin",
            headers=self.headers,
            json={"mood": 9, "reflection": "Too high mood score"},
        )

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["code"], "validation_error")
        self.assertIn("mood", body["error"])

    def test_missing_auth_returns_unauthorized_error_shape(self):
        response = self.client.post(
            "/api/checkin",
            json={"mood": 3, "reflection": "Missing auth headers"},
        )

        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertEqual(body["code"], "unauthorized")
        self.assertEqual(body["error"], "Unauthorized")

    def test_ml_failure_does_not_crash_submission(self):
        with patch("app.services.checkin.get_database", return_value=None):
            with patch("app.services.checkin.is_model_loaded", return_value=True):
                with patch("app.services.checkin.analyze_sentiment", side_effect=RuntimeError("model down")):
                    with patch("app.services.checkin.is_emotion_loaded", return_value=False):
                        with patch("app.services.checkin.get_suggestion_for_checkin_async", new=AsyncMock(return_value="Take a pause")):
                            with patch("app.services.checkin._append_fallback_entry"):
                                with patch("app.services.checkin._read_fallback_entries", return_value=[]):
                                    response = self.client.post(
                                        "/api/checkin",
                                        headers=self.headers,
                                        json={"mood": 2, "reflection": "Today felt heavy"},
                                    )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["sentiment"], "PENDING")
        self.assertTrue(body["analysis_retry_pending"])
        self.assertIn("Analysis unavailable", body["warning"])

    def test_database_failure_returns_safe_internal_message(self):
        db = type("DB", (), {})()
        db.checkins = type("Checkins", (), {"insert_one": AsyncMock(side_effect=RuntimeError("db exploded"))})()

        with patch("app.services.checkin.get_database", return_value=db):
            with patch("app.services.checkin.is_model_loaded", return_value=True):
                with patch(
                    "app.services.checkin.analyze_sentiment",
                    return_value={"label": "POSITIVE", "confidence": 0.9, "normalized_score": 4.7},
                ):
                    with patch("app.services.checkin.is_emotion_loaded", return_value=False):
                        with patch("app.services.checkin.get_suggestion_for_checkin_async", new=AsyncMock(return_value="Keep going")):
                            response = self.client.post(
                                "/api/checkin",
                                headers=self.headers,
                                json={"mood": 4, "reflection": "Had a nice day"},
                            )

        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["code"], "database_unavailable")
        self.assertEqual(body["error"], "Could not save your entry. Please try again.")
        self.assertNotIn("exploded", body["error"])

    def test_unhandled_errors_return_safe_internal_server_error(self):
        with patch("app.routes.checkin.create_checkin", side_effect=RuntimeError("boom")):
            response = self.client.post(
                "/api/checkin",
                headers=self.headers,
                json={"mood": 3, "reflection": "Trigger server failure"},
            )

        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["code"], "internal_server_error")
        self.assertEqual(body["error"], "Something went wrong on our side.")

    def test_not_found_uses_consistent_json_shape(self):
        response = self.client.get("/api/route-that-does-not-exist")

        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["code"], "not_found")
        self.assertEqual(body["error"], "Not found")


if __name__ == "__main__":
    unittest.main()
