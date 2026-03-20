import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import connect_to_mongo, close_mongo_connection, get_db
from app.routes.checkin import router as checkin_router
from app.services.sentiment_service import warmup_sentiment_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    if get_db() is not None:
        logger.info("Connected to MongoDB")
    else:
        logger.warning("MongoDB unavailable; using in-memory fallback for entries")

    should_warmup = os.getenv("SENTIMENT_PRELOAD_ON_STARTUP", "true").lower() == "true"

    if should_warmup:
        try:
            warmup_sentiment_model()
            logger.info("Sentiment model warmed up")
        except Exception as error:
            logger.warning("Sentiment model warmup skipped: %s", error)

    logger.info("MindMirror api is ready.")
    yield

    await close_mongo_connection()
    logger.info("Closed MongoDB connection")

app = FastAPI(
    title="MindMirror API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(checkin_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "MindMirror API is running"}