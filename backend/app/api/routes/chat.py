from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db

from app.api.deps import get_pipeline
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.pipeline import ConversationPipeline, StaleConversationError

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, pipeline: ConversationPipeline = Depends(get_pipeline)) -> ChatResponse:
    try:
        return pipeline.chat(request.npc_id, request.player_message, game_scope=request.game_scope)
    except StaleConversationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.delete('/{npc_id}')
def clear_chat(npc_id: int, db: Session = Depends(get_db)):
    from sqlalchemy import select, delete
    from app.models import NPC, Player, Conversation, Memory
    # Same lock order as chat/transfer so clearing cannot race a pending reply.
    from app.services.state.locking import lock_player
    lock_player(db)
    npc = db.scalar(select(NPC).where(NPC.id == npc_id).with_for_update())
    if npc is None:
        raise HTTPException(status_code=404, detail='NPC not found')
    from uuid import uuid4
    npc.memory_revision = str(uuid4())
    npc.pending_item = None
    db.execute(delete(Conversation).where(Conversation.npc_id == npc_id))
    db.execute(delete(Memory).where(Memory.npc_id == npc_id))
    db.commit()
    return {'npc_id': npc_id, 'cleared': True}
