from typing import Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.api.deps import get_pipeline
from app.schemas.chat import ChatResponse
from app.services.pipeline import ConversationPipeline

router = APIRouter(prefix='/inventory', tags=['inventory'])


class TransferRequest(BaseModel):
    npc_id: int = Field(ge=1)
    item: Literal['wood', 'axe', 'saw', 'hammer', 'rope', 'water', 'food', 'fruits', 'string', 'bow']
    direction: Literal['to_player', 'to_npc']


@router.post('/transfer', response_model=ChatResponse)
def transfer(request: TransferRequest, pipeline: ConversationPipeline = Depends(get_pipeline)):
    from fastapi import HTTPException
    message = f'give me {request.item}' if request.direction == 'to_player' else f'I give you {request.item}'
    try:
        return pipeline.chat(request.npc_id, message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
