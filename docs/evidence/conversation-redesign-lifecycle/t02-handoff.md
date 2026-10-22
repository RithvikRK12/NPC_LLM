# lifecycle/T02 handoff

Date: 2026-10-18 (Asia/Kolkata)
Owner: Main Agent

## Deliverable

Added `Lifecycle.new_game(expected_scope)` over the atomic LifecycleStore boundary. It validates and detaches the expected world scope, returns typed invalid-input errors without touching storage, delegates once, and preserves typed stale-scope failures. SQL scope rotation, run-state reset, generated canon deletion and invalidation of old turns remain inside `SQLTurnStore.new_game`, serialized with authoritative game writes.

## Test-first and verification evidence

- Before implementation, the new facade tests failed because `Lifecycle.new_game` did not exist.
- `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_lifecycle test_conversation_persistence_lifecycle`: SQLite 22/22 pass.
- PostgreSQL 16.15 lifecycle runner: 22/22 pass on disposable database `npc_test_lifecycle_t02_144d2a1bd329`, dropped in `finally`; [log](t02-logs/postgresql.log).
- Conversation suite: 511/511 pass; [log](t02-logs/conversation.log).
- Full backend suite: 979/979 pass; [log](t02-logs/backend.log).
- `git diff --check`: exit 0.

The PostgreSQL runner includes the real SQL lifecycle suite with clear/finalization races and reset/late-write scope checks. The facade's reset delegation also runs against that configured SQL store.

## Scope and remaining work

This task adds no reset policy beyond the existing authoritative SQL reset. Production cache and coordinator wiring still need to carry scope/epoch through all async requests and reads.
