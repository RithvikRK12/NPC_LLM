from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class StateUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    trust: float = Field(default=0.0, ge=-1.0, le=1.0)
    fear: float = Field(default=0.0, ge=-1.0, le=1.0)
    aggression: float = Field(default=0.0, ge=-1.0, le=1.0)
    curiosity: float = Field(default=0.0, ge=-1.0, le=1.0)


class FactualProposal(BaseModel):
    """Non-authorizing selection contract; omitted cosmetic fields need no repair.

    Supplied effects still undergo validation. Never inherit model prose or intent
    into executable output. Keep the full legacy shape accepted for providers
    that choose to return it.
    """
    model_config = ConfigDict(extra='forbid')
    answer_kind: Literal['answer', 'clarify']
    fact_ids: list[str] = Field(default_factory=list, max_length=2)
    action: Literal['speak'] = 'speak'
    item: None = None
    state_update: StateUpdate = Field(default_factory=StateUpdate)
    intent: str = ''
    emotion: str = ''
    dialogue: str = ''
    reasoning: str = ''


class LLMResponse(BaseModel):
    answer_kind: Literal["chat", "answer", "clarify"] = "chat"
    fact_ids: list[str] = Field(default_factory=list, max_length=2)
    intent: str = Field(min_length=1)
    emotion: str = Field(min_length=1)
    dialogue: str = Field(min_length=1, max_length=600)
    action: str = Field(min_length=1)
    item: str | None = None
    reasoning: str = Field(min_length=1)
    state_update: StateUpdate
