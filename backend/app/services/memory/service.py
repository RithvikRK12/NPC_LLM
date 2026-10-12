from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import hashlib
import logging
import json
import re
import unicodedata

from sqlalchemy import JSON, case, func, or_, select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.services.memory.importance import MIN_IMPORTANCE
from app.models.npc import NPC
from app.models.player import Player
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
    game_scope: str | None = None
    source_event_id: str | None = None
    source_conversation_id: int | None = None
    epistemic_status: str = 'interpretation'
    authority: str = 'inferred'
    lifecycle: str = 'active'
    correction_of_id: int | None = None
    superseded_by_id: int | None = None
    retrieval_mode: str = "semantic"

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "npc_id": self.npc_id,
            "event": self.event,
            "importance": self.importance,
            "emotion": self.emotion,
            "timestamp": self.timestamp.isoformat(),
            "score": self.score,
            "retrieval_mode": self.retrieval_mode,
            "score_kind": "cosine_importance_recency" if self.retrieval_mode == "semantic" else "lexical_importance_recency",
            "event_type": self.event_type,
            "quest_id": self.quest_id,
            **{key: getattr(self, key) for key in ('game_scope', 'source_event_id', 'source_conversation_id',
                 'epistemic_status', 'authority', 'lifecycle', 'correction_of_id', 'superseded_by_id')},
        }


class MemoryService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._embedder = EmbeddingService()
        self.last_retrieval_trace: dict[str, Any] = {}

    def store_conversation(self, npc, conversation):
        from app.services.memory.provenance import store_conversation
        return store_conversation(self, npc, conversation)

    def store_memory(self, npc: NPC, event: str, importance: float, emotion: str,
                     *, event_type: str = 'legacy', quest_id: str | None = None,
                     game_scope: str | None = None, source_event_id: str | None = None,
                     source_conversation_id: int | None = None, epistemic_status: str = 'interpretation',
                     authority: str = 'inferred', claim_text: str | None = None) -> Memory | None:
        if importance < MIN_IMPORTANCE:
            return None
        player = self._db.get(Player, 1)
        game_scope = game_scope or (player.game_scope if player else None)
        if source_event_id:
            existing = self._db.scalar(select(Memory).where(Memory.npc_id == npc.id,
                Memory.game_scope == game_scope, Memory.source_event_id == source_event_id))
            if existing is not None:
                return None
        event = event[:512]
        key = duplicate_key(event, event_type, quest_id)
        consolidatable = event_type in {'preference', 'personal_fact', 'commitment', 'item_request', 'player_claim'}
        if (source_event_id is None or epistemic_status == 'claim') and (consolidatable or event.startswith(('Player stated', 'Pending item request'))):
            existing = self._db.scalar(select(Memory).where(Memory.npc_id == npc.id, Memory.game_scope == game_scope, Memory.lifecycle == 'active', Memory.duplicate_key == key))
            if existing is not None:
                if source_event_id is None:
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
                        event_type=event_type, quest_id=quest_id, duplicate_key=key, game_scope=game_scope,
                        source_event_id=source_event_id, source_conversation_id=source_conversation_id,
                        epistemic_status=epistemic_status, authority=authority, claim_text=claim_text)
        self._db.add(memory)
        self._db.flush()
        self._db.refresh(memory)
        return memory

    def retrieve_relevant_memories(self, npc: NPC, query: str, top_k: int = 5, *,
                                  event_types: list[str] | None = None, quest_id: str | None = None,
                                  since: datetime | None = None, until: datetime | None = None) -> list[RetrievedMemory]:
        bound = get_settings().memory_candidate_count
        result_limit = min(max(top_k, 0), bound)
        trace = {'mode': 'empty', 'reason': 'not_started', 'candidate_limit_per_path': bound,
                 'materialization_limit': 2 * bound, 'result_limit': result_limit,
                 'vector_index_build': 'all_eligible_vector_pairs_on_cache_miss',
                 'malformed_vector_id_limit': 50,
                 'semantic_candidates': 0, 'lexical_candidates': 0, 'selected_ids': []}
        self.last_retrieval_trace = trace

        def finish(result, mode, reason):
            trace.update(mode=mode, reason=reason, selected_ids=[m.id for m in result])
            logger.info('memory_retrieval %s', json.dumps(trace, sort_keys=True))
            return result

        if result_limit <= 0:
            return finish([], 'empty', 'nonpositive_top_k')
        def utc_naive(value):
            return value.astimezone(timezone.utc).replace(tzinfo=None) if value and value.tzinfo else value
        since, until = utc_naive(since), utc_naive(until)
        if since and until and since > until:
            finish([], 'empty', 'invalid_date_range')
            raise ValueError('since must not be after until')
        kinds = tuple(sorted(set(event_types))) if event_types is not None else None
        if kinds == ():
            return finish([], 'empty', 'empty_event_types')
        player = self._db.get(Player, 1)
        if player is None:
            return finish([], 'empty', 'missing_player')
        filters = [Memory.game_scope == player.game_scope, Memory.lifecycle == 'active',
                   Memory.npc_id == npc.id, Memory.importance >= MIN_IMPORTANCE,
                   Memory.event_type.notin_(['excluded', 'routine'])]
        if kinds is not None:
            filters.append(Memory.event_type.in_(kinds))
        if quest_id is not None:
            filters.append(Memory.quest_id == quest_id)
        if since is not None:
            filters.append(Memory.timestamp >= since)
        if until is not None:
            filters.append(Memory.timestamp <= until)
        self._db.flush()
        # Keep the existing scoped semantic index; only its vector build reads all
        # eligible vectors. Each subsequent ORM materialization has an SQL LIMIT.
        semantic_filters = filters + [Memory.embedding_model == self._embedder.model_key,
                                      Memory.semantic_embedding.is_not(None)]
        revision = self._db.scalar(select(NPC.memory_revision).where(NPC.id == npc.id))
        cache_key = (self._db.get_bind(), npc.id, player.game_scope, revision,
                     self._embedder.model_key, kinds, quest_id, since, until)
        index = cached_index(cache_key, lambda: CandidateIndex.build(
            self._db.execute(select(Memory.id, Memory.semantic_embedding).where(*semantic_filters)).all(),
            self._embedder.dimensions))
        candidates = {}
        reason = 'no_eligible_indexed_vectors'
        if index.ids:
            try:
                query_embedding = self._embedder.embed(query, query=True)
                candidates = dict(index.search(query_embedding, bound)[:bound])
                reason = 'query_embedding_available'
            except EmbeddingUnavailable:
                # No fabricated vector or cosine score is used on this path.
                logger.warning('Semantic query embedding unavailable; using bounded lexical retrieval')
                reason = 'query_embedding_unavailable'
        semantic_rows = list(self._db.scalars(select(Memory).where(
            *semantic_filters, Memory.id.in_(candidates)).order_by(Memory.id).limit(bound))) if candidates else []
        trace['semantic_candidates'] = len(semantic_rows)

        lexical_filters = list(filters)
        if reason == 'query_embedding_available':
            # SQL NULL and JSON null both occur in historical/ORM writes.
            lexical_filters.append(or_(Memory.embedding_model.is_(None),
                Memory.embedding_model != self._embedder.model_key,
                Memory.semantic_embedding.is_(None), Memory.semantic_embedding == JSON.NULL,
                Memory.id.in_(index.rejected_ids)))
        # At most 12 distinct ASCII query terms, each at most 32 characters. LIKE
        # parameters are escaped, not interpolated. No Python-wide record scan.
        tokens = sorted(set(re.findall(r'[a-z0-9]{2,32}', query[:500].lower())))[:12]
        matches = [case((func.lower(Memory.event).contains(t, autoescape=True), 1), else_=0) for t in tokens]
        lexical_hits = sum(matches) if matches else 0
        ordering = ([lexical_hits.desc()] if matches else []) + [
            Memory.importance.desc(), Memory.timestamp.desc(), Memory.id.desc()]
        lexical_rows = list(self._db.scalars(select(Memory).where(*lexical_filters)
                                            .order_by(*ordering).limit(bound)))
        trace['lexical_candidates'] = len(lexical_rows)
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        def rank(rows, mode):
            scored = []
            for memory in rows:
                if outside_world(memory.event):
                    continue
                age_hours = max((now - utc_naive(memory.timestamp)).total_seconds() / 3600.0, 0.0)
                recency = 1.0 / (1.0 + age_hours / 24.0)
                relevance = (min(1.0, max(-1.0, candidates[memory.id])) if mode == 'semantic'
                             else sum(t in memory.event.lower() for t in tokens) / max(len(tokens), 1))
                score = relevance * .65 + memory.importance * .20 + recency * .15
                scored.append(RetrievedMemory(
                    id=memory.id, npc_id=memory.npc_id, event=memory.event,
                    importance=memory.importance, emotion=memory.emotion, timestamp=memory.timestamp,
                    score=score, retrieval_mode=mode, **{key: getattr(memory, key) for key in (
                        'event_type', 'quest_id', 'game_scope', 'source_event_id', 'source_conversation_id',
                        'epistemic_status', 'authority', 'lifecycle', 'correction_of_id', 'superseded_by_id')}))
            return sorted(scored, key=lambda m: (m.score, m.id), reverse=True)

        semantic, lexical = rank(semantic_rows, 'semantic'), rank(lexical_rows, 'lexical')
        # Separate rankings are not numerically comparable. Interleave semantic
        # first so vectorless experience gets context slots even in a full index.
        ordered = []
        for i in range(max(len(semantic), len(lexical))):
            if i < len(semantic):
                ordered.append(semantic[i])
            if i < len(lexical):
                ordered.append(lexical[i])
        result, seen = [], set()
        for memory in ordered:
            key = duplicate_key(memory.event, memory.event_type, memory.quest_id)
            if key in seen:
                continue
            seen.add(key)
            result.append(memory)
            if len(result) >= result_limit:
                break
        modes = {m.retrieval_mode for m in result}
        mode = 'mixed' if len(modes) > 1 else next(iter(modes), 'empty')
        if reason == 'query_embedding_available' and lexical_rows:
            reason = 'eligible_memories_without_indexed_vectors'
        return finish(result, mode, reason)
