# interactions implementation tasks

**Goal:** Deliver the `interactions` responsibility in the NPC conversation redesign.
**Status:** T01–T02 locally verified; 2/2 local tasks complete. Persistence and operation gateway integration remain downstream.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§3.3,6.3.
**Owned files / integration targets:** backend/app/services/conversation/interactions.py; backend/tests/test_conversation_interactions.py.
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

### interactions/T01: Implement pure negotiation transition table

- [x] **Task complete locally** — consent, persistence and execution remain downstream.

**Depends on:** contracts/T03; contracts/T05.
**Acceptance criteria:** InteractionPolicy.plan(current, proposal, context) suspends on topic shift, cancels explicitly, resumes only explicit relevant references, and expires only when relevant preconditions fail. One active item negotiation per NPC.
**Test expectations:** Table-driven transitions include no expiry after arbitrary time/turns, unrelated revision churn, purpose-like words, changed item/quantity/ownership, cancellation and ambiguous suspended references.

- [x] Add focused failing behavioral tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent contract/context/read-port checks; record evidence.
- [x] Review acceptance criteria and update task/master progress.

### interactions/T02: Bind consent and compound-request selection

- [x] **Task complete locally** — store transition application, durable consent consumption and operation execution/recheck remain downstream.

**Depends on:** interactions/T01.
**Acceptance criteria:** Construct ConsentBinding from question ID/turn, answer evidence span, exact operation arguments and checked preconditions. Multiple supported requests ask which first and persist choices; selection authorizes only selected candidate for recheck.
**Test expectations:** Bare yes after topic shift never transfers; explicit resume with missing consent asks again; stale/cancelled/expired/fulfilled confirmations fail; unselected compound actions never queue; duplicate confirmations cannot reuse consent.

- [x] Add focused failing behavioral/contract tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent contract/context/read-port checks; record evidence.
- [x] Review acceptance criteria and update task/master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | interactions_t01 / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reviewed and reran after proposal/T01 | [Handoff/red-green evidence](../evidence/conversation-redesign-interactions/t01-handoff.md); focused 11/11, adjacent 50/50, conversation 213/213 and backend 676/676 pass | Pure policy only; accepted context contract enforces one active item negotiation; consent and durable CAS remain downstream |
| T02 | interactions_t02 / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reviewed and reproduced | [Handoff/red-green evidence](../evidence/conversation-redesign-interactions/t02-handoff.md); focused 18/18, adjacent 57/57, conversation 250/250, backend 713/713; diff check clean | Consent binds exact offered/current-turn operation; gateway must freshly recheck selected command; durable use and execution remain downstream |
