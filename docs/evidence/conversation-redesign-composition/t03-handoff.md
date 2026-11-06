# composition/T03 handoff

Implemented 2026-10-14 in the explicitly recorded historical-receipt/current-activity expansion. Owned changes are `backend/app/services/conversation/composition.py`, the two composition test files, the composition golden fixture, the new `composition-t03-history.json` fixture, and these `t03-*` evidence files. No task/master/graph files, frozen shared contracts/ports, provider adapters, legacy composer, or player database were changed by this worker.

## Delivered behavior

`ReplyAssembler.assemble` now treats an authentic committed `OperationReceipt` as historical evidence. Its `after_revisions` remain the immutable commit snapshot; they do not have to equal current resource revisions or appear in the current snapshot. Receipt rendering still requires an exact admitted turn, scope and NPC, an explicit visible `operation_receipt` source with the exact receipt ID/NPC, and the canonical argument digest terms token. The caller still authenticates the committed receipt lookup; a digest is not proof of persistence. `AssemblyEvidence` and `OperationReceipt` fields and immutability contracts are unchanged.

Receipt clauses use historical wording. Accepted inspection says `I agreed to inspect the ship.`; completed inspection says `The ship inspection was completed.`; a successful wait command says `I began waiting.`. Receipt rendering no longer asserts that an accepted inspection is currently incomplete, a historically completed inspection is currently complete, or an earlier wait is still ongoing. Other receipt clauses already described historical outcomes and remain unchanged. The T01 golden fixture was updated for these three intentional catalog changes.

Current activity remains a separate `MechanicalFact` rendered by `FactSlot(fact.exact)`. Each selected fact must resolve to the exact adapter-provided current resource source, visible in scope, with its source revision equal to `AssemblyEvidence.revisions`. Stale/missing current activity therefore still blocks assembly, and stale current activity still blocks composition before generation. No current status, progress, cancellation, or completion is inferred from an accepted receipt or activity ID. `ReceiptSlot(progress)` and attempts to promote accepted receipts to completed remain invalid, even when a separate authoritative activity fact reports completion.

Receipt clauses export only their authenticated immutable receipt source in `AssembledReply.evidence_dependencies`. Current fact clauses independently export their revision-checked sources. Historical `after_revisions` are no longer mislabeled as current publication dependencies. Existing fact checks, exact spans, lossless beats, scope/policy checks, and finalizer ownership of epoch/fence/current-evidence publication rechecks remain intact. This pure assembler does not implement a finalizer or claim end-to-end publication safety.

## Acceptance evidence

- Accepted inspection receipt at revision 2 plus cancellation at revision 3 now composes and assembles as `I agreed to inspect the ship. The ship inspection was cancelled; it is not underway.` with exact separate receipt/fact spans and receipt/activity dependencies.
- The same immutable accepted receipt separately accompanies progress and current completion facts at revision 3 without changing its outcome or receipt fields.
- Accepted and completed historical receipts remain renderable after current activity advances, or when no current activity projection is supplied. Neither case creates current activity speech.
- A selected stale current-tense activity fact or missing current activity fact fails `EVIDENCE_CHANGED`; absence of current projection never permits receipt progress/completion promotion.
- Historical receipt authentication remains fail closed for missing sources, wrong terms tokens, wrong source kind/scope/NPC, and server-private sources. Existing wrong receipt turn/scope/NPC tests remain green.

## Verification

All commands ran from repository root. Pure focused cases use detached fixtures, scripted generation and injected time; no live provider or player database was used. Existing full backend regression infrastructure runs its own isolated test setup.

| Check | Exact command | Exit | Evidence/result |
| --- | --- | --- | --- |
| RED before production changes | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_composition*.py'` | 1 | `t03-red.txt`: 38 tests, 14 expected subcase/test failures on historical receipt checks and current-state catalog wording |
| Focused GREEN | Same focused command | 0 | `t03-green.txt`: 38 tests pass |
| Conversation modules/contracts | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | 0 | `t03-conversation.txt`: 144 tests pass |
| Immutable contract dependencies | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_contract_values.py'` | 0 | `t03-dependency-contracts.txt`: 13 tests pass |
| Legacy composer | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_dialogue_compose.py'` | 0 | `t03-legacy-composer.txt`: 16 tests pass |
| Full backend regression | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` | 0 | `t03-backend.txt`: 607 tests pass; existing `datetime.utcnow` deprecations and expected negative-path/embedding-fallback logs remain |
| Tracked whitespace diff | `git diff --check` | 0 | `t03-diff-check.txt`: clean |
| Legacy unchanged | `git diff --exit-code -- backend/app/dialogue/compose.py` | 0 | `t03-legacy-diff.txt`: unchanged |
| Owned untracked artifacts | Python `compile`, `json.loads`, terminal-newline and trailing-whitespace checks | 0 | `t03-artifact-check.txt`: source/tests compile, fixtures parse, whitespace clean |

The workspace's composition files are untracked, so `git diff --check` alone cannot validate their whitespace; the explicit owned-artifact check covers them. No remaining local blocker is known. Concrete provider conformance, durable stage budgets, authentic database receipt retrieval, live activity adapters, whole-response semantic validation and finalizer publication checks remain their respective owners' integration responsibilities.
