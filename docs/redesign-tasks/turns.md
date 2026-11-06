# turns implementation tasks

**Goal:** Deliver the `turns` responsibility in the NPC conversation redesign.
**Status:** T01–T02 locally verified; 2/2 local tasks complete. Concrete persistence/coordinator integration remains pending.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§4,5.2,5.4.
**Owned files / integration targets:** backend/app/services/conversation/turns.py; backend/tests/test_conversation_turns.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### turns/T01: Implement submission and retry lookup

- [x] **Task complete locally** — database atomicity/concurrency remains a persistence-adapter gate.

**Depends on:** ports/T02.
**Acceptance criteria:** TurnService.submit(submission) validates key, deduplicates payload and enqueues durable sequence through its port; lookup(key, request_id) returns pending/final/invalidated without generation.
**Test expectations:** Fake-store same payload returns same turn; different payload conflicts; stale scope/epoch rejected; concurrent admission contract allocates unique sequences.

- [x] Add focused failing behavioral/contract tests; expected missing-service failures recorded in the handoff.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent store/conversation conformance; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### turns/T02: Implement ordered claims and phase recovery

- [x] **Task complete locally** — atomicity, crash durability and coordinator use remain integration gates.

**Depends on:** turns/T01.
**Acceptance criteria:** claim_next(key, worker_id, lease_policy) claims earliest nonterminal only; persist attempt/repair consumption before dispatch and resume stored phase/output/receipt. Storage failures remain pending; no process-local mutex correctness assumption.
**Test expectations:** Fake clock tests lease replacement/fence, no later-turn bypass, restart before/after dispatch, preserved call budgets and receipt-first recovery; different NPC streams claim independently.

- [x] Add focused failing behavioral/contract tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record evidence.
- [x] Review acceptance criteria and update task/master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | turns_t01 / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reproduced focused 11/11, store-port 32/32, conversation 163/163 | [Handoff](../evidence/conversation-redesign-turns/t01-handoff.md); all reproduced checks exit 0, no failures/skips | Fake store does not prove DB atomicity/concurrency; persistence-adapters/T02 remains required |
| T02 | turns_t02 / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reviewed | [Handoff/red-green evidence](../evidence/conversation-redesign-turns/t02-handoff.md); focused 29/29, store-port 32/32, conversation 202/202, full backend 665/665 pass | Store-owned atomic claims/fencing/recovery; fake process restart does not establish SQL atomicity/crash durability; coordinator integration remains required |
