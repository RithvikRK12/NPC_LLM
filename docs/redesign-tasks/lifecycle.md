# lifecycle implementation tasks

**Goal:** Deliver the `lifecycle` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§4,5.1,5.4,6.7.
**Owned files / integration targets:** backend/app/services/conversation/lifecycle.py; backend/tests/test_conversation_lifecycle.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [game-adapters](game-adapters.md), [persistence-adapters](persistence-adapters.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### lifecycle/T01: Implement clear-chat boundary

- [ ] **Task complete**

**Depends on:** ports/T02; persistence-adapters/T04.
**Acceptance criteria:** Lifecycle.clear(key) atomically increments epoch, invalidates queued/active work, deletes transcript/results/drafts/summaries/reports/interpretations/negotiations and retains minimal digest/status tombstones, canon and accepted operations. Preserve authored identity and relationship/encounter progress.
**Test expectations:** Deletion/preservation matrix; clear before operation prevents effect; clear after commit preserves effect/receipt but suppresses old speech/canon; old retry invalidated, no erased text recovered; canon origin survives deletion.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### lifecycle/T02: Implement new-game scope and async invalidation

- [ ] **Task complete**

**Depends on:** lifecycle/T01; game-adapters/T03.
**Acceptance criteria:** Lifecycle.new_game(expected_scope) serializes with game writes, replaces scope and resets all run state including generated canon. Authored identity survives; old receipts are recovery-only and cannot leak to new context. All caches/async writes carry scope/NPC/epoch.
**Test expectations:** Reset during generation/operation/summary/delivery; stale expected scope rejected; late workers/index entries cannot revive old state; cache key collision across runs excluded; no old operation replay.

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
