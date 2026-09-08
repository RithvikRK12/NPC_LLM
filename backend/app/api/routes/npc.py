from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.npc import NPC
from app.schemas.npc import NPCRead

router = APIRouter(prefix="/npc", tags=["npc"])


@router.get("/{npc_id}", response_model=NPCRead)
def get_npc(npc_id: int, db: Session = Depends(get_db)) -> NPCRead:
    npc = db.scalar(select(NPC).where(NPC.id == npc_id))
    if npc is None:
        raise HTTPException(status_code=404, detail="NPC not found")
    return NPCRead.model_validate(npc)