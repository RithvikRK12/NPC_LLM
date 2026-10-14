# persistence-adapters implementation tasks

**Goal:** Deliver the `persistence-adapters` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§5,6.4,6.6–6.7,9–10.
**Owned files / integration targets:** backend/app/models/conversation*.py; backend/app/models/character_canon.py (new); backend/app/models/{conversation,memory}.py; backend/app/database/conversation_migration.py (new); backend/app/services/conversation/adapters/persistence.py (new); backend/tests/test_conversation_persistence.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [baseline](baseline.md), [game-adapters](game-adapters.md), [ports](ports.md), [turns](turns.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### persistence-adapters/T01: Add scoped schema and additive migration

- [ ] **Task complete**

**Depends on:** ports/T02; baseline/T01.
**Acceptance criteria:** Create streams, turns, operations, pending interactions, canon and summaries from §5.1; extend transcript/memory metadata. Enforce request/sequence/operation uniqueness, canon active heads and one active negotiation. Preserve unknown legacy provenance without promoting it; exclude unmappable legacy scope.
**Test expectations:** Migration on fresh and populated temporary DBs; unique constraints reject duplicates; no existing provenance rewritten; canon/receipts independent of transcript cascades; explicit legacy-ID mapping fixtures.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### persistence-adapters/T02: Implement admission, claims and durable budgets

- [ ] **Task complete**

**Depends on:** persistence-adapters/T01; turns/T02.
**Acceptance criteria:** Atomic scoped admission allocates sequence and deduplicates; claim oldest nonterminal with fence/CAS and durable attempt/repair ledger before provider dispatch. Implement pending scan and receipt/status lookup for restart recovery.
**Test expectations:** SQLite/PostgreSQL concurrent duplicate admissions/claims, stale workers, queue restart, phase recovery and uncertain provider dispatch; no call-budget reset on retries.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### persistence-adapters/T03: Implement receipt transaction and common writer discipline

- [ ] **Task complete**

**Depends on:** persistence-adapters/T02; game-adapters/T01.
**Acceptance criteria:** Execute_once locks player/world then stream/resources in fixed order, rechecks key/fence/position/consent and recovers existing receipt first. Gameplay consequences, receipt and phase commit together; typed denial has no effect. SQLite uses lock_player, not FOR UPDATE assumptions.
**Test expectations:** Both DB engines: concurrent same turn, cross-NPC shared-item contention, rollback on receipt insertion failure and lost commit acknowledgment; one effect/receipt and no silent substitution.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### persistence-adapters/T04: Implement publication, lifecycle and scoped read stores

- [ ] **Task complete**

**Depends on:** persistence-adapters/T03.
**Acceptance criteria:** Implement atomic finalization/clear/reset/summary CAS ports; scoped history including /world; remove old conversational payloads while preserving tombstones and receipt/canon origin metadata. Close reads before external calls.
**Test expectations:** Both DB engines: publication rollback, stale evidence/canon/interaction, clear/reset races, late summary, old-epoch lookup and cache fallback; instrument no provider/embedding/semantic call under transaction.

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
| T04 | Unassigned / not started | Not run | None recorded |
