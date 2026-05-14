import logging
import os
import time
from typing import Optional

from transformers import pipeline

logger = logging.getLogger(__name__)

_sentiment_pipeline = None
_emotion_pipeline = None
_suggestion_pipeline = None

# ── Hugging Face custom trained mood model ──────────────────────────────────
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "krishna6699/MoodRegression2"

tokenizer = None
model = None

def load_huggingface_model():
    global tokenizer, model

    if tokenizer is not None and model is not None:
        return

    logger.info("Loading custom Hugging Face model...")

    hf_token = os.getenv("HUGGINGFACE_TOKEN")

    print("HF TOKEN EXISTS:", hf_token is not None)

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        token=hf_token
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        token=hf_token
    )

    logger.info("Custom model loaded successfully")
    
def load_models() -> None:
    """
    Load NLP models once at startup (sentiment + emotion + optional suggestion generator).
    Subsequent calls are no-ops to guarantee single-load.

    Sentiment model priority:
    1. Custom local model at ./mood_model  (your trained regression model)
    2. Fallback: distilbert-base-uncased-finetuned-sst-2-english  (HuggingFace)
    """
    global _sentiment_pipeline, _emotion_pipeline, _suggestion_pipeline

    if _sentiment_pipeline is not None and _emotion_pipeline is not None:
        logger.debug("NLP models already loaded — skipping")
        return

    start = time.perf_counter()

    # ── Sentiment model ──────────────────────────────────────────────────────
    try:    
        load_huggingface_model()
        _sentiment_pipeline = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        device=-1,
        )
        logger.info("Custom mood model loaded successfully")

    except Exception as e:

        logger.warning(
            "Failed to load custom Hugging Face model (%s). Falling back to SST-2.",
            e,
        )

        _sentiment_pipeline = None

    if _sentiment_pipeline is None:

        logger.info("Loading fallback DistilBERT SST-2 sentiment model...")

        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1,
        )

        logger.info("Fallback sentiment model loaded")

    # ── Emotion model ────────────────────────────────────────────────────────
    if _emotion_pipeline is None:
        logger.info("Loading emotion classification model...")
        _emotion_pipeline = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=1,
            device=-1,
        )
        logger.info("Emotion model loaded")

    # ── Suggestion model (optional) ──────────────────────────────────────────
    if _suggestion_pipeline is None:
        try:
            logger.info("Loading suggestion generation model (FLAN-T5 base)...")
            _suggestion_pipeline = pipeline(
                "text2text-generation",
                model="google/flan-t5-small",
            )
            logger.info("Suggestion model loaded — dynamic AI suggestions enabled")
        except Exception as e:
            logger.warning(
                "Suggestion model not loaded; check-ins will use static suggestions. Error: %s",
                e,
            )

    elapsed = time.perf_counter() - start
    logger.info("All NLP models ready in %.2fs", elapsed)


def load_model() -> None:
    """Backward-compatible entry point: load all models."""
    load_models()


def is_model_loaded() -> bool:
    """True if sentiment model is loaded (used by check-in for sentiment)."""
    return _sentiment_pipeline is not None


def is_emotion_loaded() -> bool:
    """True if emotion classification model is loaded."""
    return _emotion_pipeline is not None


def is_suggestion_model_loaded() -> bool:
    """True if the dynamic suggestion generation model is loaded."""
    return _suggestion_pipeline is not None


def _is_custom_model() -> bool:
    """True if the loaded sentiment pipeline is the custom regression model."""
    if _sentiment_pipeline is None:
        return False
    try:
        model_path = _sentiment_pipeline.model.config._name_or_path
        return "MindMirrorRegression" in model_path
    except Exception:
        return False


def analyze_sentiment(text: str) -> dict:
    """
    Run sentiment analysis on the given text.

    Handles two model types automatically:

    Custom regression model (your trained model):
        - Outputs a single raw score (LABEL_0)
        - Score is clamped and normalised to 0–5 mood scale
        - label is derived from the score position:
            score < 1.5  → NEGATIVE
            score > 3.5  → POSITIVE
            otherwise    → NEUTRAL
        - confidence is expressed as distance from the midpoint (2.5)

    Fallback SST-2 classifier:
        - Outputs POSITIVE / NEGATIVE + confidence 0–1
        - Normalised exactly as before

    Returns:
        dict with keys:
            - label: "POSITIVE", "NEGATIVE", or "NEUTRAL"
            - confidence: float 0.0–1.0
            - normalized_score: float 0.0–5.0 (mapped to mood scale)
    """
    if _sentiment_pipeline is None:
        load_models()

    result = _sentiment_pipeline(text, truncation=True, max_length=512)[0]

    if _is_custom_model():
        # ── Custom regression model ──────────────────────────────────────────
        # The pipeline returns {"label": "LABEL_0", "score": <raw_logit>}
        raw_score = float(result["score"])

        # Clamp to 0–5 in case the model occasionally overshoots
        normalized = round(max(0.0, min(5.0, raw_score)), 2)

        # Derive a human-readable label from the score
        if normalized >= 3.5:
            label = "POSITIVE"
        elif normalized <= 1.5:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        # Express confidence as how far the score is from neutral (2.5), scaled to 0–1
        confidence = round(min(1.0, abs(normalized - 2.5) / 2.5), 4)

        logger.debug(
            "Custom model → raw=%.4f  normalized=%.2f  label=%s  conf=%.4f",
            raw_score, normalized, label, confidence,
        )

    else:
        # ── Fallback SST-2 classifier ────────────────────────────────────────
        label = result["label"]        # "POSITIVE" or "NEGATIVE"
        confidence = result["score"]   # 0.0 to 1.0

        if label == "POSITIVE":
            normalized = round(2.5 + (confidence * 2.5), 2)
        else:
            normalized = round(2.5 - (confidence * 2.5), 2)

        label = label  # already uppercase string

    return {
        "label": label,
        "confidence": round(float(confidence), 4),
        "normalized_score": normalized,
    }


def analyze_emotion(text: str) -> dict:
    """
    Run emotion classification on the given text.

    Uses j-hartmann/emotion-english-distilroberta-base (anger, disgust, fear,
    joy, neutral, sadness, surprise). Returns the top emotion.

    Returns:
        dict with keys:
            - emotion_label: str (e.g. "joy", "sadness")
            - emotion_confidence: float 0.0–1.0
    """
    if _emotion_pipeline is None:
        raise RuntimeError("Emotion model not loaded. Call load_models() first.")

    result = _emotion_pipeline(text, truncation=True, max_length=512, top_k=1)
    item = result[0] if isinstance(result, list) else result
    if isinstance(item, list):
        item = item[0] if item else {}
    label = item.get("label", "")
    label = label.lower() if isinstance(label, str) else str(label)
    score = float(item.get("score", 0.0))

    return {
        "emotion_label": label,
        "emotion_confidence": round(score, 4),
    }


def generate_suggestion(
    mood: int,
    sentiment_score: Optional[float] = None,
    sentiment_label: Optional[str] = None,
    emotion_label: Optional[str] = None,
    reflection_snippet: Optional[str] = None,
) -> Optional[str]:
    """
    Generate one short, supportive suggestion based on detected sentiment and context.

    Uses FLAN-T5 to produce a dynamic suggestion. Returns None if the model
    is not loaded or generation fails (caller should fall back to static suggestions).
    """
    if _suggestion_pipeline is None:
        return None

    parts = [f"The user's mood is {mood} out of 5."]
    if sentiment_score is not None:
        sentiment_desc = sentiment_label.lower() if sentiment_label else "neutral"
        parts.append(f"Their sentiment is {sentiment_desc} (score {sentiment_score:.1f}/5).")
    if emotion_label:
        parts.append(f"Their primary emotion is {emotion_label}.")
    if reflection_snippet and reflection_snippet.strip():
        snippet = reflection_snippet.strip()[:200].replace("\n", " ")
        parts.append(f'They wrote: "{snippet}"')

    context = " ".join(parts)
    prompt = (
        f"You are a compassionate wellness coach. {context} "
        "Give one specific, actionable, and kind suggestion to help them. "
        "Write exactly one sentence. Do not repeat the context. Do not use a list."
    )

    try:
        out = _suggestion_pipeline(
            prompt,
            max_length=80,
            min_length=15,
            do_sample=True,
            temperature=0.75,
            top_p=0.92,
            repetition_penalty=1.3,
            num_return_sequences=1,
        )
        if not out or len(out) == 0:
            return None
        first = out[0]
        if isinstance(first, str):
            text = first.strip()
        elif isinstance(first, dict):
            text = first.get("generated_text")
            if not text and first:
                for k, v in first.items():
                    if k.endswith("_text") and isinstance(v, str):
                        text = v
                        break
            text = (text or "").strip()
        else:
            text = ""
        if text:
            return text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    except Exception as e:
        logger.warning("Suggestion generation failed: %s", e)
    return None
