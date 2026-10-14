# finalization implementation tasks

**Goal:** Deliver the `finalization` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
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

- [ ] **Task complete**

**Depends on:** contracts/T03; ports/T02; canon/T02; memory/T01; interactions/T02.
**Acceptance criteria:** Finalizer.commit(turn, fence, reply, continuity_plan) checks active key/fence/stream position, exact evidence dependencies, canon heads and interaction revisions. Refresh/reassemble outside transaction on relevant change; unrelated churn is not blanket rejection.
**Test expectations:** Fake store rejects stale fence/epoch/canon/evidence; current activity may invalidate progress speech while historical receipt remains valid; no provider invocation under lock.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### finalization/T02: Publish final result and continuity atomically

- [ ] **Task complete**

**Depends on:** finalization/T01; persistence-adapters/T04.
**Acceptance criteria:** Single publication transaction writes exact final text, lossless beats, accepted canon/memory, interaction transitions and terminal result. Read committed fulfilled negotiation status so stale plans cannot reactivate it; replay exact stored dialogue.
**Test expectations:** Inject failure between transcript and canon writes: all rollback; final retry byte-for-byte identical; fulfilled interaction preserved; persistent evidence churn returns recoverable conflict without false finalization.

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
