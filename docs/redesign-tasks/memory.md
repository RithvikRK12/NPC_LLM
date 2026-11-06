# memory implementation tasks

**Goal:** Deliver the `memory` responsibility in the NPC conversation redesign.
**Status:** T01–T03 locally accepted; 3/3 task deliverables verified. Concrete dirty-marker, lineage and summary-store durability remain adapter integration gates.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§3.4,4,6.6; Proposal §15.
**Owned files / integration targets:** backend/app/services/conversation/memory.py; backend/app/services/memory/* (compatible adapters); backend/tests/test_conversation_memory.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [canon](canon.md), [contracts](contracts.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### memory/T01: Plan attributed reports, interpretations and retrieval

- [x] **Task complete locally** — storage, correction CAS and summary refresh remain T02/adapters.

**Depends on:** contracts/T03; ports/T01.
**Acceptance criteria:** MemoryPolicy.plan(turn, reply, proposal) retains source references, uncertainty and retraction/supersession; emotions are temporary observations. Verified events remain authoritative elsewhere; reject unseen drafts and unverified mechanics.
**Test expectations:** Player says delivered never becomes delivery event; retracted preference excluded; current inventory overrides recollection; cross-scope/epoch/NPC retrieval excluded even with index matches.

- [x] Add focused failing behavioral tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused and adjacent contract/port checks; record evidence.
- [x] Review acceptance criteria and update task/master progress.

### memory/T02: Refresh summaries outside turn path

- [x] **Task complete locally** — concrete durable source/lineage reads and CAS remain persistence-adapter gates.

**Depends on:** memory/T01; canon/T02; ports/T02.
**Acceptance criteria:** SummaryService.refresh(key, source_range, revisions, deadline) uses durable dirty/source revision markers, checks epoch/source/correction revisions before publish and preserves attribution. Index is disposable; valid prior summary or scoped unsummarized retrieval survives outage.
**Test expectations:** Missed notification recovered via scan; late summary after clear/reset or canon revision rejected; retracted reports never revived; embedding/summary failure does not fail mandatory turn or promote report authority.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | memory_t01 / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reviewed and reproduced | [Handoff/red-green evidence](../evidence/conversation-redesign-memory/t01-handoff.md); focused 5/5, adjacent memory/contracts/port 35/35 pass; broader backend later reproduced at 843/843 during T02 review | Reports remain unverified; scoped filtering only; durable correction CAS/index/summary are adapter duties |
| T02 | memory_t02 / locally accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | 22 focused, 32 store-port, 15 canon, 70 contracts, 380 conversation and 843 backend tests pass; independent review approved after correction-link snapshot fix; evidence `../evidence/conversation-redesign-memory/t02-handoff.md` | Concrete trusted lineage reader, durable dirty scans/source filtering/CAS and PostgreSQL behavior remain unverified |
| T03 | Main Agent / locally accepted 2026-10-18 | [Handoff](../evidence/conversation-redesign-memory/t03-handoff.md); memory provenance 14/14, behavior pipeline 13/13, game adapters 48/48; full backend 937 passed with one open T04 publication error | Both callers embed after commit and common writer release; optional failures preserve attributed rows |

### memory/T03: Keep conversation embeddings outside writer transactions

- [x] **Task complete locally** — legacy pipeline and timed bow callers persist attributed rows with their authoritative transaction and embed after commit.

**Recorded expansion (2026-10-18):** Review during game-adapters/T03 found that `quests/bow.py:finish_if_ready` calls `MemoryService.store_conversation`, which can invoke `EmbeddingService.embed`, while the quest route owns the common Player writer lock and transaction. Inspection then found the same `store_conversation` call from the legacy conversation pipeline while its transaction is still open. This violates the shared no-embedding-under-lock invariant. The follow-up covers these two existing conversation-memory callers and their common persistence/embedding boundary; it must preserve event attribution, atomicity expectations, and retry behavior. It does not change gameplay or extend memory policy.
**Depends on:** game-adapters/T03.
**Acceptance criteria:** Legacy conversation memory writes, including timed bow completion, must not call an embedding/provider while a database transaction or common game writer lock is held. Persist the attributed memory row with the authoritative conversation transaction, then calculate and store its optional embedding after commit with scope/source/idempotency rechecks. Embedding failure must not roll back or duplicate the authoritative event. Any additional persistence/outbox seam needed to meet these criteria must be recorded as a separate task before implementation.
**Test expectations:** Verify an embedding spy observes no active database transaction/writer lock for pipeline and bow paths; verify attributed rows commit exactly once across retries and embedding failure; run existing pipeline, bow quest and memory regressions.

- [x] Add focused regression tests for embedding outside the writer boundary in both callers.
- [x] Implement the bounded memory/embedding separation without changing game rules.
- [x] Run focused memory, pipeline, game-adapter and adjacent backend checks.
- [x] Review and record the handoff.
