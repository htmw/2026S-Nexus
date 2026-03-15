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
    created_at: datetime
    predicted_mood: Optional[float] = None
    feedback: Optional[str] = None
    feedback_source: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "64b8f0c2e1a2b3c4d5e6f7g",
                    "mood": 4,
                    "reflection": "Had a productive day and enjoyed a walk outside.",
                    "created_at": "2024-06-19T12:34:56Z",
                    "predicted_mood": 4.12,
                    "feedback": "You sound mostly positive today. Keep this momentum and note what helped.",
                    "feedback_source": "model"
                }
            ]
        }
    }