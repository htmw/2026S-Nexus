import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.auth import reject_therapist_mutations
from app.database import connect_to_mongo, close_mongo_connection
from app.routes.auth import router as auth_router
from app.routes.checkin import router as checkin_router
from app.routes.insight import router as insight_router
from app.routes.mood import router as mood_router
from app.routes.therapist import router as therapist_router
from app.services.nlp import load_models

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

app.include_router(auth_router, prefix="/api")
app.include_router(checkin_router, prefix="/api")
app.include_router(insight_router, prefix="/api")
app.include_router(mood_router, prefix="/api")
app.include_router(therapist_router, prefix="/api")


@app.middleware("http")
async def therapist_readonly_guard(request, call_next):
    # Backend-level safety net: therapist role cannot mutate patient data endpoints.
    role = (request.headers.get("x-user-role") or "").strip().lower()
    try:
        reject_therapist_mutations(request, role)
    except Exception as error:
        if getattr(error, "status_code", None) == 403:
            return JSONResponse(status_code=403, content={"detail": str(error.detail)})
        raise
    return await call_next(request)

@app.get("/")
async def root():
    return {"message": "MindMirror API is running"}