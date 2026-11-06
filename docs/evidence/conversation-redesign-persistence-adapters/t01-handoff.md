# persistence-adapters/T01 handoff

Date: 2026-10-15 (Asia/Kolkata)
Status: locally implemented and verified on isolated SQLite databases.

## Scope delivered

- Added scoped SQLAlchemy records for `conversation_streams`, `conversation_turns`, `conversation_operations`, `pending_interactions`, `character_canon`, and `conversation_summaries`.
- Enforced stream, request, sequence, operation-turn, canon revision, active canon-head, and single active item-negotiation uniqueness in the schema. Active-head and active-negotiation indexes are partial indexes for SQLite and PostgreSQL.
- Added nullable `turn_id`, `conversation_epoch`, `sequence`, and `origin` linkage to legacy transcripts; added nullable `conversation_epoch` and `source_turn_id` to memories.
- Added an additive, idempotent migration and database initialization wiring. Unknown legacy scope/provenance remains null. Only conversation IDs explicitly present in `legacy_id_map` receive redesigned identity fields.
- Canon and operation receipt rows have no foreign key/cascade path through display transcript rows. The focused deletion check removes a transcript and confirms both records remain.

## Verification

RED was observed before implementation: four focused tests errored because `app.database.conversation_migration` did not exist.

Passing checks:

- `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_persistence_schema -v` — 4 passed.
- `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_semantic_memory backend.tests.test_inventory_migration -v` — 21 passed.
- From `backend/tests`: `PYTHONPATH=.. ../../.venv/bin/python -m unittest test_memory_provenance -v` — 14 passed.
- `git diff --check` — passed at handoff review.

The conversation-wide check was run with `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v`. At that moment it ran 250 tests and failed with one in-progress `interactions/T02` placeholder assertion (`test_selection_binds_only_the_selected_offered_action`) and eight unrelated fixture validation errors where `stone` was no longer an allowed test capability value. No persistence-schema test failed in that run.

## Limits

- The original 2026-10-15 handoff had no PostgreSQL service, so it left DDL and index execution unverified at that time. The service became available on 2026-10-18; the PostgreSQL gap was resolved by the acceptance addendum below.
- This task establishes schema and additive migration behavior only. It does not verify T02 atomic admission/claims, T03 receipt transactions, T04 lifecycle/read-store semantics, or SQLite/PostgreSQL concurrent behavior.

## Main Agent PostgreSQL acceptance addendum

Date: 2026-10-18 (Asia/Kolkata)

- PostgreSQL 16.15 was reachable at `127.0.0.1:5433` using the local Compose service. Tests used a uniquely named disposable database with the `npc_test_t01_` prefix and dropped it after the run.
- Initial PostgreSQL execution exposed test portability issues: legacy test DDL used SQLite-only `DATETIME`, broad metadata creation included the unrelated pgvector memory type, and expected constraint violations were not isolated from PostgreSQL's aborted-transaction behavior. The T01 tests were updated to create only relevant schema and use savepoints for expected constraint failures.
- `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_persistence_schema -v` — SQLite, exit 0, 4 passed, 0 failed/errors/skipped.
- `CONVERSATION_TEST_ADMIN_URL='postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/mvp' PYTHONPATH=backend .venv/bin/python docs/evidence/conversation-redesign-persistence-adapters/run_t01_postgres_acceptance.py` — exit 0, PostgreSQL 16.15, 4 passed, 0 failed/errors/skipped. The runner creates and drops a unique `npc_test_t01_*` database; the conversation test suite supports `CONVERSATION_TEST_DATABASE_URL` and refuses names outside the disposable prefix.
- `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_semantic_memory backend.tests.test_inventory_migration -v` — exit 0, 21 passed, 0 failed/errors/skipped. One existing `datetime.utcnow()` deprecation warning was emitted.
- `git diff --check -- backend/tests/test_conversation_persistence_schema.py docs/redesign-tasks/persistence-adapters.md docs/redesign-master-progress.md` — exit 0.

Main Agent reviewed the T01 criteria and accepts the local PostgreSQL schema/migration gate. T02–T04 transaction and race gates remain open.
