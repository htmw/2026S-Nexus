from pymongo import AsyncMongoClient
from app.config import settings

client: AsyncMongoClient = None
db = None

async def connect_to_mongo():
    global client, db
    client = AsyncMongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.checkins.create_index([("user_id", 1), ("created_at", -1)])

async def close_mongo_connection():
    global client
    if client:
        await client.close()

def get_database():
    return db