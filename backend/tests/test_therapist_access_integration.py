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
class TestTherapistAccessIntegration(unittest.TestCase):
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
        suffix = uuid.uuid4().hex[:10]
        self.therapist_id = f"therapist-{suffix}"
        self.patient_id = f"patient-{suffix}"
        self.headers = {
            "x-user-id": self.therapist_id,
            "x-user-role": "therapist",
        }
        asyncio.run(self._reset_records())

    def tearDown(self):
        asyncio.run(self._reset_records())

    async def _reset_records(self):
        await self.db.checkins.delete_many({"user_id": self.patient_id})
        await self.db.therapist_patient_links.delete_many(
            {"therapist_id": self.therapist_id, "patient_id": self.patient_id}
        )
        await self.db.patient_profiles.delete_many({"patient_id": self.patient_id})

    async def _seed_linked_patient(self, sharing_enabled: bool):
        await self.db.therapist_patient_links.insert_one(
            {
                "therapist_id": self.therapist_id,
                "patient_id": self.patient_id,
                "active": True,
                "linked_at": datetime.now(timezone.utc),
            }
        )
        await self.db.patient_profiles.insert_one(
            {
                "patient_id": self.patient_id,
                "name": "Integration Patient",
                "email": "integration.patient@example.com",
                "sharing_enabled": sharing_enabled,
            }
        )

    async def _seed_checkin(self):
        await self.db.checkins.insert_one(
            {
                "user_id": self.patient_id,
                "created_at": datetime.now(timezone.utc),
                "reflection": "I feel better today.",
                "sentiment_label": "positive",
                "confidence_score": 0.92,
            }
        )

    def test_therapist_views_patient_with_sharing_on(self):
        asyncio.run(self._seed_linked_patient(sharing_enabled=True))
        asyncio.run(self._seed_checkin())

        journal_response = self.client.get(
            f"/api/therapist/patients/{self.patient_id}/journal",
            headers=self.headers,
        )
        self.assertEqual(journal_response.status_code, 200)
        journal_payload = journal_response.json()
        self.assertEqual(len(journal_payload["entries"]), 1)

        mood_response = self.client.get(
            f"/api/therapist/patients/{self.patient_id}/mood",
            headers=self.headers,
        )
        self.assertEqual(mood_response.status_code, 200)
        mood_payload = mood_response.json()
        self.assertEqual(len(mood_payload["points"]), 1)
        self.assertEqual(mood_payload["points"][0]["sentiment_label"], "positive")

    def test_therapist_views_patient_with_sharing_off(self):
        asyncio.run(self._seed_linked_patient(sharing_enabled=False))
        asyncio.run(self._seed_checkin())

        response = self.client.get(
            f"/api/therapist/patients/{self.patient_id}/journal",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("not shared", response.json().get("detail", "").lower())

    def test_unlinked_therapist_cannot_view_patient(self):
        awaitable = self.db.patient_profiles.insert_one(
            {
                "patient_id": self.patient_id,
                "name": "Integration Patient",
                "email": "integration.patient@example.com",
                "sharing_enabled": True,
            }
        )
        asyncio.run(awaitable)
        asyncio.run(self._seed_checkin())

        response = self.client.get(
            f"/api/therapist/patients/{self.patient_id}/journal",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 403)

    def test_therapist_attempts_edit_delete_rejected(self):
        asyncio.run(self._seed_linked_patient(sharing_enabled=True))

        response = self.client.delete(
            f"/api/therapist/patients/{self.patient_id}/journal",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
