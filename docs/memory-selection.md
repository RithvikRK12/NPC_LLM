# Selective semantic NPC memory

Conversation logging and durable memory are separate. Every turn remains a
Conversation record and can enter the latest six exchanges of context.
`importance.py` still classifies events before long-term storage; embeddings
neither decide importance nor authorize gameplay actions.

## Importance and audit flags

- Quest phase change: 0.95; server crafting completion: 1.0.
- Successful ownership-checked transfer: 0.90.
- Explicit player preference, personal fact or commitment: 0.75.
- Changed pending item request, including cancellation: 0.70.
- Routine conversation: 0.10; rejected, fallback or outside-world dialogue: 0.

Retention threshold: 0.65. Each conversation stores
`validated_output.memory_classification`, also returned by chat/transfer APIs.
Fields include important, importance, category, reason, event, stored and version.
A duplicate can be important with stored=false because an existing memory was
refreshed. Player statements remain unverified claims, not world facts.

## Real embeddings

`embedding.py` uses local Ollama `/api/embed` with `nomic-embed-text` and 768
float32 dimensions. Documents use `search_document:`, queries use `search_query:`.
Vectors are checked for shape, finite values and nonzero norm, then normalized.
There is no hashing fallback. SHA-256 in `service.py` is only an exact duplicate
fingerprint, not a representation of meaning.

Similarity can now connect “frightened of the woods” with “afraid of forests”.
This still does not imply reliable reasoning about negation or truth. Similar
sentences are deliberately NOT automatically merged; “I like forests” and “I do
not like forests” must remain separate claims.

## Two-stage retrieval

1. SQL filters by NPC, retention threshold, model/revision and presence of a
   semantic vector. Routine and excluded categories cannot enter the index.
   Optional event-type, quest and inclusive UTC timestamp constraints apply
   before vector search. Naive timestamps are interpreted as UTC.
2. A FAISS HNSW graph uses normalized inner product (cosine similarity) to
   select up to 40 candidates, configurable from 20 to 50. HNSW uses M=32,
   efConstruction=100 and efSearch=100; it is approximate nearest-neighbour
   search rather than an exhaustive Python cosine loop.
3. Only those candidate records are loaded. Metadata is checked again, known
   outside-world memories are removed, and candidates receive the existing score:

   `0.65 * cosine_similarity + 0.20 * importance + 0.15 * recency`

   `recency = 1 / (1 + max(age_hours, 0) / 24)`

4. Sort by score, consolidate identical event summaries within event type and
   quest, then return up to five. If filtering leaves fewer than five, do not
   invent or pad memories. A semantically distant but important event outside
   the candidate set cannot be rescued by reranking; tune candidate count and
   measure recall when growing the game.

## Metadata and consolidation

New Memory fields: event_type, quest_id, duplicate_key, embedding_model and
semantic_embedding. Quest progress/completion use quest_id `get_bow`. Transfers
are not automatically attributed to a quest because players can give items for
other reasons. NPC and timestamp remain existing fields.

Unicode normalization, case folding, whitespace normalization and trailing
sentence punctuation removal identify identical claims and pending requests.
Their timestamp and maximum importance are refreshed within that NPC; transfers
remain individual historical events. Retrieval collapses repeated identical
summaries to avoid spending several context slots on the same fact. Contradiction
resolution and paraphrase consolidation are not implemented. Historical rows
with unknown category remain `legacy` rather than receiving guessed labels.

Service usage:

```python
MemoryService(db).retrieve_relevant_memories(
    npc, "How is my bow coming along?", top_k=5,
    event_types=["quest_progress", "quest_completion"],
    quest_id="get_bow", since=start_time, until=end_time,
)
```

Inspection API (URL-encode spaces):
`GET /memory/1/search?query=bow&quest_id=get_bow&event_type=quest_progress`
Optional `since` and `until` take ISO timestamps. Default chat retrieval remains
NPC-wide so player preferences are not accidentally excluded by a quest filter.
`GET /memory/1` still lists stored records, including unindexed legacy rows.

## Cache consistency and cost

The database persists vectors; FAISS graphs are disposable in-process caches,
not separate files requiring synchronization. A graph key includes the database
engine, NPC, model, metadata scope and NPC memory_revision. ORM memory writes
change that UUID in the same transaction; chat clear and new-game bulk deletion
also change it. Rollback restores the previous revision, preventing uncommitted
memories from leaking into a later request. Each worker reads the shared revision
rather than relying on process-local invalidation messages.

There are at most 32 cached graphs. First use, mutation, reset, changed filters
or eviction can require loading eligible vectors and rebuilding a graph. Warm
queries read one revision and at most 40 candidate records, with graph search
instead of loading and comparing every memory. This implementation favours
correctness for the small demo; it does NOT promise cheap writes at huge scale.
For high-write workloads, use persistent database HNSW or incremental indexing
with transactional change capture. Direct SQL memory changes outside these code
paths must also update `npcs.memory_revision` to invalidate caches.

## Setup and existing data

From the project root, using its Python virtual environment:

```sh
.venv/bin/python -m pip install -r backend/requirements.txt
ollama serve
# In another terminal, only if the model is not already present:
ollama pull nomic-embed-text
PYTHONPATH=backend .venv/bin/python -m app.services.memory.reindex
```

Equivalent when using backend/.venv: change into backend and run
`.venv/bin/python -m app.services.memory.reindex`.

Settings in backend/.env.example include EMBEDDING_MODEL, EMBEDDING_BASE_URL,
EMBEDDING_DIMENSIONS, EMBEDDING_REVISION, EMBEDDING_TIMEOUT_SECONDS and
MEMORY_CANDIDATE_COUNT. When changing model weights/preprocessing under the same
tag, bump EMBEDDING_REVISION and reindex; never mix incompatible vectors.

Startup applies an additive schema migration. Existing hashed 1536-dimensional
vectors and conversations are preserved, but hashed vectors are never searched.
The reindex command batches important unindexed or wrong-model memories through
the semantic model. It supports --npc-id and --batch-size, commits successful
batches, rolls back a failed batch and can be resumed. Legacy importance scores
are preserved, not reclassified; low-priority legacy rows remain unindexed.

If Ollama fails, an important event is still stored without a semantic vector
and an error is logged. Retrieval falls back to no long-term memories while
recent dialogue and authoritative state remain available; it does not silently
use hashes. Run reindex after recovery to repair missing vectors. The existing
new-game reset clears memories each launch, so personalization remains within a
playthrough. The complete conversation log and important memories are not capped.

## Validation

`PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests`

Tests cover the existing game pipeline plus embedding contracts, actual FAISS
nearest-neighbour search, candidate bounds, reranking, metadata prefilters,
normalized duplicates, cache reuse, rollback, reset, incompatible vectors,
provider outage, resumable reindexing and additive migrations. Unit tests use
controlled vectors to avoid network/model nondeterminism. The live Nomic smoke
check is separate; a paraphrase check is evidence of semantic matching, not a
large-scale quality or latency benchmark.

Implementation references: [Ollama embedding API](https://docs.ollama.com/api/embed),
[Nomic task prefixes](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5),
[FAISS index types](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes).
