from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMBaseModel


class NPCRead(ORMBaseModel):
    id: int
    name: str
    role: str
    trust: float
    fear: float
    aggression: float
    curiosity: float
    location: str
    current_state: str
    pending_item: str | None = None
    inventory: list[str]


class NPCStateUpdate(BaseModel):
    trust: float | None = None
    fear: float | None = None
    aggression: float | None = None
    curiosity: float | None = None
    current_state: str | None = None


class NPCEmotionEdit(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    game_scope: str = Field(min_length=1)
    trust: float = Field(ge=0, le=1)
    fear: float = Field(ge=0, le=1)
    aggression: float = Field(ge=0, le=1)
    curiosity: float = Field(ge=0, le=1)
