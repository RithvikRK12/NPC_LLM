# baseline implementation tasks

**Goal:** Deliver the `baseline` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Proposal §§2,16,19,21; Detailed design §§9–10.
**Owned files / integration targets:** docs/evidence/conversation-redesign-baseline/; backend/tests/fixtures/conversation/; docs/redesign-policy-inventory.md.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** None. Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### baseline/T01: Inventory current contracts and mechanical authority

- [ ] **Task complete**

**Depends on:** None.
**Acceptance criteria:** Document live /chat path, all input/output/context limits, existing renderer contracts, game-rule owners, internal commits, revision writers, and explicit game_id/timeline_id mapping decisions. Identify reusable code without claiming redesign completion.
**Test expectations:** Trace one ordinary and one action path by inspection; enumerate current regression commands and all inventory/quest/activity writers, including non-chat endpoints.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### baseline/T02: Measure provider health and response origins

- [ ] **Task complete**

**Depends on:** baseline/T01.
**Acceptance criteria:** Capture representative Craftsman and Gatherer sessions with exact provider/model/configuration, generated/scripted/fallback/error counts, and ordinary/action/repair p50/p95. Use isolated fixtures, never a player save. Record unavailable measurements honestly.
**Test expectations:** Replay identical fixtures; distinguish healthy-provider fallback from outage fallback and explicit mock; verify diagnostics contain no credentials.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### baseline/T03: Freeze evaluation fixtures and policy candidates

- [ ] **Task complete**

**Depends on:** baseline/T02.
**Acceptance criteria:** Freeze at least 40 scenarios, generally 4–8 turns, across both NPCs and the Proposal §19 categories. Inventory candidate deadline/token/beat/queue/lease/summary/retention policies; numeric shipping limits remain subject to measurement and product acceptance.
**Test expectations:** Validate scenario IDs, initial state, expected mechanical outcomes, model settings and scoring denominators; check every required scenario category has coverage.

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
| T03 | Unassigned / not started | Not run | None recorded |
