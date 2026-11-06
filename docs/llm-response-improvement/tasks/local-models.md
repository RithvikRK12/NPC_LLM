# Local model task packet

Source: Stage 3 and Stage 4 of [`../../llm-response-improvement-plan.md`](../../llm-response-improvement-plan.md). Local inference only.

## M01 — screen local model compatibility and resource fit

Dependencies: E01, D01; D02 for production-path screening.

- [x] Inspect hardware and installed models; verify current official model/provider details before choosing a candidate.
- [x] Resolve the selected artifact/download allowance with the user; Gemma 3 12B Q4_K_M was explicitly selected and downloaded locally.
- [x] Pin Gemma tag/digest/quantization/provider and active context; complete fixed-context and closed-loop dialogue smoke. Screened one live proposal adapter call on Gemma and Llama. The user then selected the existing Llama model due to Gemma's resource cost; no further Gemma inference will be performed.
- [x] Screen composition and repair contracts and cold/warm behavior for the selected model; do not change production defaults. Llama composition/repair schemas returned typed outputs in all three screens; proposal was valid in two of three and malformed once, remaining fail-closed. One focused cold-load sample measured the first request separately from 23 warm requests. Gemma follow-up was omitted per the user's instruction to use the existing Llama only.

Acceptance: a candidate fits/serves required contracts or a specific evidence-backed blocker is recorded.

Progress: Apple M5 / 16 GB unified memory; Ollama 0.34.2. Model identities are in [`../../evidence/llm-response-improvement/model-inventory.md`](../../evidence/llm-response-improvement/model-inventory.md). The user prefers the existing Llama model due to Gemma's resource cost; no further Gemma inference will be run. Gemma's earlier measurements and interrupted full run are preserved. Proposal/composition/repair plus receipt-aware local screens are recorded in [`../../evidence/llm-response-improvement/structured-adapter-screen.md`](../../evidence/llm-response-improvement/structured-adapter-screen.md); r8 receipt composition was rejected for a malformed canon candidate. Current code stamps trusted provenance and fills a missing receipt slot server-side while preserving strict validation. The empty reply issue is contract-rejected and the original discrepancy preserved in the structured screen record. Cold-load/warm latency results are in [`../../evidence/llm-response-improvement/repeatability-comparison.md`](../../evidence/llm-response-improvement/repeatability-comparison.md). Full durable runtime remains disabled by local policy.

## M02 — compare full quality and local operating cost

Dependencies: E01, M01, P01, D02 result.

- [x] Run unchanged control and full prompt comparisons on the selected Llama model using frozen fixed-context inputs, then run closed-loop focused checks. Focused 24-turn Llama/Gemma model screen, all three 176-turn Llama prompt conditions, and Llama/Gemma closed-loop t04 are complete. Full Gemma run was stopped by user request and is quarantined.
- [x] Repeat all three selected 44-scenario/176-turn Llama prompt variants once under matching controls. Preserve errors and all six frozen denominators: directness 44, coverage 12, continuity 16, character consistency 44, grounding 44, naturalness 88.
- [x] Report warm request latency, model memory, cutoff suspicion, schema-stage validity, and missing outputs for repeated dialogue runs; cold-start/complete-turn latency and production fallback/repair distributions remain unavailable without the enabled durable route.
- [x] Export independent blind forms for all six dimensions; retain review/calibration gaps and do not invent a score-to-pass mapping from the 1–5 anchors.
- [x] Recommend retaining current prompt/configuration pending review; user prefers existing Llama for resource fit. The cutoff counts are not human quality scores.

Acceptance: operational prompt-run repeatability is documented with missing outputs counted and no gain claimed. Semantic model/prompt effects cannot be established because the user waived reviews; no adoption is recommended.
