# interactions/T01 handoff

## Scope and status

- Task: `interactions/T01`, pure interaction transition table.
- Status: implemented locally; ready for Main Agent review.
- Contract dependency: accepted `contracts/T03` and `contracts/T05`, including typed direct-only `InteractionLifecycleCue` values and current-turn server-evaluated precondition states.
- Owned code changes: `backend/app/services/conversation/interactions.py` and `backend/tests/test_conversation_interactions.py`.
- This task does not persist transitions, bind consent, choose/execute operations, or inspect game state directly.

## Behavior delivered

`InteractionPolicy.plan(current, proposal, context)` requires the current pending map to match the immutable accepted context snapshot. It validates the proposal's source references against the exact current player message before consuming lifecycle cues.

- A new concern not linked to an active interaction's question suspends that active negotiation.
- Explicit direct cancellation targets only the interaction ID named by the validated cue.
- Resume requires a validated direct cue to a suspended interaction and a matching current server-evaluated `satisfied` state. Missing or `unavailable` state asks for clarification; no consent is created.
- Only a matching server-evaluated `failed` precondition state expires a pending interaction. Changed item or target terms expire only when accompanied by that current failed state.
- Elapsed turns, arbitrary time, purpose-like wording, and unrelated revision changes do not expire a request. A changed item transfer amount is invalid under the shared one-item `PendingInteraction` contract.
- Multiple suspended interactions linked to the same concern ask which request; the policy does not select the newest record.
- No-op status evaluations do not churn revisions. Each emitted transition advances its expected revision once.
- `ContextPacket` validation enforces at most one active item negotiation per NPC conversation; a regression test preserves that contract.

## Tests and commands

Commands ran from the repository root using `.venv`.

| Exact command | Exit | Result |
| --- | ---: | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_interactions -v` before implementation | 1 | Expected RED: 9 tests failed with `AssertionError: T01 pure interaction transition policy is absent` |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_interactions -v` after implementation | 0 | 11 passed |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_interactions backend.tests.test_conversation_contracts_interfaces backend.tests.test_conversation_context backend.tests.conversation_port_conformance backend.tests.test_read_ports -v` | 0 | 50 passed |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | 1 | 212 tests ran; 204 passed and 8 errored because `app.services.conversation.proposal` is not yet present (`proposal/T01` dependency work) |
| `git diff --check` | 0 | No whitespace errors |

The broad test run failure is outside this task's owned module. It consisted of eight `ModuleNotFoundError: No module named 'app.services.conversation.proposal'` errors in `test_conversation_proposal.py`.

## Limitations and follow-up

- The policy treats `interaction_links` as question relevance references; natural-language relevance classification remains with proposal interpretation. Text such as “purpose” or “later” is never used as a lifecycle rule.
- The policy consumes, but does not produce or authenticate, `InteractionPreconditionState`. A trusted server/context adapter must supply fresh matching evaluations.
- Consent binding and compound-request selection remain `interactions/T02`; durable compare-and-swap application and execution remain adapter/finalization work.
- Quantity is fixed to one item by the existing `PendingInteraction` contract. A quantity change cannot be represented as a valid pending negotiation and is rejected by contract validation.
