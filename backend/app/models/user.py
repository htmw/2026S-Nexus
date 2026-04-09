from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserInDB(BaseModel):
    """Represents a user document as stored in MongoDB."""

    id: Optional[str] = Field(None, alias="_id")
    name: str
    email: EmailStr
    password: str  # hashed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
