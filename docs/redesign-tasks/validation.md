# validation implementation tasks

**Goal:** Deliver the `validation` responsibility in the NPC conversation redesign.
**Status:** validation/T01–T03 locally accepted; coordinator integration, production semantic evaluation and release quality measurement remain open.
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

- [x] **Task complete** — Main Agent accepted 2026-10-18 after contracts/T09 added fail-closed whole-reply coverage.

**Depends on:** contracts/T03; composition/T01; contracts/T06.
**Acceptance criteria:** ResponseValidator.check(reply, context, current_evidence) returns structured findings for complete assembled reply, references, evidence revisions, mechanical implications, attribution and canon conflicts; checkers receive narrow projections.
**Test expectations:** Correct slot surrounded by contradictory prose is blocked; unknown IDs and unsupported shops/caches/recipes/routes fail; report is not witnessed event; harmless soft-spot and fear idioms pass.

- [x] Add focused failing behavioral/contract tests for structural, grounding and coverage outcomes.
- [x] Implement the bounded validator through its frozen projections; fail closed on incomplete coverage.
- [x] Run focused, adjacent and full backend checks; record passing evidence.
- [x] Review acceptance criteria and record handoff/output changes.

### validation/T02: Add concern, repetition and style evaluation hooks

- [x] **Task complete locally** — Main Agent accepted 2026-10-18; advisory only, offline hooks.

**Depends on:** validation/T01.
**Acceptance criteria:** Separate blocking/advisory findings, concern coverage, speaker identity, repetition and pacing. Semantic checking starts offline; optional runtime port is disabled unless measurement justifies activation and never authorizes gameplay.
**Test expectations:** Mixed concern omitted from reply is detectable in calibrated fixtures despite addressed IDs; purposeful repeated facts differ from accidental repetition; no mandatory semantic call on greeting.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### validation/T03: Implement bounded speech-only repair service

- [x] **Task complete locally** — Main Agent accepted 2026-10-18 after independent focused/full-suite verification.

**Depends on:** validation/T01; proposal/T02.
**Acceptance criteria:** RepairService.repair(candidate, findings, evidence, deadline) accepts coordinator-granted token, corrects speech/canon candidates only, rebuilds spans and revalidates whole reply. Proposal-format repair consumes the same single turn token.
**Test expectations:** Scripted repair preserves receipt and cannot add/replace/run operations; failed repair admits no canon; Unicode offsets rebuilt; coordinator contract forbids second repair after format recovery.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | validation_t01_fix / Main Agent accepted 2026-10-18; gpt-6-luna / medium | [Handoff](../evidence/conversation-redesign-validation/t01-handoff.md); validation 13/13, contract validation 5/5, composition 38/38, canon 15/15, conversation 518/518, backend 986/986; diff check clean | Structural/grounding regressions pass; claim coverage is explicit and incomplete extraction blocks canon validation |
| T02 | Main Agent / accepted 2026-10-18 | Focused 6/6, validation 19/19, backend 1015/1015; `git diff --check` clean | [Handoff](../evidence/conversation-redesign-validation/t02-handoff.md) | Concern coverage is an offline assessment hook, not semantic proof; all findings are advisory |
| T03 | validation_t03 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | Focused 17/17, adjacent 128/128, backend 1015/1015; `git diff --check` clean | [Handoff](../evidence/conversation-redesign-validation/t03-handoff.md) | Coordinator must provide a fresh durable shared-budget reservation and rebuild projections for repaired speech |
