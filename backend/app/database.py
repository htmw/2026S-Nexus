"""
MongoDB database connection and configuration for Mind Mirror.
"""

import os
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "")

DATABASE_NAME = os.getenv("MONGODB_DATABASE", "mind_mirror")
COLLECTION_JOURNALS = "journals"

_client: MongoClient | None = None


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def get_database() -> Database:
    """Get MongoDB database connection. Creates client if not already connected."""
    global _client
    if not MONGODB_URI:
        raise ValueError(
            "MONGODB_URI not set. Create backend/.env with MONGODB_URI. See .env.example"
        )
    if _client is None:
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=_int_env("MONGODB_SERVER_SELECTION_TIMEOUT_MS", 1200),
            connectTimeoutMS=_int_env("MONGODB_CONNECT_TIMEOUT_MS", 1200),
            socketTimeoutMS=_int_env("MONGODB_SOCKET_TIMEOUT_MS", 2000),
            retryWrites=False,
        )
    return _client[DATABASE_NAME]


def get_journals_collection():
    """Get the journals collection."""
    return get_database()[COLLECTION_JOURNALS]
