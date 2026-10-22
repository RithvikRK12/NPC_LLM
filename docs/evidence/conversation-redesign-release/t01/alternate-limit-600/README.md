# Alternate output-limit replay: 600 characters

This is the measurement-only output of `evaluation-release/T05`. It uses the frozen 44-scenario / 176-turn fixture and the same fingerprint-verified configured model as the 240-character baseline. The only replay-policy change is the ordinary-dialogue JSON schema ceiling: 240 → 600 characters. The existing 600-character story-request ceiling is unchanged. No production limit is approved by this experiment.

## Replay evidence

- Fixture: `npc-conversation-baseline-evaluation-v1`, SHA-256 `a76b3c16c8be6a535af708544ad5c1ea9b3fcb7ef27ef06524c56b63f427e3bc`
- Model: `llama3:latest`, Ollama 0.34.2, manifest digest `sha256:365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1`
- Generated: 176/176 turns; 44 scenarios; 0 provider fallbacks/errors
- State digest: unchanged (`181dbe28b6d31e38ab69ef8e0fb3975d552ac18610c0baf463d9ab8d5f4ff24a`)
- Latency: p50 2.535 s; p95 4.606 s
- Reply lengths: maximum 536 characters; 0/176 reached 600
- Scoring denominators: directness 44, coverage 12, continuity 16, character consistency 44, grounding 44, naturalness 88
- Replay-policy SHA-256: `4716d57fdad98ea50dddc981e34fef9d28ce562a874515319a113cce8e6be97d`

## Human review steps

Two people should review independently. Give one person `human-calibration-reviewer_1.json` and the other `human-calibration-reviewer_2.json`. Before submitting, reviewers should not discuss scores.

Each form has the same 24 candidate samples (four for each dimension, balanced across Craftsman and Gatherer). For every sample, enter an integer `score` from 1 (poor) to 5 (strong) using only that row's dimension-specific `anchors`. Use `review_notes` for a short reason or uncertainty. Score the NPC reply shown in `candidate_dialogue` in light of `player_input` and `prior_visible_dialogue`; do not infer gameplay effects beyond the displayed evidence. Save and return the completed JSON form without changing sample text, anchors, or replay metadata.

After both forms are returned, compare scores by `sample_ref` and dimension. Record disagreements and any agreed rubric clarification separately; keep both original score files unchanged. These reviews calibrate the measurement rubric. They do not by themselves select a production output limit or approve release quality.

## Files

- `configured-replay-results.json`: turn-level output, latency, provider origin, fixture/model fingerprints, unchanged state digests, denominators, and replay-policy identity.
- `quality-samples.json`: denominator-preserving rows for all six scoring dimensions.
- `human-calibration-template.json`: combined calibration template.
- `human-calibration-reviewer_1.json` and `human-calibration-reviewer_2.json`: independent, blank scoring forms.
