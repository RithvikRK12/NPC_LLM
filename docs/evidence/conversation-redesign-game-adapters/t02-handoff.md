# game-adapters/T02 implementation handoff

Implemented 2026-10-18 by bounded worker `game_adapters_t02`. Independent review found no blocking defect; Main Agent reproduced focused, conversation and full backend checks and accepted T02. No task packet or master progress checkbox was changed by the worker.

## Files and interface changes

- `backend/app/services/conversation/adapters/game.py`: public detached `GameReadAdapter` implementing the existing `CapabilityReadPort` / `WorldReadPort` shapes; immutable internal `ConsentSnapshot`; final current precondition, exact target, one-unit ownership and current consent rechecks; safe typed `Denied` results for expected rule failures; effect savepoint rollback.
- `backend/app/services/craftsman.py`: pure `conversation_command_available(command, state)` helper shared by descriptions and the existing activity owner. Two existing branch predicates now call this helper without changing endpoint behavior, staging gates, command replay or transaction ownership. Main Agent confirmed this minimal owner-file refactor was within T02 scope.
- `backend/tests/test_conversation_game_adapters.py`: 29 isolated SQLite tests, including the original 15 T01 checks. Expected rule-rejection assertions now check typed denials; success fixtures obtain real current descriptors inside their caller transaction.
- This handoff.

No contracts, ports, storage models, routes or transport wiring changed. No shared resource revision counters, provider invocation, game save access, relationship scoring, or new game capability was added. The T01 eight-command allowlist and stable turn-derived command identity remain intact.

`GameReadAdapter.read_capabilities(scope, npc_id, visibility)` returns only existing immutable capability descriptors. Per-role availability derives from audited existing rules, current inventory, opening/story gates and the shared Craftsman activity gate. Exact current inventory constrains the item domain; an empty unavailable stock uses the frozen nonempty item schema domain while `available=False`. Public unavailable reasons use one fixed safe sentence. Preconditions carry opaque semantic gate fingerprints, not executable authorization or T03 monotonic resource revisions.

`read_facts(scope, npc_id, epoch, visibility)` returns only immutable `MechanicalFact` values. It projects exact inventory quantities, legacy quest status/progress, bow phase, and the NPC's public encounter/activity state. Craftsman facts include ship quest phase/materials from the existing quest snapshot. It does not call record/quest creators or timed reward writers. It omits private social scores, pending item, raw encounter commands/checkpoints, NPC current-state strings and private denial details. Requests for `npc_private` still receive only these public mechanical facts. A wrong game scope or unknown NPC receives no values. Reads detach immediately: changing ORM state later does not change returned contracts. Active conversational epoch validation remains the injected context/gateway storage boundary; the supplied epoch labels detached evidence identity and does not authorize gameplay.

`GameOperationAdapter.execute` now returns `GameOperationEffect | Denied`. Non-typed API misuse and absence of a caller transaction still raise static programming errors. Expected `ValueError` / owner `HTTPException` failures become fixed public `NOT_AVAILABLE` or `TERMS_CHANGED` values; exception text/details are never copied. Infrastructure exceptions continue to propagate for full caller rollback. An internal SQL savepoint rolls back all attempted effects on a normal denial. The existing player writer lock is acquired **before** that savepoint: SQLite's deferred BEGIN would otherwise let releasing a first-statement savepoint commit effects independently of the caller. Original caller rollback/reopen tests prove this remains correct.

Every request must present exactly the current descriptor's preconditions, including direct requests without consent. Empty tuples cannot bypass the comparison. Under the caller's writer transaction, the adapter refreshes scope/role/target/story state, checks exact canonical target reference, rechecks exact one-unit item ownership, and invokes only the registered owner. An old selected item is denied when missing; another available item is never substituted. Unsupported quantities remain forbidden by frozen typed arguments.

Consent-backed execution requires a server-injected `consent_loader(turn, interaction_id)` that runs within the same caller transaction immediately before dispatch. Missing loaders/snapshots fail closed. The immutable `ConsentSnapshot` contains the current persisted interaction, an **independently authoritative current operation**, exactly the current question and separately admitted answer texts, and the exact expected answer substring. The adapter revalidates these typed values, current status/fingerprint/question identity/text, current operation command/arguments/target/modality/question terms, answering turn, current game preconditions and exact answer span. This extra current operation is necessary because frozen `PendingInteraction` item negotiations retain item/quantity/target but do not carry transfer command direction. Reusing the question text as an answer span is rejected.

The existing Craftsman request produces only `ActivityResult(stage='accepted')` and accepted-outing facts. No inspection completion command was registered. Trusted physical staging remains in the existing owner; its completed inspection and resulting ship quest become visible only after that owner has actually established them.

## RED/GREEN evidence

All commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1` using the existing virtual environment. Test data is a fresh disposable SQLite file for each test, seeded independently of any player save/provider. Temporary logs named below retain exact local output.

| Phase | Exact command | Exit | Result |
| --- | --- | --- | --- |
| Initial T02 RED | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_game_adapters.py' > /private/tmp/game-t02-red.log 2>&1` | 1 | 23 cases; six missing-view/consent assertions and two legacy expected service exception escapes |
| First GREEN after denial boundary/SQLite transaction correction | Same focused command, output `/private/tmp/game-t02-green.log` | 0 | 23 tests pass; original T01 rollback checks exposed and verified the SQLite savepoint correction |
| Target/shared-owner RED | Same focused command, output `/private/tmp/game-t02-second-red.log` | 1 | 26 cases; changed target alias incorrectly transferred; shared owner helper absent |
| Current command terms RED | Same focused command, output `/private/tmp/game-t02-consent-red.log` | 1 | 27 cases; current consent snapshot lacked independently authoritative command terms |
| Current modality RED | Same focused command, output `/private/tmp/game-t02-modality-red.log` | 1 | Current negated operation incorrectly authorized transfer; corrected by exact current modality comparison |
| Question-as-answer RED | Same focused command, output `/private/tmp/game-t02-answer-red.log` | 1 | 28 cases; question text reused as answer span incorrectly authorized transfer |
| Empty-preconditions RED, Main Agent review | Same focused command, output `/private/tmp/game-t02-empty-red.log` | 1 | 29 cases; empty checked-precondition tuple incorrectly bypassed comparison |
| Final focused GREEN | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_game_adapters.py' > /private/tmp/game-t02-final-focused.log 2>&1` | 0 | 29 tests pass |
| Final adjacent conversation | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' > /private/tmp/game-t02-final-conversation.log 2>&1` | 0 | 344 tests pass |
| Final full backend/mechanical regressions | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests > /private/tmp/game-t02-final-backend.log 2>&1` | 0 | 807 tests pass |
| Tracked whitespace | `git diff --check` | 0 | No diagnostics |
| Owned-file whitespace | Existing venv Python checks every line of the three owned Python files against `line.rstrip()` | 0 | All three files pass; covers untracked additions omitted by `git diff` |

Final suites emit existing datetime/Starlette/httpx deprecation warnings and the existing lexical-retrieval fallback notice. No failing tests were omitted. No PostgreSQL test was represented as passing.

## Acceptance mapping and integration limits

- **Detached authoritative views and safe denials:** public-only immutable projections, wrong-scope exclusion, no read record creation, detached snapshots, generic safe reasons and owner exception redaction tests pass.
- **Craftsman/Gatherer/inventory/quest/activity conformance:** both NPC roles and every registered command are checked against actual dispatch; additional active/completed outing, blocked/resolved Gatherer and empty-stock cases pass. Existing bow material consumption/reward restrictions and quest rollback tests remain green.
- **Exact final rechecks:** changed ownership/role/target references, stale encounter revision, changed/cancelled/missing consent, current command-direction/modality substitution, question/answer mismatch, question-as-answer and empty-precondition bypass tests all deny without changing inventories or substituting an item.
- **Accepted versus completed:** an inspection request sets active outing and leaves completion false/ship quest absent. Only trusted staged owner completion yields completion true and ship quest material gathering. Dialogue cannot dispatch that command.
- **Transaction boundary:** original T01 rollback tests plus a private owner exception after a flushed mutation prove savepoint rollback and caller rollback remain effective on SQLite. No outer commit/rollback was introduced.

The current-consent loader is an injected authoritative storage boundary with deterministic conformance fixtures. This worker did not implement a concrete persisted loader, durable `OperationGateway`, receipt write, lease/epoch checks, lost-acknowledgement recovery, or PostgreSQL lock/concurrency proof. Persistence must supply authenticated current operation/question/answer snapshots, recover existing receipts before dispatch, and commit receipts atomically with these effects. A fake loader does not establish that production integration is wired. The adapter's semantic fingerprints do not satisfy T03 resource-version/write-path requirements. T03 remains dependent on persistence-adapters/T01; no expansion was made into it.

T02 is locally accepted with the integration limits above; this handoff makes no whole-module or runtime completion claim.
