# Architecture Mapping

This MVP maps the paper's blocks to concrete modules:

- Context Builder: `backend/app/services/context/`
- Prompt Builder: `backend/app/services/prompts/`
- LLM Service: `backend/app/services/llm/`
- Validation: `backend/app/services/validation/`
- Rule Engine V1: `backend/app/services/rule_engine/`
- Role Conditioning: `backend/app/services/npc/conditioning.py`
- State Update: `backend/app/services/state/`
- Memory System: `backend/app/services/memory/`
- Conversation Logging: `backend/app/models/conversation.py`
- API: `backend/app/api/`
- Game Frontend: `frontend/godot/`

The frontend does not contain AI logic. It only sends player input and renders the backend response.

## Selective semantic memory

`importance.py` decides whether an accepted interaction deserves a durable memory.
`embedding.py` calls local Ollama Nomic embeddings (768 dimensions, normalized,
query/document task prefixes). The old hashed `embedding` column is legacy data;
new vectors live in `semantic_embedding` with a model/revision identifier.

`index.py` builds cached FAISS HNSW graphs from SQL-filtered vectors, scoped to an
NPC, model, optional event types, quest and time range. A transactional NPC memory
revision invalidates old graph snapshots after writes, deletions and resets.
`service.py` retrieves 40 candidates, fetches only their records, filters and
consolidates duplicates, and reranks with 0.65 similarity + 0.20 importance + 0.15
recency to return up to five memories. Conversation history remains separate.

The database is authoritative; indexes are disposable in-process caches. Graphs
are rebuilt on first use, after memory mutation or cache eviction, not on every
ordinary dialogue request. See `memory-selection.md` for setup and limitations.
