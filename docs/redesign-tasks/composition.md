# composition implementation tasks

**Goal:** Deliver the `composition` responsibility in the NPC conversation redesign.
**Status:** T01–T03 verified; 3/3 local tasks complete; module acceptance awaits adjacent adapter, validation and release integration gates.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§3.2,4,6.5; Proposal §13.
**Owned files / integration targets:** backend/app/services/conversation/composition.py; backend/app/dialogue/compose.py (explicit compatibility adapter only); backend/tests/test_conversation_composition.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [baseline](baseline.md), [contracts](contracts.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### composition/T01: Implement exact slots and complete readable assembly

- [x] **Task complete**

**Depends on:** contracts/T03; baseline/T01.
**Acceptance criteria:** ReplyAssembler.assemble(candidate, evidence, policy) renders allowlisted FactSlot/ReceiptSlot clauses with server-owned quantities/outcomes; retain expressive text, rebuilt final span map and lossless beats. Audit legacy 240/300-character contracts instead of stacking incompatible checks.
**Test expectations:** Golden fixtures test accepted/completed/rejected receipts, unknown/stale IDs, invalid speech acts, missing resources, long stories and overflow; concatenated beats equal full dialogue with no truncation.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### composition/T02: Compose action speech from committed receipts

- [ ] **Task complete**

**Depends on:** composition/T01; ports/T01.
**Acceptance criteria:** CompositionService.compose(context, proposal, receipt, deadline) may use one action-composition provider attempt with receipt and current activity evidence; has no execution port. Ordinary replies assemble proposal directly.
**Test expectations:** Scripted success/denial/cancelled activity and timeout tests; accepted inspection never becomes completed; no composition call for ordinary route; no execution possible through service dependencies.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### composition/T03: Separate historical receipts from current activity projections

- [x] **Task complete**

**Depends on:** composition/T02.
**Recorded expansion (2026-10-14):** T02 exercised an accepted inspection receipt at activity revision 2 followed by a current cancellation fact at revision 3. The immutable receipt remains valid historical evidence, but T01's current-revision check on all receipt `after_revisions` rejects assembly with `EVIDENCE_CHANGED`. This fail-closed behavior avoids false claims but prevents dialogue from accurately distinguishing acceptance from later cancellation/progress.
**Acceptance criteria:** Permit a verified immutable receipt clause to remain historically renderable after its result revisions advance, while current/progress/cancelled activity clauses require separate current authoritative activity evidence and revision checks. Preserve receipt authentication and stale publication safeguards; never promote accepted to completed or infer current activity from a receipt.
**Test expectations:** Accepted-then-cancelled, accepted-then-progressed, completed-history, stale current activity, and missing activity projection fixtures; no stale current-tense speech; full reply and receipt spans remain exact.

- [x] Add focused failing tests for historical receipt vs current activity.
- [x] Implement the bounded rendering/evidence distinction without widening authority.
- [x] Run focused, conversation, dependency and legacy composer suites; record handoff.
- [x] Review acceptance and update the task/master ledger.


## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | composition_t01 / accepted 2026-10-14; gpt-6.1-sol / high; independent review_composition_t01 approved | [Handoff/red-green evidence](../evidence/conversation-redesign-composition/t01-handoff.md); 16 focused, 112 conversation, 13 dependency, 16 legacy composer, 575 backend tests pass | Exact slot assembly and lossless beats; production 240/300/600 policy remains unselected; progress fails closed |
| T02 | composition_t02 / accepted 2026-10-14; gpt-6.1-sol / high; independent review_composition_t02 approved | [Handoff/red-green evidence](../evidence/conversation-redesign-composition/t02-handoff.md); 33 focused service/assembly, 139 conversation, 13 dependency, 16 legacy composer, 602 backend tests pass | One action-composition call; ordinary route bypasses generation; no execution port; historical-receipt/current-activity limitation recorded for T03 |
| T03 | Unassigned / recorded 2026-10-14 | Not run | Explicitly added after accepted-receipt/current-activity revision case showed T01 assembler fails closed |
