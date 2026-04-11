import asyncio
import os
import uuid
import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from pymongo import AsyncMongoClient

import app.database as database_module
from app.main import app


@unittest.skipUnless(os.getenv("TEST_MONGODB_URI"), "TEST_MONGODB_URI not set")
class TestMoodHistoryIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.mongo_uri = os.getenv("TEST_MONGODB_URI")
        cls.mongo_db_name = os.getenv("TEST_MONGODB_DATABASE", "mind_mirror_integration")
        cls.mongo = AsyncMongoClient(cls.mongo_uri)
        cls.db = cls.mongo[cls.mongo_db_name]
        database_module.db = cls.db

    @classmethod
    def tearDownClass(cls):
        asyncio.run(cls.mongo.close())

    def setUp(self):
        self.user_id = f"patient-{uuid.uuid4()}"
        self.headers = {
            "x-user-id": self.user_id,
            "x-user-role": "patient",
        }
        asyncio.run(self.db.checkins.delete_many({"user_id": self.user_id}))

    def tearDown(self):
        asyncio.run(self.db.checkins.delete_many({"user_id": self.user_id}))

    def test_empty_history(self):
        response = self.client.get("/api/mood/history", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"entries": []})

    def test_single_entry_history(self):
        asyncio.run(
            self.db.checkins.insert_one(
                {
                    "user_id": self.user_id,
                    "created_at": datetime.now(timezone.utc),
                    "sentiment_label": "positive",
                    "confidence_score": 0.88,
                }
            )
        )

        response = self.client.get("/api/mood/history", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 1)
        self.assertEqual(payload["entries"][0]["sentiment_label"], "positive")

    def test_multiple_entries_history(self):
        now = datetime.now(timezone.utc)
        asyncio.run(
            self.db.checkins.insert_many(
                [
                    {
                        "user_id": self.user_id,
                        "created_at": now,
                        "sentiment_label": "negative",
                        "confidence_score": 0.45,
                    },
                    {
                        "user_id": self.user_id,
                        "created_at": now.replace(second=(now.second + 1) % 59),
                        "sentiment_label": "neutral",
                        "confidence_score": 0.51,
                    },
                ]
            )
        )

        response = self.client.get("/api/mood/history", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 2)

    def test_unauthenticated_returns_401(self):
        response = self.client.get("/api/mood/history")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
