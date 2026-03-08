from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "mindmirror"

    class Config:
        env_file = ".env"


settings = Settings()
