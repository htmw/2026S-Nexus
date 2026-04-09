from datetime import datetime, timezone
from typing import Optional

from pymongo.errors import DuplicateKeyError

from app.database import get_database
from app.services.auth import hash_password


async def create_user(name: str, email: str, password: str) -> dict:
    """
    Create a new user in the database.

    Returns the inserted user document with string `_id`.
    Raises ValueError if the email is already registered.
    """
    db = get_database()

    email = email.lower().strip()

    user_doc = {
        "name": name.strip(),
        "email": email,
        "password": hash_password(password),
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        raise ValueError("Email already registered")

    user_doc["_id"] = str(result.inserted_id)
    return user_doc


async def get_user_by_email(email: str) -> Optional[dict]:
    """
    Retrieve a user document by email.

    Returns the user dict with `_id` as a string, or None if not found.
    """
    db = get_database()
    user_doc = await db.users.find_one({"email": email.lower().strip()})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
    return user_doc
