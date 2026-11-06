# baseline implementation tasks

**Goal:** Deliver the `baseline` responsibility in the NPC conversation redesign.
**Status:** T01 inventory and T02 provider measurement verified; 2/3 tasks complete. Frozen evaluation fixtures pending.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Proposal §§2,16,19,21; Detailed design §§9–10.
**Owned files / integration targets:** docs/evidence/conversation-redesign-baseline/; backend/tests/fixtures/conversation/; docs/redesign-policy-inventory.md.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** None. Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### baseline/T01: Inventory current contracts and mechanical authority

- [x] **Task complete**

**Depends on:** None.
**Acceptance criteria:** Document live /chat path, all input/output/context limits, existing renderer contracts, game-rule owners, internal commits, revision writers, and explicit game_id/timeline_id mapping decisions. Identify reusable code without claiming redesign completion.
**Test expectations:** Trace one ordinary and one action path by inspection; enumerate current regression commands and all inventory/quest/activity writers, including non-chat endpoints.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### baseline/T02: Measure provider health and response origins

- [x] **Task complete**

**Depends on:** baseline/T01.
**Acceptance criteria:** Capture representative Craftsman and Gatherer sessions with exact provider/model/configuration, generated/scripted/fallback/error counts, and ordinary/action/repair p50/p95. Use isolated fixtures, never a player save. Record unavailable measurements honestly.
**Test expectations:** Replay identical fixtures; distinguish healthy-provider fallback from outage fallback and explicit mock; verify diagnostics contain no credentials.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants. Measurement runner implemented; its fixture setup now flushes synthetic scope before a versioned writer refresh.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### baseline/T03: Freeze evaluation fixtures and policy candidates

- [x] **Task complete**

**Depends on:** baseline/T02.
**Acceptance criteria:** Freeze at least 40 scenarios, generally 4–8 turns, across both NPCs and the Proposal §19 categories. Inventory candidate deadline/token/beat/queue/lease/summary/retention policies; numeric shipping limits remain subject to measurement and product acceptance.
**Test expectations:** Validate scenario IDs, initial state, expected mechanical outcomes, model settings and scoring denominators; check every required scenario category has coverage.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | baseline_inventory / accepted by Main Agent; 2026-10-14; gpt-6.1-sol / medium | `.venv/bin/python docs/evidence/conversation-redesign-baseline/inspect_inventory.py` exit 0; 8 inspections; Main Agent reproduced. [Inventory](../redesign-policy-inventory.md), [manifest](../evidence/conversation-redesign-baseline/inspection-manifest.json); focused regressions 30 passed, 0 failed/skipped ([logs](../evidence/conversation-redesign-schedule/main-verification.json)) | Source paths/traces/limits/writers reviewed. No runtime redesign or live measurement certified. contracts/T01 ready; T02 measurement ready. |
| T02 | Main Agent / accepted 2026-10-18; configured model llama3:latest; Ollama 0.34.2 | [Evidence/report](../evidence/conversation-redesign-baseline/measurement/README.md); focused tests 5/5; exact isolated collector exit 0, 28 live turns, 140 credential checks; ordinary/action/repair p50/p95 recorded with repair n=0; model digest recorded | Two NPCs × two identical replays, 6 generated / 12 scripted / 10 healthy-provider fallback / 0 errors, no explicit mock; repair timing unavailable because the existing runtime does not generate repairs. Quality and shipping acceptance remain evaluation-release gates. |
| T03 | Main Agent / accepted 2026-10-18; model identifier unavailable in this runtime | [Handoff](../evidence/conversation-redesign-baseline/t03/handoff.md); fixture suite 6/6, T02 tooling 5/5, diff check exit 0; [fixture report](../evidence/conversation-redesign-baseline/t03/fixture-report.json) | 44 scenarios across both NPCs, 22 categories, explicit mechanical expectations and score denominators; current policy candidates recorded with no shipping limits selected; human calibration is evaluation-release/T01 |
