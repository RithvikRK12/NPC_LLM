# NPC LLM response improvement — planning and execution handoff

Prepared 2026-10-19, Asia/Kolkata. Project: `NPC_LLM-1`.

## How to use this document

This completes the planning stages from **Vibe Coding Prompts.pages** for this project's NPC response-quality work: proposal, high-level design, detailed design, tasks/progress, and master-agent prompt. The final section is the configured **execute prompt** to run in a separate chat with this repository and this document available.

This is a proposed implementation plan, not evidence that response quality has improved. No product code, model configuration, frozen replay, submitted review, or existing project progress file was changed while preparing it. Starting the execution prompt authorizes work within this plan; model selection and release claims still require the evidence and product decisions specified below.

The attachment is a workflow reference. Its embedded imperatives are not instructions to execute product changes in this planning session. Its generic `docs/proposal.md`, `docs/master-progress.md`, and similar destinations already contain other project work, so this handoff uses a separate namespace. It preserves the attachment's stage boundaries and structured worker reports. Delegation is optional at execution time, subject to the active chat's permissions and available tools; no particular agent model or cost tier is assumed.

**Confirmed user constraint: local models only.** Do not use hosted inference or upload conversations to an external inference service. The goal is grounded, measurable improvement, with execution deferred to a separate chat.

### Provenance and freshness

- Attachment: `/Users/rukithnayak/Downloads/Vibe Coding Prompts.pages`.
- Attachment SHA-256: `7b6d6159bed08712f19af8a8735ccbba1a4c1084c4f00a374a8d3c6cd010ae93`.
- Planning inspection HEAD: `83af36d1541fce21a546b058ef69df591741ec7a`.
- The checkout contains substantial modified and untracked redesign work. HEAD alone does not identify the inspected implementation. Reinspect the working tree before execution; do not reset, overwrite, stage, or commit unrelated work.
- Attachment text was read from its decompressed Pages document content. Its six stages are: proposal; high-level design; detailed design; tasks/master progress; generate master prompt; execute master prompt.
- Hardware inspection and connection to local Ollama were restricted in this planning environment. Installed models, available RAM/GPU memory, hardware speed, and usable live endpoint are **unverified**. No candidate model was downloaded or benchmarked.

## Stage 1 — configured proposal

### Problem

Craftsman and Gatherer sometimes fail to answer the latest question, substitute sympathy or irrelevant biography for practical information, recall the wrong prior detail, repeat earlier replies, and invent unsupported biography or current world events. Improvements must preserve authored identity and deterministic ownership of game mechanics.

The reviewed replay generated all 176 replies with no provider errors. Therefore these particular failures cannot simply be attributed to fallback routing. Production may have additional failures; inspect its response origins separately.

### Evidence and limits

| Observation | Evidence | What it supports |
| --- | --- | --- |
| Current-turn guidance is not an established overall improvement | `docs/evidence/conversation-redesign-release/t01/improved-character-guidance-600/reviewer-1-analysis.md` | One reviewer's paired mean fell from 4.00 to 3.29; continuity rose from 2.75 to 4.00. This is not independent agreement or a general quality estimate. |
| Practical follow-ups receive nonanswers | Same directory, `human-calibration-reviewer_1-completed.json`, Craftsman/Gatherer scenario 02, t2–t3 | Measure missing substantive answers, distinguish unsupported mechanics from absent information. |
| Gatherer recalls company instead of fruit | Same completed review, `gatherer-04:t2` | Test recall against actual visible dialogue rather than plausible profile content. |
| Father is declared dead | Same completed review, `craftsman-02:t4` | Preserve unspecified survival as an explicit always-visible identity limit. |
| Forecast and changing forest layout are invented | Same completed review, scenarios 01 t3 | Test current-world claims against supplied facts. |
| Four responses hit 600 characters without sentence-final punctuation | Same directory, `README.md` and `configured-replay-results.json` | Investigate likely cutoffs; punctuation alone is not proof of semantic completeness. |
| The replay is a dialogue-only measurement adapter | `docs/evidence/conversation-redesign-release/t01/configured_replay.py` | Do not equate its outputs with production structured-pipeline behavior. |
| Compact projection omits a specific authoring limit | `backend/app/services/context/characters/craftsman.json`; `backend/app/services/context/character_profiles.py` | Full biography leaves father's survival unspecified; projected continuity mentions name/location/service but omits survival. |
| Existing rollout gates remain open | `docs/redesign-tasks/evaluation-release.md`; `docs/redesign-master-progress.md` | Reuse existing thresholds and integration gates; do not mark the redesign released. |

The reviewed model is recorded as local Ollama `llama3:latest`, digest `sha256:365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1`, temperature 0.2. Treat that as a historical measurement configuration, not proof of today's active deployment. No cross-model result exists in the inspected replay variants.

### Goals

1. Answer the actual current request, including separate emotional and practical concerns.
2. Recall the correct prior detail and handle topic switches without stale repetition.
3. Maintain distinct authored voices and preserve unspecified biography.
4. Ground present-world assertions and offers of playable actions in supplied evidence.
5. Identify whether a stronger local model improves the same workload enough to justify its latency and memory cost.
6. Preserve structured contracts, consent, receipts, retries, history scope, and existing mechanics.

### Non-goals

- Rebuild the conversation architecture, add a new memory subsystem, invent a social state machine, or expand response banks without diagnostic evidence.
- Invent rope/wood gameplay, tutorials, travel, services, weather simulation, or forest events to satisfy a review comment.
- Rewrite character identities or silently accept generated lore as world truth.
- Raise the 600-character hard maximum or change the historical baseline's ordinary-dialogue policy.
- Add hosted inference, switch embedding models, tune unrelated game systems, or ship a model because of general benchmark reputation.
- Automatically launch a previously unapproved redesign rollout.

### Users and scenarios

The player talks to Craftsman or Gatherer about personal life, work, feelings, practical game information, and prior conversation. The developer needs reproducible local evidence that separates model limitations from missing context and runtime behavior.

Required scenarios: emotional plus practical request; explicit follow-up demanding the omitted answer; day-going-well topic switch; father/background question; fruit recall; changed opinion; unknown current weather; unsupported demonstration offer; supported action with exact consent and receipt; legitimate reminder/repetition; quoted or hypothetical action; cleared or wrong-NPC history.

### Functional requirements

- FR1: Inventory the actually used route, provider, model digest, context, budgets, origins, and failure handling before changing behavior.
- FR2: Deliver essential identity limits in compact profiles without dumping full bibles or exceeding the existing 4,200-character projection bound.
- FR3: Use existing authoritative facts/capabilities to explain implemented practical behavior. If evidence is absent, identify the uncertainty and ask only for information that would resolve it.
- FR4: Distinguish recalling prior speech from asserting its truth. A false historical world claim may be recalled as prior speech and corrected; it must not become current evidence.
- FR5: Test concise, substantive answers and unsupported action promises using the existing prompt seams. Do not require every answer to start identically or prohibit brief empathy.
- FR6: Evaluate baseline and stronger local candidates with frozen inputs and recorded provenance. Keep failed/missing outputs in denominators.
- FR7: Verify production structured generation separately, including proposal, no-operation replies, receipt-based composition, repair, and fallback.
- FR8: Report observed improvements and unresolved failures separately. Produce evidence and a reversible configuration recommendation.

### Non-functional requirements

- Local inference only; redact credentials and private configuration from evidence.
- Preserve deterministic game authority, exact consent binding, at-most-once effects, receipt truth, and scoped visible history.
- Keep legacy and versioned request behavior compatible; configuration must not silently route durable turns through the legacy executor.
- Bound generation, memory, context, latency, and repair work; measure actual values rather than inventing a playable latency target.
- Maintain immutable historical artifacts and distinguish offline observations, deterministic checks, live model measurements, human review, and release acceptance.

### Acceptance

Implementation acceptance requires targeted deterministic tests and the relevant adjacent regressions to pass, with exact commands and evidence. Wording assertions alone do not establish model compliance. Live candidate prose is reviewed semantically rather than against a single exact sentence.

Quality/release thresholds already recorded in `docs/redesign-tasks/evaluation-release.md` T03 are: relevance ≥90%; mixed-concern coverage ≥90%; canon consistency ≥95%; healthy-provider fallback <5%; accidental consecutive repetition <2%; measured route p50/p95; product acceptance of playable latency/readable limits. Preserve them. Document the criterion and denominator used to convert a rubric score into a pass before scoring; do not equate an average 1–5 rating with a pass percentage. A targeted experiment does not satisfy all rollout gates.

Two independent human reviews of the same replay and rubric calibration remain required for the existing broader acceptance process. Generate review forms when needed; never fabricate reviewers, agreement, or completion. Missing reviews can block acceptance without blocking useful implementation and measurement.

### Open decisions

| Decision | Treatment during execution |
| --- | --- |
| Available hardware and installed models | Inspect locally; ask for RAM/GPU/hardware details only if tools cannot establish them. |
| Download/storage allowance | Reuse installed models first. Before a substantial new download, show exact artifact size and resource need and resolve allowance with the user. |
| Candidate identity and quantization | Choose after hardware and schema compatibility screening. Verify current official local-provider/model documentation; pin exact tag, digest, quantization, and context settings. No universal winner is preselected. |
| Acceptable latency and memory use | Measure baseline and candidates; obtain product preference before deployment selection. Do not invent a budget. |
| Missing practical item knowledge | Audit implemented mechanics first. Reuse genuine existing facts; ask for authoring intent only if a new game rule is necessary. |
| Human reviewers | Prepare self-contained blind forms. Continue independent work while reviews are pending. |

## Stage 2 — configured high-level design

### Architecture

Reuse the existing conversation architecture. Add a small evaluation workstream and make bounded profile/context/prompt changes where evidence supports them. Evaluate a local model upgrade as a separate variable. Integrate only measured improvements into the existing generation and deployment seams.

```text
Authored identity + scoped visible history + authoritative facts/capabilities
    -> existing context/profile projection
    -> existing prompt builder
    -> local structured generation adapter
    -> existing proposal / interaction / operation policy
    -> existing deterministic game services and committed receipts
    -> existing composition / validation / bounded repair / fallback
    -> existing finalization / API / Godot display

Read-only evaluation snapshots -> candidate local generation -> evidence export
                                               -> blind human review
```

The evaluation harness has no mutation, consent-consumption, active-interaction-write, canon-write, or production-finalization port. Mechanical integration checks use isolated test databases and existing adapters.

### Components and boundaries

| Workstream | Responsibility | Existing seams |
| --- | --- | --- |
| Runtime diagnosis | Establish active path and response origins; audit budget units | `backend/app/api/routes/chat.py`, `backend/app/main.py`, `backend/app/api/deps.py`, `backend/app/services/pipeline.py`, `backend/app/services/llm/structured.py` |
| Identity/context | Retain critical authoring constraints and practical evidence | `backend/app/services/context/character_profiles.py`, `backend/app/services/context/characters/`, `backend/app/services/conversation/adapters/context_read.py`, `backend/app/services/conversation/adapters/game.py` |
| Prompt experiment | Current question, recall, missing evidence, supported offers | `backend/app/services/prompts/builder.py`, shared character direction |
| Local evaluation | Frozen prompt comparisons and conversational rollouts; provenance and review | Existing shadow contracts in `backend/app/services/conversation/shadow.py`; new isolated evaluation files below |
| Integration/selection | Confirm runtime contract compatibility, latency, fallback, rollback recommendation | `backend/app/services/conversation/application.py`, proposal/composition/validation/repair; settings and existing release packet |

### Decisions and tradeoffs

- Prefer **small context fixes plus controlled local-model evaluation**. Prompt-only work cannot supply absent information; model-only work cannot establish missing game facts.
- Keep critical identity invariants always visible. Do not depend on keyword selection to retrieve a prohibition needed on an unrelated personal turn.
- Start with minimal prompt changes, preserving T04 direction and recorded variants. Do not keep appending redundant prohibitions; compare one explicit variant at a time.
- Reuse existing capabilities; an inventory containing rope does not establish a demonstration or training mechanic.
- Use fixed-context comparisons to isolate model effects, then closed-loop conversations to test accumulated drift. These answer different questions.
- Do not introduce a production semantic judge, additional model call, or repair loop merely to improve offline scores.
- Keep mechanical validation strict. Existing advisory repetition checks are supporting signals, not proof of intent or a blanket production rejection rule.

### Dependencies, reliability, and observability

The existing stack is Python/FastAPI/Pydantic/SQLAlchemy and Godot; local inference uses the configured OpenAI-compatible endpoint. Reuse existing libraries. New dependencies require a demonstrated need. A local endpoint error stays a provider error; it must not silently become a mock success.

Evidence must separate generated, scripted, mock, fallback, timeout, malformed output, and validation rejection when the path exposes them. Record cold-load versus warm latency, request versus complete-turn latency, and any repair calls. Never compare a dialogue-only request's latency directly with a multi-stage production turn without labeling both.

Principal risks: stale working-tree assumptions; unavailable local hardware; schema incompatibility; whole-JSON overhead; context omitted by projection/budgeting; fluent unsupported claims; slower model causing deadline-driven fallbacks; accidental weakening of consent/receipt validation. Mitigate with path diagnosis, pinned runs, focused negative tests, and isolated integration before deployment.

## Stage 3 — configured detailed design

### File ownership

Keep existing shared APIs unless diagnosis proves a change necessary. New evaluation-only files are proposed targets, not existing APIs:

- `backend/app/services/conversation/quality_experiments.py`: immutable experiment records, manifest validation, comparison summaries; no I/O or game mutation.
- `backend/tests/test_conversation_quality_experiments.py`: fake-provider evaluation/provenance tests.
- `backend/tests/fixtures/conversation/response-quality-focused-v1.json`: supplemental focused cases; never substitute it for the frozen 44-scenario fixture.
- `docs/evidence/llm-response-improvement/run_experiment.py`: CLI orchestrator for local calls and versioned evidence output, adapting existing shadow code without modifying historical evidence.
- `docs/evidence/llm-response-improvement/`: diagnosis, per-run manifests/results/forms, comparisons, and integration reports.
- `docs/llm-response-improvement/`: execution progress, task packets, and runbook, materialized from this handoff in task D01.

Modifications should stay in the existing profile, prompt, context-read, and generation seams identified above. Do not create new production modules for evaluation-only concerns.

### Proposed evaluation contracts

Use frozen dataclasses or the project's immutable-contract conventions. Keep these evaluation-only; do not expand gameplay contracts.

`ExperimentManifest`: schema version; run ID; input mode (`fixed_context` or `closed_loop`); dataset hash; ordered sample refs; prompt/profile/schema hashes; context snapshot hash; local endpoint host without secrets; exact model tag/digest/quantization; provider version; temperature; seed if supported; context size; token and character budgets with units; hardware description; cold/warm condition; repetition index; start/end timestamps.

`SampleOutcome`: run/sample IDs; stage; output origin/status; optional candidate text; optional validated structured result; safe error category; elapsed time; returned finish reason; token usage when reported; number of calls/repairs; input hash. Missing text remains missing and scorable as a failure under the recorded criterion.

Proposed narrow interfaces:

```python
validate_manifest(manifest: ExperimentManifest) -> None
compare_compatible_runs(left: ExperimentRun, right: ExperimentRun) -> ComparisonReport
```

Validation rejects absent model identity, hosted inference targets, output-path collisions, changed sample order, incompatible comparison inputs, and invalid budget units. For model-only comparisons, all non-model input hashes/settings match; hardware must match for latency attribution. Permit the model identity and its declared necessary compatibility settings to differ, and label any such setting difference. Never silently accept it as a pure model-only comparison.

The CLI's `--help` must document actual implemented arguments. Minimum controls: input fixture, prompt variant/snapshot, local endpoint, exact model, output directory, mode, and smoke/full selection. Credentials come from existing safe configuration, never command-line literals or exported manifests. Output directories are new per run and fail closed if populated. Keep old `configured_replay.py` and its baseline manifest checks intact.

### Runtime diagnosis

Inspect these facts before product changes:

1. `/chat` requests with `request_id` use durable/versioned transport; requests without it use the legacy pipeline. Confirm which payload the current Godot client sends and which runtime is enabled.
2. `Settings.conversation_enabled` defaults false; the historical replay model and the default `Settings.llm_model` are not evidence of the active configuration. Read only required non-secret settings.
3. Inspect representative provider output and final displayed text with origins. An offline generated repetition and a production fallback repetition require different fixes.
4. `StructuredGenerationAdapter.generate(..., response_budget)` sends the value as `max_tokens`, checks the length of serialized returned JSON against it, and the prompt calls it a character limit. Proposal/composition callers pass an output character limit. Determine whether valid structured metadata crowds out dialogue or causes rejection. This is a **potential defect to reproduce**, not an established explanation for the dialogue-only replay.
5. Confirm existing context budget retention keeps the relevant finalized turn. Do not add retrieval or summarization machinery when the correct detail is already in the prompt.

If the budget issue is reproduced, define separate, bounded units for final dialogue code points, serialized contract characters, and generation tokens. Version any policy/adapter contract change and update all callers/tests. Keep final dialogue ≤600 code points, stage deadlines, call limits, and memory limits. Do not merely remove bounds or silently multiply 600. If changing a frozen public contract is required, record a small design addendum and affected callers before implementation.

### Identity and practical evidence

Retain `project_profile(role, message, recent=(), *, name=None)` and its detached return semantics. Put the father's unspecified survival in always-included authored continuity/bounds, not only a background card or full bible. Preserve the 4,200-character projection maximum, unknown-role behavior, two-card limit, and fixed identity.

For practical turns, audit `read_capabilities()` and actual deterministic item/quest behavior. Project only information the NPC is entitled to know, using existing authored/mechanical evidence types. Distinguish general conversational advice from an actual playable action. Do not infer a service from occupational identity. If no implemented rope-use mechanic exists, say that the conversation cannot establish one and resolve the player's intended task; do not invent instructions and mark them grounded.

### Prompt experiment

Start from a frozen copy of the current guidance. Test a compact variant expressing these behaviors:

- Give the requested substantive answer early; brief empathy may accompany it.
- When asked to recall, use the relevant visible prior statement, preserving its attribution; do not substitute a profile preference.
- When asked a new personal question, answer it rather than replaying the previous work answer.
- Do not offer to demonstrate, follow, train, inspect, or perform another action without corresponding supplied capability. Capability presence still does not establish consent.
- When practical evidence is absent, state the specific unknown and ask one useful question; do not replace the answer with a promise of future help.
- Avoid invented present weather/events and unspecified biography; retain a natural character voice.
- Finish cleanly within the configured dialogue limit. Prefer deleting optional material to padding or truncating the substantive answer.

These are behavioral targets, not mandatory exact dialogue. Keep prior frozen direction constants/variants reproducible. Any wording changes that affect a historical runner must not silently relabel old provenance.

### Evaluation design

**Focused smoke:** use all four turns of scenarios `craftsman-01`, `craftsman-02`, `gatherer-01`, and `gatherer-02` (16 turns), then the four `gatherer-04` recall turns (20 total). Include the two Craftsman recall successes in full evaluation so an apparent fix does not erase continuity gains. Supplemental negative cases cover unsupported services, known/unknown practical facts, correction, and clear/wrong-NPC history.

**Fixed-context mode:** freeze each input from the current recorded replay, including prior dialogue and exact projected profile/evidence. Render prompts once, store hashes/snapshots, and send identical snapshots to each model. Current model-generated output does not become another sample's input in this mode. Freeze prompt version before a model-only comparison.

**Closed-loop mode:** reuse the same ordered player turns and frozen initial state; each model's generated history feeds its later turns. Record this divergence explicitly. Compare conversation outcomes, not a claim that all later prompts were identical. Events scheduled before each turn retain their existing semantics.

**Experiment sequence:**

1. Reproduce a fresh baseline with current prompt/model, leaving old results untouched.
2. Screen one stronger local instruction model that fits measured hardware; a second candidate is optional if the first fails compatibility or offers an unresolved tradeoff.
3. Run baseline versus candidate on fixed baseline prompt snapshots.
4. Test context/prompt fixes on the baseline model.
5. Test the same fixes on the candidate. A complete two-model × two-guidance comparison is required to claim an interaction or attribute combined gains separately; otherwise label the narrower comparison accurately.
6. Run the full 44-scenario/176-turn suite for finalists and a production-path integration sample. Repeat finalist runs at least once under the same declared settings to expose instability; record seed support and nondeterminism.

Preserve original scoring denominators: directness 44, coverage 12, continuity 16, character consistency 44, grounding 44, naturalness 88. Report supplemental case denominators separately. Intentional reminders/repeats and induced outages get explicit labels; do not remove poor outcomes after seeing results. Different dimensions can score the same text, so the mean of 24 dimension scores is not 24 independent conversations.

No model becomes the recommendation solely because it has the highest mean. Review critical unsupported-world/canon failures, each quality dimension, failure rates, latency, and resources. If tradeoffs remain, present the measured options and keep the baseline configuration until the user chooses.

### Error handling and integration

Count unavailable endpoint, out-of-memory, timeout, unsupported schema, invalid JSON, invalid IDs/spans, and budget overflow separately. Never retry indefinitely or substitute mock success. Existing turn-wide repair/call allowances remain authoritative.

No-operation production replies derive from `proposal.reply`; receipt-bearing composition can use another generation stage. Test both, rather than assuming every turn has proposal plus composition calls. Test post-commit generation failure through receipt-preserving fallback, exact retry/idempotency, quoted/hypothetical action, and history clear. Narrative canon extraction remains fail-closed where the existing runtime lacks a trusted claim producer.

### Test strategy

- Pure tests: critical profile constraints survive topic selection; manifests and comparisons reject incompatible inputs; missing outputs remain counted; smoke refs are exact; output paths cannot overwrite evidence; evaluation exposes no mutation authority.
- Prompt/context tests: both prompt paths receive current-turn/history/identity evidence; practical facts/capabilities are genuine; unknown state stays unknown. These prove delivery, not generated quality.
- Fake-transport adapter tests: schema compatibility, valid structured overhead if the budget defect is reproduced, token/character bounds, Unicode, finish reasons, deadlines, and unavailable-provider behavior.
- Live local measurements: blinded semantic review of focused and full cases, origin distributions, warm/cold latency and resource measurements. Preserve raw candidate artifacts and manifests.
- Integration: existing proposal, composition, operation, repair, API/lifecycle, SQLite/PostgreSQL and Godot checks appropriate to changed boundaries. Mark unavailable environments explicitly; a skipped database/client gate is not a pass.

## Stage 4 — task division and master progress

All implementation tasks below begin unchecked. Planning and inspection are complete; no task has implementation acceptance yet.

### Progress destination

On execution, create `docs/llm-response-improvement/master-progress.md` and one packet per workstream: `tasks/diagnosis.md`, `tasks/evaluation.md`, `tasks/context.md`, `tasks/prompts.md`, `tasks/local-models.md`, `tasks/integration.md`. Copy the task IDs, dependencies, acceptance, and tests below into those files. This handoff remains the design source; record later approved changes as dated addenda rather than silently rewriting assumptions.

Each progress entry records owner, state (`not_started`, `in_progress`, `blocked`, `verified`, `awaiting_human_review`), changed files, commands/exit codes, evidence paths, unresolved issues, and next task. A module checkbox is complete only when all its tasks and stated adjacent gates pass. Existing redesign progress is separate; link evidence without marking unrelated modules complete.

| Module | Initial status | Tasks |
| --- | --- | --- |
| Diagnosis | [ ] Not started | D01, D02 |
| Evaluation | [ ] Not started | E01 |
| Context | [ ] Not started | C01, C02 |
| Prompts | [ ] Not started | P01 |
| Local models | [ ] Not started | M01, M02 |
| Integration | [ ] Not started | I01 |

### D01 — materialize packets and establish runtime baseline

**Dependencies:** none. **Owner scope:** planning namespace, evidence diagnosis only; runtime files read-only.

- [ ] Inspect `git status`, applicable repository instructions, source files, and current client/runtime route. Create the progress and task files above without overwriting unrelated files.
- [ ] Record required non-secret settings, model identity if accessible, hardware, and local provider availability; identify unavailable evidence explicitly.
- [ ] Reproduce representative personal, mixed practical, recall, and action replies in isolated sessions if available. Capture route/origin and displayed versus generated text.
- [ ] Publish `docs/evidence/llm-response-improvement/diagnosis.md` with facts, hypotheses, unknowns, exact commands, and next task.

**Acceptance:** actual path and provider evidence are recorded or precisely unavailable; no inference from defaults; no production state changed. **Validation:** schema/payload inspection and safe isolated measurements; no new tests for documentation alone.

### E01 — implement isolated experiments and provenance

**Dependencies:** D01. **Files:** new evaluation module, tests, supplemental fixture, runner listed in Stage 3.

- [ ] Add failing fake-provider tests for missing/error outputs, exact sample refs/denominators, fixed versus closed-loop history, incompatible model-only inputs, output collisions, local-only endpoint policy, and read-only boundaries.
- [ ] Implement the proposed immutable records, manifest checks, comparison interface, CLI, prompt snapshots, and blind-form exports. Reuse shadow types where practical.
- [ ] Verify old fixture/runner hashes and historical outputs remain unchanged. Confirm a fake run writes only its new output directory.
- [ ] Record passing focused tests and exact runner help/example invocations in the task packet.

**Acceptance:** comparisons are reproducible and cannot silently conflate prompt and model changes; fixture outcomes and errors remain in denominators. **Tests:** `test_conversation_quality_experiments.py` and `test_conversation_replays.py`.

### D02 — reproduce and resolve structured-output budget ambiguity

**Dependencies:** D01; E01 before using live comparison results. **Files:** `backend/app/services/llm/structured.py`, relevant proposal/composition callers, prompt/settings/contracts only if reproduction requires them; `backend/tests/test_conversation_generation_adapter.py`.

- [ ] Construct a semantically valid typed response with final dialogue within policy but serialized JSON larger than that dialogue budget; measure actual rejection and token allocation behavior.
- [ ] Record whether this is a defect under the intended contract. If confirmed, write a bounded addendum with explicit units, chosen limits, compatibility and migration before implementation; otherwise close as verified no-change with evidence.
- [ ] For a confirmed defect, add the failing adapter/caller cases, implement the smallest bounded fix, and verify oversized dialogue, oversized JSON, token allocation, Unicode, schema failure, and deadlines.

**Acceptance:** budget meaning is explicit and tested; no unbounded output or relaxed final dialogue ceiling. **Tests:** generation adapter, proposal, composition-service, repair, and contract/settings suites touched by the fix. Existing tests that encoded the ambiguous behavior require an explicit rationale for changed expectations.

### C01 — preserve compact identity constraints

**Dependencies:** D01. **Files:** `backend/app/services/context/characters/craftsman.json`, `backend/app/services/context/character_profiles.py` only if necessary, `backend/tests/test_character_profiles.py`.

- [ ] Add a failing projection test proving father's unspecified survival is present for greetings, mood, background, and unrelated practical turns; retain no death/disaster expansion in formative lore.
- [ ] Add the missing constraint to always-included authored continuity; avoid a special-case generated answer.
- [ ] Verify detached results, ≤4,200 characters, ≤2 optional cards, unknown roles, and both prompt paths. Preserve existing authored identity.

**Acceptance:** critical constraint reaches the model independent of keyword matches. **Tests:** character profiles, context adapter, generation adapter. Live compliance remains a separate P01/M02 result.

### C02 — ground practical answers in implemented knowledge

**Dependencies:** D01. **Files:** existing game/context adapters and authored catalog only as evidence requires; focused context/game-adapter tests and supplemental fixture.

- [ ] Trace rope/wood uses and supported commands to deterministic services. Record which claims the NPC can actually make, including what is unknown.
- [ ] Add contrasting known/unknown/unsupported-action fixtures. Add failing projection tests only for a proven missing existing fact or capability.
- [ ] Project genuine missing knowledge through existing evidence types, if needed. Do not invent a gameplay feature or a tutorial promise. If no projection change is needed, document that result and retain the negative cases.
- [ ] Verify no hidden stock/location disclosure, unauthorized operation, or promotion of player/NPC claims to mechanical facts.

**Acceptance:** every practical claim/offer has a source or explicit uncertainty; audit is allowed to conclude no code change. **Tests:** context adapter, game adapters, capabilities, proposal/operation negative cases.

### P01 — test a minimal current-turn and recall revision

**Dependencies:** E01, C01, C02; use D02 result for structured-path measurements. **Files:** shared character direction and prompt builder, character-profile tests, supplemental cases; new versioned evidence.

- [ ] Freeze baseline prompts/profiles and implement one compact candidate direction with the Stage 3 behavior targets. Preserve recorded historical variants.
- [ ] Add meaningful evidence-delivery tests for relevant prior speech, present question, critical identity limits, and capability boundaries; avoid treating instruction substring checks as quality proof.
- [ ] Generate the focused cases with baseline model and baseline/fixed guidance. Review substantive answers, recall, topic switches, supported/unsupported offers, clean endings, and successful continuity controls.
- [ ] Retain or revise the candidate based on evidence; a neutral/negative result remains valid and does not justify shipping it.

**Acceptance:** change is traceable, frozen variants reproducible, and behavioral results recorded without unsupported claims. **Tests:** character profiles, generation adapter, replay/experiment suites plus live focused review.

### M01 — screen local model compatibility and resource fit

**Dependencies:** E01, D01; D02 for production-path screening. **Files:** new experiment configs/manifests and evidence only.

- [ ] Inspect hardware and installed models. Check current official model/provider information for a suitable stronger instruction model, local execution, exact format, and quantization. Document candidate rationale without asserting a quality gain.
- [ ] Resolve substantial download allowance if needed. Run one model at a time; record model identity, memory/load behavior, context size, schema support and local endpoint.
- [ ] Screen complete proposal/composition/repair schemas and the focused smoke. Record malformed/unsupported outputs and timeouts, not only successful text.

**Acceptance:** at least one candidate demonstrably fits and serves required contracts, or an evidence-backed blocker explains why not. **Validation:** fake contract tests and local smoke with explicit endpoint/model identity; no default production model change.

### M02 — compare full quality and local operating cost

**Dependencies:** E01, M01, P01, D02 result. **Files:** new experiment run directories, forms, and `comparison.md`.

- [ ] Execute the experiment sequence in Stage 3, including the unchanged model/prompt control and both fixed-context and closed-loop finalist evaluation. Keep all manifests and raw outcomes.
- [ ] Repeat finalist runs at least once; separate cold/warm and request/turn latency, resource usage, schema errors, fallback, repairs, and cutoffs.
- [ ] Export independent blind forms and a comparison with all six original denominators. State missing reviews and calibration limits; record the exact score-to-pass rule before scoring.
- [ ] Recommend a measured candidate/configuration or keep the baseline if gains, reliability, or resource tradeoffs are unresolved. Do not convert one-reviewer scores into release acceptance.

**Acceptance:** model and prompt contributions are distinguished; no invented benchmark gain; errors remain counted; broader quality claims await required review. **Validation:** experiment compatibility checks, state digests, full local runs and reviewer provenance checks.

### I01 — validate production path and prepare adoption handoff

**Dependencies:** C01, C02, D02, P01, M02; compatibility review and product latency/resource decision before deployment selection. **Files:** existing generation/runtime config seams if supported by results; relevant integration tests; `docs/llm-response-improvement/runbook.md`.

- [ ] Run representative real structured-path turns with the finalist, covering no-operation `proposal.reply`, receipt-based composition, repair, provider failure, and receipt-safe fallback in isolated state.
- [ ] Verify exact consent, quoted/hypothetical requests, retry/idempotency, scope/epoch clear and finalized output; never replay a committed effect to improve speech.
- [ ] Run focused then relevant broader backend checks. Run required PostgreSQL/Godot gates if changed boundaries require them; report unavailable gates honestly.
- [ ] Document exact pinned model/configuration, enable prerequisites, rollback retaining receipts, measured latency/resources, unresolved review/rollout gates, and the evidence-backed recommendation. Keep the current deployment unchanged if the product decision or a required gate is missing.
- [ ] Update this workstream's progress; link changes to the existing redesign packets only where their actual acceptance criteria are met.

**Acceptance:** bounded implementation is verified and adoption is reviewable; no unsupported shipping claim. **Tests:** impacted existing API/lifecycle, operations/interactions, generation/proposal/composition/repair suites; applicable isolated database/client gates.

### Sequencing and review focus

Start D01 → E01. C01/C02 and D02 are separate diagnosis-driven deliverables; M01 can screen while P01 is developed if tools and file ownership allow. M02 follows the stabilized interfaces and variants. I01 is the final integration gate. Sequential execution is valid; shared profile/prompt/test files must have one active writer.

Review these five risks explicitly: legitimate recall versus unwanted repetition; recalling an earlier false statement without reaffirming it; a topic change after a practical failure; enough structured metadata to exceed the dialogue-sized JSON budget; and generation failure after a committed operation. They belong respectively to E01/P01, P01, P01, D02, and I01.

### Baseline verification commands

Run from repository root; these are planned checks, **not results from this planning session**. Narrow tests during changes and broaden after relevant fixes pass.

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_character_profiles.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_generation_adapter.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_replays.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_quality_experiments.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'
git diff --check
```

The new quality-experiments test command is runnable only after E01 creates that file. A discovery command reporting zero tests does not count as verification. Use the actual implemented runner's `--help` for live commands; do not run the historical frozen-model command against an unpinned replacement or write new results into old replay directories.

## Stage 5 — configured master-agent instructions

Use these instructions as the master agent's operating contract when executing this workstream.

1. You are the Main Agent for a focused response-quality improvement, not a replacement conversation redesign. Read this entire handoff, current workstream progress, applicable instructions, and the specific task's source files before changes.
2. Establish actual state and file ownership. Preserve existing modified/untracked work and immutable evidence. Do not overwrite the project's generic proposal/design/prompt/progress files.
3. Keep all inference local. Confirm actual model identity; never infer it from a mutable tag or defaults. Inspect hardware before choosing an upgrade. Do not silently substitute a cloud endpoint or mock output.
4. Pick the next ready task and state its scope, dependencies, affected files, and proof of completion. Record hypothesis separately from observed failure. Diagnose before implementation.
5. Work through bounded tasks with meaningful failing behavioral tests when code behavior changes, minimal implementation, focused checks, then relevant adjacent checks. Documentation-only changes need review rather than artificial tests.
6. Optional delegation: use bounded workers only when permitted by the active session and useful. Give each worker its packet, this document's global constraints, direct contracts/fixtures, exact file ownership, expected tests, and report format. Never let two workers edit the same shared seam concurrently. Do not assume access to a cheaper model or spawn agents just because the template mentions them.
7. Check every worker report against code and verification evidence. The Main Agent owns integration and progress. A worker's statement that tests pass is not a substitute for accessible results.
8. Generate live comparisons with pinned inputs/provenance and isolated output directories. Distinguish fixed-context versus closed-loop inputs, guidance effects versus model effects, and offline quality versus production integration.
9. Ask only for missing decisions that materially block the dependent task: inaccessible hardware details, substantial model download allowance, new gameplay intent, or latency/resource selection. Continue independent tasks while awaiting answers. Do not ask again about local-only inference or the requested scope.
10. Update workstream task/progress files after each completed task. Record scope additions before acting. Stop at a genuine external blocker only after completing unaffected work, and leave an exact resume instruction.
11. Never weaken game authority, receipts, consent, scope, or validation to raise language scores. Never claim semantic completeness from punctuation, concern IDs, instruction substrings, or test counts alone.
12. Finish with changed files, exact tests/results, measured quality/resource tradeoffs, risks, pending reviews/gates, recommendation, and next task. Implementation completion, model selection, quality acceptance, and release are separate states.

### Worker or task report format

```text
Task ID and scope:
Inputs / dependency versions:
Files changed:
Observed failure or measurement question:
Change and rationale:
Tests / measurement commands and exit codes:
Results, counts, and evidence paths:
Unverified claims / unavailable environments:
Mechanical and compatibility risks:
Follow-up tasks or required user decisions:
Progress status:
```

## Stage 6 — final prompt to run in the separate chat

Copy the following prompt into a new chat with this repository available. Attach this Markdown document if the new chat cannot read the repository file.

```text
Execute the NPC LLM response improvement workstream defined in
docs/llm-response-improvement-plan.md.

Read that document in full. Treat its Stage 1 requirements, Stage 2 architecture,
Stage 3 design, Stage 4 task definitions, and Stage 5 master-agent instructions
as the workstream specification. I want grounded improvements to Craftsman and
Gatherer responses, with LOCAL MODELS ONLY. Do not use hosted inference.

Begin by reinspecting the current working tree and any applicable instructions.
Preserve existing modified/untracked work and all historical replay/reviewer
artifacts. The source checkout may have changed since the handoff was written.
Record material differences before adapting the plan. Do not restart the broader
conversation redesign or overwrite its generic proposal/design/progress files.

Materialize this workstream's packets and master progress in
docs/llm-response-improvement/ if absent, then execute the next ready task,
starting with D01. Continue through ready implementation and measurement tasks;
do not stop after restating the plan. Use bounded subagents only when the active
session permits them and delegation materially helps, with explicit ownership.
Sequential execution is acceptable.

Diagnose the actual runtime path and output origins first. Verify the structured
JSON/token/dialogue budget ambiguity before fixing it. Preserve critical compact
identity constraints, use real practical facts/capabilities, and test current-turn
answers and recall with the existing failing exchanges and successful controls.
Do not invent new gameplay, broaden memory architecture without evidence, or
weaken consent, receipts, validation, idempotency, or scope boundaries.

Inspect hardware and installed local models before selecting a stronger candidate.
Use current official model/provider information and pin identity/quantization.
Ask about substantial download allowance and unresolved product latency/resource
tradeoffs only when they become necessary. If tooling cannot inspect hardware,
ask for the missing facts while continuing independent code/evaluation work.

Compare models on fixed prompt/context snapshots before claiming a model effect,
then test closed-loop multi-turn behavior and the real structured production path.
Keep the model/prompt controls, six frozen scoring denominators, missing outputs,
provenance, local resource measurements, and immutable baseline evidence intact.
Do not predict a percentage improvement or silently choose a winner.

Run meaningful focused tests for each code change, then the relevant adjacent
regressions. Record commands, exit codes, counts, evidence, and unavailable gates.
Never invent human reviewer scores or turn pending review into accepted quality.
Pending human review does not prevent preparing the remaining implementation,
blind forms, resource comparison, and adoption/rollback recommendation.

After each task update workstream progress. At the end report what changed,
what was verified, actual measured gains or regressions, local operating costs,
unresolved decisions/gates, and the next recommended action. If blocked, complete
unaffected work and leave an exact resumable task state. Keep deployment unchanged
until the plan's product decisions and required adoption gates are satisfied.
```
