# validation implementation tasks

**Goal:** Deliver the `validation` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§3.4,4,6.5; Proposal §12.
**Owned files / integration targets:** backend/app/services/conversation/validation.py; backend/app/services/validation/{models,service}.py; backend/tests/test_conversation_validation.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [composition](composition.md), [contracts](contracts.md), [proposal](proposal.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### validation/T01: Implement independent structural and grounding checkers

- [ ] **Task complete**

**Depends on:** contracts/T03; composition/T01.
**Acceptance criteria:** ResponseValidator.check(reply, context, current_evidence) returns structured findings for complete assembled reply, references, evidence revisions, mechanical implications, attribution and canon conflicts; checkers receive narrow projections.
**Test expectations:** Correct slot surrounded by contradictory prose is blocked; unknown IDs and unsupported shops/caches/recipes/routes fail; report is not witnessed event; harmless soft-spot and fear idioms pass.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### validation/T02: Add concern, repetition and style evaluation hooks

- [ ] **Task complete**

**Depends on:** validation/T01.
**Acceptance criteria:** Separate blocking/advisory findings, concern coverage, speaker identity, repetition and pacing. Semantic checking starts offline; optional runtime port is disabled unless measurement justifies activation and never authorizes gameplay.
**Test expectations:** Mixed concern omitted from reply is detectable in calibrated fixtures despite addressed IDs; purposeful repeated facts differ from accidental repetition; no mandatory semantic call on greeting.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### validation/T03: Implement bounded speech-only repair service

- [ ] **Task complete**

**Depends on:** validation/T01; proposal/T02.
**Acceptance criteria:** RepairService.repair(candidate, findings, evidence, deadline) accepts coordinator-granted token, corrects speech/canon candidates only, rebuilds spans and revalidates whole reply. Proposal-format repair consumes the same single turn token.
**Test expectations:** Scripted repair preserves receipt and cannot add/replace/run operations; failed repair admits no canon; Unicode offsets rebuilt; coordinator contract forbids second repair after format recovery.

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
