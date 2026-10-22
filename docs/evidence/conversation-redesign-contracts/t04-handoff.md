# contracts/T04 implementation handoff

Task: `contracts/T04`. Implementer: `contracts_t04`. Workspace: `/Users/rukithnayak/Documents/NPC_LLM-1`.

## Delivered

Appended immutable Pydantic value envelopes to `backend/app/services/conversation/contracts.py`. Existing T01–T03 definitions, including `Result[T]`, were preserved. Review corrections modify only the new T04 section. Added `backend/tests/test_conversation_contracts_interfaces.py` and portable valid/rejected JSON fixtures `backend/tests/fixtures/conversation/t04-{valid,rejected}.json`.

| Value | Concrete interpretation of detailed design §§4–6 |
| --- | --- |
| `OptionalResult[T]` | Tagged `status=success/failure`, typed optional value and expected `ConversationError`. Success must explicitly supply `value`, including `None`; failure requires an error. `success(None)` means no turn is ready, never an error. Existing `Result` keeps its original exactly-one-non-null-branch invariant. Ports should use `OptionalResult[TurnLease]` for claim-next. |
| `LeasePolicy` | Explicit schema version, policy version and finite positive lease duration. Separate from `ConversationPolicy`; no tuning default or negotiation expiry. |
| `TurnLease` | Exact `TurnRef`, worker ID, positive durable fence, nonterminal phase, UTC claim and expiry. `validate_current` compares the authoritative active key, fence, earliest nonterminal sequence and aware current time. It cannot establish which turn is earliest. |
| `InteractionTransition` / `InteractionPlan` | Explicit compare-and-swap expected revision plus full replacement interaction; `None` expects absence and initial revision zero, otherwise replacement advances exactly one. Plan is bound to one exact turn and carries consent bindings and optional required clarification. `validate_current` prevents stale revision overwrite, including an operation-committed fulfillment. |
| `MemoryWrite` / `MemoryPlan` | Scoped/epoch-bound attributed memory writes with expected head and explicit nullable correction link. New records start at zero; replacement advances one and requires a correction link. Reports retain unverified player-message provenance; interpretations remain tentative; verified recollections require authoritative event/receipt provenance. `validate_current` rejects changed/missing heads and creation collisions. |
| `ContinuityPlan` | One exact turn, accepted canon changes, scoped memory and interaction subplans, and relevant evidence revisions. `validate_revisions` checks only named dependencies; unrelated revision churn is ignored. `validate_reply` resolves canon spans against the exact accepted final text and matches any final-speech memory source to that reply. |
| `ClearResult` | Explicit `cleared` outcome and previous/current keys. Exactly one epoch increment within the same NPC and game scope. Does not claim to prove deletion/preservation effects. |
| `WorldResult` | Explicit `reset` outcome, previous/new game scopes, detached recursively immutable state projection and revisions. Requires scope replacement; adapter controls run-state reset and API mapping. |
| `SourceRange` / `SummaryEntry` / `SummaryRecord` | Inclusive positive turn-sequence range within an explicit key, attributed memory entries with exact source `TurnRef`s and nullable correction link, source/correction revisions and a matching SHA-256 digest, plus summary revision. Entries preserve uncertainty and active/superseded status. Scoped range checks reject cross-epoch references. `validate_current` rejects changed key or relevant source/correction revisions. |
| `ProviderAttempt` | Added under the coordinator's recorded T04 expansion to cover §5.2/§5.4 durable budgets. Exact turn, attempt ID, dispatch fence, purpose, UTC dispatch stamp, and `dispatched`/`output_persisted` status. A dispatched attempt forbids output; persisted output is required and must be `TurnProposal` for ordinary proposal/proposal-format repair or `CandidateReply` for composition/final-response repair. Required `repair_kind` is `proposal_format` or `final_response` for repair and explicitly null for ordinary stages; both paths share purpose `repair`. The persisted dispatch consumes its purpose even when no output exists. |
| `RecoveredReply` / `TurnRecovery` | Exact turn/fence wrapper around persisted assembly; recovery snapshot holds status, current fence, nullable submission, attempts, receipt and assembly. Duplicate purpose/attempt IDs are rejected, preserving one repair consumption. Historical attempts/assembly keep their original positive fences, which must not exceed the current fence after lease replacement. Receipt identity is checked using its frozen available fields (turn ID/scope/NPC). Invalidated tombstones reject submission, attempts/outputs and assembly; necessary scoped receipt remains permitted. Finalized status carries its exact final result. |

Revision digest uses SHA-256 of UTF-8 JSON for the `source_revisions.resources` map, sorted keys, separators `(',', ':')`, `ensure_ascii=False`. This is a stable integrity description, not an authenticity proof.

No services, ports, adapters, task checkboxes, master status, or graph files were edited by this worker.

## Verification

Commands ran from repository root. Exact output is in adjacent evidence logs.

| Command/check | Exit | Result/evidence |
| --- | ---: | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts_interfaces.py' -v` before initial implementation | 1 | Nine expected missing-interface assertion failures; `t04-red.log` |
| Same focused command after recovery scope expansion, before its implementation | 1 | Eleven expected missing-recovery-value assertion failures; `t04-recovery-red.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_contracts_interfaces.ConversationInterfaceContractTests.test_proposal_format_repair_consumes_the_single_shared_repair_token -v` before review correction | 1 | Expected missing repair-path assertion failure; `t04-repair-path-red.log` |
| Same focused command after implementation | 0 | 12/12 pass; `t04-green.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` | 0 | 71/71 pass, including T01–T03 and current ports conformance; `t04-conversation-suite.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_contract_values.py' -v` | 0 | 13/13 pass; `t04-dependency-contracts.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` | 0 | 534/534 pass; `t04-backend-suite.log`. Existing scripted rejection/retrieval-fallback diagnostics are present; no failures or skips reported. |
| Model/union JSON schema and infrastructure-import boundary check | 0 | 80 model schemas, six union schemas and typed legacy/optional result schemas pass; no DB/provider/HTTP infrastructure import; `t04-boundary-check.log` |
| `git diff --check` and explicit untracked-owned-file whitespace check | 0 | `t04-diff-check.log` |

An initial green attempt revealed two malformed rejected fixtures: Python deep-copy preserved shared fixture aliases, so changing one nested key/turn also changed its expected counterpart. Those rejected fixtures were rebuilt from their independently decoded JSON values; production validators were unchanged by that fixture correction.

## Structural limits and unresolved interpretation

Detailed design §4 names these envelopes but does not prescribe their field layouts. The table above freezes the bounded concrete interpretation for review; no numeric deployment values or product expiry policy were invented. Test lease duration is only a fixture value.

The values do not prove that a source exists, that a report/correction is semantically accepted, that an interaction transition is allowed by the full policy, or that lifecycle effects committed. Source/revision map completeness and authoritative/current lookup belong to owning adapters. In particular, finalization must check actual active canon heads against `CanonChange.expected_revision`, active scope/epoch/fence and stream position, current interaction/memory heads, exact evidence dependencies, and atomically persist publication. These contracts never grant mechanics authority.

The summary adapter must include all applicable source and correction heads in `source_revisions`; the value cannot discover omitted authoritative dependencies. `SummaryEntry.memory` deliberately reuses frozen attributed `MemoryRecord` rather than introducing a second prose/authority model. A nullable correction link records the absence of a correction, rather than inventing one; active/superseded status remains explicit.

The recovery snapshot intentionally preserves historical attempt fences rather than equating them with the current claim fence: §5.2 requires consumed budgets to survive replacement. Old assemblies are recoverable data which require fresh publication revalidation. Frozen T02 receipts lack an epoch/fence field; receipt recovery checks their available turn/scope/NPC identity and relies on scoped turn identity and the gateway's transaction for epoch/fence authorization.

No runtime database/provider calls were made for this contract task. Backend test success does not certify future SQLite/PostgreSQL adapter transaction gates.

## Independent review correction: shared repair token

Review reproduced a legitimate unsupported path: proposal-format repair can produce `TurnProposal`, while the first T04 implementation allowed only `CandidateReply` for purpose `repair`. `ProviderAttempt.repair_kind` now distinguishes `proposal_format` and `final_response`, validates the corresponding persisted output type, and rejects a repair tag on ordinary proposal/composition attempts. Both repair paths retain the same `purpose=repair`, so recovery permits only one across the entire turn. A dispatched proposal-format repair with unavailable output consumes the token and prevents a later final-response repair, including after fence replacement. Shared valid/rejected fixtures and a new test cover both repair orders, output compatibility, explicit null/tag semantics, crash consumption and round trips. The focused, conversation, dependency, full backend, schema/import and diff checks above were rerun after this correction.
