# capabilities implementation tasks

**Goal:** Deliver the `capabilities` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§3.2,6.1,6.4.
**Owned files / integration targets:** backend/app/services/conversation/capabilities.py; backend/tests/test_conversation_capabilities.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [baseline](baseline.md), [game-adapters](game-adapters.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### capabilities/T01: Build descriptors from authoritative views

- [ ] **Task complete**

**Depends on:** ports/T01; baseline/T01.
**Acceptance criteria:** CapabilityReader.read(scope, npc_id) exposes audited command IDs, typed parameters, allowed targets, availability and supported speech acts derived from existing rule owners; private denials have safe public reasons.
**Test expectations:** Fake Craftsman/Gatherer states exercise available/unavailable roles and targets; unknown commands absent; no independent permissions table or private-state disclosure.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### capabilities/T02: Verify descriptor and executor conformance

- [ ] **Task complete**

**Depends on:** capabilities/T01; game-adapters/T02.
**Acceptance criteria:** For each registry command compare visible availability/preconditions with the same service used at execution; stale snapshots never grant permission.
**Test expectations:** Shared adapter fixtures cover ownership, quantity, quest and activity states; changed availability is rejected on recheck; inspect-versus-complete distinction retained.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | Unassigned / not started | Not run | None recorded |
| T02 | Unassigned / not started | Not run | None recorded |
