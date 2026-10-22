# persistence-adapters/T06 handoff — accepted

## Scope

T06 adds portable durable schema and migration support for attributed contract-memory revisions and summary CAS metadata. Per the recorded scope clarification in the task packet, T04 owns the transaction semantics: active memory revision CAS, dirty-key scanning, summary publication CAS, and matching dirty-marker clear.

## Changes

- Added `conversation_memory_revisions`, keyed by scope, NPC, memory identity, and revision, with a partial unique active-head index on SQLite and PostgreSQL.
- Added `summary_revision` and `summary_dirty` to conversation streams and `revision` to stored summaries.
- Extended `upgrade_conversation_schema` with idempotent additive columns and table creation. Existing stream and summary data remain intact with defaults for new metadata.
- Added fresh-schema, populated-upgrade, repeatability, and active-memory-head constraint coverage.

## Verification

- SQLite: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_persistence_schema.py' -v` — 6/6 passed.
- PostgreSQL 16.15: disposable `npc_test_t06_*` database, same schema suite — 6/6 passed; runner dropped the database.
- `git diff --check` — clean.

T06 is accepted locally. Persistence-adapters/T04 resumes for contract-memory write CAS, scoped reads, summary CAS/dirty scanning, and race/rollback acceptance.
