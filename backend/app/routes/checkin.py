import logging

from typing import List
from fastapi import APIRouter, Depends, status

from app.schemas.checkin import CheckinRequest, CheckinResponse
from app.services.checkin import create_checkin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["checkin"])

@router.post(
    "/checkin", 
    response_model=CheckinResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new check-in",
)
async def submit_checkin(
    checkin: CheckinRequest,
):
    doc = await create_checkin(
        mood=checkin.mood,
        reflection=checkin.reflection,
    )

    return CheckinResponse(
        id=doc["_id"],
        mood=doc["mood"],
        reflection=doc["reflection"],
        sentiment_score=doc["sentiment_score"],
        sentiment_label=doc["sentiment_label"],
        sentiment_confidence=doc["sentiment_confidence"],
        emotion_label=doc.get("emotion_label"),
        emotion_confidence=doc.get("emotion_confidence"),
        suggestion=doc.get("suggestion"),
        created_at=doc["created_at"],
    )

