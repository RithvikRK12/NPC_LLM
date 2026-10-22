# baseline/T03 handoff

**Status:** accepted by Main Agent, 2026-10-18. Model identifier unavailable in this runtime; no model-effort routing claim.

## Scope and files

- `backend/tests/fixtures/conversation/baseline-evaluation-v1.json` — frozen 44-scenario baseline, schema version 1; 22 scenarios each for Craftsman and Gatherer, four player turns each, 22 category IDs, distinct initial scopes, fixed inventories/quest/activity/revision state, provider and lifecycle events, and expected mechanical outcomes.
- `backend/tests/test_conversation_baseline_scenarios.py` — six deterministic checks for scenario counts/IDs, category coverage, model settings, initial state, expected outcome mapping, provider/lifecycle/receipt events, score denominators, separate scoring dimensions and policy inventory.
- `docs/evidence/conversation-redesign-baseline/t03/policy-candidates.md` — inventories current and candidate total/stage deadline, context token, output/beat, queue, lease, summary and retention controls. It records current conflicts and unset values; it selects no shipping thresholds.
- `docs/evidence/conversation-redesign-baseline/t03/fixture-report.json` — fixture SHA-256, category counts, per-dimension denominator sizes and model digest.
- `fixture-tests.log`, `measurement-tests.log` — current reproductions.

## Verification

From `/Users/rukithnayak/Documents/NPC_LLM-1`:

| Command | Result |
| --- | --- |
| `.venv/bin/python -m unittest backend.tests.test_conversation_baseline_scenarios` | exit 0; 6 passed, 0 failed/skipped |
| `.venv/bin/python -m unittest discover -s docs/evidence/conversation-redesign-baseline/measurement -p 'test_measure.py'` | exit 0; 5 passed, 0 failed/skipped |
| `git diff --check` | exit 0 |

Test-first evidence: the scenario validator first failed because the fixture did not exist; after the fixture was added, the policy-inventory assertion first failed because its document did not exist. The final validator passes. The T02 measurement harness regression first failed on the missing scope-preparation helper and passed after the helper flushes the fixture scope before the versioned writer refresh.

## Acceptance review

- At least 40 scenarios, 4–8 turns, both NPCs — **pass**: 44 scenarios, 4 turns each, 22 per NPC.
- Proposal §19 scenario coverage — **pass**: all 18 required categories are covered; the fixture includes four additional operation/recovery cases.
- Frozen state, model settings and mechanical outcomes — **pass**: unique synthetic game scopes, resource revisions, explicit expected outcomes, source prompt hashes, and the exact T02 `llama3:latest` manifest digest are recorded.
- Separate score dimensions and denominators — **pass**: directness 44, coverage 12, continuity 16, character consistency 44, grounding 44, naturalness 88 turn samples. No composite score is defined.
- Policy candidates — **pass**: all nine controls are inventoried; no numeric shipping value is selected.

Human rubric calibration remains pending for evaluation-release/T01. This handoff freezes inputs and scoring denominators; it does not claim language-quality results or product acceptance. The scenario fixture is a planned evaluation input, not a live-model replay of all 44 scenarios.
