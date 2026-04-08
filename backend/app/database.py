from pymongo import AsyncMongoClient
from app.config import settings

client: AsyncMongoClient = None
db = None

async def connect_to_mongo():
    global client, db
    client = AsyncMongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

async def close_mongo_connection():
    global client
    if client:
        await client.close()

def get_database():
    return db