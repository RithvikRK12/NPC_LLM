# Local shadow run ledger

## Quarantined runs

The Gemma full 176-turn run was stopped at the user's direction to stop using that model due to its local resource cost. Its fresh directory `runs/gemma3-t04-full176-fixed-warm-4096-240-r1` contains 176 prompt snapshots but no manifest, outcomes, or summary; do not score or compare it. The local Ollama process is now unloaded. Preserve the installed artifact and partial evidence without further Gemma inference.

One attempted detached Llama launch during an interactive-run diagnostic did not start a second process and left an empty temporary log at `/tmp/llm-response-improvement-llama3-full176-r2.log`; it produced no model requests or evidence directory.

The following immutable directories were produced before the runner verified active Ollama context. Each manifest declared 8,192, while `ollama ps` and `/api/ps` showed the loaded allocation was 4,096. Preserve the artifacts for audit, but do not score, compare, or present their dialogue as valid P01 results. They are not deleted or rewritten.

| Variant | Run ID | Directory | Reason |
|---|---|---|---|
| t04 | `66a35fe6-a529-4332-91e0-8b90d1fa3c78` | `runs/llama3-t04-smoke-fixed-warm-r1` | Declared/observed context mismatch (8192/4096) |
| updated_profiles | `a811e744-4a60-4b89-b6e2-5af227400225` | `runs/llama3-updated-profiles-smoke-fixed-warm-r1` | Declared/observed context mismatch (8192/4096) |
| improved_guidance | `755dbf53-8ad8-4c84-b497-9604bf50ddf7` | `runs/llama3-improved-guidance-smoke-fixed-warm-r1` | Declared/observed context mismatch (8192/4096) |

Each produced 20/20 syntactically valid dialogue outputs and unchanged state digests, with runner wall times 50.85s, 58.93s, and 60.37s. These operational observations are retained, but the runs are excluded from quality measurement because their context provenance is wrong.

The following second set declared an active 4,096 context and did have matching `/api/ps` readback, but was generated before the runner made the per-turn dialogue schema uniform and included the schema in its provenance hash. The manifest declared 600 while ordinary turns were capped at 240 and story turns at 600. Preserve, but do not score or compare these directories.

| Variant | Run ID | Directory | Reason |
|---|---|---|---|
| t04 | `54912e69-f5bd-4575-95e6-f443c6a95a60` | `runs/llama3-t04-smoke-fixed-warm-context4096-r2` | Manifest dialogue ceiling does not identify the per-turn 240/600 schema |
| updated_profiles | `30bea246-91a0-4f5b-b5a6-7c316d55e417` | `runs/llama3-updated-profiles-smoke-fixed-warm-context4096-r2` | Manifest dialogue ceiling does not identify the per-turn 240/600 schema |
| improved_guidance | `fcd6d328-b3ac-4fb0-aa32-8192e7e47604` | `runs/llama3-improved-guidance-smoke-fixed-warm-context4096-r2` | Manifest dialogue ceiling does not identify the per-turn 240/600 schema |

These produced 20/20 valid JSON responses and unchanged state digests. As exploratory diagnostics, they showed many outputs exactly at the ordinary 240-codepoint limit, but the count is not treated as a comparable cutoff measurement because the run contract did not record the per-turn schema.

## Validated reruns

Append each run here only after the runner's final `/api/ps` readback confirms the selected pinned model and declared active context. Keep each run directory immutable and fresh. Live runs are dialogue-shadow only, not structured production-path evidence. Blind forms remain pending human review.

### Llama 3 fixed-context prompt controls (24-turn focused set)

The runner was updated to make the 240-codepoint dialogue ceiling uniform across turns and bind that schema into the manifest. Supplemental fixture v2 includes the successful Craftsman `t2`/`t3` recall controls alongside failing exchanges. This baseline uses context 4096, warm repetitions 1, `num_predict=256`, JSON ceiling 16384, dialogue ceiling 240, and the pinned `llama3:latest` digest recorded in its manifest. This is the fixed-context baseline for prompt variants, not an adoption result.

| Variant | Run ID | Directory | Valid outputs | Cutoff-suspected | Wall time | Active context | State |
|---|---|---|---:|---:|---:|---:|---|
| t04 | `7d979f9b-88b6-4189-b359-32ed8bbec4a5` | `runs/llama3-t04-focused24-fixed-warm-4096-240-r1` | 24/24 | 17/24 | 106.247s | 4096 | before/after digests unchanged |
| Gemma 3 t04 | `05fb6779-183e-4b3d-b46f-0bb607155819` | `runs/gemma3-t04-focused24-fixed-warm-4096-240-r1` | 24/24 | 5/24 | 131.816s | 4096 | before/after digests unchanged |

Gemma model-only screen conditions match the Llama baseline: dataset, 24 sample refs, fixed history, prompt/profile/schema snapshots, context 4096, temperature 0.2, token ceiling 256, serialized JSON ceiling 16384, dialogue ceiling 240, warm condition, and one repetition. The model identity/quantization differ as intended. Gemma used 8,049,225,890 reported resident bytes versus Llama's 5,003,804,671; wall time was 25.569s longer for 24 turns. Per-request latency (all 24 generated outputs; nearest-rank p95): Llama p50 3.730s / p95 8.920s, Gemma p50 5.294s / p95 7.603s. These are single-run descriptive measurements. Cutoff counts are operational only, not semantic scores or a winner.

| Prompt variant | Run ID | Directory | Valid outputs | Cutoff-suspected | Wall time | Active context | Per-request p50 / p95 |
|---|---|---|---:|---:|---:|---:|---:|
| updated_profiles | `ebaab7fc-bb20-44e6-ad9d-d5cf0ad92753` | `runs/llama3-updated-profiles-focused24-fixed-warm-4096-240-r1` | 24/24 | 17/24 | 82.709s | 4096 | 3.233s / 4.726s |
| improved_guidance | `e318e60a-83a4-421e-abbd-770c26f2cef2` | `runs/llama3-improved-guidance-focused24-fixed-warm-4096-240-r1` | 24/24 | 20/24 | 90.898s | 4096 | 3.947s / 5.077s |

### Closed-loop focused runs

Each model was run on the same 24 scenarios, feeding its generated prior replies into later turns. Both produced 24/24 valid JSON outputs with unchanged before/after state digests. Llama t04: run `af16b03b-0bec-4c8e-a936-e3d0eba963cb`, 17/24 cutoff-suspected, wall 83.766s, request p50/p95 3.502s/4.032s. Gemma t04: run `400fb159-6255-4949-9565-2d54e7e8637f`, 2/24 cutoff-suspected, wall 183.686s, request p50/p95 7.391s/11.613s. The closed-loop condition intentionally changes history and is not pooled with fixed-context results. These are single-run operational/behavior samples; no human scores or adoption conclusions.

No human review scores have been entered.

### Llama 3 full fixed-context baseline (44 scenarios / 176 turns)

| Run ID | Directory | Valid outputs | Missing/errors | Cutoff-suspected | Wall time | Active context | Request p50 / p95 | State |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `3b0ebc0a-8ca0-4891-ad8e-6183359ac9d1` | `runs/llama3-t04-full176-fixed-warm-4096-240-r1` | 176/176 | 0 | 52/176 | 573.620s | 4096 | 3.144s / 4.998s | unchanged |

The run uses the exact baseline frozen dataset (`a76b3c…f427e3bc`), t04 prompt/profile/schema hashes, temperature 0.2, 256-token generation ceiling, 16,384-character JSON ceiling, 240-codepoint dialogue ceiling, fixed context, and warm condition. The six original scoring joins are complete at their frozen denominators: directness 44, coverage 12, continuity 16, character consistency 44, grounding 44, naturalness 88. No blind form has been human-scored. Cutoffs and valid JSON are operational signals only; quality acceptance is pending review.

### Llama 3 full fixed-context prompt variants (44 scenarios / 176 turns)

| Variant | Run ID | Directory | Valid | Missing/errors | Cutoff-suspected | Wall time | Request p50 / p95 | Context |
|---|---|---|---:|---:|---:|---:|---:|---:|
| updated_profiles | `2b0222dd-b758-4bd4-a9de-314fd15d0933` | `runs/llama3-updated-profiles-full176-fixed-warm-4096-240-r1` | 176/176 | 0 | 108/176 | 584.448s | 3.262s / 4.823s | 4096 |
| improved_guidance | `d049261c-bd35-4e41-ba64-07ae873a4ec3` | `runs/llama3-improved-guidance-full176-fixed-warm-4096-240-r1` | 176/176 | 0 | 82/176 | 651.429s | 3.807s / 5.043s | 4096 |

These are paired prompt-only runs on the same Llama digest, baseline replay histories, fixture/sample refs, generation parameters and hardware. Relative to t04 (52/176 cutoffs, 573.620s wall, p50/p95 3.144s/4.998s), updated_profiles had 108/176 cutoffs, 584.448s wall, p50/p95 3.262s/4.823s; improved_guidance had 82/176 cutoffs, 651.429s wall, p50/p95 3.807s/5.043s. Both variants have more cutoff-suspected replies; improved_guidance is also slower. The cutoff/latency signals are operational comparisons, not semantic quality scores. Each run retains all six exact denominators. No variant is adopted pending blind human review.

Direct structured proposal adapter outcomes are documented in [`structured-adapter-screen.md`](structured-adapter-screen.md). The complete enabled durable route remains unavailable under current local settings.

### Full Llama repeatability runs

After the user waived human reviews on 2026-10-20, each of the three full 176-turn fixed-context Llama prompt variants was repeated once with all controls matched to repetition 1. All six frozen scoring denominators remain exact in both repetitions; none were scored by humans. See [`repeatability-comparison.md`](repeatability-comparison.md) for run IDs, latency quantiles, resource measurements, and interpretation. The repeats all generated 176/176 with unchanged state digests. Cutoff-suspected counts by variant were t04 52/67, updated_profiles 108/106, and improved_guidance 82/83 across repetitions 1/2. No prompt winner or semantic gain is inferred.

Additional direct structured Llama stages screened on 2026-10-20 against the frozen `t05-valid.json` context fixture. Reusable command: `.venv/bin/python docs/evidence/llm-response-improvement/screen_structured_stages.py --output docs/evidence/llm-response-improvement/runs/llama3-structured-stages-screen-r{1,2,3}.json` (run separately with each output path, local loopback via approved elevated route). Results: composition and repair each returned typed one-segment `CandidateReply` on all three runs; proposal returned a one-segment `TurnProposal` on r2/r3 and `GenerationMalformed` on r1. The r1 process exited 1; r2/r3 exited 0. Records pin Llama digest/quantization and preserve safe failure categories. These isolated stage checks do not replace live full application integration.
