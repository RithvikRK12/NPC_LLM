from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trust: float = Field(default=0.0, ge=-1.0, le=1.0, allow_inf_nan=False)
    fear: float = Field(default=0.0, ge=-1.0, le=1.0, allow_inf_nan=False)
    aggression: float = Field(default=0.0, ge=-1.0, le=1.0, allow_inf_nan=False)
    curiosity: float = Field(default=0.0, ge=-1.0, le=1.0, allow_inf_nan=False)


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str = Field(min_length=1)
    emotion: str = Field(min_length=1)
    dialogue: str = Field(min_length=1, max_length=240)
    action: str = Field(min_length=1)
    item: str | None = None
    reasoning: str = Field(min_length=1, max_length=500)
    state_update: StateUpdate

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "LLMResponse":
        if self.action in {"give_item", "receive_item"} and not self.item:
            raise ValueError("transfer actions require an item")
        if self.intent == "confirm_transfer" and self.action != "ask_question":
            raise ValueError("confirm_transfer must ask a question")
        if self.intent == "cancel_transfer" and self.action in {"give_item", "receive_item"}:
            raise ValueError("cancel_transfer must not transfer an item")
        return self
