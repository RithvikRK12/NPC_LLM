# evaluation-release implementation tasks

**Goal:** Deliver the `evaluation-release` responsibility in the NPC conversation redesign.
**Status:** T01 replay boundary, configured-model replay, denominator-preserving samples, and separate blind reviewer forms are implemented and locally verified. T01 remains incomplete pending two independent human score sets, disagreement discussion, agreement evidence, and rubric freeze. T05 is a separately tracked, measurement-only 600-character replay; T06 repeats that same run with context/T04's updated authored character-guidance bundle. Neither task selects a shipping limit or model. 2/6 tasks accepted.
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

- [x] **Task closed: replay complete; human calibration explicitly waived**

**Depends on:** baseline/T03; proposal/T02; diagnostics/T02; validation/T02.
**Acceptance criteria:** Run frozen ≥40 multi-turn scenarios across both NPCs with immutable state/model fixtures and human-calibrated scoring for relevance, mixed coverage, continuity, consistency, grounding and naturalness separately. Shadow has no mutation/canon-write/active-interaction ports.
**Test expectations:** Negative dependency test proves shadow cannot mutate; preserve sample counts/paraphrases and judge/human agreement evidence; mechanical assertions deterministic, live prose not exact-string asserted.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

**Closeout (2026-10-20):** The user waived human reviews and retained Llama 3, as recorded in [the response-improvement runbook](../llm-response-improvement/runbook.md). Read-only replay/dependency checks remain accepted. No judge/human agreement or semantic percentage is claimed; original calibration requirements are retained above for audit. This waiver closes T01 for the local-play scope.

### evaluation-release/T02: Run complete mechanical and lifecycle adoption gate

- [x] **Task complete**

**Depends on:** coordinator/T03; api-adapter/T03; godot-adapters/T03; capabilities/T02; evaluation-release/T01.
**Acceptance criteria:** All existing mechanical regressions and new pure/SQLite/PostgreSQL/API/Godot suites pass, including concurrency, receipt atomicity, clear/reset/fence, retry and semantic-authority invariants. Replace old social-history exclusion assertions with context-versus-authorization assertions.
**Test expectations:** Record commands/exit codes/environment and failure counts; require zero invariant failures; all §5.4 crash points and §8 errors mapped to test IDs; isolated DBs only.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

**Closeout (2026-10-20):** [Mechanical handoff](../evidence/conversation-redesign-release/t02/handoff.md): backend 1,129/1,129; PostgreSQL eight runners / 153 executions; Godot 16/16 functional scenarios. Crash/error coverage and shutdown-warning limitations are recorded explicitly.

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

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [ ] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

**Local deliverables complete (2026-10-20):** [Runbook](../conversation-redesign-runbook.md), both live NPC profiles/outage fallbacks, disabled-admission/pending recovery, committed-receipt recovery and exact final HTTP replay are verified. Broad rollout approval and the final task checkbox remain pending T03. Local pilot is enabled only by the explicit launcher profile.

### evaluation-release/T05: Run a separate alternate output-limit replay

- [x] **Task complete**

**Depends on:** baseline/T03.
**Acceptance criteria:** Preserve the frozen 240-character baseline outputs. Replay the same 44 scenarios/176 turns against the fingerprint-verified model using a 600-character ordinary-dialogue ceiling, with the original story ceiling unchanged. Export separate results, quality samples, denominator counts, and two independent blind reviewer forms under a clearly labeled alternate-limit directory. Record the changed limit as the only replay-policy difference; this is measurement evidence and does not approve a production limit.
**Test expectations:** Prove the default payload remains 240, the alternate payload uses 600 for ordinary dialogue, story requests retain their existing 600 ceiling, output paths cannot overwrite baseline artifacts, and exported provenance/denominators identify the alternate policy. Run the alternate replay and record all 176 outcomes and unchanged state digests.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### evaluation-release/T06: Replay the frozen suite with updated character guidance

- [x] **Task complete locally; subsequent human scoring waived**

**Depends on:** baseline/T03; context/T04; evaluation-release/T05.
**Acceptance criteria:** Repeat the exact frozen 44-scenario/176-turn suite using the same fingerprint-verified model, temperature and 600-character ordinary-dialogue ceiling as T05. Supply context/T04's versioned compact Craftsman/Gatherer profiles, topic-selected details, and shared character direction to each generation prompt. Save outputs, hashes, denominators and two new independent reviewer forms in a dedicated directory. Record both profile file digests/revisions and prompt hash; preserve T05 and the submitted pre-update reviewer scores unchanged. This measures the updated character-guidance bundle, not a new model or shipping policy.
**Test expectations:** Verify both roles receive their current profile projection and shared direction, the existing T05 outputs remain intact, and the new replay records exact provenance. Generate all 176 turns with unchanged read-only state digests; preserve all six scoring denominators and build new forms containing only the new candidates.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | Closed with explicit human-review waiver, 2026-10-20 | [Original replay handoff](../evidence/conversation-redesign-release/t01/handoff.md); frozen 44 scenarios / 176 turns; dependency isolation tests | User retained Llama 3 and waived human reviews; existing scores/forms preserved, no agreement or quality percentages invented |
| T02 | Accepted, 2026-10-20 | [Mechanical handoff](../evidence/conversation-redesign-release/t02/handoff.md), 1,129 backend tests; eight PostgreSQL runners; 16 Godot scenarios | Zero functional/invariant failures; three fixture shutdown resource warnings explicitly retained |
| T03 | Open: broader release gate | [Latest live screen](../evidence/conversation-redesign-release/t03/live-route-summary.json); exact model/policy and route samples | Small functional screen does not certify semantic thresholds or accepted product latency |
| T04 | Local runbook/checks delivered; broad approval pending T03 | [Play/rollback runbook](../conversation-redesign-runbook.md); application rollback/recovery tests and live NPC/outage screen | Existing receipts/effects preserved; new admission pauses, existing identities replay; no broad release approval |
| T05 | Main Agent / accepted 2026-10-18 | [Alternate replay evidence and review instructions](../evidence/conversation-redesign-release/t01/alternate-limit-600/README.md); 44 scenarios / 176 generated turns; matching state digests; all six denominators preserved; focused conversation suite 15/15; graph acyclic; `git diff --check` clean | Separate measurement candidate; 0/176 reached 600 characters (max 536); original 240-character artifacts preserved |
| T06 | Main Agent / accepted locally 2026-10-19 | [Updated character guidance replay and reviewer forms](../evidence/conversation-redesign-release/t01/updated-character-guidance-600/README.md); 44 scenarios / 176 generated turns; matching read-only state digests; updated profile/direction provenance; focused replay tests 16/16 and conversation suite 603/603; Reviewer 1 completed 24/24 and candidate/provenance checks match | Same frozen model/configuration and 600-character policy as T05; 13 outputs reached the ceiling and 12 ended without sentence-final punctuation; no second independent T06 review is available |

### Follow-up: validation-contract repair (2026-10-20)

[Evidence](../evidence/conversation-redesign-release/validation-contract/README.md): backend 1,140/1,140; PostgreSQL eight runners / 153 executions; three freshly rerun Godot scenarios; 8/8 sampled ordinary/action replies generated without degradation. Purpose clarification and deliberate outages are separate. This repairs wire/provenance failures and does not close T03 semantic thresholds or T04 broader rollout approval.
