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
    llm_structured_output: bool = True
    llm_timeout_seconds: float = Field(default=120.0, gt=0)
    embedding_model: str = Field(default="nomic-embed-text")
    embedding_base_url: str = "http://127.0.0.1:11434"
    embedding_dimensions: int = Field(default=768, ge=1)
    embedding_revision: str = "v1"
    embedding_timeout_seconds: float = Field(default=30.0, gt=0)
    memory_candidate_count: int = Field(default=40, ge=20, le=50)
    conversation_memory_retrieval_enabled: bool = False
    conversation_memory_retrieval_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    conversation_memory_retrieval_top_k: int = Field(default=5, ge=1, le=20)
    conversation_memory_candidate_limit: int = Field(default=40, ge=1, le=100)
    conversation_history_turn_limit: int = Field(default=12, ge=1, le=100)
    max_dialogue_chars: int = 240
    memory_top_k: int = 5
    conversation_enabled: bool = False
    # The structured contract/output bounds are the selected, bounded defaults;
    # all other runtime policy stays unset until a deployment explicitly configures it.
    conversation_policy_version: str | None = None
    conversation_total_deadline_seconds: float | None = None
    conversation_provider_stage_budget_seconds: float | None = None
    conversation_context_token_limit: int | None = None
    conversation_generation_token_limit: int | None = Field(default=2048, ge=1, le=16384)
    conversation_contract_json_char_limit: int | None = Field(default=16384, ge=1, le=65536)
    conversation_output_char_limit: int | None = None
    conversation_beat_char_limit: int | None = None
    conversation_queue_capacity: int | None = None
    conversation_lease_duration_seconds: float | None = None
    conversation_summary_trigger_turns: int | None = None
    conversation_diagnostic_retention_seconds: float | None = None
    conversation_delivery_wait_seconds: float | None = None
    conversation_worker_count: int | None = None
    conversation_worker_id: str | None = None

    @property
    def cors_origins(self) -> List[str]:
        if self.app_cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
