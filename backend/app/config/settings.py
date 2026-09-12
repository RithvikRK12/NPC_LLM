from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", env_file_encoding="utf-8", extra="ignore")

    app_title: str = "Modular Closed-Loop Control Architecture MVP"
    app_cors_origins: str = "*"
    database_url: str = Field(default="sqlite:///./mvp.db")
    llm_base_url: str = Field(default="")
    llm_api_key: str = Field(default="")
    llm_model: str = Field(default="gpt-4.1-mini")
    llm_timeout_seconds: float = Field(default=120.0, gt=0)
    embedding_model: str = Field(default="nomic-embed-text")
    embedding_base_url: str = "http://127.0.0.1:11434"
    embedding_dimensions: int = Field(default=768, ge=1)
    embedding_revision: str = "v1"
    embedding_timeout_seconds: float = Field(default=30.0, gt=0)
    memory_candidate_count: int = Field(default=40, ge=20, le=50)
    max_dialogue_chars: int = 240
    memory_top_k: int = 5

    @property
    def cors_origins(self) -> List[str]:
        if self.app_cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()