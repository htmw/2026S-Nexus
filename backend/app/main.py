import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import connect_to_mongo, close_mongo_connection
from app.services.nlp import load_models
from app.routes.checkin import router as checkin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Connecting to MongoDB...")
    await connect_to_mongo()
    logger.info("MongoDB connected")

    logger.info("Loading NLP models...")
    load_models()

    logger.info("MindMirror API ready")
    yield

    #shutdown
    await close_mongo_connection()
    logger.info("MindMirror API shut down")

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