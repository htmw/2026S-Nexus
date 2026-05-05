"""
migrations/2026_04_22_add_patient_profiles.py

Seeds the patient_profiles collection from the users collection so that
existing patients have a profile document with sharing_enabled=False.

Run once:
    python -m migrations.2026_04_22_add_patient_profiles
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from pymongo import AsyncMongoClient


async def run_migration() -> None:
    mongodb_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "mind_mirror")

    client = AsyncMongoClient(mongodb_uri)
    db = client[database_name]

    # Ensure indexes exist before writing
    await db.therapist_patient_links.create_index(
        [("therapist_id", 1), ("patient_id", 1)], unique=True
    )
    await db.therapist_patient_links.create_index("patient_id")
    await db.patient_profiles.create_index("patient_id", unique=True)

    # Seed patient_profiles for every user not already present
    users_cursor = db.users.find({}, {"_id": 1, "name": 1, "email": 1})
    seeded = 0
    async for user in users_cursor:
        patient_id = str(user["_id"])
        exists = await db.patient_profiles.find_one({"patient_id": patient_id})
        if exists:
            continue
        await db.patient_profiles.insert_one(
            {
                "patient_id": patient_id,
                "name": user.get("name", "Unknown"),
                "email": user.get("email", ""),
                "sharing_enabled": False,   # opt-in; patient enables in settings
                "created_at": datetime.now(timezone.utc),
            }
        )
        seeded += 1

    await client.close()
    print(f"Migration complete: {seeded} patient_profiles seeded.")


if __name__ == "__main__":
    asyncio.run(run_migration())
