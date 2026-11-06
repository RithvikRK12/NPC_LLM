# evaluation-release/T01 handoff

**Status:** Incomplete; configured-model replay and deterministic evidence are ready for review. Two independent human score sets, disagreement discussion, reviewer agreement, and rubric freeze remain pending. Updated 2026-10-18 (Asia/Kolkata).

## Scope

Supporting workstream `evaluation-release/T01`: a read-only shadow replay over the frozen `baseline-evaluation-v1.json`, exact score denominator preservation, and preparation for human-calibrated language scoring. No production conversation behavior, mechanics, canon, or active interactions were changed.

## Files changed

- `backend/app/services/conversation/shadow.py` — forwards scheduled external events and initial visible history into each immutable turn input; records generated history with explicit player/NPC speaker order.
- `backend/tests/test_conversation_replays.py` — adds event/history, configured payload, schema parsing, frozen settings/model fingerprint, no-write dependency, and blind reviewer-form checks.
- `docs/evidence/conversation-redesign-release/t01/configured_replay.py` — adds a credential-redacted configured-provider callback and reproducible replay/export command; model tag digest and server version must match the frozen fixture. `--prepare-review-forms` rebuilds reviewer forms without network calls.
- `configured-replay-results.json` — exact configuration digests, model response rows, origin counts, state digests, latency summary, and frozen score denominators.
- `quality-samples.json` — per-dimension samples with missing outputs represented explicitly.
- `human-calibration-template.json`, `human-calibration-reviewer_1.json`, and `human-calibration-reviewer_2.json` — a 24-row balanced calibration subset; the two reviewer sheets have the same references and independent blank score fields.
- `docs/redesign-tasks/evaluation-release.md` and `docs/redesign-master-progress.md` — task evidence and current handoff state.

The fixture was not changed. Its expected mechanics are not passed to the generator. The runner exposes no game, persistence, canon-write, interaction-write, or operation ports. Candidate generation is dialogue-only; this replay is not an end-to-end coordinator or game-adapter integration test.

## Tests and replay

Working directory: `/Users/rukithnayak/Documents/NPC_LLM-1`; Python `.venv` 3.12.14; fixture `backend/tests/fixtures/conversation/baseline-evaluation-v1.json`.

| Command | Exit | Result |
| --- | ---: | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_replays backend.tests.test_conversation_baseline_scenarios backend.tests.test_conversation_proposal backend.tests.test_conversation_generation_adapter backend.tests.test_conversation_diagnostics backend.tests.test_conversation_validation backend.tests.test_conversation_validation_quality` | 0 | 75 passed, 0 failed/skipped |
| `.venv/bin/python docs/evidence/conversation-redesign-release/t01/configured_replay.py` | 0 | 44 scenarios, 176/176 generated turns, 0 provider errors, 0 state digest change |
| `.venv/bin/python docs/evidence/conversation-redesign-release/t01/configured_replay.py --prepare-review-forms` | 0 | Two separate forms, 24 rows each, six dimensions, 12 rows per NPC per form |
| `git diff --check` | 0 | clean |

The replay used `OpenAICompatibleProvider`, `llama3:latest`, Ollama 0.34.2, manifest `sha256:365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1`, temperature 0.2, structured output, 120-second request timeout, and 5-second connect timeout. The runner verified the live tag digest and server version before generation. The frozen fixture SHA-256 is `a76b3c16c8be6a535af708544ad5c1ea9b3fcb7ef27ef06524c56b63f427e3bc`; model-settings digest is `e657d9d7935e47a9f8a04e6810037ffa396e4d26d0bfa3834f62ed615747f44c`.

Measured turn latency was p50 2.401 seconds and p95 3.338 seconds (n=176). All origins were `generated`. Frozen denominators were directness 44, coverage 12, continuity 16, character consistency 44, grounding 44, and naturalness 88; the exported samples match the fixture exactly. The replay adapter requested `maxLength: 240` in the structured-output schema for ordinary replies; it did not slice returned text. Forty-seven of 176 replies reached that bound, and 32 of those ended with an alphanumeric character. The 24 rating rows represent 16 unique turns: 11 unique turns reached the bound, and seven ended alphanumerically. Reviewers should score the text exactly as returned, including incomplete endings. No quality target is claimed before human scoring.

Test-first evidence: event forwarding and initial-history retention each failed on the missing behavior before implementation. Configured-adapter tests first failed because the runner did not exist; the manifest comparison exposed Ollama's bare digest format before normalization. Focused checks passed after those corrections.

## Acceptance review

- Frozen 44-scenario, 4-turn corpus across both NPC roles — **verified** by the full 176-turn run and fixture digest.
- Frozen state/model inputs and read-only boundary — **verified locally**; initial and final state digests are identical, and the adapter dependency check excludes mutation/game/database layers.
- Complete score denominator and missing-output preservation — **verified locally**; all six exported row counts match the frozen fixture.
- Configured provider/model — **verified** by live manifest/version preflight and 176 generated responses; no mock substitution occurred.
- Human rubric calibration — **pending**. Reviewer 1 and reviewer 2 need to independently score the same 24 rows before discussing disagreements.
- Reviewer agreement and rubric freeze — **pending**. Calculate quadratic weighted Cohen's kappa from the submitted integer scores, record disagreements and clarifications, then freeze the rubric version. Do not substitute agent-generated scores.

## Risks and next step

This evidence measures candidate dialogue from a read-only prompt adapter, not the durable coordinator/application pipeline. The 240-character bound is fixture provenance and remains an unresolved product policy; the observed candidates at that bound require human review. The replay does not establish release quality thresholds or rollout readiness.

Next exact task: finish `evaluation-release/T01` by collecting the two blind reviewer forms, recording reviewer agreement and rubric freeze. `evaluation-release/T02` remains gated on T01 acceptance. No new task was added.
