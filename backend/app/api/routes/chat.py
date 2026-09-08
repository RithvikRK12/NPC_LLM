from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_pipeline
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.pipeline import ConversationPipeline

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, pipeline: ConversationPipeline = Depends(get_pipeline)) -> ChatResponse:
    try:
        return pipeline.chat(request.npc_id, request.player_message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc