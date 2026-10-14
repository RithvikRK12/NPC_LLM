# godot-adapters implementation tasks

**Goal:** Deliver the `godot-adapters` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §7.2; Proposal §17.
**Owned files / integration targets:** frontend/godot/scripts/conversation_gateway.gd (new); frontend/godot/scripts/conversation_presenter.gd (new); frontend/godot/scripts/{chat_window,main,craftsman_gateway,gatherer_gateway}.gd; frontend/godot/tests/conversation_*_smoke.gd (new).
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [api-adapter](api-adapter.md), [contracts](contracts.md), [game-adapters](game-adapters.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### godot-adapters/T01: Implement stable request tracking and polling

- [ ] **Task complete**

**Depends on:** contracts/T03; api-adapter/T01.
**Acceptance criteria:** conversation_gateway owns stable IDs, pending status/polling/retry and scope/epoch checks; obtain key from /world. Persist/reuse same ID for delivery retries; new submission gets new ID. Disconnect resolves existing turn and refreshes world.
**Test expectations:** Mock backend/headless tests cover 202 polling, redelivery/disconnect after commit, same ID after retry/restart, new ID for new input, invalidation while polling and no new action on status read.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### godot-adapters/T02: Present ordered final dialogue and lossless beats

- [ ] **Task complete**

**Depends on:** godot-adapters/T01; api-adapter/T02.
**Acceptance criteria:** conversation_presenter displays finalized turns once by ID/sequence, suppresses obsolete keys, advances using terminal/invalidated server metadata and preserves complete long text. Window composes presenter/gateway. Clear/new-game copy explains biography/action lifetime.
**Test expectations:** Out-of-order/delayed duplicate replies, clear/reset during beats and suppressed sequence gap; long-story reconstruction matches final_dialogue; narrative text never triggers motion/items; existing controls remain usable.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### godot-adapters/T03: Centralize revision-aware world and activity application

- [ ] **Task complete**

**Depends on:** godot-adapters/T02; game-adapters/T03; api-adapter/T03.
**Acceptance criteria:** Chat/world/encounter gateways share resource-revision-aware snapshot application; never repeated inventory deltas. Animations follow verified activity/event identity with deduplication, independent of textual beats.
**Test expectations:** Different-NPC shared inventory snapshots arrive out of order; old response cannot rewind inventory/quest/activity; duplicate event cannot animate twice; disconnect after action refreshes authoritative state; story wording cannot trigger animation.

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
