# coordinator implementation tasks

**Goal:** Deliver the `coordinator` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§1,4–5,8–10.
**Owned files / integration targets:** backend/app/services/conversation/coordinator.py; backend/app/services/pipeline.py; backend/tests/test_conversation_coordinator.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [capabilities](capabilities.md), [composition](composition.md), [context](context.md), [diagnostics](diagnostics.md), [fallback](fallback.md), [finalization](finalization.md), [game-adapters](game-adapters.md), [lifecycle](lifecycle.md), [operations](operations.md), [persistence-adapters](persistence-adapters.md), [proposal](proposal.md), [turns](turns.md), [validation](validation.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### coordinator/T01: Sequence pure conversation with injected ports

- [ ] **Task complete**

**Depends on:** turns/T02; context/T02; capabilities/T01; proposal/T02; validation/T03; fallback/T02; finalization/T01; diagnostics/T01.
**Acceptance criteria:** Coordinator drives detached context→proposal→interaction/operation decision→assembly→validation→continuity→finalization using injected dependencies. One ordinary proposal; at most one repair shared by format and speech; no mandatory summary call.
**Test expectations:** Scripted ports/fake clock pin call graph, budgets, malformed proposal and repair failure; final fallback enters next turn history; coordinator does not import concrete provider/DB or implement inventory/canon rules.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### coordinator/T02: Integrate action composition and durable recovery

- [ ] **Task complete**

**Depends on:** coordinator/T01; operations/T02; composition/T02; persistence-adapters/T04; game-adapters/T03.
**Acceptance criteria:** Resolve operation once then compose from committed receipt; persist phase/budget before calls, resume output/receipt on restart and use fallback if dispatch outcome lost. No provider/embedding/semantic calls under locks; same-ID recovery never executes twice.
**Test expectations:** Crash-point matrix §5.4, timeout after effect, old worker return, cross-NPC generation, budget exhaustion and DB busy/commit uncertainty; final text retry immutable and action remains committed.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### coordinator/T03: Wire durable worker and versioned pipeline switch

- [ ] **Task complete**

**Depends on:** coordinator/T02; lifecycle/T02.
**Acceptance criteria:** Same application service supports synchronous wait and queued continuation; durable pending scan survives restart. Queue/lease/deadline policies are validated; HTTP timeout cannot discard admitted work or reset budgets. Legacy rollback never bypasses receipt boundary for unresolved redesigned turns.
**Test expectations:** Disconnect after admission, restart with pending turn, saturation/fake-clock policy limits and feature-switch rollback with existing receipt; no dependence on process-local notification for recovery.

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
