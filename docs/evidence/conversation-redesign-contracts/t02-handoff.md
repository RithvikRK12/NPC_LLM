# contracts/T02 implementation handoff

Task: `contracts/T02`. Implementer: `contracts_turn_values`. Branch: `master-progress`.
Every command cwd: `/Users/rukithnayak/Documents/NPC_LLM-1`.
Main Agent owns acceptance and packet/master changes. No commits, workers,
network/provider/HTTP/database calls, runtime wiring, or T03 accepted record/result
types were added. Frozen T01 definitions and fixture were preserved.

## Files

- `backend/app/services/conversation/contracts.py`: appended immutable T02 values and their small typed dependencies; module docstring/imports updated for pure hash/JSON utilities.
- `backend/tests/test_conversation_contracts_turn_values.py`: 24 pure contract tests.
- `backend/tests/fixtures/conversation/contracts-t02-valid.json`: literal detached turn, operation, pending, candidate, receipt fixtures including Unicode supporting spans and canonical digest vector.
- `docs/evidence/conversation-redesign-contracts/t02*`: this handoff and full command output logs.

## Verification

Exact command for each focused log below:

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts_turn_values.py' -v
```

| Log | Exit | Count/result |
| --- | --- | --- |
| `t02-red.log` | 1 | 15 tests; 15 expected failures, T02 absent, before implementation |
| `t02-green-initial.log` | 1 | 15 tests; 1 failure from an incorrect test equating current question turn with originating turn; corrected after design review |
| `t02-red-action-choice.log` | 1 | 17 tests; 1 expected validation error because action-choice values were not yet implemented |
| `t02-red-consent-edges.log` | 1 | 19 tests; 5 expected failures proving missing exact offered-choice/sequence checks |
| `t02-red-receipt-consistency.log` | 1 | 22 tests; 1 expected failure, explicit receipt consistency check absent |
| `t02-red-choice-modality.log` | 1 | 23 tests; 6 expected failures proving missing direct/current-question choice checks |
| `t02-red-current-question-order.log` | 1 | 24 tests; 1 expected failure, current question TurnRef absent before review correction |
| `t02-green.log` | 0 | 24 tests, all pass, final implementation including current question ordering |

Additional exact commands:

| Command | Exit | Result/log |
| --- | --- | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts.py' -v` | 0 | 16/16 frozen T01 tests; `t02-t01-regression.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` | 0 | 40/40 final conversation suite; `t02-conversation-suite.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_contract_values.py' -v` | 0 | 13/13 reused pure dependency cases; `t02-dependency-contracts.log` |
| `git diff --check` | 0 | No findings; `t02-diff-check.log` |

Final infrastructure/schema check, exit 0, `t02-boundary-check.log`:

```sh
PYTHONPATH=backend .venv/bin/python - <<'PY'
import sys
from pydantic import TypeAdapter
from app.services.conversation import contracts as c
for name in ['ContextPacket','CapabilityDescriptor','TurnProposal','CandidateReply','AssembledReply','PendingInteraction','ConsentBinding','OperationReceipt']:
    getattr(c, name).model_json_schema()
for name in ['ReplySegment','OperationDecision','AuthoritativeResult','ProposalReference','ParameterSchema']:
    TypeAdapter(getattr(c, name)).json_schema()
assert not any(name.split('.')[0] in {'sqlalchemy','fastapi','httpx','godot'} for name in sys.modules)
print('T02 public model and union schemas build; import is infrastructure-free.')
PY
```

Full application discovery was deliberately excluded by the assigned pure-only,
no-database/provider/network boundary. These results do not certify adapters or
runtime redesign integration. No skipped tests occur in the reported pure suites.

## Acceptance matrix

| Requirement | Value/check | Test coverage/result |
| --- | --- | --- |
| Detached context | ContextPacket includes every §3.2 field, typed profile/canon/evidence/turn/summary values, frozen revision/version maps | Roundtrip, nested detach/freeze, scope/epoch/visibility rejection; pass |
| Capability view | CapabilityDescriptor has command-specific closed parameter schema, target references, availability/safe reason, typed preconditions, speech acts | Item schema/empty schema accepted; arbitrary parameter schema, malformed values and permission fields rejected; pass |
| Proposal | TurnProposal covers concern kinds, resolved entity/topic/unresolved references, attributed reports/corrections, zero-or-more typed operation candidates, interaction links, ordered segments/canon candidates | Multiple candidates remain proposals; every direct/quoted/hypothetical/negated/ambiguous modality represented; duplicate IDs and dangling local concern/correction links rejected; pass |
| Exact source references | TextSpan resolution against supplied exact texts through TurnProposal.validate_references; local canon support resolves immediately against expressive segment text | Astral emoji + combining Unicode offsets; unknown/overflow references rejected; pass |
| Strict segments/renderers | ExpressiveSegment/FactSlot/ReceiptSlot discriminated union, extra-forbid; fixed renderer IDs `fact.exact` and `receipt.{accepted,progress,completed,rejected}` | Arbitrary expressions, renderer/speech-act mismatch, quantity/text injection into slots, unknown tags rejected; pass |
| Candidate/assembly | CandidateReply source/version metadata + segment support; AssembledReply complete final text, exact partitioning beats, detached span map, evidence dependencies, typed continuity references | All source origins including mock; strict versions; dropped characters, stale text IDs, overflow, overlapping support rejected; explicit validate_segment_texts checks exact post-repair support; pass |
| Pending lifetime | PendingInteraction active/suspended/cancelled/fulfilled/expired; expired requires `preconditions_changed`, no timer fields | All statuses exercised; timeout/TTL rejected, resumed question can have later ID/turn while preserving origin; validate_question checks exact lookup, same key, sequence at/after origin; pass |
| Outstanding action choice | PendingInteraction action_choice has >=2 frozen unique offered_operations, each direct and bound to current question, required response choice | Options remain values, no queue; quoted/hypothetical/negated/ambiguous/stale/unasked options rejected; pass |
| One active item per NPC | ContextPacket rejects more than one active item_negotiation, permits suspended and action-choice records alongside it | Scoped uniqueness/active constraints; pass |
| Consent binding | ConsentBinding current question TurnRef/answer turn/span + requested operation/terms + preconditions; explicit validate_against | Current question ID/key must match; answer sequence strictly follows current question sequence; current question must be at/after interaction origin. Active/current exact question, target/item/fingerprint/answer text required; action-choice selection must equal a full offered value, stale/unoffered selection rejected; pass |
| One ready operation | OperationDecision union NoOperation/ClarificationRequired/Denied/ReadyToRecheck, single operation field; ready rejects non-direct modalities | All four variants roundtrip; operations arrays/authorization tokens/authorized fields rejected; pass |
| Audited operation vocabulary | give_item/receive_item have item-only arguments over existing ten ITEMS; six Craftsman dialogue commands have strict empty arguments | All registered shape variants pass; quantity, unsupported item/commands, physical completion/combat/checkpoint payloads rejected; pass |
| Receipt outcomes | OperationReceipt immutable accepted/completed/rejected with typed TransferResult/CommandResult/ActivityResult/RejectionResult, UTC commit, revisions/events | Accepted activity is not completed; outcome/stage/ID/direction/quantity mismatches and arbitrary result maps rejected; pass |
| Receipt linkage | verify_operation compares command, target and canonical argument digest against supplied detached operation | Exact SHA-256 vector, command/argument/target/digest mismatches rejected; pass |

## Canonical vocabulary and digest

Audited mapping: `give_item` / `receive_item` map to the existing one-unit
StateService transfer actions, respectively toward player / toward NPC. They
accept `{item: <existing item>}` only; quantity is never model supplied. Existing
Craftsman dialogue commands `report_wreck`, `begin_ship_inspection`, `wait`,
`resume`, `postpone`, `return` accept `{}`. This is shape vocabulary, not a new
permission table or registration of every route. Concrete adapters must audit,
resolve and register capabilities before any execution. Intro/physical
inspection completion/checkpoints/Gatherer combat/ship repair are absent.

Canonical SHA-256 input is exactly sorted-key JSON of `command_id` + typed
`arguments`, separators `(',', ':')`, `ensure_ascii=False`, UTF-8. Fixture vector:

```text
{"arguments":{"item":"wood"},"command_id":"give_item"}
2368bba4518a8215141f5aaadfb23970d07d0fce1ce31dcc43e0370cd62c6de2
```

Target is compared separately. IDs, spans and modality are not digest terms.
Digest consistency grants no execution authority and proves no persisted receipt
existence. Gateway receipt recovery and transactional authority checks remain
mandatory.

## Risks and follow-up

- T03 owns CanonRecord/CanonChange, MemoryRecord, FinalTurnResult and interface result/status values. T02's CanonCandidate is only a model addition/revision intent linked to exact segment text and explicit correction ID; ContextPacket.active_canon currently uses frozen T01 NarrativeCanon evidence. ContinuityChangeRef only carries candidate ID/final span for the T03 handoff; it is not an accepted CanonChange.
- `VisibleTurn`, `ContextSummary`, `TextValue`, `ReplySource` are minimal detached input metadata, not persistence or API adapters. There is no implicit legacy game/timeline mapping.
- Source/reference authenticity and semantic attribution are not proven by shape. Proposal boundaries must call validate_references against exact accepted messages; interaction logic must call validate_question/validate_against with current persisted terms and exact answer text. A structurally direct candidate does not establish actual intent; policies own that determination.
- ConsentBinding now requires the full current `question_turn: TurnRef`. Shape validation checks its ID/key against question_turn_id/answering key and enforces `answering_turn.sequence > question_turn.sequence`; validate_against checks current PendingInteraction question ID/key and requires question sequence at/after the origin. Owning interaction logic still resolves/authenticates the supplied TurnRef against persisted state.
- No collection/output/context shipping limits were invented. T01's one explicit policy remains frozen; context/composition boundaries must enforce its configured measured budgets/token accounting and full reply/beat bounds.
- Renderer IDs are a closed contract allowlist only; actual exact rendering, receipt/activity state lookup (including later progress), availability and semantic grounding belong to composition/capabilities/validation owners.
- Values never expire negotiations by time; `expired` currently uses one explicit reason code `preconditions_changed`. Owning policy determines which relevant preconditions failed.
- Existing typed Pydantic trusted escapes remain documented: model_construct/model_copy(update=...) must not decode external payloads.

Next owners: `contracts/T03`; then `ports`, `proposal`, `interactions`,
`capabilities`, `composition`, `operations`, and concrete game/persistence adapters
under their declared dependency gates. Main Agent review remains the acceptance
gate; no packet/master checkboxes were changed here.

## Review correction: current question ordering

Review identified that comparing an answer only to the interaction origin could
bind an answer submitted before a later restatement. The required question_turn
field and direct sequence comparison close that value-level gap. The new test
uses origin sequence 1, current question sequence 3, rejects answer sequences 2
and 3, and accepts answer sequence 4. It also rejects wrong question turn IDs,
cross-epoch question keys, and a current question preceding the origin. The
existing resumed-question test now supplies the later question TurnRef explicitly.
No T01 field or fixture was changed. Final focused/combined/dependency tests and
schema/import/whitespace checks were rerun after this correction.
