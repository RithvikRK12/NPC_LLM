# ports implementation tasks

**Goal:** Deliver the `ports` responsibility in the NPC conversation redesign.
**Status:** T01–T02 verified; 2/2 local tasks complete; module acceptance awaits concrete adapter integration gates.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§2,4–5.
**Owned files / integration targets:** backend/app/services/conversation/ports.py; backend/tests/conversation_port_conformance.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [contracts](contracts.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### ports/T01: Declare narrow read, generation and policy-facing protocols

- [x] **Task complete**

**Depends on:** contracts/T03.
**Acceptance criteria:** Define world/context/memory/capability reads, generation purpose/deadline/budget, clock and trace protocols using only contracts. Carry scope and visibility explicitly; expose no shared ORM session.
**Test expectations:** Fake implementations conform; dependency inspection finds no FastAPI, SQLAlchemy or concrete provider imports; fixtures exclude private authorization evidence from public views.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### ports/T02: Declare atomic write and recovery protocols

- [x] **Task complete**

**Depends on:** ports/T01.
**Acceptance criteria:** Define turn store, operation gateway, finalization store, lifecycle store and summary store contracts including fencing, CAS revisions, uniqueness, receipt recovery, durable attempts and invalidated lookup. Provide reusable fake repositories and conformance cases.
**Test expectations:** Conformance cases pin same-ID replay/conflict, oldest-turn claims, stale fences, atomic rollback and scoped recovery; protocol signatures match Detailed design §4.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | ports_t01 / accepted 2026-10-14; gpt-6-luna / medium; independent review_ports_t01 approved | [Handoff/red-green evidence](../evidence/conversation-redesign-ports/t01-handoff.md); 4/4 focused, 47/47 conversation and 12/12 read-port tests pass; diff check clean | Seven pure read/generation/clock/trace protocols; concrete adapters remain outside scope |
| T02 | ports_t02 / accepted 2026-10-14; gpt-6.1-sol / high; independent review_ports_t02 approved | [Handoff/red-green evidence](../evidence/conversation-redesign-ports/t02-handoff.md); 32/32 focused, 91/91 conversation, 13/13 dependency and 554/554 backend tests pass | Five atomic write/recovery protocols and reusable fake conformance cases; SQL/database atomicity remains unproven |
