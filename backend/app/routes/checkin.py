import logging

from fastapi import APIRouter, status

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
        id=doc["id"],
        mood=doc["mood"],
        reflection=doc.get("reflection"),
        created_at=doc["created_at"],
        predicted_mood=doc.get("predicted_mood"),
        feedback=doc.get("feedback"),
        feedback_source=doc.get("feedback_source"),
    )

