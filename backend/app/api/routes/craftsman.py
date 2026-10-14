from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import NPC
from app.schemas.craftsman import CraftsmanCommand, CraftsmanCheckpoint
from app.services.opening import current_run
from app.services.craftsman import apply_command, checkpoint
router = APIRouter(prefix='/craftsman',tags=['craftsman'])
@router.post('/command')
def command(request: CraftsmanCommand, db: Session = Depends(get_db)):
    player = current_run(db,request.game_scope)
    npc = db.get(NPC,request.npc_id)
    if npc is None: raise HTTPException(404,'NPC not found')
    result = apply_command(db,player,npc,request.command,request.request_id,request.expected_revision,request.payload)
    db.commit()
    return result
@router.put('/checkpoint')
def save_checkpoint(request: CraftsmanCheckpoint, db: Session = Depends(get_db)):
    player = current_run(db,request.game_scope)
    result = checkpoint(db,player,request.checkpoint,request.expected_revision)
    db.commit()
    return result
