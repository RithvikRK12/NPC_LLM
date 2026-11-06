# composition/T01 handoff

Implemented 2026-10-14, bounded to pure assembly. No master/packet/graph edits, legacy adapter changes, provider calls, or application/player database access were made by the assembler or its focused tests. Broader existing regression tests use their own test infrastructure.

## Delivered behavior

- `backend/app/services/conversation/composition.py` adds `ReplyAssembler.assemble(candidate, evidence, policy) -> Result[AssembledReply]` and the local immutable `AssemblyEvidence` read snapshot. Frozen contracts/ports are unchanged.
- `fact.exact` renders only adapter-supplied `MechanicalFact` or `AuthoredKnowledge.content`. Narrative canon, reports, and interpretations cannot become exact mechanical facts.
- The fixed receipt renderer catalog uses committed receipt result fields for transfer item, quantity, direction, activity outcome and changed/no-change command status. Rejections use safe generic command clauses; internal reason codes are never printed. Accepted inspection never becomes completed inspection. `progress` fails closed because the frozen contracts have no authoritative current activity-progress projection.
- Unknown slots, mismatched turn/scope/NPC, private sources, missing resource/source entries, stale resource revisions and unsupported receipt speech acts return typed failures. There is no execution/provider/store dependency.
- Expressive prose is retained byte-for-byte as Python Unicode text. One ASCII space joins ordered segments; spans exclude the inserted separators. Every final segment span is rebuilt, and canon candidate offsets are relocated into that exact final text, including after repair and Unicode slot expansion.
- Complete text and every beat use only the injected `ConversationPolicy.output_char_limit` and `beat_char_limit`. The partitioner prefers whitespace boundaries, preserves every character, handles unbroken words, and keeps a short reply in one beat. It checks suffix feasibility so representable leading/interword/trailing whitespace is retained. If no nonblank bounded partition exists, assembly fails rather than deleting whitespace. Concatenated beats equal complete dialogue exactly.

## Adapter and next-task handoff

`AssemblyEvidence` contains `turn`, caller-owned final `text_id`, `facts`, `receipts`, current `revisions`, `resource_sources`, and `receipt_sources`. Tuples and nested frozen contract values prevent mutation, and lookup IDs must be unique. Evidence authenticity is the calling adapter's responsibility; these values and structural checks neither prove persistence nor grant permission.

Every selected fact source must match the corresponding unique `resource_sources` entry exactly; its `source_id` is the exact `RevisionSet.resources` key and its revision must match the current snapshot. Every resource in a selected receipt's `after_revisions` must have exactly one matching current resource source. The assembler does not infer resource kinds from names. Only relevant selected dependencies are exported in `AssembledReply.evidence_dependencies`, deduplicated in encounter order.

Each selected receipt requires its own explicit `operation_receipt` source with exact receipt ID, current scope/NPC, public or NPC-private visibility, and revision equal to the receipt's canonical `argument_digest`. This digest is an immutable **terms token**, not proof of commit state or a unique digest of every receipt field. The adapter must resolve the authentic committed receipt. Receipt dependencies include both that source and every relevant after-resource source. Receipt lookups must belong to the admitted turn. Resource/epoch/publication rechecks still belong to their owning boundaries.

The candidate's `source.policy_versions['bounds']` must equal the injected policy version (the frozen shared fixture convention); schema versions must also match. Source versions and final `text_id` ownership must be supplied by future composition/coordinator adapters.

The assembler deliberately retains expressive text even if it contains a mechanically consequential contradiction. Whole-reply validation remains mandatory in the response-validation owner; these tests do not claim semantic safety or authorize canon/game effects. No legacy adapter is needed for this standalone pure module. T02 action-composition and runtime wiring remain outside this task.

## Legacy policy conflict audit

`t01-legacy-limit-audit.txt` records the exact source search. Current live defaults conflict: `Settings.max_dialogue_chars=240`; ordinary validator/prompt/provider constrain 240; selected Craftsman story paths use 600; `LLMResponse.dialogue` caps 600; final factual rendering still rechecks 240; the separate legacy composer imposes `DialogueText <=300` and `DialoguePolicy.max_text_chars <=300`; HTTP `final_dialogue` has no matching limit. Baseline/T01 inventory documents the same mismatch.

No 240/300/600 threshold is stacked onto the new assembler and no shipping limit is chosen. Fixture values (2000 total / 80 per beat, and boundary-case overrides) are test inputs only. Tests demonstrate 601 characters can pass under an explicit 601 policy and 602 cannot, with no truncation. Baseline measurements/product acceptance and later provider/transport/client wiring must choose and consistently apply production policy. This remains an unresolved release integration policy conflict, not evidence that a particular new output limit is accepted.

## Verification

Commands ran from repository root with no live provider. Logs are in this directory; each command's observed exit code is recorded below.

| Check | Command | Exit | Evidence/result |
| --- | --- | --- | --- |
| Initial RED | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_composition.py'` | 1 | `t01-red.txt`; 14 expected missing-assembler assertion failures |
| Whitespace regression RED | Same focused command | 1 | `t01-whitespace-red.txt`; representable trailing/interword whitespace failed in two subcases before correction |
| Short-beat regression RED | Same focused command | 1 | `t01-short-beat-red.txt`; short reply unnecessarily split before correction |
| Final focused GREEN | Same focused command | 0 | `t01-green.txt`; 16/16 pass |
| Conversation contracts/modules | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | 0 | `t01-conversation.txt`; 112/112 pass |
| Dependency contracts | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_contract_values.py'` | 0 | `t01-dependency-contracts.txt`; 13/13 pass |
| Legacy composer | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_dialogue_compose.py'` | 0 | `t01-legacy-composer.txt`; 16/16 pass |
| Full backend regression | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` | 0 | `t01-backend.txt`; 575/575 pass; existing `datetime.utcnow` deprecation warnings and expected negative-path/embedding-fallback diagnostic logs remain |
| Existing tracked diff | `git diff --check` | 0 | `t01-diff-check.txt`; clean |
| Numeric conflict inventory | `rg -n 'max_dialogue_chars\|240\|300\|600\|max_text_chars\|DialogueText\|final_dialogue\|text_overflow'` over settings, validation models/service, prompt, provider, grounding, legacy composer, chat schema and legacy composer tests | 0 | `t01-legacy-limit-audit.txt` |

The first dependency attempt used `-p 'test_dependency*.py'`, matched zero tests and exited 5 (`t01-dependency.txt`); it is not counted as verification. The correct existing dependency suite subsequently passed. A no-index diff check for new files returned the normal differences exit code 1 without whitespace diagnostics; a direct whitespace check is recorded separately because these implementation files are not yet tracked in this shared workspace.

Golden fixtures: `backend/tests/fixtures/conversation/composition-t01-golden.json`. Behavioral tests: `backend/tests/test_conversation_composition.py`. No tests or results establish concrete database atomicity, provider quality, live Godot integration, measured product output budgets, or full-system publication safety.
