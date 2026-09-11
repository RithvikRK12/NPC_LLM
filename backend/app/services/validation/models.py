from __future__ import annotations

from pydantic import BaseModel, Field


class StateUpdate(BaseModel):
    trust: float = Field(default=0.0, ge=-1.0, le=1.0)
    fear: float = Field(default=0.0, ge=-1.0, le=1.0)
    aggression: float = Field(default=0.0, ge=-1.0, le=1.0)
    curiosity: float = Field(default=0.0, ge=-1.0, le=1.0)


class LLMResponse(BaseModel):
    intent: str = Field(min_length=1)
    emotion: str = Field(min_length=1)
    dialogue: str = Field(min_length=1, max_length=240)
    action: str = Field(min_length=1)
    item: str | None = None
    reasoning: str = Field(min_length=1)
    state_update: StateUpdate