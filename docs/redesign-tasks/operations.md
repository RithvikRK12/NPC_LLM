# operations implementation tasks

**Goal:** Deliver the `operations` responsibility in the NPC conversation redesign.
**Status:** operations/T01–T02 accepted locally; 2/2 task deliverables verified; concrete gateway/game-adapter integration remains pending.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§4,6.3–6.4.
**Owned files / integration targets:** backend/app/services/conversation/operations.py; backend/app/services/validation/items.py; backend/app/services/craftsman_intent.py; backend/tests/test_conversation_operations.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [contracts](contracts.md), [interactions](interactions.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### operations/T01: Implement pure operation decision policy

- [x] **Task complete**

**Depends on:** contracts/T03; interactions/T02.
**Acceptance criteria:** OperationPolicy.decide(proposal, interaction_plan, context) returns NoOperation/ClarificationRequired/Denied/ReadyToRecheck; reject ineligible modalities, invalid commands/targets/parameters and ambiguous consent. Retire heuristic interception in redesigned path.
**Test expectations:** Quotes, negations, hypotheticals and ambiguous answers do not execute; multiple supported actions clarify; unrelated purpose words do not transfer; confidence values confer no permission.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### operations/T02: Dispatch only typed audited operations

- [ ] **Task complete**

**Depends on:** operations/T01; ports/T02.
**Acceptance criteria:** Dispatch ReadyToRecheck through OperationGateway.execute_once(turn, fence, decision); no generated state_update/action strings or relationship deltas. Gateway outcome is the only receipt source; operation policy has no prose or provider dependency.
**Test expectations:** Fake gateway checks at most one invocation, exact command arguments, typed denials, and narrative/report inability to authorize; stage retry uses existing receipt through gateway contract.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | operations_t01 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / medium | [Handoff](../evidence/conversation-redesign-operations/t01-handoff.md); focused 14/14, interactions 18/18, contracts 70/70, conversation 305/305; `git diff --check` exit 0 | Pure policy only; gateway execution, atomic receipts and durable rechecks remain T02 |
| T02 | Main Agent / accepted 2026-10-18; model identifier unavailable in current runtime | [Handoff](../evidence/conversation-redesign-operations/t02-handoff.md); focused 20/20, store-port 32/32, interactions 18/18, contracts 70/70, conversation 311/311, backend 774/774; `git diff --check` exit 0 | Injected gateway dispatch and receipt-first retry verified with doubles; concrete adapter transaction/atomicity remains outside this packet task |
