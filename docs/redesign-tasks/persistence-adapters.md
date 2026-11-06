# persistence-adapters implementation tasks

**Goal:** Deliver the `persistence-adapters` responsibility in the NPC conversation redesign.
**Status:** T01–T06 accepted on SQLite/PostgreSQL. Context packet composition from these detached scoped reads is tracked separately as context/T03.
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

- [x] **Task complete**

**Depends on:** ports/T02; baseline/T01.
**Acceptance criteria:** Create streams, turns, operations, pending interactions, canon and summaries from §5.1; extend transcript/memory metadata. Enforce request/sequence/operation uniqueness, canon active heads and one active negotiation. Preserve unknown legacy provenance without promoting it; exclude unmappable legacy scope.
**Test expectations:** Migration on fresh and populated temporary DBs; unique constraints reject duplicates; no existing provenance rewritten; canon/receipts independent of transcript cascades; explicit legacy-ID mapping fixtures.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### persistence-adapters/T02: Implement admission, claims and durable budgets

- [x] **Task complete**

**Depends on:** persistence-adapters/T01; turns/T02.
**Acceptance criteria:** Atomic scoped admission allocates sequence and deduplicates; claim oldest nonterminal with fence/CAS and durable attempt/repair ledger before provider dispatch. Implement pending scan and receipt/status lookup for restart recovery.
**Test expectations:** SQLite/PostgreSQL concurrent duplicate admissions/claims, stale workers, queue restart, phase recovery and uncertain provider dispatch; no call-budget reset on retries.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### persistence-adapters/T03: Implement receipt transaction and common writer discipline

- [x] **Task complete** — accepted by Main Agent 2026-10-18 after SQLite/PostgreSQL review and reproduction.

**Depends on:** persistence-adapters/T02; game-adapters/T01; contracts/T07.
**Acceptance criteria:** Execute_once locks player/world then stream/resources in fixed order, rechecks key/fence/position/consent and recovers existing receipt first. Gameplay consequences, receipt and phase commit together; typed denial has no effect. SQLite uses lock_player, not FOR UPDATE assumptions.
**Test expectations:** Both DB engines: concurrent same turn, cross-NPC shared-item contention, rollback on receipt insertion failure and lost commit acknowledgment; one effect/receipt and no silent substitution.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### persistence-adapters/T04: Implement publication, lifecycle and scoped read stores

- [x] **Task complete** — Main Agent accepted 2026-10-18 after SQLite/PostgreSQL acceptance.

**Depends on:** persistence-adapters/T03; contracts/T07; persistence-adapters/T06.
**Acceptance criteria:** Implement atomic finalization/clear/reset/summary CAS ports; scoped history including /world; remove old conversational payloads while preserving tombstones and receipt/canon origin metadata. Close reads before external calls.
**Test expectations:** Both DB engines: publication rollback, stale evidence/canon/interaction, clear/reset races, late summary, old-epoch lookup and cache fallback; instrument no provider/embedding/semantic call under transaction.

- [x] Add focused lifecycle, contract-memory, scoped-read and summary-store tests.
- [x] Implement the bounded lifecycle, memory publication, scoped-read and summary-store adapters through the existing contracts; preserve shared invariants.
- [x] Run focused SQLite/PostgreSQL checks and the full backend suite; record passing evidence.
- [x] Cover new-game/summary publication race and detached-read connection boundary; provider/semantic refresh boundary is covered by finalization tests.
- [x] Keep unsupported authored/event evidence fail-closed. Full `ContextReadPort` packet composition and producer-ID integration are recorded as context/T03 because they require context-owned sources beyond this persistence task.

### persistence-adapters/T05: Persist monotonic shared-resource revision counters

- [x] **Task complete**

**Recorded expansion (2026-10-18):** game-adapters/T03 requires revision-labelled snapshots, but the accepted schema has no durable all-resource counter store. Existing encounter revisions are local to two activities; NPC memory revision is a cache/CAS token, and quest/inventory/world records have no monotonic counter. This task supplies storage for that already-required T03 behavior.
**Depends on:** persistence-adapters/T01.
**Acceptance criteria:** Add an additive, idempotent `players.resource_revisions` JSON ledger for the active `Player.game_scope`; existing rows receive an empty object without changing other player data. Keep the schema portable across SQLite/PostgreSQL. The field is storage only: it never commits independently or grants authority. Game-adapters/T03 owns stable resource keys, increments under `lock_player`, coherent snapshot projection, and clearing the ledger atomically when `game_scope` changes.
**Test expectations:** Fresh and populated migration, idempotence, preservation of existing player fields, empty legacy ledger default, isolated SQLite and PostgreSQL databases. No player save may be used.

- [x] Add focused failing migration/schema tests for the cases above.
- [x] Implement the bounded additive model/migration and initialization wiring; preserve shared ownership.
- [x] Run SQLite and PostgreSQL checks and relevant adjacent regressions; record evidence.
- [x] Review acceptance criteria, handoff and affected task interface; update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | persistence_t01 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | [Handoff](../evidence/conversation-redesign-persistence-adapters/t01-handoff.md); SQLite schema 4/4; PostgreSQL 16.15 isolated schema 4/4; adjacent semantic-memory/inventory 21/21; `git diff --check` exit 0 | Fresh/populated migration, repeatability, scoped uniqueness, explicit legacy mapping, unknown provenance preservation, and receipt/canon transcript independence verified on both engines; T02–T05 remain separate deliverables |
| T02 | persistence_t02 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | [Handoff](../evidence/conversation-redesign-persistence-adapters/t02-handoff.md); SQLite 23/23, PostgreSQL 16.15 23/23, adjacent 65/65, full backend 876/876; Main Agent independently reproduced focused SQLite/PostgreSQL and full backend; diff check exit 0 | Atomic admission/order, fenced claims, durable budgets/recovery and fail-closed scoped receipt lookup; T03–T04 remain separate |
| T03 | persistence_t03 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | [Handoff](../evidence/conversation-redesign-persistence-adapters/t03-handoff.md); SQLite 47/47, PostgreSQL 16.15 47/47, full backend 935/935; `git diff --check` clean | Atomic operation/effect/interaction/receipt transaction, persisted consent reload and common writer discipline; lifecycle/publication remains T04 |
| T04 | Main Agent / accepted 2026-10-18 | [Lifecycle/publication tests](../evidence/conversation-redesign-persistence-adapters/t04-lifecycle-tests.md); SQLite and PostgreSQL 16.15 focused suites 24/24 each, full backend 961/961; `git diff --check` clean | Atomic lifecycle/publication and summary stores, scoped finalized reads, fail-closed unsupported evidence, both lifecycle races, and external-call transaction boundaries verified; context packet composition is separately recorded as context/T03 |
| T05 | persistence_t05 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | [Handoff](../evidence/conversation-redesign-persistence-adapters/t05-handoff.md); SQLite 5/5 and adjacent 77/77, PostgreSQL 16.15 9/9 with T01 schema, full backend 876/876; Main Agent independently reproduced focused SQLite/PostgreSQL and full backend; diff check exit 0 | Additive Player ledger preserves legacy state and caller rollback; game-adapters/T03 owns revision writes, snapshots and scope reset |
| T06 | Main Agent / accepted 2026-10-18 | [Handoff](../evidence/conversation-redesign-persistence-adapters/t06-handoff.md); schema/migration suite SQLite 6/6 and PostgreSQL 16.15 6/6; `git diff --check` clean | Additive storage primitives for contract-memory revisions and durable summary CAS state; T04 owns adapter transaction semantics |
| T07 | Main Agent / accepted 2026-10-18 | [Handoff](../evidence/conversation-redesign-persistence-adapters/t07-handoff.md); SQL finalization 22/22 SQLite and PostgreSQL 16.15; adjacent 36/36; full backend 975/975; diff check clean | Refreshed reply and plan are persisted after exact revalidation; terminal interactions cannot be reactivated; retryable evidence conflicts refresh outside transaction |

### persistence-adapters/T06: Add durable contract memory and summary CAS state

- [x] **Task complete** — Main Agent accepted 2026-10-18 after SQLite/PostgreSQL migration acceptance.

**Recorded expansion (2026-10-18):** While implementing persistence-adapters/T04, review found the legacy `Memory` table cannot persist `conversation.MemoryRecord.memory_id` or its exact revision/correction CAS state. `ConversationSummary` likewise has no revision counter or durable dirty marker required to recover summary work after missed notifications. These are storage prerequisites for already-defined FinalizationStore and SummaryStore ports; this task records only their durable schema and migration seam.
**Depends on:** persistence-adapters/T01; contracts/T03; memory/T02.
**Scope clarification (2026-10-18):** T06 delivers the portable schema and migration seam only. The recorded `FinalizationStore` and `SummaryStore` transaction behavior, including revision CAS, dirty-key scans, restart recovery, and matching-summary clear, remains part of persistence-adapters/T04.
**Acceptance criteria:** Add portable, additive, idempotent storage for immutable scoped contract-memory revisions/source attribution and summary revision/dirty state. Preserve legacy Memory rows and keep this store separate from mechanics authority. Provide database constraints and columns needed by T04 to implement same-transaction memory revision CAS and durable dirty-key scan after finalized source changes.
**Test expectations:** Fresh/populated SQLite/PostgreSQL migration, idempotence and legacy preservation; duplicate active memory revision rejection and subsequent revision acceptance; stream summary revision/dirty columns persist across connections.

- [x] Add focused failing schema tests.
- [x] Implement additive portable schema and initialization/migration wiring.
- [x] Run isolated SQLite and PostgreSQL checks and adjacent memory/persistence regressions.
- [x] Review and record handoff.

### persistence-adapters/T07: Close SQL finalization revalidation gaps

- [x] **Task complete** — Main Agent accepted 2026-10-18 after finalization/T02 SQL integration REDs and SQLite/PostgreSQL GREEN acceptance.

**Depends on:** persistence-adapters/T04; contracts/T03; finalization/T01.
**Acceptance criteria:** Relevant `EVIDENCE_CHANGED` results are retryable so the finalization facade can refresh outside the transaction. The durable publication boundary supports a bounded, validated replacement reply/continuity plan after refresh, without accepting mismatched turn/fence or skipping evidence/revision checks. Before applying interaction transitions, load the current scoped interactions and enforce `InteractionPlan.validate_current`, including active current-question/consent state; fulfilled status from an operation commit cannot be reactivated by a stale finalization plan.
**Test expectations:** SQLite and PostgreSQL: refreshed exact speech can publish once; stale fence or mismatched reply is rejected; operation-fulfilled interaction stays fulfilled under a racing/stale finalization; rollback and replay behavior remains intact.

- [x] Add focused failing publication tests on both database engines through the real Finalizer/SQLTurnStore boundary.
- [x] Implement retryable relevant evidence conflicts, refreshed reply persistence, and terminal-interaction guards.
- [x] Run SQLite/PostgreSQL acceptance, adjacent lifecycle/finalization checks and full backend suite.
- [x] Record handoff, evidence and limitations.
