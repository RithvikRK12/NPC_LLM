from pydantic import BaseModel

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