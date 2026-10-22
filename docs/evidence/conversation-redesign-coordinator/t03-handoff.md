# coordinator/T03 handoff

Task: `coordinator/T03` — wire durable worker continuation and versioned pipeline switch. Main Agent accepted locally on 2026-10-18.

## Scope and outputs

- Added `backend/app/services/conversation/application.py` with `ProductionCoordinatorPorts`, `ConversationRuntime`, and explicit-policy runtime assembly. It wires SQL context reads, structured generation, operation receipt lookup/dispatch, assembly, validation, durable repair reservation, continuity planning, fallback, and finalization.
- Added deployment settings for the `ConversationPolicy`, worker identity/count, and delivery wait. No numeric runtime defaults were chosen. A partial policy is rejected; enabled runtime requires a complete policy.
- Startup initializes/seeds the database, constructs the runtime, invokes durable `resume_pending()`, and closes workers at shutdown. Without runtime configuration, startup checks for pending durable work and fails safely if such work cannot be resumed.
- Added the `conversation_enabled` switch. When rolled back, new versioned requests are paused; existing identities continue through the durable application service. The coordinator stops new generation and operation dispatch and can finalize an already committed receipt through its receipt-aware fallback.
- Coordinated API dependency binding with `api-adapter/T03`. Its final projection gap was subsequently closed by the API task's durable compatibility projection.

## Verification

- RED: the new runtime assembly test initially failed with `ModuleNotFoundError` for `app.services.conversation.application`.
- Focused application/API/worker/coordinator suite: 44 passed. Application/API subset after the end-to-end compatibility assertion: 20 passed.
- Conversation suite: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` — 580 passed, 0 failed/skipped.
- Full backend suite: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 1,048 passed, 0 failed/skipped.
- `git diff --check` — exit 0.
- SQLite integration: `SQLReceiptTransactionTests` committed a real item transfer and receipt with `SQLTurnStore.execute_once`; a fresh runtime resumed the expired lease with rollback disabled, did not call the provider, finalized the exact receipt, and left the effect/receipt count at one. The adjacent api-adapter/T03 handoff records the final versioned route result and exact retry.
- No live provider call was made. The existing PostgreSQL persistence acceptance remains linked from the persistence packet; this new production startup/rollback integration was run on isolated SQLite.

## Acceptance and limitations

- Durable pending-key discovery, sync delivery wait, queued continuation, queue/lease/deadline validation, startup recovery, and receipt-safe rollback are wired to the production SQL store.
- The feature remains disabled unless a complete, explicitly configured policy is supplied. This preserves the design's unselected numeric latency/context/queue values.
- At this handoff's completion, the `SQLTurnStore` finalizer stored a resource snapshot and the API correctly failed closed while compatibility projection ownership was resolved. api-adapter/T03 subsequently added the durable projection at the finalization boundary and verified degraded delivery and retry.
- Canon claim/evidence extraction remains fail-closed as recorded in the master risks. No generated canon is admitted through an untrusted projection.

## Files changed for this handoff

- `backend/app/services/conversation/application.py`
- `backend/app/config/settings.py`
- `backend/app/main.py`
- `backend/app/api/deps.py`
- `backend/app/api/routes/chat.py`
- `backend/app/services/conversation/worker.py`
- `backend/tests/test_conversation_application.py`
- `backend/tests/test_conversation_api.py`
- `docs/redesign-tasks/coordinator.md`
- `docs/redesign-tasks/api-adapter.md`
- `docs/redesign-master-progress.md`
