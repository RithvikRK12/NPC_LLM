# diagnostics implementation tasks

**Goal:** Deliver the `diagnostics` responsibility in the NPC conversation redesign.
**Status:** T01–T02 locally verified; 2/2 local tasks complete. Coordinator event production and retention enforcement remain integration work.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §6.8; Proposal §20.
**Owned files / integration targets:** backend/app/services/conversation/diagnostics.py; backend/app/services/decision_trace.py; backend/tests/test_conversation_diagnostics.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [contracts](contracts.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### diagnostics/T01: Extend structured trace projection

- [x] **Task complete locally** — best-effort isolation and evaluation export remain T02.

**Depends on:** contracts/T03; ports/T01.
**Acceptance criteria:** TraceSink.emit records turn/key/sequence/fence/attempt, stage timing, policy/prompt/schema versions, exact provider settings, source IDs, concise decisions/spans, authorization/receipt, findings, repair consumption and final origin. No hidden reasoning or credentials.
**Test expectations:** Capturing sink asserts fields for generated/repaired/fallback/mock/recovery routes; secret redaction and debug-draft separation; injected monotonic timings reproducible.

- [x] Add focused failing behavioral tests; missing-module and cross-turn receipt failures observed before implementation.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused and adjacent trace-port/read-port checks; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### diagnostics/T02: Isolate diagnostic failures and support scoring export

- [x] **Task complete locally** — coordinator wiring and storage policy enforcement remain downstream.

**Depends on:** diagnostics/T01.
**Acceptance criteria:** Trace sink exceptions are best effort and cannot change gameplay, finalization or receipt recovery. Export reproducible counts, token usage when available, origin, repetition and route latency for evaluation with retention/access policy metadata.
**Test expectations:** Sink outage during successful operation/finalization leaves result intact; exports separate healthy fallback/outages and ordinary/action/repair p50/p95 with sample counts; no unsupported healthy-generation claim.

- [x] Add focused failing behavioral tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent trace-port/read-port checks; record evidence.
- [x] Review acceptance criteria and update task/master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | main_agent / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reproduced full backend suite | [Handoff](../evidence/conversation-redesign-diagnostics/t01-handoff.md); focused 5/5, trace/read-port 21/21, legacy trace 8/8; full backend 655/655 pass; `git diff --check` clean | Safe projection only; coordinator event production and T02 sink isolation/export remain open |
| T02 | diagnostics_t02 / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reviewed and reproduced | [Handoff/red-green evidence](../evidence/conversation-redesign-diagnostics/t02-handoff.md); focused 9/9, adjacent 25/25, conversation 235/235 pass; `git diff --check` clean | Best-effort sink/export boundary only; coordinator wiring and retention/access enforcement remain open; no healthy-generation rate claimed |
