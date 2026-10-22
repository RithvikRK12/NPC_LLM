# Evaluation task packet

Source: Stage 3 and Stage 4 of [`../../llm-response-improvement-plan.md`](../../llm-response-improvement-plan.md).

## E01 — isolated experiments and provenance

Dependencies: D01. Proposed files: evaluation-only module/tests/fixture/runner and new evidence directory. Do not alter historical replay fixtures, runners, outputs, or reviewer artifacts.

- [x] Add fake-provider tests for missing/error outcomes, exact sample refs and denominators, fixed versus closed-loop histories, incompatible model-only comparisons, output collisions, local-only endpoints, and read-only boundaries.
- [x] Implement immutable manifests/outcomes, compatibility validation, comparison interface, CLI, prompt snapshots, and blind-form exports; reuse shadow types where useful.
- [x] Preserve missing results in denominators and record provenance/resource data. Fail closed on populated output paths and hosted inference targets.
- [x] Verify the historical fixture hash and record the runner hash mismatch; existing historical outputs and reviewer artifacts remain untouched. A 24-turn CLI fake run verifies full orchestration writes only under a fresh temporary run directory.

Acceptance: model and prompt comparisons cannot be conflated, errors remain counted, old evidence is unchanged. Tests: `test_conversation_quality_experiments.py`, `test_conversation_replays.py`.

Progress: core code, `--help`, and fake end-to-end CLI orchestration are implemented. Focused suites and adjacent safety/lifecycle suites passed. The frozen dataset hash matches; the current historical runner source hash differs from archived metadata, as recorded in D01 diagnosis. Historical outputs were untouched. Initial context-mismatched/schema-mismatched runs and the user-stopped Gemma full run are quarantined. Focused Llama/Gemma fixed-context and closed-loop runs are recorded. The three Llama full prompt variants each completed 176/176 twice at matching settings; all six frozen denominators, missing slots, and blind forms are exact. User waived human reviews; no semantic scores are entered and no quality winner is claimed. See [`../../evidence/llm-response-improvement/repeatability-comparison.md`](../../evidence/llm-response-improvement/repeatability-comparison.md).
