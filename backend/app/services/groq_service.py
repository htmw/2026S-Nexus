"""
Groq-based suggestion generator.

Uses Groq's free API (Llama 3.1 8B) to generate a short, personalised
wellness suggestion based on the user's mood, sentiment, emotion, and
reflection text.

Falls back gracefully (returns None) if:
  - GROQ_API_KEY is not set
  - The API call fails for any reason
  - The response is empty or malformed

The caller (suggestions.py) handles the fallback chain.
"""

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a warm, compassionate wellness coach embedded in a daily journaling app.
Your job is to read a brief summary of how the user is feeling and respond with ONE short, specific, actionable suggestion to support their wellbeing.

Rules:
- Write exactly one sentence (max 30 words).
- Be warm and direct — no filler phrases like "I suggest" or "you might want to consider".
- Make it concrete and immediately actionable.
- Never repeat back the user's words or mood score.
- Never use lists, bullet points, or multiple sentences.
- Vary your suggestions — avoid generic advice like "go for a walk" every time."""


def _build_user_message(
    mood: int,
    sentiment_score: Optional[float],
    sentiment_label: Optional[str],
    emotion_label: Optional[str],
    reflection_snippet: Optional[str],
) -> str:
    """Build the user-facing context message sent to the model."""
    parts = [f"Mood: {mood}/5."]

    if sentiment_label and sentiment_score is not None:
        parts.append(f"Reflection sentiment: {sentiment_label.lower()} ({sentiment_score:.1f}/5).")

    if emotion_label:
        parts.append(f"Primary emotion detected: {emotion_label}.")

    if reflection_snippet and reflection_snippet.strip():
        snippet = reflection_snippet.strip()[:300].replace("\n", " ")
        parts.append(f'Journal entry: "{snippet}"')

    return " ".join(parts)


async def generate_suggestion_groq(
    mood: int,
    sentiment_score: Optional[float] = None,
    sentiment_label: Optional[str] = None,
    emotion_label: Optional[str] = None,
    reflection_snippet: Optional[str] = None,
) -> Optional[str]:
    """
    Call Groq API and return a single-sentence wellness suggestion.
    Returns None on any failure so the caller can fall back gracefully.
    """
    if not settings.GROQ_API_KEY:
        logger.debug("GROQ_API_KEY not set — skipping Groq suggestion")
        return None

    user_message = _build_user_message(
        mood, sentiment_score, sentiment_label, emotion_label, reflection_snippet
    )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": 80,
        "temperature": 0.8,
        "top_p": 0.9,
    }

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)

        if response.status_code != 200:
            logger.warning(
                "Groq API returned %s: %s",
                response.status_code,
                response.text[:200],
            )
            return None

        data = response.json()
        text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not text:
            logger.warning("Groq API returned an empty response")
            return None

        # Clean up — remove any leading/trailing quotes the model might add
        text = text.strip('"').strip("'").strip()

        logger.info("Groq suggestion generated successfully")
        return text[0].upper() + text[1:] if len(text) > 1 else text.upper()

    except httpx.TimeoutException:
        logger.warning("Groq API request timed out")
    except httpx.RequestError as exc:
        logger.warning("Groq API request failed: %s", exc)
    except Exception as exc:
        logger.warning("Unexpected error calling Groq API: %s", exc)

    return None