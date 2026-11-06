# validation/T03 handoff

Task: `validation/T03` — bounded speech-only repair. Owner: `validation_t03` (worker `finalization_t02`). Model/reasoning: `gpt-6.1-sol` / high. Date: 2026-10-18.

**Status: ready for Main Agent review; not accepted.** Shared contracts, validator, provider, SQL, coordinator, task packets and master progress were not edited.

## Files and interface

- `backend/app/services/conversation/repair.py`: new `RepairService`, `RepairAllowance`, `RepairEvidence`, `RepairedReply`, and narrow injected hook/validator protocols.
- `backend/tests/test_conversation_repair.py`: 17 deterministic behavior/architecture cases using the existing contract store fake, real `ReplyAssembler`, and real `ResponseValidator`.
- This handoff and `t03-logs/` contain evidence.

Construction: `RepairService(repair_hook, validator, policy)`. Invocation: `repair(candidate, findings, evidence, deadline, allowance=...) -> Result[RepairedReply]`.

`RepairEvidence` carries detached `ContextPacket`, `AssemblyEvidence`, and optional fixed `ReadyToRecheck`. `RepairAllowance(recovery, reserve)` consumes its handoff once, rejects a turn whose recovered shared repair purpose was already spent (including proposal-format recovery), and invokes the coordinator's durable reservation callback before generation. The callback returns a fresh committed `ProviderAttempt` for `repair/final_response`, or a typed error. Current turn/fence/kind/status are checked before dispatch.

The repair hook receives the candidate, exact findings, immutable evidence, bounded child deadline and output budget; it returns only `CandidateReply | ConversationError`. Provider-specific error adaptation belongs to that hook. The existing `GenerationPort` was not expanded to carry findings/candidate.

The service strictly revalidates candidate output, preserves source identity/policy, stamps `origin='repaired'`, requires exact committed receipt coverage, and uses `ReplyAssembler` to rebuild all final Unicode segment/canon spans and lossless beats. The injected validator then checks the whole assembled replacement. Blocking findings, stale report revisions, render failures, invalid output, callback errors and elapsed deadlines release no candidate/reply/canon result. Successful `RepairedReply` contains the validated candidate and assembly together, plus unchanged operation/receipts for downstream planning.

## Acceptance outcomes

| Requirement | Evidence |
| --- | --- |
| Coordinator-granted allowance required; one shared repair token | Ungranted, second-use and failed-dispatch allowances reject; persisted proposal-format consumption survives fake-store restart; a stale allowance snapshot still reaches and is rejected by the authoritative shared budget |
| Recorded before dispatch | Scripted hook checks the store recovery's `repair_consumed` flag before returning any output; uncertain reservation dispatches nothing |
| Speech/canon candidates only | Operation-bearing output rejects; no gateway/store/executor is a service dependency; exact fixed operation and receipt serialize identically before/after approved repair |
| Immutable committed outcome | Missing or invented receipt slots reject; renderer uses the original receipt; contradictory surrounding prose is blocked by real whole-reply validation |
| Rebuild Unicode spans | Final text `A🙂éZ I gave you 1 wood.` has newly calculated outcome span `[6,24)` and canon support `[1,4)`; segment text validation resolves exact strings |
| Validate replacement before releasing canon | Blocking contradiction with proposed canon yields an error and no value; stale report and validator exception fail closed; ordinary speech and advisory-only reports pass |
| Bounded deadlines/errors | No reservation at expired parent deadline; late output discarded at child deadline; failed dispatch consumes allowance and cannot dispatch twice |
| Repair outside database/execution boundary | Service takes detached values and callbacks only; fresh-process import loads none of SQLAlchemy/FastAPI/httpx/OpenAI. Coordinator must call after releasing its transaction; reservation callback must commit/release before returning |

## Exact commands and results

All commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1`; no live provider or player save was used.

1. **RED before implementation**:

   `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_repair.py' -v > docs/evidence/conversation-redesign-validation/t03-logs/red.log 2>&1`

   Exit **1**; **13 expected assertion failures**, all `T03 speech-only RepairService is absent`, no import errors. [RED log](t03-logs/red.log).

2. Initial implementation passed those **13/13**: same focused command redirected to `t03-logs/first-green.log`, exit **0**. [Initial GREEN](t03-logs/first-green.log).

3. Expanded focused acceptance:

   `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_repair.py' -v > docs/evidence/conversation-redesign-validation/t03-logs/green.log 2>&1`

   Exit **0**; **17/17 pass**, no skips/errors. [Final focused GREEN](t03-logs/green.log).

4. Adjacent checks:

   `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_validation test_conversation_contracts_validation test_conversation_composition test_conversation_composition_service test_conversation_finalization test_conversation_fallback test_conversation_proposal test_conversation_turns -v > docs/evidence/conversation-redesign-validation/t03-logs/adjacent.log 2>&1`

   Exit **0**; **128/128 pass**, no skips/errors. [Adjacent log](t03-logs/adjacent.log).

5. Full backend:

   `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v > docs/evidence/conversation-redesign-validation/t03-logs/backend-final.log 2>&1`

   Exit **0**; **1015/1015 pass**, no skips/errors. [Final backend log](t03-logs/backend-final.log). Existing datetime `utcnow()` deprecation warnings remain in unrelated paths.

6. `git diff --check` — exit **0**.

An intermediate expanded/full run caught one architectural failure, `test_repair_import_has_no_database_or_game_execution_dependencies`: importing concrete provider exception definitions loaded `httpx`. The service now accepts typed `ConversationError` values from its injected hook and uses standard exception handling, removing that infrastructure dependency. The complete earlier run (**1015 tests, exactly that one failure**) is retained in [backend.log](t03-logs/backend.log); the final full run above is green.

## Limits and coordinator follow-up

- `reserve` is a trusted coordinator boundary: it must reserve a **fresh** durable attempt, recheck current fencing/budget, commit, and release its transaction. Existing `TurnStore.record_attempt` may return an idempotent replay; its documentation explicitly says replay is not a new dispatch grant. The service cannot infer database commit state or grant freshness from a detached `ProviderAttempt` alone. The coordinator must not wrap a replay as a new allowance. A local allowance is single-use; the durable store supplies cross-worker/restart enforcement.
- The injected whole-reply validator must rebuild any offline semantic claim/canon projections from the replacement text. The service checks its report/revisions and never treats absent or blocking validation as accepted output. Deterministic validation does not prove all free prose safe.
- Provider dispatch/output persistence, SQL connection instrumentation, semantic projection production, coordinator wiring and downstream canon admission/publication remain their existing owners' responsibilities. This deliverable does not publish continuity or authorize gameplay.

Proposed ledger update for Main Agent: mark validation/T03 ready for review with focused 17/17, adjacent 128/128 and backend 1015/1015 evidence; record the coordinator integration requirements above. No checkbox/status edit was made by this worker. Follow-up: coordinator/turn orchestration must wire fresh allowance reservation, guarded repair hook, durable attempt output handling, and exact replacement validation projections.
