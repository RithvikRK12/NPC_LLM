# composition/T02 handoff

Implemented 2026-10-14, bounded to action-speech composition. This worker changed only `backend/app/services/conversation/composition.py`, added `backend/tests/test_conversation_composition_service.py`, and wrote `t02-*` evidence. No frozen contracts/ports, accepted assembler behavior, task/master/graph, legacy composer, concrete provider, or application/player database was changed.

## Delivered interface and behavior

`CompositionService(generation: GenerationPort, policy: ConversationPolicy).compose(context, proposal, receipt, deadline) -> Result[CandidateReply]` has two injected dependencies and no execution, repository, or game-service port.

- With no receipt, it directly wraps the proposal's ordered reply and canon candidates using current version metadata. This consumes zero generation calls. Selected fact slots still require available current evidence; receipt slots without a receipt fail closed.
- With a supplied authentic committed receipt, it makes exactly one `generation.generate('composition', derived_context, stage_deadline, policy.output_char_limit)` call. The stage deadline is capped by both the caller's deadline and the explicit provider-stage policy. The response budget is the configured complete output character budget; concrete generation adapters must map that budget consistently to provider controls.
- Receipt scope, NPC, turn, policy and current activity source revisions are checked before dispatch. No private authorization reason is projected. Timeout and late output return `PROVIDER_TIMEOUT`; an already expired caller deadline dispatches nothing. There is no retry, repair call, fallback call, or operation execution.
- Returned values must be `CandidateReply` with exact current schema/policy metadata and supported concern references. An action candidate must contain the exact supplied receipt's outcome slot. Unknown facts/receipts, unsupported evidence provenance, stale selected facts, and a slot upgrading acceptance to completion/progress are rejected as `PROVIDER_INVALID_OUTPUT`.
- Full expressive prose remains a candidate for the separate whole-response validator. Composition does not claim semantic proof, publication authority or canon admission.

## Frozen GenerationPort adaptation

The frozen port accepts only a `ContextPacket`, not a receipt parameter. Locally, the service creates a new detached packet with one `VerifiedEvent` appended to `visible_facts`. Its evidence ID is `composition-receipt:<receipt_id>`. Its content comes exclusively from the existing server-owned exact receipt renderer; its timestamp is the commit timestamp; its single `operation_receipt` source uses the exact receipt ID, immutable argument digest terms token, scope/NPC, server attribution and `npc_private` visibility. ID collisions fail closed. The original context and receipt remain unchanged.

The renderer projection exposes safe quantity/outcome text, not internal denial codes, target/consent/private authorization details or event IDs. The caller remains responsible for authentic receipt resolution: neither a detached receipt nor its argument digest proves persistence. Receipt outcome cannot be rewritten with later activity status.

Current activity is retained only from adapter-supplied `MechanicalFact` evidence with `activity` sources whose revisions match the current packet. The service does not derive progress, cancellation or completion from elapsed time, an activity ID, player report, or accepted receipt. A current exact fact can support a `FactSlot`; `ReceiptSlot(progress)` remains unsupported because the frozen receipt contract has no structured current progress outcome. No new public contract or policy shipping defaults were introduced.

## Call/repair budget boundary

Each invocation dispatches at most one composition purpose and zero repair purposes. Durable turn-wide stage consumption, ownership fencing, recovery and deduplication remain the coordinator's responsibility. It must persist the composition attempt before dispatch, including through a guarded GenerationPort wrapper, and avoid invoking this service again for a consumed attempt. This service deliberately has no hidden process-local attempt counter or TurnStore dependency; such a counter would reset on restart and would not satisfy the frozen durable budget contract. A composition timeout does not erase the committed receipt or grant another composition/repair/operation attempt.

## Adjacent fail-closed activity limitation

The cancellation test uses a realistic accepted activity receipt with activity revision `1 -> 2` and a later current cancellation fact at revision `3`. Composition preserves both separately and accepts only the original `accepted` receipt slot plus the exact current fact. The accepted T01 assembler then rejects assembly with `EVIDENCE_CHANGED`, because its current-receipt policy requires every `receipt.after_revisions` token to match the current snapshot. No dialogue is published and no newer acceptance/completion receipt is invented.

This is a real integration limitation, not full support for publishing cancelled/current activity speech. Historical immutable receipt outcomes and current activity evidence need independently checked rendering semantics. The coordinator agreed to record separate `composition/T03` follow-up work rather than widen this T02 deliverable or silently change accepted T01 behavior. The service tests explicitly assert the existing fail-closed result.

## Verification

All commands ran from repository root using scripted generation and injected monotonic time; no live provider or player database was used. Full backend regressions used the existing isolated test infrastructure.

| Check | Command | Exit | Evidence |
| --- | --- | --- | --- |
| RED | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_composition_service.py'` | 1 | `t02-red.txt`; 17 expected missing-CompositionService assertion failures |
| Focused GREEN | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_composition*.py'` | 0 | `t02-green.txt`; 33 tests |
| Conversation modules/contracts | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | 0 | `t02-conversation.txt`; 139 tests |
| Adjacent immutable contracts | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_contract_values.py'` | 0 | `t02-dependency-contracts.txt`; 13 tests |
| Legacy composer | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_dialogue_compose.py'` | 0 | `t02-legacy-composer.txt`; 16 tests |
| Full backend | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` | 0 | `t02-backend.txt`; 602 tests; existing datetime.utcnow deprecations and expected negative-path/embedding-fallback logs remain |
| Tracked whitespace | `git diff --check` | 0 | `t02-diff-check.txt` |
| Legacy unchanged | `git diff --exit-code -- backend/app/dialogue/compose.py` | 0 | `t02-legacy-diff.txt` |
| New implementation artifacts | Python `compile`, terminal newline and trailing-whitespace checks for the owned source/test files | 0 | `t02-artifact-check.txt` |

The focused dependency test proves import isolation from FastAPI, SQLAlchemy, httpx and OpenAI in a fresh process, the constructor accepts only generation/policy, and no execution entry point or execution-port dependency exists. It does not claim database atomicity, concrete provider conformance, runtime coordinator wiring, live wording quality, measured policy acceptance or end-to-end activity publication safety.
