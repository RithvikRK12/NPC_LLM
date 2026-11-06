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

    game_scope: str | None = None
    source_event_id: str | None = None
    source_conversation_id: int | None = None
    epistemic_status: str = 'interpretation'
    authority: str = 'inferred'
    lifecycle: str = 'active'
    correction_of_id: int | None = None
    superseded_by_id: int | None = None
