from __future__ import annotations

from datetime import datetime
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.npc import NPC
from app.models.conversation import Conversation
from app.models.player import Player
from app.models.quest import Quest
from app.services.context.models import ConversationContext
from app.services.memory.service import MemoryService
from app.services.validation.knowledge import outside_world
from app.models.bow_quest import BowQuest
from app.services.quests.bow import snapshot


class ContextBuilder:
    def __init__(self, db: Session, memory_service: MemoryService | None = None) -> None:
        self._db = db
        self._settings = get_settings()
        self._memory_service = memory_service or MemoryService(db)

    def build(self, npc: NPC, player: Player, player_input: str) -> ConversationContext:
        quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id))
        quest_payload = snapshot(self._db.get(BowQuest, player.id))

        memories = self._memory_service.retrieve_relevant_memories(npc=npc, query=player_input, top_k=self._settings.memory_top_k)
        # Always include the latest exchanges, independently of semantic memory ranking.
        recent = list(self._db.scalars(
            select(Conversation).where(Conversation.npc_id == npc.id)
            .order_by(Conversation.id.desc()).limit(6)
        ))
        recent_dialogue = []
        for turn in reversed(recent):
            if outside_world(turn.player_input) or outside_world(turn.final_dialogue):
                continue
            recent_dialogue.append({"role": "user", "content": turn.player_input})
            accepted = dict(turn.validated_output or {})
            accepted.pop("memory_classification", None)
            accepted["dialogue"] = turn.final_dialogue
            recent_dialogue.append({"role": "assistant", "content": json.dumps(accepted)})
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
                "inventory": list(npc.inventory or []),
            },
            memories=[memory.to_payload() for memory in memories if not outside_world(memory.event)],
            recent_dialogue=recent_dialogue,
            quest=quest_payload,
            inventory=list(player.inventory or []),
            location=player.current_location,
            time=datetime.utcnow().isoformat(timespec="seconds"),
            npc_name=npc.name,
            npc_role=npc.role,
        )