# finalization/T01 handoff

Date: 2026-10-18. Main Agent review. Status: accepted locally as the prevalidated publication facade.

## Changed files

Implementation was already present in the shared workspace when this review began. Main Agent did not change production code. `backend/app/services/conversation/finalization.py` defines `Finalizer` and an injected `PublicationRefresh` hook; `backend/tests/test_conversation_finalization.py` exercises it against a store double.

## Verification

Commands ran from the repository root with `.venv/bin/python` and deterministic in-memory fixtures:

- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_finalization.py'` — exit 0; 16 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts*.py'` — exit 0; 70 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_canon.py'` — exit 0; 15 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_interactions.py'` — exit 0; 18 passed, 0 failed/skipped.
- Independent reviewer additionally reproduced store ports 32/32 and memory 5/5; all commands exited 0.
- `git diff --check` — exit 0.

## Acceptance mapping and evidence limits

- Scope, epoch, fence, sequence, strict fence type, and continuity-plan identity are prechecked or delegated to the frozen `FinalizationStore` write contract; fake-store tests reject stale conditions before refresh.
- Exact evidence dependencies are passed to the store even when the expected-revision map is empty. The fake rejects missing or changed source values.
- Canon-head and interaction revisions are rechecked by the store boundary; fake tests reject stale canon and a fulfilled interaction reactivation.
- Retryable relevant evidence changes may request one bounded replacement plan after `commit` returns; the callback is not passed into the store. Replacement reply/plan are prechecked again. Unrelated churn does not trigger refresh.
- Historical receipt references survive a stale current-activity refresh; persistent evidence churn returns a recoverable conflict at the refresh limit.
- Independent read-only review found no blocking facade defect.

`PublicationStore` is an in-memory contract double. These tests do not establish SQL transaction atomicity, rollback across transcript/canon writes, durable identical retry, writer-lock order, fencing races, or SQLite/PostgreSQL behavior. Those remain persistence-adapters/T04 and finalization/T02 gates. Provider work is not part of the facade; the refresh hook's generation budget remains coordinator-owned.

## Follow-up

- `finalization/T02`: implement the concrete atomic publication transaction after `persistence-adapters/T04`.
- `coordinator/T01`: invoke the facade with prevalidated reply and continuity plan; keep refresh outside the store boundary.
