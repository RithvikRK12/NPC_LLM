# Llama full fixed-context repeatability comparison

Date: 2026-10-20. Two repetitions per prompt variant; 44 scenarios / 176 turns each. This compares operational outputs only. Human review was waived by the user, so no semantic scores, score-to-pass mapping, quality pass rate, or prompt winner is claimed.

## Controls and denominators

All pairs match on model tag/digest/quantization, dataset and ordered sample refs, context and schema hashes, active context 4096, temperature 0.2, generation ceiling 256 tokens, serialized JSON ceiling 16,384 characters, dialogue ceiling 240 code points, provider version, and warm condition. Only repetition, run ID, prompt/profile snapshot for the variant, and generated outputs differ. `seed` is unsupported/unset. Each run reports the same initial and final state digest.

Every run retains the frozen six scoring denominators:

| Dimension | Denominator per run |
|---|---:|
| Directness | 44 |
| Coverage | 12 |
| Continuity | 16 |
| Character consistency | 44 |
| Grounding | 44 |
| Naturalness | 88 |

## Results

| Prompt variant | Repeat | Run ID | Generated / missing | Cutoff-suspected | Wall seconds | Request p50 / p95 seconds | Resident bytes | Active context |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| t04 | 1 | `3b0ebc0a-8ca0-4891-ad8e-6183359ac9d1` | 176 / 0 | 52 | 573.620 | 3.144 / 4.998 | 5,003,804,671 | 4096 |
| t04 | 2 | `2559ad5c-11fa-42a8-ba62-23e4aff35283` | 176 / 0 | 67 | 438.968 | 2.531 / 3.688 | 5,003,804,671 | 4096 |
| updated_profiles | 1 | `2b0222dd-b758-4bd4-a9de-314fd15d0933` | 176 / 0 | 108 | 584.448 | 3.262 / 4.823 | 5,003,804,671 | 4096 |
| updated_profiles | 2 | `9c3d1a88-6a5f-41d6-8f50-34aad97d8489` | 176 / 0 | 106 | 626.991 | 3.614 / 4.731 | 5,003,804,671 | 4096 |
| improved_guidance | 1 | `d049261c-bd35-4e41-ba64-07ae873a4ec3` | 176 / 0 | 82 | 651.429 | 3.807 / 5.043 | 5,003,804,671 | 4096 |
| improved_guidance | 2 | `96b5c67c-04e0-4f72-bf5f-6ba810b1b491` | 176 / 0 | 83 | 784.742 | 4.484 / 6.565 | 5,003,804,671 | 4096 |

Latency quantiles are recomputed from each run's `elapsed_seconds` values for all 176 generated requests; p50 is the median and p95 uses nearest-rank. Model resident size is Ollama's measured model allocation, not total system memory. Python runner peak RSS was 48,709,632 platform units for t04 repeat 2, 48,447,488 for updated_profiles repeat 2, and 48,513,024 for improved_guidance repeat 2; the platform unit is bytes on this host. Warm means model was already loaded; no cold-start latency is measured here.

## Interpretation and limits

- All six runs completed 176/176 with no missing/provider errors and unchanged state digests.
- Cutoff-suspected counts varied between repeats: t04 52→67, updated_profiles 108→106, improved_guidance 82→83. The prompt variants do not show a stable operational advantage over t04 on this signal; t04 repeat 2 was lower, but repeat 1 was slower than repeat 2. Cutoff suspicion is not a semantic quality score.
- Request latency varied across runs. Improved_guidance repeat 2 was the slowest (p50 4.484s, p95 6.565s, 784.742s total). Repetition and machine load may contribute; two runs do not establish a stable route latency distribution.
- Local model memory was constant at 5,003,804,671 bytes and active context 4096. No model upgrade or download occurred.
- The user waived human reviews. The blind forms remain unscored and are retained as provenance artifacts. No response-quality improvement, acceptance threshold, or winning prompt is asserted. Keep the existing prompt/configuration pending the enabled structured application route and explicit product acceptance of observed latency/readability.

## Non-scored artifact spot checks

These are concrete examples observed by the implementation agent, not human review or a substitute score. In both `improved_guidance` repeats, `gatherer-04:t2` recalls “quiet attentive company”; baseline t04 instead repeats the fruit-stash answer, while both variants correctly answer the explicit later fruit recall control at `gatherer-04:t3`. The improved Craftsman rope follow-up `craftsman-02:t3` says to wait because the rope's purpose is unknown, but both runs are cutoff-suspected. Grounding remains unresolved: improved-guidance repeat 2 invents a rain forecast for `craftsman-01:t3` and a recent wild-animal incident for `gatherer-01:t3`. Full examples and the candidate direction are documented in [`../../llm-response-improvement/candidate-guidance.md`](../../llm-response-improvement/candidate-guidance.md).

## Per-run artifacts

Each run's immutable manifest, outcomes (including missing-output slots), prompt snapshots, scoring samples, and blind forms are in `runs/llama3-{variant}-full176-fixed-warm-4096-240-r{1,2}/`. The runner command shape and pinned parameters are recorded in the manifests; repeat 2 used the same CLI controls with `--repetition 2` and new output directories.

## Focused cold-load measurement

After explicitly unloading the installed Llama model, the same dialogue runner ran the 24-turn focused t04 fixed-context set. Run ID `f3c9b3e6-f363-4611-9680-d2ff625e7e19`; 24/24 generated, zero missing/errors, 16 cutoff-suspected, wall 65.247s, before/after state digests unchanged. The first request (`craftsman-01:t1`) took 5.739s including model load and inference. The remaining 23 requests were warm, median 2.703s, maximum 3.205s; all-request p50/p95 were 2.731/3.205s. Ollama reported 5,003,804,671 model bytes resident (all in VRAM) and active context 4096. This is one cold-start observation plus a 23-request warm sample, not a stable latency distribution or complete-turn measurement. The model was reloaded by the run and remains installed.

Command: `PYTHONPATH=backend:backend/tests .venv/bin/python docs/evidence/llm-response-improvement/run_experiment.py --selection smoke --mode fixed_context --prompt-variant t04 --endpoint http://127.0.0.1:11434/v1 --model-tag llama3:latest --model-digest 365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1 --quantization Q4_0 --context-size 4096 --generation-limit-tokens 256 --serialized-contract-limit-characters 16384 --dialogue-limit-codepoints 240 --condition cold --repetition 3 --blind-label G --output-dir docs/evidence/llm-response-improvement/runs/llama3-t04-focused24-cold-warm-4096-240-r3 --timeout-seconds 180 --hardware-description 'Apple M5, 16 GB unified memory; model unloaded before first request'` — exit 0.

The three full repetition-2 commands shared the same controls and used `--selection full --mode fixed_context --condition warm --repetition 2 --timeout-seconds 120`; variants/output directories/labels were `t04` / `llama3-t04-full176-fixed-warm-4096-240-r2` / D, `updated_profiles` / `llama3-updated-profiles-full176-fixed-warm-4096-240-r2` / E, and `improved_guidance` / `llama3-improved-guidance-full176-fixed-warm-4096-240-r2` / F. Each included the same endpoint, pinned Llama tag/digest/Q4_0, context 4096, 256-token generation limit, 16,384-character JSON limit, 240-codepoint dialogue limit, and Apple M5 / 16 GB hardware description. All three commands exited 0.
