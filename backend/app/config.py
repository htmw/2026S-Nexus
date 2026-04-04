from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        extra="ignore",
    )

    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("MONGODB_URL", "MONGODB_URI"),
    )
    DATABASE_NAME: str = Field(
        default="mindmirror",
        validation_alias=AliasChoices("DATABASE_NAME", "MONGODB_DATABASE"),
    )


settings = Settings()
