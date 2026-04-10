import logging

from typing import List
from fastapi import APIRouter, Depends, status

from app.schemas.checkin import CheckinRequest, CheckinResponse
from app.services.auth import get_current_user_id
from app.services.checkin import create_checkin, get_checkins_by_user

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
    user_id: str = Depends(get_current_user_id)
):
    doc = await create_checkin(
        user_id = user_id,
        mood=checkin.mood,
        reflection=checkin.reflection,
    )

    return CheckinResponse(
        id=doc["_id"],
        user_id = doc["user_id"],
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

@router.get(
    "/checkins",
    response_model=List[CheckinResponse],
    summary="Get all check-ins for the authenticated user",
)
async def list_checkins(user_id: str = Depends(get_current_user_id)):
    docs = await get_checkins_by_user(user_id)
    return [
        CheckinResponse(
            id=doc["_id"],
            user_id=doc.get("user_id"),
            mood=doc["mood"],
            reflection=doc.get("reflection"),
            sentiment_score=doc.get("sentiment_score"),
            sentiment_label=doc.get("sentiment_label"),
            sentiment_confidence=doc.get("sentiment_confidence"),
            emotion_label=doc.get("emotion_label"),
            emotion_confidence=doc.get("emotion_confidence"),
            suggestion=doc.get("suggestion"),
            created_at=doc["created_at"],
        )
        for doc in docs
    ]