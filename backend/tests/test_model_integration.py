import os
import unittest
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import app.main as main_module
import app.services.checkin as checkin_service
import app.services.sentiment_service as sentiment_service
from app.main import app


class TestSentimentFallback(unittest.TestCase):
    def test_local_success_uses_local_result(self):
        with patch("app.services.sentiment_service._analyze_local", return_value=("POSITIVE", 0.9)):
            with patch.dict(
                os.environ,
                {
                    "SENTIMENT_USE_REMOTE_MODEL": "false",
                    "SENTIMENT_USE_REMOTE_FALLBACK": "true",
                },
                clear=False,
            ):
                label, score = sentiment_service.analyze_sentiment("I feel great")

        self.assertEqual(label, "POSITIVE")
        self.assertAlmostEqual(score, 0.9)

    def test_local_failure_falls_back_to_remote(self):
        with patch("app.services.sentiment_service._analyze_local", side_effect=RuntimeError("local failed")):
            with patch("app.services.sentiment_service._analyze_remote", return_value=("NEGATIVE", 0.8)):
                with patch.dict(
                    os.environ,
                    {
                        "SENTIMENT_USE_REMOTE_MODEL": "false",
                        "SENTIMENT_USE_REMOTE_FALLBACK": "true",
                    },
                    clear=False,
                ):
                    label, score = sentiment_service.analyze_sentiment("I feel bad")

        self.assertEqual(label, "NEGATIVE")
        self.assertAlmostEqual(score, 0.8)

    def test_both_fail_returns_neutral(self):
        with patch("app.services.sentiment_service._analyze_local", side_effect=RuntimeError("local failed")):
            with patch("app.services.sentiment_service._analyze_remote", side_effect=RuntimeError("remote failed")):
                with patch.dict(
                    os.environ,
                    {
                        "SENTIMENT_USE_REMOTE_MODEL": "false",
                        "SENTIMENT_USE_REMOTE_FALLBACK": "true",
                    },
                    clear=False,
                ):
                    label, score = sentiment_service.analyze_sentiment("Any text")

        self.assertEqual(label, "NEUTRAL")
        self.assertAlmostEqual(score, 0.0)


class TestApiErrorHandling(unittest.TestCase):
    def setUp(self):
        checkin_service._memory_store.clear()

    def _client(self, *, raise_server_exceptions=True):
        stack = ExitStack()
        stack.enter_context(patch.object(main_module.settings, "MONGODB_REQUIRE_ATLAS", False))
        stack.enter_context(patch("app.main.connect_to_mongo", new=AsyncMock()))
        stack.enter_context(patch("app.main.close_mongo_connection", new=AsyncMock()))
        stack.enter_context(patch("app.main.get_db", return_value=None))
        stack.enter_context(patch("app.services.checkin.get_db", return_value=None))
        stack.enter_context(patch("app.services.checkin._append_fallback_entry", return_value=None))
        stack.enter_context(patch("app.services.checkin._read_fallback_entries", return_value=[]))
        stack.enter_context(
            patch.dict(
                os.environ,
                {"SENTIMENT_PRELOAD_ON_STARTUP": "false"},
                clear=False,
            )
        )
        self.addCleanup(stack.close)
        return TestClient(app, raise_server_exceptions=raise_server_exceptions)

    def test_checkin_survives_sentiment_failure(self):
        with self._client() as client:
            with patch("app.services.checkin.analyze_sentiment", side_effect=RuntimeError("ml unavailable")):
                response = client.post(
                    "/api/checkin",
                    json={"mood": 4, "reflection": "Had a rough afternoon"},
                )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["sentiment"], "NEUTRAL")
        self.assertEqual(body["confidence"], 0.0)
        self.assertTrue(body["suggestion"])

    def test_checkin_survives_suggestion_failure(self):
        with self._client() as client:
            with patch("app.services.checkin.get_suggestion", side_effect=RuntimeError("suggestion unavailable")):
                response = client.post(
                    "/api/checkin",
                    json={"mood": 3, "reflection": "Doing okay today"},
                )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(
            body["suggestion"],
            "Your reflection was saved. Insights are temporarily unavailable right now.",
        )

    def test_global_error_handler_returns_consistent_payload(self):
        async def raise_unhandled_error():
            raise RuntimeError("boom")

        route = APIRoute("/api/__test/error", raise_unhandled_error, methods=["GET"])
        app.router.routes.append(route)
        self.addCleanup(lambda: app.router.routes.remove(route))

        with self._client(raise_server_exceptions=False) as client:
            response = client.get("/api/__test/error")

        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["error"]["code"], "internal_server_error")
        self.assertEqual(body["error"]["message"], "Something went wrong. Please try again.")
        self.assertTrue(body["error"]["request_id"])
        self.assertEqual(response.headers["X-Request-ID"], body["error"]["request_id"])


if __name__ == "__main__":
    unittest.main()
