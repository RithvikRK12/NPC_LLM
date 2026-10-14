# evaluation-release implementation tasks

**Goal:** Deliver the `evaluation-release` responsibility in the NPC conversation redesign.
**Status:** Not started; no redesign implementation verified in this planning pass.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§6.8,10; Proposal §§19,21–23.
**Owned files / integration targets:** backend/tests/fixtures/conversation/; backend/tests/test_conversation_replays.py (new); docs/evidence/conversation-redesign-release/; docs/conversation-redesign-runbook.md (new).
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [api-adapter](api-adapter.md), [baseline](baseline.md), [capabilities](capabilities.md), [coordinator](coordinator.md), [diagnostics](diagnostics.md), [godot-adapters](godot-adapters.md), [proposal](proposal.md), [validation](validation.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### evaluation-release/T01: Build read-only shadow and calibrated replay runner

- [ ] **Task complete**

**Depends on:** baseline/T03; proposal/T02; diagnostics/T02; validation/T02.
**Acceptance criteria:** Run frozen ≥40 multi-turn scenarios across both NPCs with immutable state/model fixtures and human-calibrated scoring for relevance, mixed coverage, continuity, consistency, grounding and naturalness separately. Shadow has no mutation/canon-write/active-interaction ports.
**Test expectations:** Negative dependency test proves shadow cannot mutate; preserve sample counts/paraphrases and judge/human agreement evidence; mechanical assertions deterministic, live prose not exact-string asserted.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### evaluation-release/T02: Run complete mechanical and lifecycle adoption gate

- [ ] **Task complete**

**Depends on:** coordinator/T03; api-adapter/T03; godot-adapters/T03; capabilities/T02; evaluation-release/T01.
**Acceptance criteria:** All existing mechanical regressions and new pure/SQLite/PostgreSQL/API/Godot suites pass, including concurrency, receipt atomicity, clear/reset/fence, retry and semantic-authority invariants. Replace old social-history exclusion assertions with context-versus-authorization assertions.
**Test expectations:** Record commands/exit codes/environment and failure counts; require zero invariant failures; all §5.4 crash points and §8 errors mapped to test IDs; isolated DBs only.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### evaluation-release/T03: Measure quality and approve rollout policy

- [ ] **Task complete**

**Depends on:** evaluation-release/T02; baseline/T02.
**Acceptance criteria:** Require ≥90% relevance, ≥90% mixed-concern coverage, ≥95% canon consistency, <5% healthy-provider fallback, <2% accidental consecutive repetition. Report route p50/p95 and exact model settings; obtain product acceptance for playable latency/readable limits before shipping. Benchmark model candidates on same suite without assuming replacement.
**Test expectations:** Record denominators, excluded intentional repeats/outages, representative human reviews and configuration/policy compatibility across provider/Pydantic/composer/Godot; failures remain release blockers, not waived via weaker grounding.

- [ ] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [ ] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [ ] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### evaluation-release/T04: Document staged adoption and receipt-safe rollback

- [ ] **Task complete**

**Depends on:** evaluation-release/T03.
**Acceptance criteria:** Additive/versioned cohort rollout runbook preserves accepted actions/receipts; stored canon may remain inactive on rollback. Verify both NPC profiles/fallbacks and health; no unresolved redesigned turn routes through receipt-unaware legacy executor.
**Test expectations:** Exercise enable/disable during pending, operation-committed and final states; exact final retry and no duplicated/reversed legitimate effects; record rollout/rollback decision and evidence.

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
| T04 | Unassigned / not started | Not run | None recorded |
