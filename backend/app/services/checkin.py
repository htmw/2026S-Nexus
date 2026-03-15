import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import get_db
from app.services.nlp import generate_feedback

logger = logging.getLogger(__name__)

async def create_checkin(
        mood: int, 
        reflection: Optional[str] = None
) -> dict:
    db = get_db()
    feedback_result = generate_feedback(reflection)
    checkin_data = {
        "mood": mood,
        "reflection": reflection,
        "created_at": datetime.now(timezone.utc),
        "predicted_mood": feedback_result["predicted_mood"],
        "feedback": feedback_result["feedback"],
        "feedback_source": feedback_result["feedback_source"],
    }
    result = await db.checkins.insert_one(checkin_data)
    checkin_data["id"] = str(result.inserted_id)
    return checkin_data

