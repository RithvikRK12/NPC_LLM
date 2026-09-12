from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.memory import Memory
from app.schemas.memory import MemoryRead

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{npc_id}", response_model=list[MemoryRead])
def get_memories(npc_id: int, db: Session = Depends(get_db)) -> list[MemoryRead]:
    memories = list(db.scalars(select(Memory).where(Memory.npc_id == npc_id).order_by(Memory.timestamp.desc())))
    return [MemoryRead.model_validate(memory) for memory in memories]

@router.get('/{npc_id}/search')
def search_memories(npc_id: int, query: str, quest_id: str | None = None,
                    event_type: str | None = None, since: datetime | None = None,
                    until: datetime | None = None, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from app.models import NPC
    from app.services.memory.service import MemoryService
    npc = db.get(NPC, npc_id)
    if npc is None:
        raise HTTPException(status_code=404, detail='NPC not found')
    if not query.strip() or len(query) > 500:
        raise HTTPException(status_code=422, detail='query must contain 1 to 500 characters')
    try:
        rows = MemoryService(db).retrieve_relevant_memories(
            npc, query, event_types=[event_type] if event_type else None,
            quest_id=quest_id, since=since, until=until)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return [row.to_payload() for row in rows]
