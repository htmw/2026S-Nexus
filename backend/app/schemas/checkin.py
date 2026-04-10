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
    user_id: str
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

class ChartDataset(BaseModel):
    """Single dataset for Chart.js (e.g. one line). Use null for missing points."""
    label: str
    data: list[Optional[float]]


class ChartData(BaseModel):
    """Chart.js-ready structure: labels (e.g. dates) + datasets."""
    labels: list[str]
    datasets: list[ChartDataset]

class InsightResponse(BaseModel):
    checkins: list[CheckinResponse]
    mood_average_7d: Optional[float] = Field(
        None, description="7-day rolling average mood (last 7 days)"
    )
    sentiment_average_7d: Optional[float] = Field(
        None, description="7-day rolling average sentiment (last 7 days)"
    )
    mood_consistency_score: Optional[float] = Field(
        None,
        description="0–100; higher means more consistent mood over the last 7 days",
    )
    weekly_summary: Optional[str] = Field(
        None, description="Short text summary of the past week"
    )
    mood_trend: Optional[ChartData] = Field(
        None, description="Mood over time, ready for Chart.js"
    )
    sentiment_trend: Optional[ChartData] = Field(
        None, description="Sentiment over time, ready for Chart.js"
    )
    rolling_average_7d: Optional[ChartData] = Field(
        None,
        description="7-day rolling averages over time, ready for Chart.js",
    )
    suggestion: str