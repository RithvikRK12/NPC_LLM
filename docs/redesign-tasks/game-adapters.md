# game-adapters implementation tasks

**Goal:** Deliver the `game-adapters` responsibility in the NPC conversation redesign.
**Status:** game-adapters/T01–T02 locally accepted; T03 implementation is in progress after persistence-adapters/T05 acceptance.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§6.4,9; Proposal §§9–10.
**Owned files / integration targets:** backend/app/services/conversation/adapters/game.py (new); backend/app/services/{state/service,craftsman,gatherer}.py; backend/app/services/quests/*; backend/app/api/routes/{inventory,craftsman,gatherer,world}.py; backend/app/database/seed.py (game reset writer); backend/tests/test_conversation_game_adapters.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [baseline](baseline.md), [persistence-adapters](persistence-adapters.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### game-adapters/T01: Audit and adapt transaction-participating game commands

- [x] **Task complete**

**Depends on:** ports/T02; baseline/T01.
**Acceptance criteria:** Registry admits only audited existing conversation-eligible operations with typed parameters and existing rule ownership. Refactor nested/internal commits into caller transaction boundary; derive encounter command IDs from stable turn identity.
**Test expectations:** Adapter rollback tests prove inventory, quest progress, verified memory and deterministic relationship consequences share transaction; generated charm/biography never grants trust/rewards; unsupported endpoints inaccessible.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### game-adapters/T02: Implement authoritative views and typed denials

- [x] **Task complete**

**Depends on:** game-adapters/T01.
**Acceptance criteria:** Expose detached capability/fact views and normalize exceptions to safe denials. Recheck ownership/quantity/role/target/consent immediately before effect; accepted outing differs from staging-evidenced completion.
**Test expectations:** Conformance fixtures for Craftsman, Gatherer, inventory, quest and activity; inspection request cannot forge completion; changed terms reject rather than substitute; private denial data filtered.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### game-adapters/T03: Version every shared-state mutation path

- [x] **Task complete** — accepted by Main Agent 2026-10-18 after SQLite/PostgreSQL review and reproduction.

**Depends on:** game-adapters/T02; persistence-adapters/T01; persistence-adapters/T05; contracts/T07.
**Acceptance criteria:** All chat and non-chat inventory/quest/activity/world writes participate in resource revision and common writer discipline; define resource snapshot revisions consumed by publication and Godot. No new gameplay capability or relationship scoring.
**Test expectations:** Non-chat write during proposal forces relevant recheck; different-NPC operation contention, activity cancellation and reset serialized correctly; authoritative snapshots monotonically label each affected resource.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | game_adapters_t01 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | 15 focused, 330 conversation, and 793 backend tests pass; independent review approved after replay-result correction; evidence `../evidence/conversation-redesign-game-adapters/t01-handoff.md` | SQLite rollback verified; PostgreSQL concurrency and durable gateway receipt atomicity remain persistence-owned |
| T02 | game_adapters_t02 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | 29 focused, 344 conversation, and 807 backend tests pass; independent review approved; evidence `../evidence/conversation-redesign-game-adapters/t02-handoff.md` | Consent loader remains an injected trusted boundary; PostgreSQL, durable gateway/receipt wiring and T03 resource revisions remain open |
| T03 | game_adapters_t03 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high; Main Agent reviewed and reproduced | [Handoff](../evidence/conversation-redesign-game-adapters/t03-handoff.md); focused SQLite 48/48, resource-revision PostgreSQL 16.15 19/19, full backend 935/935 | All shared writer/snapshot/reset revision paths verified; API/Godot revision consumption remains downstream |
