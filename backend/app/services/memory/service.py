from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.models.npc import NPC
from app.services.memory.embedding import EmbeddingService
from app.utils.math_utils import cosine_similarity


@dataclass(slots=True)
class RetrievedMemory:
    id: int
    npc_id: int
    event: str
    importance: float
    emotion: str
    timestamp: datetime
    score: float

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "npc_id": self.npc_id,
            "event": self.event,
            "importance": self.importance,
            "emotion": self.emotion,
            "timestamp": self.timestamp.isoformat(),
            "score": self.score,
        }


class MemoryService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._embedder = EmbeddingService()

    def store_memory(self, npc: NPC, event: str, importance: float, emotion: str) -> Memory:
        memory = Memory(
            npc_id=npc.id,
            event=event,
            importance=importance,
            emotion=emotion,
            embedding=self._embedder.embed(event),
        )
        self._db.add(memory)
        self._db.commit()
        self._db.refresh(memory)
        return memory

    def retrieve_relevant_memories(self, npc: NPC, query: str, top_k: int = 5) -> list[RetrievedMemory]:
        rows = list(self._db.scalars(select(Memory).where(Memory.npc_id == npc.id).order_by(Memory.timestamp.desc())))
        if not rows:
            return []

        query_embedding = self._embedder.embed(query)
        now = datetime.now(timezone.utc)
        scored_rows: list[RetrievedMemory] = []

        for memory in rows:
            memory_embedding = memory.embedding or []
            similarity = cosine_similarity(query_embedding, memory_embedding)
            age_hours = max((now.replace(tzinfo=None) - memory.timestamp).total_seconds() / 3600.0, 0.0)
            recency = 1.0 / (1.0 + age_hours / 24.0)
            score = (similarity * 0.65) + (memory.importance * 0.20) + (recency * 0.15)
            scored_rows.append(
                RetrievedMemory(
                    id=memory.id,
                    npc_id=memory.npc_id,
                    event=memory.event,
                    importance=memory.importance,
                    emotion=memory.emotion,
                    timestamp=memory.timestamp,
                    score=score,
                )
            )

        scored_rows.sort(key=lambda item: item.score, reverse=True)
        return scored_rows[:top_k]

    def build_interaction_memory(
        self,
        npc: NPC,
        player_input: str,
        dialogue: str,
        action: str,
        relationship_mode: str | None = None,
    ) -> str:
        rule_fragment = f" Relationship mode: {relationship_mode}." if relationship_mode else ""
        return f"Player said '{player_input}'. NPC responded with '{dialogue}' and action '{action}'.{rule_fragment}"