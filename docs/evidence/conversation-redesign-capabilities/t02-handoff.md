# capabilities/T02 conformance handoff

Implemented 2026-10-18 by bounded worker `capabilities_t02`. Independent review approved the all-command stale-role case; Main Agent reproduced final focused, conversation and full backend checks and accepted T02.

## Deliverable and scope

This is a tests-only evidence task. The accepted `CapabilityReader`, `GameReadAdapter` and `GameOperationAdapter` already satisfied the observed conformance cases; no production edit or permission rule was necessary. The only changed Python file is `backend/tests/test_conversation_capabilities.py`; this handoff is the only documentation addition owned by this worker. Contracts, storage, routes, game owners, task checkboxes and master progress were not edited.

Nine new integration tests exercise the real `CapabilityReader` projection over the real game read adapter and execute through the real game operation adapter and deterministic owners. They reuse the disposable seeded SQLite fixture from `test_conversation_game_adapters` through composition, so inherited adapter tests are not duplicated by unittest discovery. Every fresh matrix operation receives a distinct turn identity; historical exact command replay remains a separate accepted behavior.

## Acceptance evidence

- **Every audited command:** a literal eight-command registry expectation and hand-derived available-command sets cover both NPC roles, fresh Craftsman state, accepted outing and completed inspection. Each descriptor is compared with actual owner dispatch in a rolled-back savepoint. Tests inspect resulting inventory counts, report state, activity acceptance and outing-control mode; they do not compute expected permissions with the production eligibility helper.
- **Story, opening and ownership gates:** pending opening and active Gatherer introduction make execution unavailable; resolved Gatherer with empty NPC/player inventory denies transfers. Exact public targets, typed schemas and public nonempty preconditions are checked alongside availability.
- **Stale selected item:** both transfer directions select wood from an available wood/axe domain, then remove wood while leaving axe available. The old descriptor cannot transfer wood or substitute axe; both inventories remain unchanged. This also covers the important case where the command remains generally available and only its selected item domain changes.
- **Changed preconditions:** stale available transfer descriptions deny after opening, role or Gatherer story changes. A review follow-up snapshots each of the eight Craftsman commands while available, changes the role, and verifies every old decision denies without changing inventory, social state, activity state/revision/command log or legacy quest progress. Every activity command whose availability can flip (`begin_ship_inspection`, `wait`, `resume`, `postpone`, `return`) denies after its activity gate changes; detached preconditions differ and state remains unchanged. `report_wreck` has no activity availability flip and is covered by the literal role/opening/activity matrix.
- **Exact terms and quantity:** an available descriptor cannot authorize an unoffered target alias or forged zero/two-unit arguments. Real success transfers exactly one of two owned wood units.
- **Quest rules:** transfer changes the existing legacy quest to 50 progress; a real material transfer in bow gathering enters crafting and consumes the materials without granting a bow or a new crafting command. The resulting empty stock becomes unavailable.
- **Acceptance versus completion:** the inspection request produces only an accepted activity, disables fresh acceptance, enables outing controls and leaves the ship quest absent. No completion command is described. Only the existing trusted physical staging service completes inspection and starts the ship-material quest; subsequent descriptors and public facts reflect that completed state.

## Test-first record

The behavioral evidence was added before any contemplated production change. The initial focused command exited 1 with one failure and one error caused by two test fixture assumptions: the bow rule owner already creates its quest on transfer, and reusing an accepted inspection's exact TurnRef correctly recovers its historical acceptance after completion. The fixture was corrected to update the existing bow quest and give each fresh matrix execution its own turn. The same conformance checks then passed without production changes.

This initial failure is **not** represented as a missing-production-behavior RED test. No production defect was found, and no artificial implementation mutation was used to manufacture RED evidence. This evidence-only task therefore does not claim a production RED/GREEN cycle.

## Commands and results

All commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1` with the existing virtual environment. Each test uses fresh disposable SQLite data; no provider or player save is accessed.

| Check | Exact command | Exit | Result / local log |
| --- | --- | --- | --- |
| Initial fixture failure | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_capabilities.py' > /private/tmp/capabilities-t02-fixture-red.log 2>&1` | 1 | 12 tests; one fixture failure, one fixture error as explained above |
| Final focused | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_capabilities.py' > /private/tmp/capabilities-t02-final-focused.log 2>&1` | 0 | 13 pass, 0 fail/skip |
| Adjacent game adapters | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_game_adapters.py' > /private/tmp/capabilities-t02-final-game.log 2>&1` | 0 | 29 pass, 0 fail/skip |
| Conversation | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' > /private/tmp/capabilities-t02-final-conversation.log 2>&1` | 0 | 353 pass, 0 fail/skip |
| Full backend | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests > /private/tmp/capabilities-t02-final-backend.log 2>&1` | 0 | 816 pass, 0 fail/skip |
| Tracked whitespace | `git diff --check` | 0 | No diagnostics |
| Owned Python whitespace | `.venv/bin/python` reads `backend/tests/test_conversation_capabilities.py` and asserts every `splitlines()` entry equals `line.rstrip()` | 0 | Pass; covers the untracked file omitted by tracked diff checks |

The suites emit the existing datetime/Starlette/httpx deprecation warnings; the full suite also emits the existing bounded lexical-retrieval fallback diagnostic. No failures were omitted.

## Limits and next integration gate

This proves descriptor/executor conformance for the current audited commands under shared deterministic SQLite fixtures. It adds no permission table and makes no claim about live provider wording, concrete durable consent loading, receipt recovery, API wiring, PostgreSQL locking/concurrency, or monotonic resource revision discipline. Those remain with the existing persistence/game-adapter/release tasks. No PostgreSQL run is represented as passing. T02 is locally accepted on this evidence; the capabilities module still awaits adjacent/runtime integration gates.
