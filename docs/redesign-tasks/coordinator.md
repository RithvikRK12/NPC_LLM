# coordinator implementation tasks

**Goal:** Deliver the `coordinator` responsibility in the NPC conversation redesign.
**Status:** T01–T03 locally accepted; broader quality and rollout gates remain open.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§1,4–5,8–10.
**Owned files / integration targets:** backend/app/services/conversation/{coordinator,application}.py; backend/app/main.py; backend/app/config/settings.py; backend/app/services/pipeline.py; backend/tests/test_conversation_{coordinator,application}.py.
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

- [x] **Task complete** — T01 locally accepted; module remains incomplete pending T02–T03 and adjacent integration gates.

**Depends on:** turns/T02; context/T02; capabilities/T01; proposal/T02; validation/T03; fallback/T02; finalization/T01; diagnostics/T01.
**Acceptance criteria:** Coordinator drives detached context→proposal→interaction/operation decision→assembly→validation→continuity→finalization using injected dependencies. One ordinary proposal; at most one repair shared by format and speech; no mandatory summary call.
**Test expectations:** Scripted ports/fake clock pin call graph, budgets, malformed proposal and repair failure; final fallback enters next turn history; coordinator does not import concrete provider/DB or implement inventory/canon rules.

- [x] Add focused behavioral/contract tests. (No pre-implementation RED result captured; documented in handoff.)
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent dependency checks; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### coordinator/T02: Integrate action composition and durable recovery

- [x] **Task complete** — accepted by Main Agent 2026-10-18 after independent review and correction follow-ups.

**Depends on:** coordinator/T01; operations/T02; composition/T02; persistence-adapters/T04; game-adapters/T03.
**Acceptance criteria:** Resolve operation once then compose from committed receipt; persist phase/budget before calls, resume output/receipt on restart and use fallback if dispatch outcome lost. No provider/embedding/semantic calls under locks; same-ID recovery never executes twice.
**Test expectations:** Crash-point matrix §5.4, timeout after effect, old worker return, cross-NPC generation, budget exhaustion and DB busy/commit uncertainty; final text retry immutable and action remains committed.

- [x] Add focused failing behavioral/contract tests for the cases above.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent dependency conformance cases; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### coordinator/T03: Wire durable worker and versioned pipeline switch

**Assignment:** Main Agent / accepted locally (2026-10-18; model identifier unavailable in current runtime). Scope: coordinator worker/application service and its versioned pipeline handoff; route binding was coordinated with api-adapter/T03. Production ports, validated settings, startup recovery, rollback behavior and receipt test are recorded in the handoff.

**Recorded T03 integration detail (2026-10-18):** `QUEUE_SATURATED` must be enforced atomically during admission; a service-side `pending()` count races concurrent submissions. T03 therefore includes a bounded, coordinated `SQLTurnStore` admission-capacity option, configured by the application policy. No schema change or gameplay behavior is added.

- [x] **Task complete locally** — accepted 2026-10-18 after production runtime assembly and SQLite startup recovery with a committed receipt.

**Depends on:** coordinator/T02; lifecycle/T02.
**Acceptance criteria:** Same application service supports synchronous wait and queued continuation; durable pending scan survives restart. Queue/lease/deadline policies are validated; HTTP timeout cannot discard admitted work or reset budgets. Legacy rollback never bypasses receipt boundary for unresolved redesigned turns.
**Test expectations:** Disconnect after admission, restart with pending turn, saturation/fake-clock policy limits and feature-switch rollback with existing receipt; no dependence on process-local notification for recovery.

- [x] Add focused failing behavioral/contract tests for the cases above.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | Main Agent / locally accepted (2026-10-18) | Focused 7/7; conversation 554/554; import boundary and diff check exit 0 | [Handoff](../evidence/conversation-redesign-coordinator/t01-handoff.md). Durable attempt/recovery and concrete adapters remain T02/integration gates. |
| T02 | Main Agent / accepted (2026-10-18; model identifier unavailable in current runtime) | Focused coordinator 18/18; composition 38/38; operations 24/24; turns 29/29; persistence 67/67; conversation 565/565; `git diff --check` exit 0 | [Handoff](../evidence/conversation-redesign-coordinator/t02-handoff.md), [conversation test log](../evidence/conversation-redesign-coordinator/t02-tests.log). SQLite/PostgreSQL adapter gates are linked from persistence-adapters/T02–T04; production pipeline/worker wiring remains T03. |
| T03 | Main Agent / locally accepted (2026-10-18; runtime model identifier unavailable) | Focused application/API/worker/coordinator 44 passed; conversation suite 580 passed; full backend 1,048 passed; `git diff --check` clean. | [Handoff](../evidence/conversation-redesign-coordinator/t03-handoff.md). Production runtime resumes and finalizes a real committed receipt without another effect when rollback is off. API still returns safe 503 when its required legacy projection is absent; tracked under api-adapter/T03. |
