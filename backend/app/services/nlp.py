import logging
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config import settings

logger = logging.getLogger(__name__)

_tokenizer = None
_model = None
_model_load_error: str | None = None


def _resolve_model_dir() -> Path:
    configured_path = Path(settings.MOOD_MODEL_DIR)
    if configured_path.is_absolute():
        return configured_path
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / configured_path


def _resolve_zip_path() -> Path | None:
    if not settings.MOOD_MODEL_ALLOW_ZIP_FALLBACK:
        return None
    if not settings.MOOD_MODEL_ZIP:
        return None
    return Path(settings.MOOD_MODEL_ZIP)


def _extract_model_if_needed(model_dir: Path) -> None:
    if model_dir.exists() and (model_dir / "config.json").exists():
        return

    zip_path = _resolve_zip_path()
    if not zip_path or not zip_path.exists():
        return

    logger.info("Extracting mood model from %s", zip_path)
    model_dir.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_path, "r") as archive:
        archive.extractall(model_dir.parent)


def _load_model_once() -> tuple[Any, Any] | None:
    global _tokenizer, _model, _model_load_error

    if _tokenizer is not None and _model is not None:
        return _tokenizer, _model

    if _model_load_error:
        return None

    model_dir = _resolve_model_dir()
    try:
        _extract_model_if_needed(model_dir)
        _tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        _model = AutoModelForSequenceClassification.from_pretrained(model_dir, local_files_only=True)
        _model.eval()
        logger.info("Mood model loaded from %s", model_dir)
        return _tokenizer, _model
    except Exception as error:
        _model_load_error = str(error)
        logger.warning("Mood model unavailable, using fallback feedback: %s", error)
        return None


def _build_feedback_from_score(score: float) -> str:
    if score >= 4.0:
        return "You sound mostly positive today. Keep this momentum and note what helped."
    if score >= 3.0:
        return "You sound fairly balanced. A short reflection break can keep your mood steady."
    if score >= 2.0:
        return "You sound a bit low right now. Try one small grounding activity and check in again later."
    return "You seem to be having a tough moment. Be gentle with yourself and consider reaching out to someone you trust."


def generate_feedback(reflection: str | None) -> dict[str, Any]:
    text = (reflection or "").strip()
    if not text:
        return {
            "predicted_mood": None,
            "feedback": "Add a short reflection to get personalized mood feedback.",
            "feedback_source": "none",
        }

    loaded = _load_model_once()
    if not loaded:
        return {
            "predicted_mood": None,
            "feedback": "Saved your entry. Model feedback is temporarily unavailable, but your reflection still matters.",
            "feedback_source": "fallback",
        }

    tokenizer, model = loaded
    inputs = tokenizer(
        text,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )

    with torch.no_grad():
        outputs = model(**inputs)
        raw_score = float(outputs.logits.squeeze().item())

    bounded_score = max(0.0, min(5.0, raw_score))
    rounded_score = round(bounded_score, 2)

    return {
        "predicted_mood": rounded_score,
        "feedback": _build_feedback_from_score(rounded_score),
        "feedback_source": "model",
    }
