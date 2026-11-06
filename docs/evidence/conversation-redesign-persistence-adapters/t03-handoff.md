# persistence-adapters/T03 Main Agent acceptance

Date: 2026-10-18 (Asia/Kolkata)
Status: accepted by Main Agent after independent code review and reproduction.

## Scope reviewed

Implemented the SQL operation gateway's atomic game effect, persisted pending-interaction transition, and receipt transaction. The gateway recovers an existing receipt before dispatch, locks and rechecks the current turn/player boundary, reloads stored consent authority and the admitted answer, then commits the effect and receipt together. Failed receipt writes roll back effects and consent fulfillment. Exact single-offer command terms come from persisted `authorized_operation`; the submitted current answer retains its own candidate/source span and cannot substitute command direction. Caller-owned game writers share the Player lock discipline and preserve rollback.

The Main Agent corrected the single-offer seam during integration: policy keeps the current answer candidate/span after comparing semantic terms against the stored operation; persistence independently reloads the stored operation and compares command, arguments, target, modality, and question. Candidate IDs and source spans remain utterance-specific.

## Verification reproduced

- `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_persistence -v` — SQLite, 47/47 passed. [Log](t03-logs/final-sqlite.log)
- `CONVERSATION_TEST_ADMIN_URL='postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/postgres' PYTHONPATH=backend .venv/bin/python docs/evidence/conversation-redesign-persistence-adapters/run_t03_postgres_acceptance.py` — PostgreSQL 16.15, isolated disposable `npc_test_t03_*`, 47/47 passed. [Log](t03-logs/final-postgresql.log)
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v` — full backend, 935/935 passed. [Log](t03-logs/backend-final.log)
- `git diff --check` — passed.

The PostgreSQL runner creates a uniquely named disposable test database, installs `vector` only there for model metadata, and drops the database. It does not connect tests to `mvp` or touch player saves.

## Handoff boundary

`persistence-adapters/T04` remains responsible for durable publication/lifecycle transactions. Game resource revision ownership is in `game-adapters/T03`. Contracts/T07 is separately accepted and freezes the single-offer consent seam. No lifecycle or publication completion is claimed here.
