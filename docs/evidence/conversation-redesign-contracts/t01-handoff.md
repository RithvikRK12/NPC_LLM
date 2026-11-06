# contracts/T01 implementation handoff

Task: `contracts/T01`. Implementer: `contracts_identity`. Branch: `master-progress`.
Cwd for every command: `/Users/rukithnayak/Documents/NPC_LLM-1`.
No commits, runtime/provider/HTTP/ORM integrations, network calls or database access.
Main Agent owns acceptance and packet/master updates.

## Files changed

- `backend/app/services/conversation/__init__.py` — empty package marker.
- `backend/app/services/conversation/contracts.py` — immutable T01 contracts and value-only validation.
- `backend/tests/test_conversation_contracts.py` — 16 pure behavioral tests.
- `backend/tests/fixtures/conversation/contracts-t01-valid.json` — hand-defined transport identities and six evidence variants.
- This directory — red/green/dependency/boundary logs and this handoff.

## Exact verification

All test commands use the repository `.venv/bin/python`, with `PYTHONPATH=backend`.
Logs contain complete unittest output including names and counts. Red tests were
written and run before the production package existed; their common prerequisite
assertion fails explicitly for the absent implementation rather than import errors.

| Command | Exit | Result | Log |
| --- | --- | --- | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts.py' -v` (before implementation) | 1 | 16 tests, 16 expected failures: T01 implementation absent | `t01-red.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts.py' -v` | 0 | 16 tests, all pass | `t01-green.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_contract_values.py' -v` | 0 | 13 tests, all pass; compatible reused scalar/value dependency conformance | `t01-dependency-contracts.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` | 0 | 16 tests, all pass; final post-refactor conversation suite | `t01-conversation-suite.log` |
| `git diff --check` | 0 | No whitespace findings | Command output empty |

Infrastructure/schema boundary check, exit 0, exact command below; stdout in
`t01-boundary-check.log`:

```sh
PYTHONPATH=backend .venv/bin/python - <<'PY'
import sys
from app.services.conversation.contracts import ConversationPolicy, RevisionSet
assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot'} for name in sys.modules)
ConversationPolicy.model_json_schema()
RevisionSet.model_json_schema()
print('T01 import is infrastructure-free; policy and revision-map JSON schemas build.')
PY
```

An initial red-run shell wrapper attempted the zsh read-only variable `status`;
that wrapper exited 1. It was immediately rerun with `result_code`; the canonical
red evidence above records the complete actual test failure output. No code
change was needed for this shell wrapper correction.

## Acceptance results

- **Immutable identities:** ConversationKey, TurnSubmission and TurnRef use frozen/extra-forbidden validated values. Nested keys are immutable. NPC and sequence are positive exact JSON integers; epoch is nonnegative. Scope and epoch have no implicit legacy game/timeline mapping. Player selectors and unknown fields are rejected. Input is nonblank, exact untrimmed text, at most 500 Unicode code points.
- **RevisionSet:** relevant resource IDs map to opaque string or nonnegative exact-integer revision tokens. The input map is copied and frozen with MappingProxyType; nested mutable tokens are rejected, and the map serializes/round-trips as an object. Mismatches request later revalidation; no mechanical conclusion is inferred from revisions.
- **SourceRef:** explicit provenance kind, source ID, revision, scope, optional integer NPC, opaque attribution and closed visibility. Kind describes source provenance (inventory/game_event/authored_content/final_speech/player_message/etc.), distinct from evidence type.
- **TextSpan:** strict, nonempty, end-exclusive code-point offsets; `resolve(texts, expected_text=...)` checks reference existence, bounds and optional exact text, including astral and combining Unicode characters. Shape validation cannot resolve references by itself; consumers must call resolve.
- **Evidence:** strict discriminated union of MechanicalFact, VerifiedEvent, AuthoredKnowledge, NarrativeCanon, PlayerReport and Interpretation. Each requires nonempty frozen source references and a UTC created_at. First three alone have derived `mechanical_eligible=True`; use still requires explicit deterministic-owner permission. Allowed provenance sets reject narrative/report sources relabeled to mechanical tags. Narrative canon authority is only `narrative_only`; reports/interpretations carry required attribution and uncertainty. Extra authority fields are rejected.
- **UTC timestamps:** shared UTCTimestamp annotation rejects naive/numeric timestamps and normalizes aware datetime/ISO timestamps to UTC.
- **Policy:** one schema-versioned ConversationPolicy, explicit required policy version and every tuning field; no shipping defaults. Preserves required 500-character input ceiling. Positive finite durations and bounded exact positive integer counts; provider budget cannot exceed total, beat bound cannot exceed full output. No negotiation expiry field; unknown fields reject attempts to add one. Test fixture budgets are test candidates only.
- **Deadline:** immutable process-local value with injected monotonic clock, no implicit wall clock. Validates finite positive budgets and finite clock readings; remaining time clamps to zero, stage deadlines cap at parent, and fake-clock expiry never changes any negotiation.
- **ConversationError:** immutable typed safe result with stable closed codes, stage, strict retryability, optional known TurnRef and nonblank safe detail; no raw exception field accepted.
- **Versions/fields/boundary:** reused only semantically compatible ContractValue/Identifier/Revision/SchemaVersion; unknown/coerced schema versions reject. No infrastructure dependencies imported. Policy/map JSON schemas build.

## Risks and handoff responsibilities

This task supplies values only. A structurally valid source reference does not
prove authenticity, currentness, NPC knowledge, or server ownership: concrete
read adapters must resolve evidence/source IDs against their authoritative scoped
read set and filter private evidence. Similarly, safe_detail is caller-supplied
public text; shape validation cannot semantically redact a secret embedded in
ordinary prose. Pydantic model_construct/model_copy(update=...) are documented
trusted escape hatches and must not decode external payloads.

Full application tests were intentionally not run because this bounded task
forbids network/DB. The declared pure conversation suite and reused pure contract
dependency suite pass; there is no claim of runtime integration completion.

Exact follow-up IDs:

- `contracts/T02` — consume these identity/evidence/policy values for proposal, negotiation and operation values; coordinate any new provenance kinds against actual owner views.
- `contracts/T03` — continuity/result fixtures and explicit legacy semantic mappings.
- `persistence-adapters/T01` — concrete scoped identity storage/new epoch and legacy handling; source authenticity and reference lookup stay at concrete boundaries.
- `baseline/T02` and `baseline/T03` — measured candidate budgets/configuration; T01 intentionally selects no shipping tuning.

Main Agent review remains the acceptance gate. No task/master checkbox was edited
by this implementer.
