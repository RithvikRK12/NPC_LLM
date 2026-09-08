from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.npc import NPC
from app.models.player import Player
from app.models.quest import Quest
from app.services.context.models import ConversationContext
from app.services.memory.service import MemoryService


class ContextBuilder:
    def __init__(self, db: Session, memory_service: MemoryService | None = None) -> None:
        self._db = db
        self._settings = get_settings()
        self._memory_service = memory_service or MemoryService(db)

    def build(self, npc: NPC, player: Player, player_input: str) -> ConversationContext:
        quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id))
        quest_payload = {
            "id": quest.id if quest else None,
            "status": quest.status if quest else "unknown",
            "progress": quest.progress if quest else 0,
        }
        memories = self._memory_service.retrieve_relevant_memories(npc=npc, query=player_input, top_k=self._settings.memory_top_k)
        return ConversationContext(
            player_input=player_input,
            npc_state={
                "id": npc.id,
                "name": npc.name,
                "role": npc.role,
                "trust": npc.trust,
                "fear": npc.fear,
                "aggression": npc.aggression,
                "curiosity": npc.curiosity,
                "location": npc.location,
                "current_state": npc.current_state,
            },
            memories=[memory.to_payload() for memory in memories],
            quest=quest_payload,
            inventory=list(player.inventory or []),
            location=player.current_location,
            time=datetime.utcnow().isoformat(timespec="seconds"),
            npc_name=npc.name,
            npc_role=npc.role,
        )