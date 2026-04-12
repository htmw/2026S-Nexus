import logging

from typing import List

from fastapi import APIRouter, Depends, status

from app.auth import AuthUser, get_current_user, require_patient
from app.schemas.checkin import CheckinRequest, CheckinResponse, SentimentCount, SentimentSummaryResponse
from app.services.checkin import create_checkin, get_checkins_by_user, get_sentiment_summary

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
    user: AuthUser = Depends(get_current_user),
):
    await require_patient(user)
    doc = await create_checkin(
        mood=checkin.mood,
        user_id=user.user_id,
        reflection=checkin.reflection,
    )

    return CheckinResponse(
        id=str(doc.get("id") or doc.get("_id") or ""),
        user_id=doc["user_id"],
        mood=doc["mood"],
        reflection=doc.get("reflection"),
        sentiment_score=doc.get("sentiment_score"),
        sentiment_confidence=doc.get("sentiment_confidence"),
        emotion_label=doc.get("emotion_label"),
        emotion_confidence=doc.get("emotion_confidence"),
        sentiment=doc["sentiment"],
        confidence=doc["confidence"],
        sentiment_label=doc.get("sentiment_label"),
        confidence_score=doc.get("confidence_score"),
        analysed_at=doc.get("analysed_at"),
        analysis_retry_pending=bool(doc.get("analysis_retry_pending", False)),
        suggestion=doc.get("suggestion"),
        predicted_mood=doc.get("predicted_mood"),
        created_at=doc["created_at"],
    )

@router.get(
    "/checkins",
    response_model=List[CheckinResponse],
    summary="Get all check-ins for the authenticated user",
)
async def list_checkins(user: AuthUser = Depends(get_current_user)):
    docs = await get_checkins_by_user(user.user_id)
    return [
        CheckinResponse(
            id=str(doc.get("id") or doc.get("_id") or ""),
            user_id=doc.get("user_id"),
            mood=doc["mood"],
            reflection=doc.get("reflection"),
            sentiment_score=doc.get("sentiment_score"),
            sentiment_label=doc.get("sentiment_label"),
            sentiment_confidence=doc.get("sentiment_confidence"),
            emotion_label=doc.get("emotion_label"),
            emotion_confidence=doc.get("emotion_confidence"),
            sentiment=doc.get("sentiment"),
            confidence=doc.get("confidence"),
            confidence_score=doc.get("confidence_score"),
            analysed_at=doc.get("analysed_at"),
            analysis_retry_pending=bool(doc.get("analysis_retry_pending", False)),
            suggestion=doc.get("suggestion"),
            predicted_mood=doc.get("predicted_mood"),
            created_at=doc["created_at"],
        )
        for doc in docs
    ]
