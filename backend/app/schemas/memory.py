from datetime import datetime

from app.schemas.common import ORMBaseModel


class MemoryRead(ORMBaseModel):
    id: int
    npc_id: int
    event: str
    importance: float
    emotion: str
    timestamp: datetime
    event_type: str = "legacy"
    quest_id: str | None = None
