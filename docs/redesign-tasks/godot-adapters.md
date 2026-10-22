# godot-adapters implementation tasks

**Goal:** Deliver the `godot-adapters` responsibility in the NPC conversation redesign.
**Status:** T01–T03 locally accepted after Godot 4.7.2 headless verification. Backend-dependent live UI integration remains open; see the task handoffs.
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

- [x] **Task complete**

**Depends on:** contracts/T03; api-adapter/T01; api-adapter/T02 (added after inspection confirmed T02 owns `/world` epoch projection required by this task's scope/epoch check).
**Acceptance criteria:** conversation_gateway owns stable IDs, pending status/polling/retry and scope/epoch checks; obtain key from /world. Persist/reuse same ID for delivery retries; new submission gets new ID. Disconnect resolves existing turn and refreshes world.
**Test expectations:** Mock backend/headless tests cover 202 polling, redelivery/disconnect after commit, same ID after retry/restart, new ID for new input, invalidation while polling and no new action on status read.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence). Existing smoke assertions now use counted checks and an explicit failure exit code; see handoff for scenario coverage limits.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### godot-adapters/T02: Present ordered final dialogue and lossless beats

- [x] **Task complete**

**Depends on:** godot-adapters/T01; api-adapter/T02.
**Acceptance criteria:** conversation_presenter displays finalized turns once by ID/sequence, suppresses obsolete keys, advances using terminal/invalidated server metadata and preserves complete long text. Window composes presenter/gateway. Clear/new-game copy explains biography/action lifetime.
**Test expectations:** Out-of-order/delayed duplicate replies, clear/reset during beats and suppressed sequence gap; long-story reconstruction matches final_dialogue; narrative text never triggers motion/items; existing controls remain usable.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence. Broader UI smoke is blocked by its unavailable `/world` backend; see handoff.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### godot-adapters/T03: Centralize revision-aware world and activity application

- [x] **Task complete**

**Depends on:** godot-adapters/T02; game-adapters/T03; api-adapter/T03.
**Acceptance criteria:** Chat/world/encounter gateways share resource-revision-aware snapshot application; never repeated inventory deltas. Animations follow verified activity/event identity with deduplication, independent of textual beats.
**Test expectations:** Different-NPC shared inventory snapshots arrive out of order; old response cannot rewind inventory/quest/activity; duplicate event cannot animate twice; disconnect after action refreshes authoritative state; story wording cannot trigger animation.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence); RED/GREEN history is in the handoff.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence. Live UI smoke remains unavailable without a backend.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | Main Agent / locally accepted 2026-10-18; implementation and static independent review pre-existed; Main Agent added a GDScript type annotation and reliable smoke-runner exit accounting | `/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot --headless --version` exit 0; `--headless --path frontend/godot --editor --quit` exit 0 with no script parse/compile errors; `--headless --path frontend/godot --script res://tests/conversation_gateway_smoke.gd` exit 0, 19 passed / 0 failed; logs in `../evidence/conversation-redesign-godot-adapters/t01-runtime/` | [Handoff](../evidence/conversation-redesign-godot-adapters/t01-handoff.md); API T02 epoch projection and T03 durable transport verified upstream. Smoke is focused on gateway contracts/guards; it does not simulate a full HTTP mock-server lifecycle. |
| T02 | Main Agent accepted 2026-10-18; implementer `/root/godot_t02_presentation`, gpt-6-luna / medium; Main Agent independently reproduced focused checks | Godot 4.7.2: presenter smoke 15/15, gateway smoke 19/19, editor import exit 0, `git diff --check` exit 0; RED regressions recorded; broader `ui_rework_smoke.gd` blocked by unavailable backend | [Handoff](../evidence/conversation-redesign-godot-adapters/t02-handoff.md); local presenter accepted; control/backend integration limits remain explicit; T03 dependencies now satisfied |
| T03 | Main Agent accepted 2026-10-18; implementer `/root/godot_t03_revisions`, gpt-6.1-sol / high; Main Agent independently reproduced core checks | Godot 4.7.2: revisioned-state 25/25, gateway 19/19, presenter 15/15; six adjacent smokes and editor import exit 0; `git diff --check` exit 0; RED/GREEN logs in `../evidence/conversation-redesign-godot-adapters/t03/` | [Handoff](../evidence/conversation-redesign-godot-adapters/t03-handoff.md); live UI smoke unavailable because backend port 8001 refused connection; legacy unlabelled transfer/salvage use read-only `/world` reconciliation |
