from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "mindmirror"
    GROQ_API_KEY: str = ""  # Set in .env — leave empty to disable Groq

    class Config:
        env_file = ".env"


settings = Settings()
