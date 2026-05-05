import logging

from typing import List

from fastapi import APIRouter, Depends, Response, status

from app.auth import AuthUser, get_current_user, require_patient
from app.schemas.checkin import CheckinRequest, CheckinResponse, SentimentCount, SentimentSummaryResponse, EntryShareToggleRequest
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
    response: Response,
    user: AuthUser = Depends(get_current_user),
):
    await require_patient(user)
    doc = await create_checkin(
        mood=checkin.mood,
        user_id=user.user_id,
        reflection=checkin.reflection,
        shared_with_therapist=checkin.shared_with_therapist,
    )

    if doc.get("warning"):
        response.status_code = status.HTTP_200_OK

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
        warning=doc.get("warning"),
        predicted_mood=doc.get("predicted_mood"),
        shared_with_therapist=doc.get("shared_with_therapist", False),
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
            warning=doc.get("warning"),
            predicted_mood=doc.get("predicted_mood"),
            shared_with_therapist=doc.get("shared_with_therapist", False),
            created_at=doc["created_at"],
        )
        for doc in docs
    ]

@router.patch(
    "/checkins/{entry_id}/sharing",
    summary="Toggle sharing for a specific entry",
)
async def toggle_entry_sharing_endpoint(
    entry_id: str,
    body: EntryShareToggleRequest,
    user: AuthUser = Depends(get_current_user),
):
    from app.services.checkin import toggle_entry_sharing
    await require_patient(user)
    result = await toggle_entry_sharing(entry_id, user.user_id, body.shared_with_therapist)
    return result