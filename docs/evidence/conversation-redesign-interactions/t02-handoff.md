# interactions/T02 handoff

## Scope and status

- Task: `interactions/T02`, exact-turn consent binding and compound-request selection.
- Status: implemented locally; ready for Main Agent review.
- Owned code changes: `backend/app/services/conversation/interactions.py` and `backend/tests/test_conversation_interactions.py`.
- This is pure policy. It does not persist transitions, execute operations, or queue unselected offers.

## Behavior delivered

- A consent binding is created only for one supported direct operation candidate tied to an active pending question. The question's exact turn and persisted final-reply text must be in the accepted context; the selected answer span must resolve against the current player message.
- Target and operation terms must match the pending interaction. The matching current `InteractionPreconditionState` must be server-evaluated as satisfied. Relevant preconditions are copied from the injected command capability view.
- A bare direct confirmation against a suspended interaction does not bind. Explicit resume with missing or unavailable precondition state still asks for a fresh confirmation. Cancelled, expired, and fulfilled interactions cannot bind.
- Multiple supported direct requests create a proposed `action_choice` interaction containing inert offered candidates and ask which action should happen first. No candidate becomes a queued operation.
- A later selection must match exactly one offered candidate by ID, command, arguments, target, and direct modality. The consent records the current selection span, but points to the exact offered operation. More than one candidate in the answer asks the user to choose only one.
- `InteractionPlan.validate_current` rejects a previously created consent plan after the authoritative interaction has become fulfilled or changed revision. Applying that terminal transition remains the store/operation adapter's responsibility.

## Tests and checks

| Exact command | Exit | Result |
| --- | ---: | --- |
| Initial RED run: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_interactions -v` | 1 | New direct-binding assertion failed as expected. The first test draft also used an item outside the frozen capability allowlist (`stone`) and a 5-character span for the 6-character word `resume`; both fixture issues were corrected. |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_interactions -v` | 0 | 18 passed. |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_interactions backend.tests.test_conversation_contracts_interfaces backend.tests.test_conversation_context backend.tests.conversation_port_conformance backend.tests.test_read_ports -v` | 0 | 57 passed. |
| `git diff --check` | 0 | No whitespace errors. |

The Main Agent will run the combined conversation and full backend suites after this handoff. No live provider or player database is required for the pure policy tests.

## Boundary and follow-up

Consent is bound to its answering `TurnRef`; this module has no durable consumption ledger. The operation/store integration must atomically compare the pending interaction revision, recheck live preconditions, and mark a successful operation fulfilled so a stale plan cannot be reused. Choice transitions are proposals until the store applies them. Capability and context authenticity remain server-adapter responsibilities.


## Main Agent review update (2026-10-15)

Main Agent reviewed the action-choice binding against detailed design §6.3 and the frozen contracts. The binding identifies only the exact offered operation and current answering turn. Its satisfied `InteractionPreconditionState` is scoped to the action-choice interaction's aggregate fingerprint; it is not proof that the selected command's preconditions passed. OperationPolicy and the transaction gateway must recheck the selected command before execution. No contract expansion was needed. Main Agent reproduced focused 18/18 and adjacent 57/57; the combined conversation suite passed 250/250 and full backend discovery passed 713/713. The duplicate import found during review was removed and focused/adjacent checks rerun.
