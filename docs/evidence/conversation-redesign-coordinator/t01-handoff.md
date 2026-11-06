# coordinator/T01 handoff

Task: `coordinator/T01` — sequence pure conversation with injected ports. Main Agent review: accepted locally on 2026-10-18.

## Files changed

- `backend/app/services/conversation/coordinator.py` — added `ConversationCoordinator` and `CoordinatorPorts`. It orders detached context, one proposal, interaction planning, operation decision/dispatch, composition, assembly evidence, assembly, whole-reply validation, optional single repair, continuity planning, and finalization. Errors use grounded fallback and then the same continuity/finalization path. It contains no SQL/provider construction or gameplay/canon policy.
- `backend/tests/test_conversation_coordinator.py` — scripted-port call-order, proposal-failure/fallback publication, no-summary, and wrong-turn-context checks.
- This handoff and coordinator packet/master ledger record the scope and checks.

## Verification

Commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1` with the repository `.venv`:

- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_coordinator.py' -v` — exit 0; 7 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -q` — exit 0; 554 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -c "import sys; import app.services.conversation.coordinator; forbidden={'sqlalchemy','fastapi','httpx','openai'}; loaded=forbidden.intersection(sys.modules); print('forbidden modules loaded:', sorted(loaded)); raise SystemExit(bool(loaded))"` — exit 0; no forbidden modules loaded.
- `git diff --check` — exit 0.

The implementation was added before the focused tests in this run, so no pre-implementation RED result is claimed. A temporary test-fixture construction error was corrected; the final focused and conversation suites are green.

## Acceptance outcomes and limits

- Detached orchestration call order — verified by scripted clean-turn test; no summary port exists in the coordinator seam.
- One ordinary proposal and one optional repair invocation — coordinator calls proposal once and offers repair only once for fully repairable blocking findings. The injected repair port must use `RepairAllowance` and durable reservation; the coordinator does not mint a repair grant.
- Malformed proposal and repair failure — malformed output is rejected without retry; one failed repair routes to fallback. Fallback is passed to continuity and finalization, making durable fallback eligible for subsequent finalized-only history reads.
- Provider/DB/game policy isolation — fresh import check passed; only detached contract values cross `CoordinatorPorts`.
- Independent read-only review found that validation revisions and successful fallback value types needed stricter checks. The coordinator now fails closed on stale validation reports, malformed fallback values, and malformed repair envelopes; regression tests cover the first two. Review follow-up passed.
- Receipt-first outcome — an operation receipt is passed through composition and retained for fallback; concrete transaction/recovery and restart behavior remain coordinator/T02 plus adapter gates.
- The tests use scripted ports and do not prove concrete provider attempt persistence, SQL receipt atomicity, or finalization storage. Those are not T01 claims. Fallback with active canon can still fail closed until the coordinator supplies the validation projections noted in the validation/fallback handoffs.

## Follow-up

- Next ready task: `coordinator/T02` — integrate action composition and durable recovery, including recorded attempt budgets, receipt-first restart recovery, and crash/timeout points.
- `coordinator/T03` remains behind T02 and lifecycle/T02. Production pipeline wiring remains a later task; this T01 deliverable does not edit the legacy pipeline.
