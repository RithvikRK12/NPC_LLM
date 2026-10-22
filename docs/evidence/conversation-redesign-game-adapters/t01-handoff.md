# game-adapters/T01 implementation handoff

Implemented 2026-10-18 by bounded worker `game_adapters_t01`. Main Agent reproduced the final checks and accepted T01 after an independent review identified and the worker corrected a false `changed=True` replay result. No task packet or master progress was changed by the worker.

## Files

- `backend/app/services/conversation/adapters/game.py` — new immutable audited registry, stable encounter identity and caller-transaction participant.
- `backend/tests/test_conversation_game_adapters.py` — 15 focused SQLite adapter tests.
- This handoff, requested by the Main Agent.

No existing service, route, contract, port, persistence model or domain policy was edited. Existing unrelated working-tree changes were preserved. Nothing was committed or staged.

## Audit and implementation

Read the packet, master shared rules, baseline policy inventory, detailed design §§6.4 and 9, frozen conversation contracts/ports, and existing owner implementations/tests. The registry is an explicit allowlist, not an enumeration of API endpoints or a reflection of the `CommandId` union.

| Registered commands | Typed arguments | Existing rule owner |
| --- | --- | --- |
| `give_item`, `receive_item` | `ItemArguments` with one enumerated item; no supplied quantity | `app.services.state.service.StateService.apply` |
| `report_wreck`, `begin_ship_inspection`, `wait`, `resume`, `postpone`, `return` | `NoArguments` | `app.services.craftsman.apply_command` |

Transfer execution constructs a server-owned legacy output with zero relationship deltas, then invokes the existing one-unit transfer/legacy quest owner and `bow.maybe_start` for its existing material/routine consequence. It never accepts generated legacy action strings, state updates, biography or charm. It does not invoke timed rewards. The adapter revalidates typed values to reject invalid `model_copy`/`model_construct` payloads.

The directly eligible owners already flush without committing: `StateService.apply`, `craftsman.apply_command`, and `bow.maybe_start`. The existing trusted `gatherer.apply_command` also flushes only. No commit refactor was necessary. Opening/salvage services and quest API writers that own commits are not dispatched by this registry; no transport semantics were changed.

`GameOperationAdapter.execute(turn, decision, *, expected_encounter_revision=None)` requires an open caller transaction, follows the existing Player-before-NPC writer order, rechecks current scope/opening/role/target/story gates, invokes existing owners, flushes, and returns a detached `GameOperationEffect`. Exceptions propagate for caller rollback. This is not the concrete `OperationGateway` and does not create a committed receipt.

Encounter keys are UUID5 over canonical JSON containing all stable `TurnRef` fields and exact command, arguments and target. Proposal candidate IDs, wording and source spans are excluded. Existing Craftsman command replay works across new sessions/adapters without another revision or memory insertion. Ordinary command results report `changed=False` on saved command-key replay and `changed=True` for a newly applied command. This describes the current adapter invocation rather than constructing an immutable historical receipt. A fresh request that the owner would no-op because an inspection is already active/complete cannot be reported as a newly accepted activity; exact historical replay remains available.

## RED/GREEN evidence

Commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1` using the existing venv. Tool outputs preserve initial execution evidence. The final post-review full-backend rerun also wrote `/private/tmp/conversation-game-adapters-t01-backend.log`.

| Phase | Exact command | Exit | Result |
| --- | --- | --- | --- |
| RED, adapter absent | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_game_adapters.py'` | 1 | 13 tests, 13 expected assertion failures: audited adapter absent |
| GREEN, first implementation | Same focused command above | 0 | 13 tests passed |
| RED, inspection no-op edge | Same focused command above | 1 | 15 tests, 1 failure: `test_inspection_noop_cannot_be_reported_as_a_new_accepted_activity`; expected `ValueError` was not raised |
| GREEN, replay-aware acceptance guard | Same focused command above | 0 | 15 tests passed |
| RED, Main Agent replay review regression | Same focused command above | 1 | 15 tests, 1 failure: `test_encounter_replay_uses_stable_turn_and_terms_across_new_adapter_instances`; replay incorrectly reported `changed=True` instead of `False` |
| GREEN, owner saved-command replay semantics | Same focused command above | 0 | 15 tests passed; replay reports no new mutation and actual revision remains unchanged |
| Adjacent conversation contracts/policies/ports | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | 0 | 330 tests passed |
| Full backend including existing mechanical regressions | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` | 0 | 793 tests passed |
| Final post-review full backend | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests > /private/tmp/conversation-game-adapters-t01-backend.log 2>&1` | 0 | 793 tests passed; final focused and conversation commands above were also rerun after the review correction, passing 15 and 330 tests |
| Existing tracked diff whitespace | `git diff --check` | 0 | No whitespace diagnostics; this command does not cover untracked additions |

Additional `git diff --no-index --check /dev/null <new-file>` checks for each new Python file emitted no whitespace diagnostics and returned 1 because the files differ from `/dev/null`; these were not counted as passing test runs. The suites emit existing datetime/Starlette deprecation warnings and intentional fallback/embedding-unavailable logs. No failed tests or skipped PostgreSQL gate are represented as passing evidence.

## Criterion mapping

1. **Audited, typed existing command registry:** immutable eight-command allowlist with named owners and role metadata; tests reject unsupported physical/combat/quest/reward endpoints and malformed/generated effect parameters before dispatch. All six existing outing controls are exercised.
2. **Caller transaction participation:** isolated SQLite rollback/reopen tests demonstrate transfer inventory and legacy quest progress rollback; bow crafting/material consumption also roll back. Adapter has no commit/rollback or provider/embedding call.
3. **Shared deterministic consequences:** one isolated caller transaction combines adapter transfers and inspection acceptance with an existing trusted Gatherer combat outcome. Explicit caller rollback restores inventory, legacy quest progress, Gatherer relationship values, encounter state, authoritative memories, and the memory-index revision. Gatherer combat/outcome commands remain excluded from the conversation registry. Inspection acceptance produces authoritative acceptance memory without inspection completion or ship quest creation. Typed transfer effects leave trust unchanged and do not grant a bow reward.
4. **Stable encounter identity:** tests cover same-turn replay across new sessions, changed scope/epoch/NPC/turn/request/sequence/command/item identity, and candidate-ID independence. Existing command replay does not duplicate memory or revision effects and its ordinary command result explicitly reports `changed=False`.

## Limits and next-owner handoff

- Evidence proves explicit SQLite caller rollback, not SQL receipt insertion failure, commit uncertainty, concurrent-worker idempotency, lease fencing, active epoch checks or receipt/effect atomicity. Transfers are not independently idempotent. Persistence must recover an existing receipt before dispatch and commit its receipt with these effects.
- No PostgreSQL suite or connection was attempted. PostgreSQL lock/receipt atomicity remains the persistence adapter gate; SQLite results do not satisfy that gate.
- The gateway must supply current exact precondition/consent authorization before calling this participant. T02 owns detached views, safe typed denials and the complete current consent/precondition integration. Owner exceptions currently propagate; they must not become public transport details.
- `expected_encounter_revision` is passed to the existing owner when supplied; omission uses its current locked revision. T02/gateway integration must bind the correct expected terms instead of treating a revision refresh as renewed consent.
- T03 owns shared resource revisions and non-chat writer discipline. This worker did not expand into those paths.
- No production wiring, API change, live provider invocation, embedding invocation, player save access or new relationship scoring was introduced. No complete runtime redesign or full gateway readiness is claimed.

Independent review found no remaining blocker within T01 after the replay correction. Main Agent reproduced the focused, conversation and full backend suites; T01 is locally accepted. PostgreSQL and receipt/gateway atomicity remain downstream integration gates.
