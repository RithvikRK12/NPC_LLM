# finalization implementation tasks

**Goal:** Deliver the `finalization` responsibility in the NPC conversation redesign.
**Status:** finalization/T01–T02 locally accepted; downstream coordinator integration remains open.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§4,5.3–5.4,6.7.
**Owned files / integration targets:** backend/app/services/conversation/finalization.py; backend/tests/test_conversation_finalization.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [canon](canon.md), [contracts](contracts.md), [interactions](interactions.md), [memory](memory.md), [persistence-adapters](persistence-adapters.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### finalization/T01: Build prevalidated publication plan and rechecks

- [x] **Task complete**

**Depends on:** contracts/T03; ports/T02; canon/T02; memory/T01; interactions/T02.
**Acceptance criteria:** Finalizer.commit(turn, fence, reply, continuity_plan) checks active key/fence/stream position, exact evidence dependencies, canon heads and interaction revisions. Refresh/reassemble outside transaction on relevant change; unrelated churn is not blanket rejection.
**Test expectations:** Fake store rejects stale fence/epoch/canon/evidence; current activity may invalidate progress speech while historical receipt remains valid; no provider invocation under lock.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### finalization/T02: Publish final result and continuity atomically

- [x] **Task complete** — Main Agent accepted 2026-10-18 after persistence-adapters/T07 closed the SQL integration defects.

**Depends on:** finalization/T01; persistence-adapters/T04.
**Acceptance criteria:** Single publication transaction writes exact final text, lossless beats, accepted canon/memory, interaction transitions and terminal result. Read committed fulfilled negotiation status so stale plans cannot reactivate it; replay exact stored dialogue.
**Test expectations:** Inject failure between transcript and canon writes: all rollback; final retry byte-for-byte identical; fulfilled interaction preserved; persistent evidence churn returns recoverable conflict without false finalization.

- [x] Add focused failing SQL integration tests; REDs reproduced on SQLite and PostgreSQL.
- [x] Verify the SQL publication boundary with persistence-adapters/T07; no facade change was needed.
- [x] Run SQLite/PostgreSQL acceptance and the full backend suite.
- [x] Review acceptance criteria and record handoff/output changes.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | finalization_t01 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | [Handoff](../evidence/conversation-redesign-finalization/t01-handoff.md); focused 16/16, contracts 70/70, canon 15/15, interactions 18/18, store ports 32/32, memory 5/5; `git diff --check` exit 0 | Facade verified with doubles only; durable SQL publication remains T02 after persistence-adapters/T04 |
| T02 | finalization_t02 / Main Agent accepted 2026-10-18; gpt-6.1-sol / high | [Handoff](../evidence/conversation-redesign-finalization/t02-handoff.md); after T07, SQL suite 22/22 SQLite and PostgreSQL 16.15; adjacent 36/36; full backend 975/975 | Atomic publication, rollback, exact replay, bounded refresh and operation-fulfilled interaction preservation verified |
