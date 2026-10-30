from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.npc import NPC
from app.schemas.npc import NPCRead, NPCEmotionEdit

router = APIRouter(prefix="/npc", tags=["npc"])


@router.get("/{npc_id}", response_model=NPCRead)
def get_npc(npc_id: int, db: Session = Depends(get_db)) -> NPCRead:
    npc = db.scalar(select(NPC).where(NPC.id == npc_id))
    if npc is None:
        raise HTTPException(status_code=404, detail="NPC not found")
    return NPCRead.model_validate(npc)


@router.patch('/{npc_id}/emotions', response_model=NPCRead)
def edit_emotions(npc_id: int, request: NPCEmotionEdit, db: Session = Depends(get_db)) -> NPCRead:
    from uuid import uuid4
    from app.services.state.locking import lock_player
    player = lock_player(db)
    if player is None or player.game_scope != request.game_scope:
        db.rollback()
        raise HTTPException(status_code=409, detail='This game has been replaced. Reload the current game.')
    npc = db.scalar(select(NPC).where(NPC.id == npc_id).with_for_update())
    if npc is None:
        db.rollback()
        raise HTTPException(status_code=404, detail='NPC not found')
    for attribute in ('trust', 'fear', 'aggression', 'curiosity'):
        setattr(npc, attribute, getattr(request, attribute))
    # A reply generated from the old state must fail the pipeline's CAS check.
    npc.memory_revision = str(uuid4())
    db.commit()
    db.refresh(npc)
    return NPCRead.model_validate(npc)
