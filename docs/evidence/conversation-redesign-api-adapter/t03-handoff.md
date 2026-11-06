# api-adapter/T03 handoff

Task: `api-adapter/T03` — bind versioned submit/status to the shared application service, map safe errors, and return a durable versioned-compatible final response. Completed by Main Agent on 2026-10-18.

## Implemented

- Versioned `/chat` submit and status use the startup-owned application runtime. If no runtime exists, submissions return 503 and do not call the legacy pipeline.
- `VersionedConversationTransport` pauses new versioned admission when `conversation_enabled` is false. An existing identity is resubmitted through the durable service so it can replay or resume its committed receipt. Unknown identities receive a typed safe 503.
- Error mapping preserves stable code, stage, retryability, turn identity, and safe detail without exposing exception context.
- Finalization now stores a legacy `ChatResponse` projection alongside revision-labelled resources. It captures authoritative NPC, inventory, quest, encounter, and scoped active legacy memory values in the publication transaction. Compatibility structured output is explicitly mapped to a no-action chat value; it cannot authorize mechanics.
- Assembled replies carry response origin and degradation reason into the immutable final result. Provider outage fallback is returned as `response_origin=fallback` with its stable failure code.
- Missing, empty, or invalid durable compatibility data fails closed as 503. Exact retry returns the same stored dialogue and receipt references. The internal compatibility projection is omitted from the public response after its legacy fields are merged.
- Requests without `request_id` continue to use the legacy pipeline.

## Verification

Working directory: `/Users/rukithnayak/Documents/NPC_LLM-1`; environment: repository `.venv` Python 3.12.14; deterministic local SQLite fixtures; no live provider calls.

- Red check before implementation: `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_application.ConversationApplicationTests.test_startup_recovery_finalizes_a_committed_receipt_without_reexecuting_it` exited 1 at the expected 503 instead of 200.
- Focused integration: `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_api test_conversation_application test_conversation_persistence test_conversation_finalization test_conversation_composition test_conversation_fallback test_conversation_coordinator test_conversation_api_lifecycle` — exit 0; 146 passed, 0 failed, 0 skipped.
- Conversation suite: `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` — exit 0; 580 passed, 0 failed, 0 skipped.
- Full backend suite: `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest discover -s backend/tests` — exit 0; 1,048 passed, 0 failed, 0 skipped.
- `git diff --check` — exit 0.

## Acceptance outcomes

- Durable degraded response: verified through a real committed SQLite operation receipt, restarted worker, provider-unavailable fallback, and versioned HTTP submit.
- Exact retry: verified identical JSON response, final dialogue, and receipt reference; game effect count remained one.
- Safe storage/internal mapping and typed retry behavior: covered by API contract suite.
- Compatibility projection: verified by Pydantic `ChatResponse` validation and full legacy field assertions in API tests.
- PostgreSQL projection-specific replay: not separately run in this handoff. Existing persistence transaction conformance remains covered in prior T04/T07 evidence; no new concurrency semantics were introduced here.
