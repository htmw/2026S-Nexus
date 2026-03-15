from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "mindmirror"
    MOOD_MODEL_DIR: str = "models/mood_regression_model"
    MOOD_MODEL_ZIP: str | None = None
    MOOD_MODEL_ALLOW_ZIP_FALLBACK: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
