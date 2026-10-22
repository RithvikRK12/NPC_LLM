# proposal/T02 handoff — typed provider and shared prompt adapter

Date: 2026-10-15  
Owner: `proposal_t02`  
Scope: provider adaptation, shared prompt parity for the existing Craftsman and Gatherer content, safe provider diagnostics, explicit mock behavior, and typed error mapping. No ports or shared contracts were changed.

## Delivered

- Added `StructuredGenerationAdapter`, which implements the frozen `GenerationPort` contract for `proposal`, `composition`, and `repair`. It chooses the typed Pydantic output model from the purpose, sends one bounded call, applies the remaining monotonic deadline as transport timeout, validates the response strictly, converts JSON arrays to the immutable tuple shape, and rejects content over the response-character budget.
- Added separate adapter exceptions for timeout, cancellation, unavailable provider, malformed output, and unsupported purpose/schema. `ProposalService` maps them into the existing `ConversationError` envelope: timeout → `PROVIDER_TIMEOUT`; unavailable → `PROVIDER_UNAVAILABLE`; malformed → `PROVIDER_INVALID_OUTPUT`; unsupported version → `PROVIDER_INVALID_OUTPUT` with a distinct stage; cancellation → `INTERNAL_FAILURE` with stage `proposal.cancelled`. Safe details do not copy provider exception text. No error-code or port expansion was introduced.
- Added `MockGenerationAdapter` as an explicitly injected mode; it reports `origin=mock`. The live adapter never substitutes mock output for missing configuration or provider failure.
- Added `StructuredPromptBuilder`, shared across supported characters and proposal/composition/repair. It supplies the existing Craftsman anchors and only source-backed Gatherer facts (gathers supplies; can share wood when in stock), preserves supplied context fields as JSON data, states the safety and exact-span rules, and embeds the output JSON schema. The existing `PromptBuilder` remains available for the still-active legacy pipeline.
- Provider diagnostics report provider/model/origin/contract and a redacted base URL. URL userinfo, query, and fragment are stripped before both request dispatch and diagnostics. API keys and provider response bodies are not reported.

## TDD and verification

RED: the new adapter test module initially failed to import `app.services.llm.structured`, as expected before implementation.

GREEN focused command:

```text
PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_generation_adapter backend.tests.test_conversation_proposal backend.tests.test_conversation_composition_service backend.tests.test_conversation_context backend.tests.test_conversation_contracts_interfaces -q
```

Result: exit 0, 66 tests passed.

The full redesign conversation discovery command ran 243 tests and failed only two existing persistence-schema tests: `test_fresh_schema_has_scoped_records_and_uniqueness` (`character_canon.accepted_claim_evidence` NOT NULL) and `test_transcript_deletion_does_not_cascade_into_canon_or_operation_receipt` (`conversations.timestamp` NOT NULL).

Full backend command:

```text
PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -q
```

Result: exit 1, 706 tests run, same two `test_conversation_persistence_schema` SQLite NOT NULL errors. The missing legacy `PromptBuilder` import detected on an earlier full-suite run was restored; legacy `test_npc_pipeline` passed afterward.

`git diff --check`: clean on final focused verification run.

## Files changed

- `backend/app/services/llm/structured.py` (new)
- `backend/app/services/prompts/builder.py` (structured builder added; legacy `PromptBuilder` retained)
- `backend/app/services/conversation/proposal.py` (narrow adapter-failure result mapping; shared T01 file)
- `backend/tests/test_conversation_generation_adapter.py` (new scripted transport and prompt/profile tests)
- `backend/tests/test_conversation_proposal.py` (distinct provider failure mapping coverage)
- `docs/evidence/conversation-redesign-proposal/t02-handoff.md` (this handoff)

## Handoff boundaries

The adapter is not yet wired into the redesigned turn coordinator/runtime composition. The legacy pipeline remains on its existing `LLMService` path; this task preserved compatibility and did not change that route. The two full-suite failures belong to the in-progress persistence schema work and do not touch provider/prompt files. Main Agent owns packet/master/graph status updates.


## Main Agent review update (2026-10-15)

Main Agent independently reproduced the focused adapter/proposal/composition/context/interface command: 66 tests passed. The handoff's earlier two persistence schema fixture errors predate the persistence/T01 fixture fixes; a new combined conversation/backend run is pending interactions/T02 completion. The implementation remains within the frozen GenerationPort boundary.
