from fastapi import APIRouter, Depends, status

from app.auth import AuthUser, get_current_user
from app.schemas.checkin import MoodHistoryPoint, MoodHistoryResponse
from app.services.checkin import get_mood_history

router = APIRouter(tags=["mood"])


@router.get(
    "/mood/history",
    response_model=MoodHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get mood history for authenticated patient",
)
async def mood_history(user: AuthUser = Depends(get_current_user)):
    # This endpoint powers charting and always scopes data to the authenticated user.
    points = await get_mood_history(user_id=user.user_id)
    return MoodHistoryResponse(
        entries=[
            MoodHistoryPoint(
                date=item["date"],
                sentiment_label=item["sentiment_label"],
                confidence_score=item["confidence_score"],
            )
            for item in points
        ]
    )
