import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import get_database
from app.services.nlp import analyze_emotion, analyze_sentiment, is_emotion_loaded, is_model_loaded
from app.services.suggestions import get_suggestion_for_checkin_async

logger = logging.getLogger(__name__)

async def create_checkin(
        user_id: str,
        mood: int, 
        reflection: Optional[str] = None
) -> dict:
    """
    Create a new check-in document.

    Runs sentiment + emotion analysis on the reflection if provided,
    then generates a suggestion via Groq → FLAN-T5 → static fallback.
    """

    db = get_database()

    sentiment_score = None
    sentiment_label = None
    sentiment_confidence = None
    emotion_label = None
    emotion_confidence = None

    if reflection and reflection.strip():
        if is_model_loaded():
            try:
                result = analyze_sentiment(reflection)
                sentiment_score = result["normalized_score"]
                sentiment_label = result["label"]
                sentiment_confidence = result["confidence"]
            except Exception:
                logger.exception("Sentiment analysis failed for check-in")
        else:
            logger.warning("NLP model not loaded; skipping sentiment analysis")

        if is_emotion_loaded():
            try:
                emotion_result = analyze_emotion(reflection)
                emotion_label = emotion_result["emotion_label"]
                emotion_confidence = emotion_result["emotion_confidence"]
            except Exception:
                logger.exception("Emotion classification failed for check-in")
        else:
            logger.warning("Emotion model not loaded; skipping emotion classification")

    # Groq → FLAN-T5 → static (async-safe)
    suggestion = await get_suggestion_for_checkin_async(
        mood=mood,
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        emotion_label=emotion_label,
        reflection=reflection,
    )

    doc = {
        "user_id": user_id,
        "mood": mood,
        "reflection": reflection,
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "sentiment_confidence": sentiment_confidence,
        "emotion_label": emotion_label,
        "emotion_confidence": emotion_confidence,
        "suggestion": suggestion,
        "created_at": datetime.now(timezone.utc),
    }

    insert_result = await db.checkins.insert_one(doc)
    doc["_id"] = str(insert_result.inserted_id)
    return doc