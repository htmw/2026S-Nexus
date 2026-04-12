from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class CheckinInDB(BaseModel):
    """Represents a check-in document as stored in MongoDB."""

    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[str] = None
    mood: int = Field(..., ge=0, le=5)
    reflection: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    emotion_label: Optional[str] = None
    emotion_confidence: Optional[float] = None
    suggestion: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
