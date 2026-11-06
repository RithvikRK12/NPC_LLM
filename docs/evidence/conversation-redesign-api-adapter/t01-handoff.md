# api-adapter/T01 handoff

Date: 2026-10-15. Worker: api_adapter_t01. Branch: master-progress.
Workdir for every command below: `/Users/rukithnayak/Documents/NPC_LLM-1`.

## Bounded change

Changed `backend/app/api/routes/chat.py`, `backend/app/schemas/chat.py`, and added `backend/tests/test_conversation_api.py`. Existing chat router registration already exposes the new route; world/router files did not require changes. DELETE/clear/reset lifecycle code and all tracker files were left untouched.

The versioned path is selected by presence of `request_id`; explicit null is invalid. Raw input is validated through frozen `TurnSubmission`/`ConversationKey` before legacy coercion. It requires schema version 1, stable ID, scope, `conversation_epoch`, NPC and nonblank message up to 500 characters. Versioned unknown fields, including client `player_id`, are rejected; player resolution remains the server service's responsibility. Missing request ID uses the existing legacy pipeline without adding a request identity or retry claim. Legacy extra fields retain their previous ignored behavior.

Submission accepts only typed status/error values. Pending replies return 202 with `schema_version`, `turn`, `phase`, `status_url`, without speech or response drafts. Finalized statuses return the durable `FinalTurnResult` fields and validated legacy `ChatResponse` projection fields; durable final dialogue overrides any projected root dialogue. State snapshots retain `state_revisions` and detached immutable contract storage. An incomplete legacy projection yields 503 rather than synthesized player state. Invalidated lookup returns 200 identity/status only, with no erased dialogue. Invalidated POST replays and typed `TURN_INVALIDATED` errors return 409; POST 200 is reserved for a durable final result.

The existing port looks up `(ConversationKey, request_id)`, not turn ID. As agreed with Main Agent, `/chat/turns/{turn_id}` carries explicit `request_id`, `game_scope`, `npc_id`, `conversation_epoch` query context in its status URL. GET only calls lookup and checks returned turn ID, request ID and full key; mismatches return 404. It does not submit, generate, execute, or invoke legacy chat.

## Verification

All commands use the workdir above and isolated deterministic tests. No live provider or player database is needed by the focused API tests.

| Phase | Exact command | Exit | Results |
| --- | --- | --- | --- |
| Initial RED | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_api.py'` | 1 | 9 tests: 1 passed, 6 failed, 2 errored; 15 assertion failure records including subtests. Failures showed redesigned requests still returned legacy 200 and absent status route; errors were downstream missing `turn` keys. 0 skipped. |
| Key isolation RED | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_api.py'` | 1 | 11 tests: 10 passed, 1 failed, 0 errors/skipped. Wrong returned lookup key exposed 202 instead of 404. |
| Compatibility/strictness RED | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_api.py'` | 1 | 12 tests: 10 passed, 2 failed, 0 errors/skipped; 4 assertion failure records including subtests. Legacy extras were rejected and versioned boolean/float NPC IDs were coerced. |
| Invalidated POST RED | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_api.py'` | 1 | 13 tests: 12 passed, 1 failed, 0 errors/skipped; invalidated POST returned 200 instead of required 409. |
| Final focused GREEN | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_api.py' -v` | 0 | 13 passed; 0 failed/errors/skipped. |
| Final conversation checks | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | 0 | 269 passed; 0 failed/errors/skipped. Includes frozen contract, turn service, store port and API cases. |
| Final adjacent ports | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_*ports.py'` | 0 | 58 passed; 0 failed/errors/skipped. |
| Full backend, after conversation checks | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_*.py' > /tmp/api-t01-full-final.log 2>&1` | 0 | 732 passed; 0 failed/errors/skipped; 6.017 seconds. Covers existing mechanical/API regressions. |
| Diff whitespace | `git diff --check` | 0 | No findings. |

Observed nonfailure output: existing Starlette/httpx deprecation warning; full suite also emits existing datetime deprecations and expected lexical-memory fallback diagnostics. No warnings were suppressed.

## Acceptance mapping and test IDs

All IDs below are `test_conversation_api.ConversationAPITests.<name>`.

| Acceptance | Test IDs |
| --- | --- |
| Required redesigned identity/version/scope/epoch, 422 invalid input/bounds, server-owned player | `test_invalid_versioned_input_rejected_before_admission`, `test_500_character_message_is_admitted` |
| Unknown NPC/save 404; stale scope/epoch and changed payload 409 | `test_unknown_npc_save_stale_key_and_payload_conflict` |
| Pending identity replay; no draft; GET only reads | `test_pending_identity_replays_without_draft_and_status_only_reads` |
| Durable final speech, legacy fields, detached redelivery and revision labels | `test_durable_final_submit_and_lookup_preserve_legacy_and_revisions` |
| Incomplete final snapshot cannot produce success | `test_incomplete_final_projection_is_not_success` |
| Invalidated tombstone has no erased final result; POST invalidation and typed invalidation are 409 | `test_invalidated_lookup_has_no_erased_response`, `test_invalidated_submit_is_conflict_and_typed_invalidation_is_409` |
| Scoped GET requires identity and rejects wrong ID/key | `test_status_requires_scope_and_checks_path_identity`, `test_mismatched_lookup_key_is_rejected` |
| Missing ID retains legacy route and no retry guarantee | `test_missing_request_id_uses_legacy_without_retry_claim` |
| Legacy unknown/player-ID fields retain ignored behavior | `test_legacy_extra_fields_keep_existing_ignored_behavior` |
| Unwired versioned POST honestly unavailable | `test_unwired_versioned_transport_is_unavailable` |

## Integration limits and follow-ups

- `api-adapter/T03` / `coordinator/T03`: versioned POST `/chat` and GET `/chat/turns/{turn_id}` remain deliberately 503 without injected service bindings. Wire both transport dependencies to the same durable application service; add synchronous delivery-budget continuation and complete stable safe error mapping there. Missing-ID legacy POST remains available.
- `api-adapter/T03` / `game-adapters/T01–T03`: real durable final projections must supply complete legacy NPC/inventory/quest/encounter data and correct resource revision tokens. Tests establish transport preservation, not authoritative snapshot production or client revision application.
- `api-adapter/T02`: clear/reset/world projection remains unchanged and is not claimed by this task.
- `persistence-adapters/T02–T04`: HTTP fakes establish no concrete database atomicity, crash durability, or PostgreSQL behavior.
- `get_legacy_pipeline` retains FastAPI-managed `get_db` dependency cleanup. `get_db` only constructs/closes an unconnected SQLAlchemy Session; versioned requests do not construct `ConversationPipeline`, query the legacy database, or create a provider. A later composition root may eliminate even this unused Session allocation. No manual generator lifecycle was introduced.

Main Agent owns task/master checkbox and graph updates; this worker did not edit trackers.
