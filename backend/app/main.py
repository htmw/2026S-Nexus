"""
Mind Mirror - AI-powered emotional check-in backend.
FastAPI app with journal entries, sentiment analysis, and MongoDB storage.
"""

import uuid
import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import JournalEntryCreate, JournalEntryResponse, SentimentCount, SentimentSummaryResponse
from app.sentiment_service import analyze_sentiment, get_suggestion, warmup_sentiment_model
from app.database import get_journals_collection

app = FastAPI(
    title="Mind Mirror API",
    description="AI-powered emotional check-in with sentiment analysis",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Backend is running 🚀"}


# In-memory fallback when MongoDB unavailable
_memory_store: list = []
_db_unavailable_until: float = 0.0


def _db_cooldown_seconds() -> float:
    raw = os.getenv("MONGODB_UNAVAILABLE_COOLDOWN_SECONDS", "30").strip()
    try:
        value = float(raw)
    except ValueError:
        value = 30.0
    return max(0.0, value)


def _should_try_db() -> bool:
    return time.monotonic() >= _db_unavailable_until


def _mark_db_unavailable() -> None:
    global _db_unavailable_until
    _db_unavailable_until = time.monotonic() + _db_cooldown_seconds()


@app.on_event("startup")
def preload_sentiment_model():
    """Optional preload to reduce first-request latency."""
    should_warmup = os.getenv("SENTIMENT_PRELOAD_ON_STARTUP", "true").lower() == "true"
    if should_warmup:
        try:
            warmup_sentiment_model()
        except Exception:
            pass


def _predict_mood_score(sentiment: str, confidence: float) -> float:
    """Convert sentiment + confidence to a 0-5 mood score for display."""
    if sentiment == "POSITIVE":
        score = 3.5 + confidence * 1.5
    elif sentiment == "NEGATIVE":
        score = 2.0 - confidence * 1.5
    else:
        score = 2.5
    return round(max(0.0, min(5.0, score)), 1)


def _create_entry(entry: JournalEntryCreate):
    """Shared logic for creating journal entry with sentiment analysis."""
    reflection_text = entry.reflection or ""
    sentiment, confidence = analyze_sentiment(reflection_text)
    suggestion = get_suggestion(reflection_text, sentiment, entry.mood)
    predicted_mood = _predict_mood_score(sentiment, confidence)
    doc = {
        "mood": entry.mood,
        "reflection": reflection_text,
        "sentiment": sentiment,
        "confidence": confidence,
        "suggestion": suggestion,
        "predicted_mood": predicted_mood,
        "created_at": datetime.utcnow(),
    }
    if _should_try_db():
        try:
            collection = get_journals_collection()
            result = collection.insert_one(doc)
            doc_id = str(result.inserted_id)
        except Exception:
            _mark_db_unavailable()
            doc_id = str(uuid.uuid4())
            doc["_id"] = doc_id
            _memory_store.append(doc)
    else:
        doc_id = str(uuid.uuid4())
        doc["_id"] = doc_id
        _memory_store.append(doc)
    return JournalEntryResponse(
        id=doc_id,
        mood=doc["mood"],
        reflection=doc["reflection"],
        sentiment=doc["sentiment"],
        confidence=doc["confidence"],
        suggestion=doc["suggestion"],
        predicted_mood=doc["predicted_mood"],
        created_at=doc["created_at"],
    )


@app.post("/journal", response_model=JournalEntryResponse)
def create_journal_entry(entry: JournalEntryCreate):
    """
    Create a journal entry with mood rating and optional reflection.
    Runs sentiment analysis on reflection text and stores sentiment + confidence in DB.
    """
    return _create_entry(entry)


@app.post("/api/checkin", response_model=JournalEntryResponse)
def create_checkin(entry: JournalEntryCreate):
    """
    Same as /journal - for frontend compatibility.
    Frontend calls POST /api/checkin with { mood, reflection }.
    """
    return _create_entry(entry)


@app.get("/api/sentiment-summary", response_model=SentimentSummaryResponse)
def get_sentiment_summary():
    """Return aggregate counts of sentiments across entries."""
    if _should_try_db():
        try:
            collection = get_journals_collection()
            pipeline = [
                {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
            grouped = list(collection.aggregate(pipeline))
            counts = [
                SentimentCount(sentiment=item.get("_id", "UNKNOWN"), count=int(item.get("count", 0)))
                for item in grouped
            ]
            total_entries = int(sum(item.count for item in counts))
            return SentimentSummaryResponse(total_entries=total_entries, counts=counts)
        except Exception:
            _mark_db_unavailable()

    sentiment_counts: dict[str, int] = {}
    for item in _memory_store:
        sentiment = str(item.get("sentiment", "UNKNOWN"))
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

    counts = [
        SentimentCount(sentiment=sentiment, count=count)
        for sentiment, count in sorted(sentiment_counts.items(), key=lambda x: x[0])
    ]
    total_entries = int(sum(item.count for item in counts))
    return SentimentSummaryResponse(total_entries=total_entries, counts=counts)
