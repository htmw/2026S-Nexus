import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import get_db

logger = logging.getLogger(__name__)

async def create_checkin(
        mood: int, 
        reflection: Optional[str] = None
) -> dict:
    db = get_db()
    checkin_data = {
        "mood": mood,
        "reflection": reflection,
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.checkins.insert_one(checkin_data)
    checkin_data["id"] = str(result.inserted_id)
    return checkin_data

