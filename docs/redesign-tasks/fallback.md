# fallback implementation tasks

**Goal:** Deliver the `fallback` responsibility in the NPC conversation redesign.
**Status:** T01–T02 locally accepted by Main Agent on 2026-10-18; active-canon fallback publication remains fail-closed until coordinator supplies T06 comparison projections.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§4,6.5; Proposal §14.
**Owned files / integration targets:** backend/app/services/conversation/fallback.py; backend/tests/test_conversation_fallback.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [composition](composition.md), [contracts](contracts.md), [proposal](proposal.md), [validation](validation.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### fallback/T01: Implement receipt-first situation fallback

- [x] **Task complete locally** — structural/grounding validation and publication-failure handling remain T02.

**Depends on:** contracts/T03; composition/T01; proposal/T02.
**Acceptance criteria:** FallbackPolicy.render(context, decision, receipt, failure) prioritizes committed receipt, then missing clarification, known unavailability, then role-specific outage speech. Both NPCs have authored fallback data; generic failure fabricates no answer.
**Test expectations:** Transfer then provider timeout still reports actual transfer; accepted inspection remains accepted; exact missing-consent/unavailable reasons and NPC-specific voice covered.

- [x] Add focused failing behavioral/contract tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused and adjacent contract/composition checks; record evidence.
- [x] Review acceptance criteria and update task/master progress.

### fallback/T02: Validate fallback and mandatory rendering failure

- [x] **Task complete locally** — Main Agent accepted 2026-10-18; canon projection integration limitation recorded.

**Depends on:** fallback/T01; validation/T01.
**Acceptance criteria:** Fallback uses same assembled-response structural/grounding checks and policy limits. If mandatory receipt text cannot be safely represented, return publication failure rather than misreport outcome.
**Test expectations:** Renderer failure, overflow and stale ongoing activity tests; successful effect survives failed speech; fallback remains recoverable and contains no invented resources or completions.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | fallback_t01 / locally accepted by Main Agent 2026-10-18; gpt-6-luna / medium | Main Agent reproduced focused 5/5, contracts 70/70, composition 38/38, conversation 385/385 and backend 848/848; independent review approved; `git diff --check` exit 0 | [Handoff](../evidence/conversation-redesign-fallback/t01-handoff.md) |
| T02 | fallback_t02 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | Focused 11/11, validation 13/13, composition 38/38, contracts 77/77; `git diff --check` clean | [Handoff](../evidence/conversation-redesign-fallback/t02-handoff.md) | Active canon requires coordinator-supplied T06 projections; until wired, fallback fails closed |
