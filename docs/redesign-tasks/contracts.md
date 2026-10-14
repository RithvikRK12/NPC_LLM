# contracts implementation tasks

**Goal:** Deliver the `contracts` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§1,3,8,10.
**Owned files / integration targets:** backend/app/services/conversation/contracts.py; backend/tests/test_conversation_contracts.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [baseline](baseline.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### contracts/T01: Define identity, evidence and policy values

- [ ] **Task complete**

**Depends on:** baseline/T01.
**Acceptance criteria:** Implement immutable ConversationKey, TurnSubmission, TurnRef, RevisionSet, SourceRef, TextSpan, six tagged Evidence classes, ConversationPolicy, Deadline and ConversationError. UTC timestamps; Unicode code-point spans; one versioned bounds policy; server-resolved player.
**Test expectations:** Round-trip fixtures; reject unknown versions/fields, invalid bounds and spans; fake clock validates finite positive policies; generated canon/reports cannot inhabit mechanical tags.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### contracts/T02: Define proposal, negotiation and operation values

- [ ] **Task complete**

**Depends on:** contracts/T01.
**Acceptance criteria:** Implement ContextPacket, CapabilityDescriptor, TurnProposal, ReplySegment union, CandidateReply, AssembledReply, PendingInteraction, ConsentBinding, OperationDecision and OperationReceipt exactly as design §3. One operation per turn; accepted differs from completed.
**Test expectations:** Strict union decoding; reject arbitrary renderer expressions, model-supplied slot quantities and malformed command arguments; exercise all modalities/statuses and exact span references.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### contracts/T03: Define continuity, result and cross-language fixtures

- [ ] **Task complete**

**Depends on:** contracts/T02.
**Acceptance criteria:** Implement CanonRecord/CanonChange, MemoryRecord, ValidationFinding/Report, FinalTurnResult and interface result/status values from §4. Beats preserve complete text; origin includes mock; scope/epoch are distinct from legacy IDs.
**Test expectations:** Shared valid/rejected JSON fixtures verify full-text beat reconstruction, revisions, correction lineage and legacy mapping; confirm values are detached and immutable.

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
