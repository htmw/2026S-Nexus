from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class CheckinRequest(BaseModel):
    mood: int = Field(..., ge=0, le=5, description="Mood score from 0 (worst) to 5 (best)")
    reflection: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional free-text reflection about how you feel",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mood": 4,
                    "reflection": "Had a productive day and enjoyed a walk outside.",
                }
            ]
        }
    }

class CheckinResponse(BaseModel):
    id: str
    mood: int
    reflection: Optional[str] = None
    sentiment_score: Optional[float] = Field(
        None, description="AI sentiment normalized to 0–5 scale"
    )
    sentiment_label: Optional[str] = Field(
        None, description="POSITIVE or NEGATIVE"
    )
    sentiment_confidence: Optional[float] = Field(
        None, description="Raw model confidence 0.0–1.0"
    )
    emotion_label: Optional[str] = Field(
        None, description="Top emotion from reflection (e.g. joy, sadness)"
    )
    emotion_confidence: Optional[float] = Field(
        None, description="Emotion model confidence 0.0–1.0"
    )
    suggestion: Optional[str] = Field(
        None, description="Personalized suggestion based on normalized sentiment/mood"
    )
    created_at: datetime