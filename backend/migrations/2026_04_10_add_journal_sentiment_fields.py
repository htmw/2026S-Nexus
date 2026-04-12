"""
Mongo migration for Sprint 2 journal sentiment fields.

Adds nullable fields to historical documents:
- sentiment_label (positive|negative|neutral)
- confidence_score (0..1 float)
- analysed_at (datetime)
- analysis_retry_pending (bool)
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from pymongo import AsyncMongoClient


def _normalize_sentiment_label(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    if text == "POSITIVE":
        return "positive"
    if text == "NEGATIVE":
        return "negative"
    if text == "NEUTRAL":
        return "neutral"
    return None


async def run_migration() -> None:
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "mind_mirror")

    client = AsyncMongoClient(mongodb_uri)
    db = client[database_name]

    # Pre-seed nullable fields for entries that have not yet been analyzed.
    await db.checkins.update_many(
        {"sentiment_label": {"$exists": False}},
        {
            "$set": {
                "sentiment_label": None,
                "confidence_score": None,
                "analysed_at": None,
                "analysis_retry_pending": False,
            }
        },
    )

    # Backfill normalized labels where legacy sentiment/confidence were present.
    cursor = db.checkins.find(
        {"sentiment": {"$exists": True}},
        {"_id": 1, "sentiment": 1, "confidence": 1, "created_at": 1},
    )
    async for doc in cursor:
        label = _normalize_sentiment_label(doc.get("sentiment"))
        confidence = doc.get("confidence")
        analysed_at = doc.get("created_at") or datetime.now(timezone.utc)
        await db.checkins.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "sentiment_label": label,
                    "confidence_score": float(confidence) if confidence is not None else None,
                    "analysed_at": analysed_at,
                }
            },
        )

    # Helpful indexes for new history/trend queries.
    await db.checkins.create_index([("user_id", 1), ("created_at", 1)])
    await db.checkins.create_index([("user_id", 1), ("sentiment_label", 1), ("created_at", 1)])
    await db.therapist_patient_links.create_index([("therapist_id", 1), ("patient_id", 1)], unique=True)
    await db.patient_profiles.create_index([("patient_id", 1)], unique=True)

    await client.close()
    print("Migration completed: sentiment fields and indexes applied.")


if __name__ == "__main__":
    asyncio.run(run_migration())
