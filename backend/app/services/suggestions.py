"""
Modular suggestion engine.

Priority chain for a single check-in:
  1. Groq API (Llama 3.1 8B)   — best quality, requires GROQ_API_KEY in .env
  2. FLAN-T5 (local)            — loaded at startup if available
  3. Static buckets             — always available, mood/sentiment based

Static ranges:
  - 0–2:        calming exercises
  - 2–3.5:      mindfulness / reflection
  - 3.5–5:      reinforcement message
"""

import asyncio
import logging
import random
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Static suggestion buckets ───────────────────────────────────────────────

CALMING: Tuple[Tuple[float, float], list[str]] = (
    (0.0, 2.0),
    [
        "Try a short breathing exercise: inhale for 4 seconds, hold for 4, exhale for 4 — repeat 5 times.",
        "Place your feet flat on the floor and name 5 things you can see, 4 you can touch, 3 you can hear.",
        "It's okay to not be okay — send a voice note to someone you trust, even just to say hi.",
        "Step outside for 5 minutes, even if just to your doorstep — fresh air shifts the nervous system.",
        "Try a 2-minute body scan: breathe slowly and notice where you're holding tension, then soften it.",
        "Put on one song you love, close your eyes, and just listen — give yourself that 3 minutes.",
    ],
)

MINDFULNESS: Tuple[Tuple[float, float], list[str]] = (
    (2.0, 3.5),
    [
        "Write down one thing that went well today, however small — your brain needs that anchor.",
        "Take a real break in the next hour: no screen, no task, just 10 minutes of doing nothing.",
        "Ask yourself: what's one thing that would make tomorrow slightly easier to prepare tonight?",
        "Drink a full glass of water right now and take three slow breaths before moving on.",
        "Set a single, small intention for the rest of the day — one thing, done well.",
        "Spend 5 minutes tidying one small area; a calmer space tends to reflect back a calmer mind.",
    ],
)

REINFORCEMENT: Tuple[Tuple[float, float], list[str]] = (
    (3.5, 5.01),
    [
        "Channel this energy into something you've been putting off — today's the right day.",
        "Share something good that happened with someone who matters to you.",
        "Take note of what's working right now — write one line about it so you can return to it later.",
        "Use this momentum to tackle the one task you've been avoiding most.",
        "This is a great state to learn something new — spend 20 minutes on a skill you've been curious about.",
        "You're thriving — pay it forward with a kind message to someone who might need a lift.",
    ],
)

RANGES = [CALMING, MINDFULNESS, REINFORCEMENT]


def get_suggestion_for_score(normalized_score: float) -> str:
    """Return a static suggestion based on a normalized 0–5 score."""
    score = max(0.0, min(5.0, normalized_score))
    for (low, high), suggestions in RANGES:
        if low <= score < high:
            return random.choice(suggestions)
    return random.choice(REINFORCEMENT[1])


def get_suggestion(avg_mood: float) -> str:
    """Static suggestion for dashboard/aggregate use (no reflection context)."""
    return get_suggestion_for_score(avg_mood)


def get_suggestion_for_checkin(
    mood: int,
    sentiment_score: Optional[float] = None,
    sentiment_label: Optional[str] = None,
    emotion_label: Optional[str] = None,
    reflection: Optional[str] = None,
) -> str:
    """
    Return the best available suggestion for a single check-in.

    Tries Groq → FLAN-T5 → static, in that order.
    This function is sync (called from async FastAPI routes via awaiting
    the async Groq call in a small event-loop helper).
    """
    # ── 1. Try Groq (async → run in current event loop if available) ──────────
    try:
        from app.services.groq_service import generate_suggestion_groq
        from app.config import settings

        if settings.GROQ_API_KEY:
            try:
                loop = asyncio.get_event_loop()
                groq_result = loop.run_until_complete(
                    generate_suggestion_groq(
                        mood=mood,
                        sentiment_score=sentiment_score,
                        sentiment_label=sentiment_label,
                        emotion_label=emotion_label,
                        reflection_snippet=reflection,
                    )
                )
                if groq_result:
                    logger.info("Using Groq suggestion")
                    return groq_result
                else:
                    logger.warning("Groq returned no output — falling back")
            except RuntimeError:
                # Already inside a running event loop (e.g. called from async context)
                # Use asyncio.ensure_future / create_task pattern instead
                logger.warning(
                    "Groq called from within a running event loop — "
                    "use await get_suggestion_for_checkin_async() instead"
                )
    except ImportError:
        pass

    # ── 2. Try FLAN-T5 ────────────────────────────────────────────────────────
    try:
        from app.services.nlp import generate_suggestion, is_suggestion_model_loaded

        if is_suggestion_model_loaded():
            flan_result = generate_suggestion(
                mood=mood,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                emotion_label=emotion_label,
                reflection_snippet=reflection,
            )
            if flan_result:
                logger.info("Using FLAN-T5 suggestion")
                return flan_result
            else:
                logger.warning("FLAN-T5 returned no output — falling back to static")
        else:
            logger.warning("FLAN-T5 not loaded — falling back to static")
    except ImportError:
        pass

    # ── 3. Static fallback ────────────────────────────────────────────────────
    logger.info("Using static suggestion")
    normalized = float(sentiment_score) if sentiment_score is not None else float(mood)
    return get_suggestion_for_score(normalized)


async def get_suggestion_for_checkin_async(
    mood: int,
    sentiment_score: Optional[float] = None,
    sentiment_label: Optional[str] = None,
    emotion_label: Optional[str] = None,
    reflection: Optional[str] = None,
) -> str:
    """
    Async version — use this when calling from an async FastAPI route or service.
    Awaits Groq directly without needing run_until_complete.
    """
    # ── 1. Try Groq ───────────────────────────────────────────────────────────
    try:
        from app.services.groq_service import generate_suggestion_groq
        from app.config import settings

        if settings.GROQ_API_KEY:
            groq_result = await generate_suggestion_groq(
                mood=mood,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                emotion_label=emotion_label,
                reflection_snippet=reflection,
            )
            if groq_result:
                logger.info("Using Groq suggestion")
                return groq_result
            else:
                logger.warning("Groq returned no output — falling back")
    except ImportError:
        pass

    # ── 2. Try FLAN-T5 ────────────────────────────────────────────────────────
    try:
        from app.services.nlp import generate_suggestion, is_suggestion_model_loaded

        if is_suggestion_model_loaded():
            flan_result = generate_suggestion(
                mood=mood,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                emotion_label=emotion_label,
                reflection_snippet=reflection,
            )
            if flan_result:
                logger.info("Using FLAN-T5 suggestion")
                return flan_result
            else:
                logger.warning("FLAN-T5 returned no output — falling back to static")
    except ImportError:
        pass

    # ── 3. Static fallback ────────────────────────────────────────────────────
    logger.info("Using static suggestion")
    normalized = float(sentiment_score) if sentiment_score is not None else float(mood)
    return get_suggestion_for_score(normalized)