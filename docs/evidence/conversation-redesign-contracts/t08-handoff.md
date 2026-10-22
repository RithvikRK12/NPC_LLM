# contracts/T08 handoff — locally accepted

## Scope

Recorded 2026-10-18 after context/T03's first integration test showed that the frozen shared `Identifier` rejected the required literal `/world` scope. Added a dedicated `GameScope` value and applied it only to contract fields that carry a game scope. General IDs and legacy game/timeline mappings remain distinct.

## Files changed

- `backend/app/services/conversation/contracts.py` — `GameScope` accepts existing opaque IDs and safe slash-prefixed paths; rejects blank, duplicate separators, traversal segments, query/fragment syntax and unsupported characters. Applied to conversation keys, provenance, memory, canon, receipts, legacy mapping and world reset results.
- `backend/tests/test_conversation_game_scope.py` — literal `/world` round-trip and unsafe-scope rejection cases.
- `docs/redesign-tasks/contracts.md`, `docs/redesign-tasks/context.md`, `docs/redesign-master-progress.md`, and task graph — recorded the required scope expansion and dependency on context/T03.

## Verification

- RED: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_game_scope -v` — exit 1; `/world` rejected by the old `Identifier` pattern, unsafe-scope test passed.
- GREEN: same focused contract test — 2/2 passed.
- SQLite and PostgreSQL context-read integration verifies `/world` is retained literally and differs from `world`; see [context/T03 handoff](../conversation-redesign-context/t03-handoff.md) and [PostgreSQL log](../conversation-redesign-context/t03-postgresql.log).
- Full backend suite: 965/965 passed as recorded in [context/T03 log](../conversation-redesign-context/t03-backend-suite.log).

No task-specific blocker remains. General identifier validation remains unchanged.
