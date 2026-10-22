# memory/T03 handoff — post-commit conversation embeddings

**Accepted locally by Main Agent: 2026-10-18.**

Conversation-derived memory rows are now flushed with their source conversation without invoking the embedder. The legacy pipeline calls the deferred embedding step only after its authoritative commit. Timed bow completion records the attributed row inside the quest transaction; the quest route invokes deferred embedding after `payload()` commits. The deferred step closes its read transaction before calling the embedder, then acquires the common Player writer and rechecks active scope, memory source ID, conversation source event and NPC before persisting an optional vector. Provider or optional vector-persistence failure leaves the authoritative row intact and does not fail the already committed turn/reward. Exact-source retries reuse the existing memory row.

Regression coverage instruments both the verified transfer pipeline and timed bow reward path. Embedding spies observe no active SQLAlchemy transaction or Player writer marker. Existing outage coverage verifies an attributed, vectorless memory survives provider failure; duplicate-source/provenance tests remain passing.

## Verification

- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_memory_provenance.py' -v` — 14/14 passed.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_behavior_pipeline.py' -v` — 13/13 passed.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_game_adapters.py' -v` — 48/48 passed.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` — 470/470 passed after the T04 publication method landed.
- Full backend discovery — 938/938 passed.
- `git diff --check` — clean.

No gameplay policy, reward rules, or memory authority rules changed. PostgreSQL-specific acceptance is not part of this bounded post-commit caller fix; the existing persistence/game adapter PostgreSQL gates remain recorded separately.
