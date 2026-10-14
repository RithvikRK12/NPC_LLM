# api-adapter implementation tasks

**Goal:** Deliver the `api-adapter` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§7.1,8–10; Proposal §17.
**Owned files / integration targets:** backend/app/api/routes/{chat,world}.py; backend/app/schemas/chat.py; backend/app/api/router.py; backend/tests/test_conversation_api.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [contracts](contracts.md), [coordinator](coordinator.md), [lifecycle](lifecycle.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### api-adapter/T01: Add versioned submit and status transport

- [ ] **Task complete**

**Depends on:** contracts/T03; ports/T02.
**Acceptance criteria:** POST /chat redesigned request requires schema_version/request_id/game_scope/epoch plus NPC/message, keeps 500-character input bound and server-resolved player. 200 carries only durable final result and preserved legacy fields; 202 carries identity/status URL without draft. Scoped GET /chat/turns/{turn_id} never executes.
**Test expectations:** FastAPI fakes test 422 invalid/bounds, 404 NPC/save, 409 stale key/payload conflict, pending/final/invalidated lookup, immutable dialogue and revision-labelled snapshots; missing ID stays legacy rather than gaining false retry guarantee.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### api-adapter/T02: Add lifecycle endpoints and scoped world projection

- [ ] **Task complete**

**Depends on:** api-adapter/T01; lifecycle/T02.
**Acceptance criteria:** DELETE /chat/{npc_id} requires expected scope/epoch and returns new epoch plus preservation explanation; POST /world/new-game requires expected scope and returns replacement. /world exposes active key/revisions and terminal/invalidated sequence info, excludes old history.
**Test expectations:** Clear/reset stale request conflicts; history scope isolation; old turn inaccessible; client refresh has enough terminal sequence information to advance past invalidated result; response keeps existing world fields.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### api-adapter/T03: Wire shared application service and safe error mapping

- [ ] **Task complete**

**Depends on:** api-adapter/T02; coordinator/T03.
**Acceptance criteria:** Synchronous delivery budget falls back to durable 202 continuation. Map stable ConversationError codes/stage/retryability/turn/safe detail to §8 outcomes; storage uncertainty stays recoverable 503/connection failure, never fabricated 200. Preserve versioned legacy compatibility.
**Test expectations:** Disconnect/poll/retry never reexecutes; provider outage yields validated degraded 200 only after persistence; DB unavailable/internal errors map safely; error details exclude internal exception context and credentials.

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
