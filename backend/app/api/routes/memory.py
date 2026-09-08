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