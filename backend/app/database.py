from pymongo import AsyncMongoClient
from app.config import settings

client: AsyncMongoClient = None
db = None

async def connect_to_mongo():
    global client, db
    client = AsyncMongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    # ── Existing indexes ─────────────────────────────────────────────────────
    await db.users.create_index("email", unique=True)
    await db.checkins.create_index([("user_id", 1), ("created_at", -1)])
    await db.checkins.create_index([("user_id", 1), ("created_at", 1)])
    await db.checkins.create_index([("user_id", 1), ("sentiment_label", 1), ("created_at", 1)])

    # ── Therapist linking indexes ────────────────────────────────────────────
    # Unique compound index prevents duplicate links; supports both lookup directions.
    await db.therapist_patient_links.create_index(
        [("therapist_id", 1), ("patient_id", 1)], unique=True
    )
    await db.therapist_patient_links.create_index("patient_id")

    # patient_profiles: one document per patient; queried by patient_id.
    await db.patient_profiles.create_index("patient_id", unique=True)

async def close_mongo_connection():
    global client
    if client:
        await client.close()

def get_database():
    return db
