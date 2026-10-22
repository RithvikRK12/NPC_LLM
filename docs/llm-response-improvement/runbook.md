# Local response experiment runbook and provisional adoption handoff

Status: research only; deployment remains unchanged. The user prefers the existing `llama3:latest`, stopped the Gemma full-set run due to resource cost, and waived human reviews on 2026-10-20. The Llama full fixed-context prompt matrix now has two repetitions per variant. Blind forms are retained but unscored; no prompt is adopted because no semantic quality result exists. Isolated receipt-aware composition now stamps trusted provenance and inserts a missing exact receipt slot server-side. The latest direct receipt-stage screen still failed strict canon validation; the enabled durable runtime policy is unset and full application integration remains incomplete.

## Pinned local configurations screened

| Tag | Digest | Quantization | Context | Ollama | Warm resident bytes |
|---|---|---|---:|---|---:|
| `llama3:latest` | `365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1` | Q4_0 | 4096 | 0.34.2 | 5,003,804,671 |
| `gemma3:12b-it-q4_K_M` | `b92b218582c521ba287f38f1d6057dcd3c6cbff036f13cac97b5d861f5e58ec3` | Q4_K_M | 4096 | 0.34.2 | 8,049,225,890 |

Both are local Ollama models; no hosted inference was used. Runs, endpoint, selected parameters, exact snapshot hashes, resource and latency measurements are in [`../evidence/llm-response-improvement/run-ledger.md`](../evidence/llm-response-improvement/run-ledger.md) and immutable per-run directories.

## Recommendation and open decisions

Retain the existing Llama model and current deployment configuration, per the user's resource preference. The focused fixed-context Gemma screen had fewer cutoff-suspected outputs (5/24 versus Llama t04 17/24) but was slower overall (131.816s versus 106.247s) and used about 61% more resident model memory. Closed-loop cutoff-suspected counts were 2/24 versus 17/24, with request p50/p95 7.391s/11.613s for Gemma and 3.502s/4.032s for Llama. These measurements identify a resource/latency tradeoff, while cutoff counts are not a quality rubric. Gemma's interrupted full run is incomplete and excluded. Direct Llama composition/repair calls returned typed values in 3/3 repeat screens; proposal returned typed output in 2/3 and `GenerationMalformed` once. Strict validation remains fail-closed. These isolated calls do not establish full route integration. The earlier empty-reply observation is rechecked: current contract and adapter tests reject empty replies, and current valid proposal samples contain one segment.

No percentage improvement, quality pass rate, or winning candidate is claimed. The user's Llama choice resolves the model resource preference for this workstream; acceptance of measured route latency/readability remains unresolved. Existing release thresholds and six denominator definitions remain in force, but human scoring was explicitly waived and no semantic pass rates can be reported.

The receipt-aware composition boundary was repaired and covered by deterministic tests. A model reply without a receipt slot now receives one server-authored slot derived from the immutable verified commit; duplicate and mismatched model slots remain invalid. The current local r8 screen failed strict canon candidate validation before the composition service returned, so live receipt-stage success remains unverified.

## Enablement prerequisites

1. Full Llama fixed-context runs and one matched repeat per prompt variant are complete; all runs retain the frozen denominators and missing outputs. User waived human reviews, so no human score or semantic winner is available. Repeat results and non-scored spot checks are in [`repeatability-comparison.md`](../evidence/llm-response-improvement/repeatability-comparison.md) and [`candidate-guidance.md`](candidate-guidance.md).
2. Run the full enabled application route in isolated state for proposal/no-operation, receipt composition, repair, provider failure, receipt-safe fallback, consent, quoted/hypothetical actions, retries/idempotency, scope/epoch clear, and finalization. This remains unavailable until a complete local durable policy is deliberately configured.
3. A single cold first-request sample plus 23 warm follow-up requests is recorded. Measure additional cold repeats and complete-turn p50/p95 on the enabled route; current production-route latency distributions are unavailable.
4. Product must accept measured latency/readability behavior before selecting any prompt adoption. The current Llama resource preference is recorded; no independent product latency threshold was provided.
5. Configure every required bounded conversation policy field deliberately. Generation defaults `2048` tokens and `16384` JSON characters alone do not enable the runtime; the feature flag is false by default. Run applicable backend, database and Godot checks before any deployment decision.

## Rollback and receipt preservation

The current versioned transport supports pausing new versioned admissions while existing keyed turns remain replayable; the behavior is covered by `test_rollback_pauses_new_versioned_admission_but_replays_existing_turn`. Startup recovery also scans pending keys, and `main.py` fails closed if pending turns exist without a complete policy, including during rollback. Therefore an adoption rollback must not delete receipt/turn storage, clear idempotency keys, rerun committed operations, or simply omit runtime policy while pending turns remain. Keep the existing runtime/receipts available for replay/finalization, set the admission feature flag off for new work, observe pending turns to resolution, and only retire the runtime/store after the operational procedure proves no recoverable work remains. This runbook is a code-backed operational recommendation; deployment-specific storage/backup behavior still requires verification before rollout.
