# operations/T02 handoff

Date: 2026-10-18. Owner: Main Agent. Status: accepted locally after independent review.

## Scope and changed files

- `backend/app/services/conversation/operations.py`: added `OperationService`, which looks up a durable receipt before evaluating the proposal, propagates lookup errors, returns a scoped recovered receipt without re-execution, and dispatches only a typed `ReadyToRecheck` through `OperationGateway.execute_once`. It calls execution at most once per invocation and validates returned receipt scope and canonical operation linkage. Non-ready decisions never call execution. The gateway remains the sole source of operation receipts.
- `backend/tests/test_conversation_operations.py`: added five service tests for exact typed dispatch, receipt-first retry, no-op/report speech not authorizing, typed denial without dispatch, and lookup failure. Added a malformed recovered receipt regression after independent review.

No SQL, game-service, route, provider, or shared contract/port files changed. The policy and service have no prose, provider, ORM, or game-service dependency. Real transaction atomicity and authoritative world rechecks remain concrete adapter responsibilities.

## Test-first and verification

All commands ran at the repository root with `.venv/bin/python` and isolated contract fixtures; no live provider or player save was used.

- Initial red: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_operations.py'` — exit 1 because `OperationService` did not exist (`ImportError`).
- Malformed-recovery regression red: same focused command — exit 1 because `OptionalResult.success(object())` raised `AttributeError` while resolving the recovered receipt.
- Focused green: same focused command — exit 0; 20 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_store_ports.py'` — exit 0; 32 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_interactions.py'` — exit 0; 18 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts*.py'` — exit 0; 70 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` — exit 0; 311 passed, 0 failed/skipped. Existing Starlette/httpx deprecation warning.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — exit 0; 774 passed, 0 failed/skipped. Existing Starlette/httpx and `datetime.utcnow()` deprecation warnings, plus the configured lexical-retrieval fallback diagnostic.
- `git diff --check` — exit 0.

An independent read-only review approved T02 after identifying the malformed recovered receipt gap; the regression failed before the guard and passed after it. The reviewer confirmed receipt-first recovery, at-most-once dispatch, typed denials/no-op no-dispatch, exact typed arguments, and gateway-only receipt production. The concrete gateway adapter was not part of this review.

## Acceptance and limits

- Ready typed decision dispatch → verified by exact decision/fence assertions and one gateway invocation.
- Existing operation receipt retry → verified; lookup occurs before policy and execution is skipped.
- Non-ready/denied decisions → verified; no execution call.
- Retry after an uncertain or successful previous operation → the injected durable gateway lookup is consulted first; persistence of the receipt is not proven by this in-process service.
- Receipt scope and selected command/arguments/target linkage → checked for new execution results. Recovered receipts are trusted as the gateway's authoritative scoped receipt after turn/scope/NPC checks.
- No concrete SQLite/PostgreSQL transaction, game-service authorization, concurrent worker, or crash-durability evidence is claimed.

## Follow-up

- `game-adapters/T01` and `persistence-adapters/T03`: implement authoritative, atomic execution and receipt recovery against the frozen gateway contract.
- `coordinator/T02`: call the service at the operation stage and preserve receipt-first recovery semantics.
