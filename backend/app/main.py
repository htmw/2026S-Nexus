import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import connect_to_mongo, close_mongo_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    logger.info("Connected to MongoDB")
    logger.info("MindMirror api is ready.")
    yield

    await close_mongo_connection()
    logger.info("Closed MongoDB connection")

app = FastAPI(
    title="MindMirror API",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "MindMirror API is running"}