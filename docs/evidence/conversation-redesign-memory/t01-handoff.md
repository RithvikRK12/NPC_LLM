# memory/T01 handoff

Date: 2026-10-15

## Scope delivered

- Added `backend/app/services/conversation/memory.py` with a pure `MemoryPolicy`.
- `plan(turn, reply, proposal)` emits only `player_report` writes whose message source is present in the accepted assembled reply's evidence dependencies. Reports keep their attribution and source reference and are always `unverified`, including claims about mechanical outcomes. Missing, mismatched, private, or out-of-scope final evidence emits no write.
- `filter_retrieval(records, key, current_facts=..., retracted_ids=...)` enforces exact scope/NPC/epoch, active status, source scope/visibility, explicit retraction IDs, and current mechanical-source precedence. It excludes interpretations from cross-turn retrieval so emotional observations do not become enduring player attributes.
- Added five focused tests in `backend/tests/test_conversation_memory.py` for mechanical claim provenance, draft exclusion, scope/status/retraction filtering, private and temporary interpretation exclusion, and current inventory precedence.

No database/index adapter, write-port integration, or summary refresh code was changed; those belong to T02/adapters.

## Verification

- RED: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_memory -v` failed because `app.services.conversation.memory` did not yet exist.
- GREEN: same focused command — **5 passed**.
- Adjacent contracts and port conformance: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_contracts_continuity backend.tests.test_conversation_contracts_interfaces backend.tests.conversation_port_conformance -v` — **30 passed**.
- Conversation suite: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` — **232 tests, 1 failure** in pre-existing `test_conversation_generation_adapter.GenerationAdapterTests.test_live_port_sends_one_bounded_request_with_remaining_deadline_and_typed_contract`; it expected credentials/query data to be stripped from the endpoint URL.
- Full backend suite: `PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests` (from `backend/`) — **603 tests, 7 errors**. The failures include legacy API tests importing missing `PromptBuilder` from `app.services.prompts.builder`, and generation-adapter tests. These failures are outside the memory module; the focused and adjacent memory checks passed.
- `git diff --check -- backend/app/services/conversation/memory.py backend/tests/test_conversation_memory.py` — clean.

## Handoff limits

The pure policy relies on the proposal boundary to validate exact current-message span contents before calling `plan`; it additionally requires a matching player-message dependency in the accepted assembled reply. Current-fact precedence is keyed by matching authoritative source kind and source ID. Durable correction-head CAS, adapters, and summary lineage remain outside T01.


## Main Agent review update (2026-10-15)

Main Agent reproduced the focused memory suite (5/5) and adjacent contracts/port checks (35/35). This task is locally accepted. The broader failures recorded above came from concurrent provider and persistence work at the time of the worker run; persistence/T01 subsequently reports its own SQLite schema checks passing. No memory policy expansion or adapter integration is included.
