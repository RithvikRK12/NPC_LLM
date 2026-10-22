# lifecycle/T01 handoff

Date: 2026-10-18 (Asia/Kolkata)
Owner: Main Agent

## Deliverable

Added `Lifecycle`, a narrow facade over the injected `LifecycleStore`. It validates and detaches the requested `ConversationKey`, returns a typed invalid-input failure without calling storage, and otherwise delegates clear exactly once. The SQL-backed integration test confirms the returned transition reflects the store's atomic epoch advance. The durable deletion/preservation matrix remains implemented and tested at the persistence adapter boundary.

## Test-first evidence and verification

- Before implementation, the focused facade tests failed because `app.services.conversation.lifecycle` did not exist.
- `PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_conversation_lifecycle.py`: 4/4 passed.
- `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_lifecycle test_conversation_persistence_lifecycle`: 18/18 passed, including existing clear/finalization race and preservation tests.
- Persistence-adapters/T04 previously passed SQLite and PostgreSQL lifecycle/publication suites 24/24 each; see [T04 evidence](../conversation-redesign-persistence-adapters/t04-lifecycle-tests.md).

## Scope and remaining work

No lifecycle policy or persistence transaction behavior was added here. `lifecycle/T02` owns new-game scope rotation and async invalidation. SQL finalization issues discovered during T02 integration are recorded separately as `persistence-adapters/T07`.
