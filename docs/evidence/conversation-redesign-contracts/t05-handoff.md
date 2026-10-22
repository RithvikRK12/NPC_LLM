# contracts/T05 handoff

## Task

- ID: `contracts/T05`.
- Owner / model / reasoning effort: `contracts_t05` / `gpt-6.1-sol` / high.
- Status: ready for Main Agent review.
- Scope and dependency versions used: accepted `contracts/T01–T04`; schema version 1 from existing `SchemaVersion`; detailed design §§3.1–3.3, 4, 5.2, 6.3. Only shared value shapes, their focused fixtures, and interface tests were changed. Main Agent remains sole packet/master writer.

## Files changed

- `backend/app/services/conversation/contracts.py` — added versioned immutable `InteractionLifecycleCue` and `InteractionPreconditionState`; default-empty proposal/context extensions; current-message/turn/ID/fingerprint validation. Empty extensions are omitted from serialization to preserve frozen JSON fixtures.
- `backend/tests/test_conversation_contracts_interfaces.py` — added seven T05 behavioral tests covering valid/rejected fixtures, exact current-message references, current pending statuses, unavailable/missing states, compatibility, and detached immutability. Existing T04 tests were preserved.
- `backend/tests/fixtures/conversation/t05-valid.json` — explicit cancellation/resume, an emoji before the evidence offsets, matching failed/satisfied state, and an unavailable state.
- `backend/tests/fixtures/conversation/t05-rejected.json` — strict version/modality/action/outcome/authority/extra-field rejections, stale/mismatched states, duplicate cue IDs, duplicate evaluation value IDs, missing required fields, and conflicting same-interaction cues.
- `docs/evidence/conversation-redesign-contracts/t05-handoff.md` — this report and durable command/output summaries. No packet/master, graph, turns, ports, context-assembler, persistence, or interaction-policy implementation was edited.

## Contract handoff

`TurnProposal.interaction_lifecycle_cues` is a tuple of `InteractionLifecycleCue(schema_version, cue_id, turn, interaction_id, action, modality, source_span, source_text)`. `action` is `cancel` or `resume`; `modality` must be `direct`. Every cue requires one nonempty exact player-message span. Cue IDs and interaction IDs must be unique within a proposal; conflicting cues for a single interaction fail closed.

The owning proposal boundary calls `proposal.validate_references(texts, context=context)`. When cues exist, context is required; the supplied text for `context.current_message.text_id` must equal the accepted current message exactly. Each cue must match `context.turn` in full (including key, request, sequence), cite the current message ID, identify a known pending interaction, and resolve its span to `source_text` exactly. Extra historical texts in the supplied lookup cannot substitute for current-message evidence. Calls without cues keep the existing method behavior and signature compatibility.

`ContextPacket.interaction_preconditions` is a detached immutable map from interaction ID to `InteractionPreconditionState(schema_version, interaction_id, turn, precondition_fingerprint, authority, outcome)`. The sole authority tag is `server_evaluated`; outcomes are `satisfied`, `failed`, or `unavailable`. Keys and value IDs must agree and refer to active/suspended records in the packet. The exact current `TurnRef` and stored interaction fingerprint must match. Unknown IDs, duplicate value IDs, stale turns, mismatched fingerprints, and terminal records are rejected. No free-text reason, private source, or authorization payload is permitted.

A missing entry means evaluation is unavailable; callers must use absence as absence of knowledge. An explicit unavailable state has the same lack of actionable knowledge. Only a matching explicit server-evaluated `failed` outcome represents authoritative relevant failure for later policy consumption. Fingerprint/revision churn alone is not a failure. None of these values changes an interaction, authorizes resume, grants consent, transfers an item, or implements clock/turn expiry. Cue interpretation and permitted transitions remain application policy; current authoritative evaluation and durable effects remain server/persistence duties.

## Tests run

All commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1`, using the repository `.venv`, local JSON fixtures, and deterministic fakes. No live provider/database was used. Pass/fail counts below count unittest methods, not fixture subcases. Raw session logs are available under `/tmp`; the summaries and failure names below persist the relevant evidence in this owned report.

| Exact command | Exit | Pass / fail / skip | Evidence |
| --- | ---: | --- | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_contracts_interfaces.InteractionCueContractTests -v` before implementation | 1 | 0 / 7 / 0 | `/tmp/t05-red.log`; all seven failed with `AssertionError: False is not true : T05 typed cue value InteractionLifecycleCue is absent` |
| Same focused command after implementation | 0 | 7 / 0 / 0 | `/tmp/t05-green-final.log`; `Ran 7 tests in 0.008s`, `OK` |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_contracts backend.tests.test_conversation_contracts_turn_values backend.tests.test_conversation_contracts_continuity backend.tests.test_conversation_contracts_interfaces backend.tests.test_conversation_context backend.tests.test_conversation_store_ports -v` | 1 | 70 / 0 failures + 1 import error / 0 | `/tmp/t05-adjacent.log`; named-module invocation could not import `conversation_store_conformance` without test directory in `PYTHONPATH`; corrected below |
| `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest backend.tests.test_conversation_contracts backend.tests.test_conversation_contracts_turn_values backend.tests.test_conversation_contracts_continuity backend.tests.test_conversation_contracts_interfaces backend.tests.test_conversation_context backend.tests.test_conversation_store_ports -v` | 0 | 102 / 0 / 0 | `/tmp/t05-adjacent-final.log`; `Ran 102 tests in 0.042s`, `OK` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` | 1 | 633 / 4 / 0 | `/tmp/t05-backend.log`; `Ran 637 tests in 5.621s`, `FAILED (failures=4)`; concurrent diagnostics failures listed below |
| `PYTHONPATH=backend .venv/bin/python /tmp/t05_boundary.py` | 0 | 82 model schemas, 8 union schemas, 2 result schemas; pure imports; 4 owned code/fixture whitespace checks passed | `/tmp/t05-boundary.log`; exact check content below |
| `git diff --check` | 0 | passed; no output | Tracked diff whitespace check; explicit owned untracked checks included in boundary script |

Full backend failures were all in `test_conversation_diagnostics.ConversationDiagnosticsTests`, each failing setup with `T01 structured diagnostics projection is not implemented` because the concurrent worker had not yet created `app.services.conversation.diagnostics`:

- `test_invalid_timings_fail_closed_instead_of_exporting_nonfinite_values`
- `test_provider_credentials_and_unrecognized_reasoning_are_never_exported`
- `test_trace_emits_scoped_identity_versions_sources_decisions_and_attempt_state`
- `test_trace_receipt_and_findings_are_summaries_without_prose`

The Main Agent was notified; these files are outside T05 ownership. The full backend suite was not claimed passing. No required T05 or adjacent boundary check was skipped.

Boundary check script used by the recorded command:

```python
import ast
import inspect
from pathlib import Path
from pydantic import BaseModel, TypeAdapter
from app.services.conversation import contracts as c
models = [(name, value) for name, value in vars(c).items()
          if inspect.isclass(value) and issubclass(value, BaseModel)
          and value.__module__ == c.__name__]
for name, model in models:
    assert isinstance(model.model_json_schema(), dict), name
for name in ('Evidence', 'ProposalReference', 'ParameterSchema', 'ReplySegment',
             'OperationDecision', 'VisibleFact', 'AuthoritativeResult', 'CanonChange'):
    assert isinstance(TypeAdapter(getattr(c, name)).json_schema(), dict), name
for model in (c.Result[c.TurnLease], c.OptionalResult[c.TurnLease]):
    assert isinstance(model.model_json_schema(), dict)
path = Path(c.__file__)
imports = []
for node in ast.walk(ast.parse(path.read_text())):
    if isinstance(node, ast.Import):
        imports.extend(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module:
        imports.append(node.module)
assert not any(name.startswith(('sqlalchemy', 'fastapi', 'app.models', 'app.database',
                                'httpx', 'openai', 'requests')) for name in imports)
print(f'PASS: {len(models)} model schemas; 8 union schemas; 2 result schemas; pure imports {imports}')
paths = [path, Path('backend/tests/test_conversation_contracts_interfaces.py'),
         Path('backend/tests/fixtures/conversation/t05-valid.json'),
         Path('backend/tests/fixtures/conversation/t05-rejected.json')]
for owned in paths:
    for number, line in enumerate(owned.read_text().splitlines(), 1):
        assert line == line.rstrip(), f'{owned}:{number}: trailing whitespace'
print('PASS: all 4 owned code/fixture files free of trailing whitespace')
```

Recorded schema/import output:

```text
PASS: 82 model schemas; 8 union schemas; 2 result schemas; pure imports ['collections.abc', 'dataclasses', 'datetime', 'hashlib', 'json', 'math', 'types', 'typing', 'pydantic', 'app.contracts.core']
PASS: all 4 owned code/fixture files free of trailing whitespace
```

## Results

| Acceptance criterion | Outcome / evidence |
| --- | --- |
| Typed proposal-only explicit cancellation/resume | Versioned direct-only cues; exact current turn/message/span/ID validation; seven focused tests and rejected fixtures pass |
| Server-evaluated relevant-precondition state tied to current pending ID/fingerprint | Typed server tag/outcomes; map identity, current turn, active/suspended status and fingerprint checks; rejected fixtures and terminal-state test pass |
| Invalid/mismatched/missing values fail closed | Invalid/stale values rejected; omitted map remains empty; unavailable remains unavailable and does not alter pending status |
| No private authorization details in public context | State has no source/reason/prose payload; extras rejected; existing context visibility validation preserved |
| Consent and lifecycle/persistence authority preserved | No authority/transition code changed; validation returns no operation or consent; valid fixture keeps existing active/suspended statuses |
| Immutable detached values and backward compatibility | New mapping/tuple/nested values immutable; mutation of input data cannot change accepted values; old T04 envelope JSON and all adjacent old contract tests pass |
| Pure imports and schemas | 82 models/8 unions/2 generic results pass; infrastructure imports absent |

Proposed packet/master update: accept `contracts/T05` after independent review/reproduction, marking 5/5 local contracts tasks complete while retaining the existing adjacent/runtime integration gates. No status updates were applied by this worker.

## Risks

- No T05 correctness issue identified by focused/adjacent checks. Whole backend success remains unverified in this shared workspace until concurrent diagnostics implementation arrives.
- Typed authority is provenance, not authentication. A server adapter must construct these evaluations from authoritative current reads; provider output cannot supply server context. Persisted/recovered packets still require fresh scoped authoritative revalidation at their owning boundary.
- Model text can claim a direct interpretation despite quotations or ambiguity; exact span evidence does not prove semantic interpretation. The interaction policy must keep cues as proposals and enforce transition/consent rules.
- Only nonempty extensions are emitted. Consumers that require explicit empty lists/maps must use their default-empty semantics; old frozen fixtures retain exact serialization.

## Follow-up tasks

- `interactions/T01`: consume `interaction_lifecycle_cues` only after `validate_references(..., context=...)`; treat missing/unavailable evaluation as lack of authoritative knowledge; use only matching explicit `failed` for relevant invalidation, never timers or revision churn. Resume/consent/transition rules remain this task's implementation responsibility.
- `proposal/T01`: decode the versioned proposal values and supply the accepted current `ContextPacket` to reference validation when lifecycle cues exist.
- `context/T01` / future concrete read adapter: existing assembler already revalidates `ContextPacket`; authoritative evaluation projection remains adapter work, with no T05 source/API expansion.
- `diagnostics/T01`: Main Agent coordinates its concurrent worker and reruns the backend suite when its implementation is ready. No new task proposed.
