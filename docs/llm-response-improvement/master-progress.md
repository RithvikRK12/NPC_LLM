# LLM response improvement — master progress

Specification: [`../llm-response-improvement-plan.md`](../llm-response-improvement-plan.md). This is an additive workstream; the existing conversation redesign progress remains authoritative for that project.

## Checkout snapshot

- Inspection date: 2026-10-19 Asia/Kolkata.
- HEAD: `83af36d` (`Add craftsman and gatherer encounter systems`), same commit recorded by the handoff.
- Branch: `master-progress`, tracking `origin/master-progress`.
- Working tree: substantial modified and untracked conversation redesign implementation, tests, frontend changes, and `docs/evidence/conversation-redesign-*` replay/reviewer artifacts. All preserved. Full initial inventory is in `../evidence/llm-response-improvement/diagnosis.md`.
- Material drift: the current Godot chat client submits durable versioned requests with `request_id`; durable conversation runtime code, policy contracts, diagnostics, and persistence adapters are now present in the working tree. Effective local settings have the conversation feature disabled and no durable policy configured, so current configured app startup is legacy-only and cannot serve a versioned request. The handoff's execution target remains applicable but its runtime-path assumptions require this diagnosis.

## Module status

| Module | Status | Tasks |
|---|---|---|
| Diagnosis | verified | D01 baseline recorded; D02 bounded contract fix implemented and focused tests pass; direct local structured path verified; full durable route unavailable |
| Evaluation | measurement complete; semantic review waived | E01 runs complete; two full fixed-context repetitions per Llama prompt variant; six denominators retained |
| Context | verified | C01, C02 |
| Prompts | candidate retained, not adopted | P01 tested twice per full variant; review waived; no semantic scores; grounding/cutoff failures remain |
| Local models | Llama-only checks complete; some scope intentionally omitted | Proposal/composition/repair structured stages screened on Llama; one cold-load sample measured; no Gemma follow-up per user direction |
| Integration | partial; full route remains gated | I01 deterministic tests and direct stage checks pass; complete enabled local application route remains disabled/unverified |

## Task log

### D01 — materialize packets and establish runtime baseline

- Owner: main agent; sequential execution.
- State: verified; subsequent read-only Ollama access and shadow experiments are recorded separately.
- Scope: new workstream docs/evidence only; runtime files read-only.
- Changed files: `docs/llm-response-improvement/master-progress.md`, six task packets, and `docs/evidence/llm-response-improvement/diagnosis.md`.
- Commands/results: see diagnosis evidence table. No automated tests run; documentation-only task. Runtime source stayed read-only.
- Evidence: `docs/evidence/llm-response-improvement/diagnosis.md`.
- Unresolved: the separate game/backend container's effective environment remains unobservable. Local Ollama is reachable through approved read-only/loopback commands; see model inventory and run ledger.
- Next: reproduce and resolve D02 using fake transport, then E01.

### D02 — structured-output budget ambiguity

- Owner: main agent.
- State: code-level fix verified; direct local adapter calls completed, while the enabled durable application path remains unavailable under current local settings.
- Scope: focused adapter contract/test and required design addendum; later single-stage adapter screening used only local Ollama and fixture context, with no production state.
- Evidence: fake-transport reproduction is archived. The user selected `2,048` generation tokens and `16,384` serialized JSON characters. A valid 917-character JSON proposal with an 11-codepoint reply passes; excess JSON, invalid/missing adapter bounds, Unicode counting, schema errors, and deadlines are tested. These values are bounded `Settings` defaults but do not configure/enable the durable runtime.
- Tests: generation adapter 21, application/settings 7, proposal 10, composition service 17, composition 21, repair 17, port conformance 5 passed. Commands used `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest <suite> -v` (except package-addressed suites). `git diff --check` passed.
- Next: keep durable runtime disabled until its other policy fields and adoption gates are satisfied. Complete remaining composition/repair local schema screening.

### C01 — compact Craftsman identity constraint

- Owner: main agent.
- State: verified.
- Changed files: `backend/app/services/context/characters/craftsman.json`, `backend/tests/test_character_profiles.py`.
- Finding: the full authoring contract already left Father’s survival unspecified, but compact `continuity` omitted it.
- Change: compact continuity now explicitly says survival is unspecified; no formative lore or biography was added.
- RED: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_character_profiles.py' -v` failed on all four projected message classes before the profile edit.
- GREEN: same command passed 10 tests; context adapter passed 3; generation adapter passed 16. `test_conversation_generation_adapter.py` is structural prompt verification, not live compliance.
- Evidence: profile/C01 test results and source in working tree.
- Next: P01 live behavior remains dependent on local provider availability.

### C02 — practical knowledge/capability audit

- Owner: main agent.
- State: verified with no code change.
- Scope: audit only; no new gameplay or evidence projection.
- Evidence: `docs/llm-response-improvement/context-audit.md`.
- Commands: `test_conversation_game_adapters.py` passed 48 tests; `test_conversation_capabilities.py` passed 13 tests; character profile suite passed 10 tests.
- Next: retain unknown rope-use and unsupported demo cases in response-quality evaluation.

### E01 — isolated evaluation records

- Owner: main agent.
- State: implementation, fake CLI orchestration, focused fixed-context/closed-loop local runs are verified; full repeats and human review remain open.
- Changed files: `backend/app/services/conversation/quality_experiments.py`, `backend/tests/test_conversation_quality_experiments.py`, `backend/tests/fixtures/conversation/response-quality-focused-v1.json`, `docs/evidence/llm-response-improvement/run_experiment.py`.
- RED: initial test discovery failed because the evaluation module was absent; later C01 behavioral test failed on all four turn classes before the compact continuity edit.
- GREEN: latest quality-experiment suite passed 17 tests; replay suite passed 16 tests; runner `--help`, `py_compile`, and `git diff --check` passed.
- Implemented: immutable manifests/outcomes/runs; local endpoint and pinned identity checks; fixed/closed-loop history paths with closed-loop divergence labeled; model-only compatibility checks; all six frozen denominator joins retaining missing outputs; exclusive prompt snapshots; blind form exports; local dialogue-shadow CLI with bounded outputs and resource timings.
- Historical provenance: frozen fixture hash matched. Current historical runner digest differs from archived metadata (see D01); archive files were not changed.
- Remaining at this 2026-10-19 checkpoint: existing full dataset/run runner hash mismatch limits claims about exact historical regeneration; prompt runs had one repetition; composition/repair schema screening and a complete enabled durable production path were unavailable under then-current runtime policy. Repeats, stage screening, and the human-review waiver are recorded in the 2026-10-20 completion update below.
- Next: prepare blind human review, run full 44-scenario/176-turn repeats, screen remaining structured stages, then implement I01 only after adoption gates. No score or winner is inferred from syntactic validity/cutoff rates.

## Verification refresh — 2026-10-19

- `test_conversation_generation_adapter.py`: 21 passed.
- `test_conversation_application.py`: 7 passed.
- `test_conversation_proposal.py`: 10 passed.
- `test_conversation_composition_service.py`: 17 passed.
- `test_conversation_composition.py`: 21 passed.
- `test_conversation_repair.py`: 17 passed.
- `conversation_port_conformance.ConversationPortConformance`: 5 passed.
- `test_conversation_quality_experiments.py`: latest run 17 passed.
- `test_conversation_replays.py`: 16 passed.
- `test_character_profiles.py`: 10 passed.
- `test_conversation_game_adapters.py` plus `test_conversation_capabilities.py`: 61 passed.
- The first two refresh invocations for application and repair used incomplete `PYTHONPATH` and failed during fixture imports; corrected invocations above passed. No code changes were made to address those invocation errors.
- After renaming the focused selection test to 24 turns, combined quality/replay/adapter/application unittest suites passed 61 tests. Pytest is unavailable, but project `unittest` is installed and was used. Latest `py_compile` and `git diff --check` passed.
- Fixed-context controls: Llama t04 / updated_profiles / improved_guidance each generated 24/24 at context 4096 with unchanged state digests and 17/24, 17/24, and 20/24 cutoff-suspected. Gemma t04 generated 24/24, 5/24 cutoff-suspected. Llama/Gemma dataset, prompt, profile, schema and context snapshot hashes match for model-only comparison. User stopped the full Gemma run due to resource cost; 176 prompt snapshots without outputs are preserved and excluded. No further Gemma inference is planned.
- Closed-loop t04: Llama and Gemma each generated 24/24 with unchanged state digests; 17/24 and 2/24 cutoff-suspected. Gemma request p50/p95 was slower (7.391s/11.613s vs 3.502s/4.032s Llama) and used reported 8.05 GB vs 5.00 GB resident model size. One repetition; not a quality winner.
- Historical direct local structured proposal adapter screen (2026-10-19): Llama returned a typed proposal with no reply segments; Gemma failed typed validation due to a missing span reference. The current contract regression and fresh screens are documented below. Full route unavailable because durable policy is unset and the feature flag is false. No production request or state mutation occurred.
- Verification refresh: combined focused evaluation/replay/adapter/application suites 61 passed; adjacent interactions/operations/lifecycle/persistence/API lifecycle/finalization/fallback/repair/validation/proposal/composition/turns/worker suites 211 passed. `py_compile`, runner `--help`, and `git diff --check` passed.
- Exact final commands/results: `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_quality_experiments test_conversation_replays test_conversation_generation_adapter test_conversation_application -v` — exit 0, 61 passed; `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_interactions test_conversation_operations test_conversation_lifecycle test_conversation_persistence_lifecycle test_conversation_api_lifecycle test_conversation_finalization test_conversation_fallback test_conversation_repair test_conversation_validation test_conversation_proposal test_conversation_composition test_conversation_application test_conversation_turns test_conversation_worker -v` — exit 0, 211 passed; `.venv/bin/python -m py_compile docs/evidence/llm-response-improvement/run_experiment.py backend/app/services/conversation/quality_experiments.py backend/app/services/llm/structured.py backend/tests/test_conversation_quality_experiments.py` — exit 0; `.venv/bin/python docs/evidence/llm-response-improvement/run_experiment.py --help` — exit 0; `git diff --check` — exit 0.
- Full Llama fixed-context comparisons completed for t04, updated_profiles, and improved_guidance at 176/176 each with zero missing/errors. Cutoff-suspected counts were 52, 108, and 82 respectively; request p50/p95 were 3.144/4.998s, 3.262/4.823s, and 3.807/5.043s. Full fixed-context six-denominator joins are intact on all three runs.
- `runbook.md` records the no-adoption recommendation, user preference for Llama, prerequisites, current code-backed rollback behavior preserving keyed receipts, and deployment-specific checks still required. Blind review is pending. Gemma's full run was stopped at user request and is incomplete. Adjacent safety/lifecycle regression batch passed 211 tests. PostgreSQL/Godot weren't run because this workstream did not change those boundaries; full local durable runtime stays disabled. Deployment remains unchanged.
- `git diff --check`: passed. No human scores or deployment changes.

## Unresolved issue follow-up — 2026-10-20

- The earlier direct Llama adapter screen recorded a typed `TurnProposal` with zero reply segments. Current checkout inspection found the proposal contract already sets `reply` to `Field(min_length=1)`, its generated schema has `minItems: 1`, and the adapter strictly validates JSON before returning. Production-equivalent array-to-tuple parsing of `reply: []` raises `ValidationError`; the adapter maps it to `GenerationMalformed`.
- Added `test_replyless_proposal_is_rejected_by_the_live_contract_adapter` in `backend/tests/test_conversation_generation_adapter.py`; it verifies rejection and schema `minItems`. Added `test_trusted_typed_proposal_with_empty_reply_is_revalidated_and_rejected` in `backend/tests/test_conversation_proposal.py`; it covers the service boundary that round-trips trusted objects. No redundant production guard was added because the existing typed contract and strict service validation already enforce the requirement. The discrepancy is documented in `docs/evidence/llm-response-improvement/structured-adapter-screen.md`; the historical result is preserved.
- Verification: `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_generation_adapter test_conversation_proposal test_conversation_coordinator test_conversation_composition_service` — exit 0, 68 passed. `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_contracts_turn_values test_conversation_contracts_interfaces test_conversation_application test_conversation_fallback test_conversation_validation` — exit 0, 74 passed. Direct reproduction using the production JSON array conversion — rejected as expected.
- Local access: ordinary sandbox access to Ollama loopback was denied; an approved elevated local command route succeeded. One fresh `StructuredGenerationAdapter` call to `llama3:latest` exited 0 and returned a typed proposal with 1 reply segment. `ollama ps` confirmed only Llama was loaded (5.0 GB, 100% GPU, context 4096). A first harness attempt exited 1 before making a request because it omitted the required deadline clock; the corrected call succeeded.
- Current source rejects reply-less proposals before they enter `ProposalService`; the specific live adapter path now also returned a nonempty reply. Full enabled application integration remains open. Existing model/prompt comparisons and deployment state are unchanged.

## Workstream completion update — 2026-10-20

- User directed skipping human reviews. Review forms remain immutable/unscored; no reviewer identity, human rating, semantic pass rate, or quality winner is recorded. An implementation-agent spot check of named examples is documented as such in [`../evidence/llm-response-improvement/repeatability-comparison.md`](../evidence/llm-response-improvement/repeatability-comparison.md) and [`candidate-guidance.md`](candidate-guidance.md).
- Completed repetition 2 for all three Llama fixed-context 176-turn prompt variants. Exact run IDs, latency, resources, denominators, and interpretation are in [`../evidence/llm-response-improvement/repeatability-comparison.md`](../evidence/llm-response-improvement/repeatability-comparison.md). Each pair matches on declared model/data/schema/context/generation controls; every run generated 176/176, had zero missing/errors, retained denominators 44/12/16/44/44/88, and left before/after state digest unchanged.
- Repeat 2: t04 cutoff-suspected 67, wall 438.968s, request p50/p95 2.531/3.688s; updated_profiles 106, wall 626.991s, p50/p95 3.614/4.731s; improved_guidance 83, wall 784.742s, p50/p95 4.484/6.565s. Each used 5,003,804,671 reported model bytes at context 4096; repeat 2 Python peak RSS was about 48–49 MB. Run 1/2 cutoff counts were t04 52/67, updated_profiles 108/106, improved_guidance 82/83. These are operational signals; no semantic quality gain is claimed. A separately unloaded 24-turn t04 sample took 5.739s for the first cold request; 23 warm follow-up requests had median 2.703s and max 3.205s. Full details are in the repeatability comparison.
- A compact prompt candidate is materialized in [`candidate-guidance.md`](candidate-guidance.md). Spot checks found improved exact Gatherer recall on `gatherer-04:t2`, with successful fruit recall at `gatherer-04:t3`, but unsupported rain forecast and wildlife incident claims persisted in `improved_guidance` repeat 2. The candidate remains unadopted; current prompt/deployment retained.
- Local `StructuredGenerationAdapter` stage screens against `llama3:latest`: composition and repair returned typed one-segment `CandidateReply` in 3/3 runs. Proposal returned a typed one-segment `TurnProposal` in 2/3 and `GenerationMalformed` in 1/3; failure remains fail-closed. Results are saved by `screen_structured_stages.py`. Gemma was not called further, per user direction. These direct calls did not exercise receipt-bound composition or full application behavior.
- Latest verification: focused quality/replay/adapter/application suite — exit 0, 62 passed; adjacent interactions/operations/lifecycle/persistence/API lifecycle/finalization/fallback/repair/validation/proposal/composition/turns/worker suite — exit 0, 212 passed; reply-less adapter/proposal regressions are included. Local Ollama command route used approved elevation because sandbox loopback is denied. No production request, persistence change, or deployment occurred.
- Remaining adoption blockers: full enabled durable route cannot run because the local feature flag is off and the complete durable policy is unset; complete-turn latency remains unmeasured; user waived semantic reviews, so there is no rubric-based quality acceptance. Preserve receipts/consent/scope and deployment unchanged. Recommendation: retain existing Llama and prompt, do not roll out the candidate; next required work is a deliberately configured isolated durable policy/full-route integration and a product decision on measured route latency/readability. No new game mechanic or memory architecture is proposed.

## Receipt composition and verification refresh — 2026-10-20

- Fixed the unresolved receipt composition omission without weakening validation: after strict adapter validation, trusted source provenance is stamped from the current turn/policy context. Receipt-aware composition appends exactly one server-created slot for the verified committed receipt if the model omitted one. Wrong IDs/outcomes and duplicate slots remain rejected; exact renderer output and activity evidence rules are unchanged. Prompt instructions now assign the receipt slot to the server and ask the model only for optional grounded prose.
- Test-first regression: `test_action_reply_requires_exact_committed_receipt_slot` failed before implementation when a prose-only candidate was returned, then passed after the trusted slot was appended; it also verifies duplicate/wrong receipt slots fail. Prompt regression and source provenance regressions pass.
- Focused composition/adapter/proposal/repair suite: exit 0, 90 tests. Relevant adjacent safety/application/regression suite: exit 0, 286 tests. The adjacent run emitted existing FastAPI/httpx, SQLAlchemy `utcnow`, and `on_event` deprecation warnings; no failures.
- Local Llama receipt-aware screen r8 is saved at [`../evidence/llm-response-improvement/runs/llama3-structured-stages-screen-r8.json`](../evidence/llm-response-improvement/runs/llama3-structured-stages-screen-r8.json). It used the pinned local Llama Q4_0 digest, Ollama 0.34.2, context 4096, and 5,003,804,671 resident bytes. Direct composition/repair were typed; proposal and receipt composition were rejected by strict validation (unknown concern, and canon addition with revision lineage respectively). Thus it does not show an end-to-end live receipt-composition pass; deterministic service tests verify the slot insertion path. One r7 harness run failed to save evidence on a provider exception; the screen now records categorized stage exceptions.
- Deployment remains unchanged. The enabled durable route remains gated because local feature settings are disabled/incomplete. Existing Llama/current prompt remain the recommendation; no semantic winner is claimed, and human forms remain unscored by user direction.

