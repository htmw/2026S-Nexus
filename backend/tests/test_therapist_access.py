import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app


class TestTherapistAccessScenarios(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.therapist_headers = {
            "x-user-id": "therapist-1",
            "x-user-role": "therapist",
        }

    def test_therapist_views_patient_with_sharing_on(self):
        with patch(
            "app.routes.therapist.get_patient_entries_for_therapist",
            new=AsyncMock(return_value=[
                {
                    "date": "2026-04-10T10:00:00Z",
                    "text": "Feeling better.",
                    "sentiment_label": "positive",
                }
            ]),
        ):
            response = self.client.get(
                "/api/therapist/patients/patient-1/journal-entries",
                headers=self.therapist_headers,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["entries"]), 1)

    def test_therapist_views_patient_with_sharing_off(self):
        with patch(
            "app.routes.therapist.get_patient_entries_for_therapist",
            new=AsyncMock(
                side_effect=HTTPException(status_code=403, detail="This patient has not shared their data with you.")
            ),
        ):
            response = self.client.get(
                "/api/therapist/patients/patient-2/journal-entries",
                headers=self.therapist_headers,
            )

        self.assertEqual(response.status_code, 403)

    def test_unlinked_therapist_cannot_view_patient(self):
        with patch(
            "app.routes.therapist.get_patient_entries_for_therapist",
            new=AsyncMock(
                side_effect=HTTPException(status_code=403, detail="Therapist is not linked to this patient")
            ),
        ):
            response = self.client.get(
                "/api/therapist/patients/patient-3/journal-entries",
                headers=self.therapist_headers,
            )

        self.assertEqual(response.status_code, 403)

    def test_therapist_delete_is_rejected(self):
        response = self.client.delete(
            "/api/therapist/patients/patient-1/journal-entries",
            headers=self.therapist_headers,
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
