# coordinator/T02 handoff

Task: `coordinator/T02` — integrate action composition and durable recovery. Main Agent accepted on 2026-10-18 after review and independent reproduction.

## Scope and files

- `backend/app/services/conversation/coordinator.py` — added optional frozen `TurnStore` recovery boundary handling, terminal-result replay, fenced recovery, pre-dispatch proposal/action-composition attempt reservation, output persistence, committed-receipt-first composition, uncertain operation commit lookup, staged assembled-reply persistence, and revalidation of recovered assembly before publication. A prior dispatched provider call without persisted output is never repeated. No provider work occurs inside the short store calls.
- `backend/tests/test_conversation_coordinator.py` — covered durable attempt ordering, malformed provider envelopes, uncertain proposal dispatch, action receipt reuse, lost composition output, uncertain operation commit, early failure receipt preservation, staged reply recovery/revalidation, final-result replay, and concurrent terminal recovery.
- `docs/redesign-tasks/coordinator.md` and `docs/redesign-master-progress.md` — task claim, acceptance, evidence, and next-task ledger.

The task stayed within the coordinator and its focused tests. Pipeline wiring and durable queue worker continuation remain coordinator/T03.

## Verification

All commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1`, using `.venv` Python 3.12.14 and deterministic local fixtures; no live provider was called.

- RED checks were observed before implementation: the new terminal recovery case failed because `recovery_store` was not accepted; receipt recovery attempted operation execution; uncertain proposal dispatch was repeated; malformed durable provider success escaped as a schema exception; staged reply and early receipt cases exposed ordering defects. Corrections were followed by green reruns.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_coordinator.py' -v` — exit 0; 18 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_composition*.py' -v` — exit 0; 38 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_operations.py' -v` — exit 0; 24 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_turns.py' -v` — exit 0; 29 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_persistence*.py' -v` — exit 0; 67 passed, 0 failed/skipped. This adapter suite uses isolated SQLite fixtures; PostgreSQL adapter acceptance remains documented in the persistence-adapters packet evidence.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -q` — exit 0; 565 passed, 0 failed/skipped. [Log](t02-tests.log). Existing Starlette/httpx and SQLAlchemy datetime deprecation warnings were emitted; no test failed.
- `git diff --check` — exit 0.

## Acceptance outcomes

- Resolve operation once, then compose from committed receipt — verified by receipt recovery tests; the operation port is skipped when a receipt exists.
- Persist proposal/composition budget before provider dispatch and typed output after — verified with ordered durable-store fake events; exhausted or uncertain purposes fail over without redispatch.
- Resume outputs/receipt/assembly after restart — persisted proposal and composition outputs are reused; recovered receipt bypasses execution; saved assembly skips regeneration and is validated against current evidence before publication.
- Lost operation acknowledgement — coordinator re-reads recovery and either composes from the durable receipt, returns a concurrently finalized exact result, or leaves the turn recoverable on lookup failure.
- Same-ID final retry — finalized result is returned unchanged, including when the caller's fence is stale; it is never regenerated.
- Receipt-safe fallback — receipt remains attached through interaction/proposal failures, and fallback evidence is checked against the exact receipt.
- No provider calls under the store transaction — calls are sequenced after each detached store method returns. Existing persistence conformance tests verify short transaction boundaries and effect/receipt atomicity.

An independent read-only review found and helped correct early receipt loss, terminal replay ordering, malformed persisted output handling, and staged assembly operation redispatch. Final focused and full conversation suites were rerun after the corrections.

## Limits and follow-up

- This task does not wire the production pipeline or durable pending-turn worker. That is `coordinator/T03`.
- Repair uses the existing single-use `RepairAllowance`/durable reservation contract; production repair-hook wiring remains in coordinator/T03 integration.
- Tests exercise coordinator durable behavior with scripted ports and verify concrete SQL behavior in adjacent persistence suites; this task does not claim a live provider or game rollout acceptance.

Next: `coordinator/T03` — wire durable worker continuation and versioned pipeline switch. Its prerequisites `coordinator/T02` and `lifecycle/T02` now have local evidence.
