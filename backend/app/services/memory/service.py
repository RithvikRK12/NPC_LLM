from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import hashlib
import logging
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.services.memory.importance import MIN_IMPORTANCE
from app.models.npc import NPC
from app.services.memory.embedding import EmbeddingService, EmbeddingUnavailable
from app.services.memory.index import CandidateIndex, cached_index
from app.config.settings import get_settings
from app.services.validation.knowledge import outside_world
logger = logging.getLogger(__name__)


def normalized_event(event):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", event).casefold()).strip().rstrip(".! ")


def duplicate_key(event, event_type, quest_id):
    # This hash identifies exact duplicates only; it is NEVER an embedding.
    return hashlib.sha256(f"{event_type}|{quest_id}|{normalized_event(event)}".encode()).hexdigest()


@dataclass(slots=True)
class RetrievedMemory:
    id: int
    npc_id: int
    event: str
    importance: float
    emotion: str
    timestamp: datetime
    score: float
    event_type: str = "legacy"
    quest_id: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "npc_id": self.npc_id,
            "event": self.event,
            "importance": self.importance,
            "emotion": self.emotion,
            "timestamp": self.timestamp.isoformat(),
            "score": self.score,
            "event_type": self.event_type,
            "quest_id": self.quest_id,
        }


class MemoryService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._embedder = EmbeddingService()

    def store_memory(self, npc: NPC, event: str, importance: float, emotion: str,
                     *, event_type: str = 'legacy', quest_id: str | None = None) -> Memory | None:
        if importance < MIN_IMPORTANCE:
            return None
        event = event[:512]
        key = duplicate_key(event, event_type, quest_id)
        consolidatable = event_type in {'preference', 'personal_fact', 'commitment', 'item_request'}
        if consolidatable or event.startswith(('Player stated', 'Pending item request')):
            existing = self._db.scalar(select(Memory).where(Memory.npc_id == npc.id, Memory.duplicate_key == key))
            if existing is not None:
                existing.timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
                existing.importance = max(existing.importance, importance)
                self._db.flush()
                return None
        vector = None
        try:
            vector = self._embedder.embed(event)
        except EmbeddingUnavailable:
            # Preserve important events even if Ollama is down; explicit reindex repairs them.
            logger.exception('Memory saved without semantic vector; run memory.reindex when Ollama is available')
        memory = Memory(npc_id=npc.id, event=event, importance=importance, emotion=emotion,
                        semantic_embedding=vector, embedding_model=self._embedder.model_key if vector else None,
                        event_type=event_type, quest_id=quest_id, duplicate_key=key)
        self._db.add(memory)
        self._db.flush()
        self._db.refresh(memory)
        return memory

    def retrieve_relevant_memories(self, npc: NPC, query: str, top_k: int = 5, *,
                                  event_types: list[str] | None = None, quest_id: str | None = None,
                                  since: datetime | None = None, until: datetime | None = None) -> list[RetrievedMemory]:
        if top_k <= 0:
            return []
        def utc_naive(value):
            return value.astimezone(timezone.utc).replace(tzinfo=None) if value and value.tzinfo else value
        since, until = utc_naive(since), utc_naive(until)
        if since and until and since > until:
            raise ValueError('since must not be after until')
        kinds = tuple(sorted(set(event_types))) if event_types is not None else None
        if kinds == ():
            return []
        filters = [Memory.npc_id == npc.id, Memory.importance >= MIN_IMPORTANCE,
                   Memory.embedding_model == self._embedder.model_key,
                   Memory.event_type.notin_(['excluded', 'routine']),
                   Memory.semantic_embedding.is_not(None)]
        if kinds is not None:
            filters.append(Memory.event_type.in_(kinds))
        if quest_id is not None:
            filters.append(Memory.quest_id == quest_id)
        if since is not None:
            filters.append(Memory.timestamp >= since)
        if until is not None:
            filters.append(Memory.timestamp <= until)
        self._db.flush()
        # SQL predicates apply BEFORE graph search. Reuse the scoped graph until its
        # transactional revision changes. Only index construction reads every vector.
        revision = self._db.scalar(select(NPC.memory_revision).where(NPC.id == npc.id))
        cache_key = (self._db.get_bind(), npc.id, revision, self._embedder.model_key, kinds, quest_id, since, until)
        index = cached_index(cache_key, lambda: CandidateIndex.build(
            self._db.execute(select(Memory.id, Memory.semantic_embedding).where(*filters)).all(),
            self._embedder.dimensions))
        if not index.ids:
            return []
        try:
            query_embedding = self._embedder.embed(query, query=True)
        except EmbeddingUnavailable:
            logger.exception('Semantic retrieval unavailable; continuing with recent dialogue and game state')
            return []
        candidates = dict(index.search(query_embedding, get_settings().memory_candidate_count))
        # Recheck metadata against DB and only materialize up to 40 candidate records.
        rows = self._db.scalars(select(Memory).where(*filters, Memory.id.in_(candidates)))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        scored = []
        for memory in rows:
            if outside_world(memory.event):
                continue
            timestamp = utc_naive(memory.timestamp)
            age_hours = max((now - timestamp).total_seconds() / 3600.0, 0.0)
            recency = 1.0 / (1.0 + age_hours / 24.0)
            similarity = min(1.0, max(-1.0, candidates[memory.id]))
            score = similarity * .65 + memory.importance * .20 + recency * .15
            scored.append(RetrievedMemory(memory.id, memory.npc_id, memory.event, memory.importance,
                                          memory.emotion, memory.timestamp, score, memory.event_type, memory.quest_id))
        scored.sort(key=lambda m: (m.score, m.id), reverse=True)
        result, seen = [], set()
        for memory in scored:
            key = duplicate_key(memory.event, memory.event_type, memory.quest_id)
            if key in seen:
                continue
            seen.add(key)
            result.append(memory)
            if len(result) >= top_k:
                break
        return result
