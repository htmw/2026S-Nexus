import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status

from app.database import get_database
from app.errors import AppError
from app.services.nlp import analyze_emotion, analyze_sentiment, is_emotion_loaded, is_model_loaded
from app.services.suggestions import get_suggestion_for_checkin_async

logger = logging.getLogger(__name__)

_memory_store: list[dict] = []
_db_unavailable_until: float = 0.0
_FALLBACK_FILE = Path(__file__).resolve().parents[2] / "data" / "checkins_fallback.json"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_fallback_dir() -> None:
    _FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)


def _serialize_entry(entry: dict) -> dict:
    payload = dict(entry)
    for key, value in payload.items():
        if isinstance(value, datetime):
            payload[key] = value.isoformat()
    return payload


def _deserialize_entry(entry: dict) -> dict:
    payload = dict(entry)
    for field in ("created_at", "analysed_at"):
        value = payload.get(field)
        if isinstance(value, str):
            try:
                payload[field] = datetime.fromisoformat(value)
            except ValueError:
                payload[field] = _now_utc() if field == "created_at" else None
        elif value is None and field == "created_at":
            payload[field] = _now_utc()
    return payload


def _read_fallback_entries() -> list[dict]:
    _ensure_fallback_dir()
    if not _FALLBACK_FILE.exists():
        return []
    try:
        raw = json.loads(_FALLBACK_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(raw, list):
        return []
    return [_deserialize_entry(item) for item in raw if isinstance(item, dict)]


def _write_fallback_entries(entries: list[dict]) -> None:
    _ensure_fallback_dir()
    serializable = [_serialize_entry(item) for item in entries]
    _FALLBACK_FILE.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_fallback_entry(entry: dict) -> None:
    entries = _read_fallback_entries()
    entries.insert(0, dict(entry))
    _write_fallback_entries(entries)


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


def _normalize_sentiment_label(label: str | None) -> str | None:
    value = (label or "").strip().upper()
    if value == "POSITIVE":
        return "positive"
    if value == "NEGATIVE":
        return "negative"
    if value == "NEUTRAL":
        return "neutral"
    if value == "PENDING":
        return "Pending"
    return None


def _history_label_or_pending(sentiment_label: str | None) -> str:
    return sentiment_label if sentiment_label in {"positive", "negative", "neutral"} else "Pending"


_ANALYSIS_UNAVAILABLE_WARNING = "Analysis unavailable right now. Your entry was still saved."


async def create_checkin(
    user_id: str, mood: int, reflection: Optional[str] = None, shared_with_therapist: bool = False
) -> dict:
    db = get_database()
    reflection_text = (reflection or "").strip()

    sentiment_score = None
    sentiment_label = None
    sentiment_confidence = None
    emotion_label = None
    emotion_confidence = None
    sentiment = None
    confidence = None
    confidence_score = None
    analysed_at = None
    analysis_retry_pending = False
    predicted_mood = float(mood)
    warning = None

    if reflection_text:
        if is_model_loaded():
            try:
                result = analyze_sentiment(reflection_text)
                sentiment = result["label"]
                confidence = float(result["confidence"])
                sentiment_score = float(result["normalized_score"])
                predicted_mood = sentiment_score
                sentiment_label = _normalize_sentiment_label(sentiment)
                sentiment_confidence = confidence
                confidence_score = confidence
                analysed_at = _now_utc()
            except Exception:
                logger.exception("Sentiment analysis failed for check-in")
                sentiment = "PENDING"
                confidence = None
                confidence_score = None
                sentiment_confidence = None
                analysis_retry_pending = True
                warning = _ANALYSIS_UNAVAILABLE_WARNING
        else:
            logger.warning("NLP model not loaded; skipping sentiment analysis")
            sentiment = "PENDING"
            confidence = None
            confidence_score = None
            sentiment_confidence = None
            analysis_retry_pending = True
            warning = _ANALYSIS_UNAVAILABLE_WARNING

        if is_emotion_loaded():
            try:
                emotion_result = analyze_emotion(reflection_text)
                emotion_label = emotion_result["emotion_label"]
                emotion_confidence = emotion_result["emotion_confidence"]
            except Exception:
                logger.exception("Emotion classification failed for check-in")
        else:
            logger.warning("Emotion model not loaded; skipping emotion classification")

    try:
        suggestion = await get_suggestion_for_checkin_async(
            mood=mood,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment,
            emotion_label=emotion_label,
            reflection=reflection_text,
        )
    except Exception:
        logger.exception("Suggestion generation failed for check-in")
        suggestion = None

    checkin_data = {
        "user_id": user_id,
        "mood": mood,
        "reflection": reflection_text,
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "sentiment_confidence": sentiment_confidence,
        "emotion_label": emotion_label,
        "emotion_confidence": emotion_confidence,
        "sentiment": sentiment,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "analysed_at": analysed_at,
        "analysis_retry_pending": analysis_retry_pending,
        "suggestion": suggestion,
        "warning": warning,
        "predicted_mood": predicted_mood,
        "shared_with_therapist": shared_with_therapist,
        "created_at": _now_utc(),
    }

    if db is not None and _should_try_db():
        try:
            result = await db.checkins.insert_one(checkin_data)
            stored = dict(checkin_data)
            stored_id = str(result.inserted_id)
            stored["id"] = stored_id
            stored["_id"] = stored_id
            return stored
        except Exception:
            logger.exception("Database insert failed for check-in")
            _mark_db_unavailable()
            raise AppError(
                "Could not save your entry. Please try again.",
                "database_unavailable",
                status_code=500,
            )

    fallback_doc = dict(checkin_data)
    fallback_doc["id"] = str(uuid.uuid4())
    fallback_doc["_id"] = fallback_doc["id"]
    _memory_store.append(fallback_doc)
    _append_fallback_entry(fallback_doc)
    return fallback_doc


async def get_checkins_by_user(user_id: str, limit: int = 500) -> list[dict]:
    db = get_database()
    if db is not None and _should_try_db():
        try:
            cursor = db.checkins.find({"user_id": user_id}).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)
            entries = []
            for doc in docs:
                item = dict(doc)
                item["_id"] = str(item.get("_id", ""))
                item["id"] = item["_id"]
                entries.append(item)
            return entries
        except Exception:
            logger.exception("Database read failed; using fallback store")
            _mark_db_unavailable()

    fallback_source = _read_fallback_entries() or _memory_store
    filtered = [item for item in fallback_source if item.get("user_id") == user_id]
    return sorted(filtered, key=lambda item: item.get("created_at", _now_utc()), reverse=True)[:limit]


async def get_sentiment_summary() -> tuple[int, dict[str, int]]:
    db = get_database()
    if db is not None and _should_try_db():
        try:
            docs = await db.checkins.find({}, {"sentiment": 1}).to_list(length=None)
            counts: dict[str, int] = {}
            for doc in docs:
                sentiment = str(doc.get("sentiment") or "").upper()
                if sentiment not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
                    continue
                counts[sentiment] = counts.get(sentiment, 0) + 1
            return int(sum(counts.values())), counts
        except Exception:
            logger.exception("Database summary read failed; using fallback store")
            _mark_db_unavailable()

    fallback_entries = _read_fallback_entries() or _memory_store
    counts: dict[str, int] = {}
    for item in fallback_entries:
        sentiment = str(item.get("sentiment") or "").upper()
        if sentiment not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
            continue
        counts[sentiment] = counts.get(sentiment, 0) + 1
    return int(sum(counts.values())), counts


async def get_mood_history(user_id: str, limit: int = 500) -> list[dict]:
    db = get_database()
    if db is not None and _should_try_db():
        try:
            docs = await db.checkins.find(
                {"user_id": user_id},
                {"created_at": 1, "sentiment_label": 1, "confidence_score": 1, "sentiment_confidence": 1},
                sort=[("created_at", 1)],
            ).limit(limit).to_list(length=limit)
            return [
                {
                    "date": doc.get("created_at"),
                    "sentiment_label": _history_label_or_pending(doc.get("sentiment_label")),
                    "confidence_score": doc.get("confidence_score", doc.get("sentiment_confidence")),
                }
                for doc in docs
            ]
        except Exception:
            logger.exception("Database mood history read failed; using fallback store")
            _mark_db_unavailable()

    fallback_source = _read_fallback_entries() or _memory_store
    user_entries = sorted(
        [item for item in fallback_source if item.get("user_id") == user_id],
        key=lambda item: item.get("created_at", _now_utc()),
    )[:limit]
    return [
        {
            "date": item.get("created_at"),
            "sentiment_label": _history_label_or_pending(item.get("sentiment_label")),
            "confidence_score": item.get("confidence_score", item.get("sentiment_confidence")),
        }
        for item in user_entries
    ]


async def get_past_entries(limit: int = 200, user_id: str | None = None) -> list[dict]:
    if user_id is None:
        db = get_database()
        if db is not None and _should_try_db():
            try:
                docs = await db.checkins.find({}, sort=[("created_at", -1)]).limit(limit).to_list(length=limit)
                source = []
                for doc in docs:
                    item = dict(doc)
                    item["_id"] = str(item.get("_id", ""))
                    item["id"] = item["_id"]
                    source.append(item)
            except Exception:
                _mark_db_unavailable()
                source = sorted(_read_fallback_entries() or _memory_store, key=lambda item: item.get("created_at", _now_utc()), reverse=True)[:limit]
        else:
            source = sorted(_read_fallback_entries() or _memory_store, key=lambda item: item.get("created_at", _now_utc()), reverse=True)[:limit]
    else:
        source = await get_checkins_by_user(user_id, limit=limit)

    return [
        {
            "id": str(item.get("id") or item.get("_id") or ""),
            "mood": int(item.get("mood", 0)),
            "reflection": str(item.get("reflection", "") or ""),
            "sentiment": str(item.get("sentiment") or "PENDING"),
            "confidence": float(item["confidence"]) if item.get("confidence") is not None else None,
            "suggestion": str(item.get("suggestion") or ""),
            "warning": item.get("warning"),
            "predicted_mood": float(item.get("predicted_mood") or 0.0),
            "shared_with_therapist": bool(item.get("shared_with_therapist", False)),
            "created_at": item.get("created_at"),
        }
        for item in source
    ]


async def _assert_therapist_can_view_patient(therapist_id: str, patient_id: str) -> None:
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Therapist views require database connectivity",
        )

    link = await db.therapist_patient_links.find_one(
        {
            "therapist_id": therapist_id,
            "patient_id": patient_id,
            "active": {"$ne": False},
        }
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Therapist is not linked to this patient",
        )

    profile = await db.patient_profiles.find_one({"patient_id": patient_id})
    sharing_enabled = bool((profile or {}).get("sharing_enabled", False))
    if not sharing_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This patient has not shared their data with you.",
        )


async def get_patient_profile_for_therapist(therapist_id: str, patient_id: str) -> dict:
    await _assert_therapist_can_view_patient(therapist_id, patient_id)

    db = get_database()
    profile = await db.patient_profiles.find_one({"patient_id": patient_id}) or {}
    return {
        "patient_id": patient_id,
        "name": str(profile.get("name", "Unknown Patient")),
        "email": str(profile.get("email", "unknown@example.com")),
        "sharing_enabled": bool(profile.get("sharing_enabled", True)),
    }


async def get_linked_patients_for_therapist(therapist_id: str, limit: int = 100) -> list[dict]:
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Therapist views require database connectivity",
        )

    links = await db.therapist_patient_links.find(
        {
            "therapist_id": therapist_id,
            "active": {"$ne": False},
        },
        {"patient_id": 1},
    ).limit(limit).to_list(length=limit)

    patients: list[dict] = []
    for link in links:
        patient_id = str(link.get("patient_id", "")).strip()
        if not patient_id:
            continue
        profile = await db.patient_profiles.find_one({"patient_id": patient_id}) or {}
        patients.append(
            {
                "patient_id": patient_id,
                "name": str(profile.get("name", "Unknown Patient")),
                "email": str(profile.get("email", "unknown@example.com")),
                "sharing_enabled": bool(profile.get("sharing_enabled", False)),
            }
        )

    return patients


async def get_patient_entries_for_therapist(therapist_id: str, patient_id: str, limit: int = 200) -> list[dict]:
    await _assert_therapist_can_view_patient(therapist_id, patient_id)

    db = get_database()
    docs = await db.checkins.find(
        {
            "user_id": patient_id,
            "shared_with_therapist": True,  # NEW: only shared entries
        },
        {
            "created_at": 1,
            "reflection": 1,
            "sentiment_label": 1,
        },
        sort=[("created_at", 1)],
    ).limit(limit).to_list(length=limit)

    return [
        {
            "date": doc.get("created_at"),
            "text": str(doc.get("reflection", "") or ""),
            "sentiment_label": _history_label_or_pending(doc.get("sentiment_label")),
        }
        for doc in docs
    ]


async def get_patient_trend_for_therapist(therapist_id: str, patient_id: str, limit: int = 500) -> list[dict]:
    await _assert_therapist_can_view_patient(therapist_id, patient_id)

    db = get_database()
    docs = await db.checkins.find(
        {
            "user_id": patient_id,
            "sentiment_label": {"$in": ["positive", "negative", "neutral"]},
            "shared_with_therapist": True,  # NEW: only shared entries
        },
        {
            "created_at": 1,
            "sentiment_label": 1,
            "confidence_score": 1,
            "sentiment_confidence": 1,
        },
        sort=[("created_at", 1)],
    ).limit(limit).to_list(length=limit)

    return [
        {
            "date": doc.get("created_at"),
            "sentiment_label": str(doc.get("sentiment_label")),
            "confidence_score": float(doc.get("confidence_score") or doc.get("sentiment_confidence") or 0.0),
        }
        for doc in docs
    ]


async def toggle_entry_sharing(entry_id: str, user_id: str, shared: bool) -> dict:
    """Toggle shared_with_therapist for a single entry. Patient-only."""
    from bson import ObjectId
    from bson.errors import InvalidId

    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database required to toggle sharing",
        )

    # Try ObjectId first (most common case for MongoDB-generated IDs).
    # Fall back to plain string for entries inserted with string IDs.
    candidates = []
    try:
        candidates.append(ObjectId(entry_id))
    except (InvalidId, TypeError):
        pass
    candidates.append(entry_id)  # also try as string

    result = None
    for candidate in candidates:
        result = await db.checkins.update_one(
            {"_id": candidate, "user_id": user_id},
            {"$set": {"shared_with_therapist": shared}},
        )
        if result.matched_count > 0:
            break

    if not result or result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found or you don't own it",
        )

    return {"entry_id": entry_id, "shared_with_therapist": shared}