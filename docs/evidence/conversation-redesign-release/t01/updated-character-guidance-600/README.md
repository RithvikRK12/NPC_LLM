# Updated character guidance replay

This is a separate measurement replay of the frozen `baseline-evaluation-v1` fixture using the same fingerprint-verified `llama3:latest` model, temperature, and 600-character dialogue ceiling as T05. The prompt now includes `context/T04`'s topic-selected compact profile for each NPC and the shared anti-repetition direction. The results and forms include the guidance digest and source profile hashes.

## Human review

Use `human-calibration-reviewer_1.json` and `human-calibration-reviewer_2.json` for two independent reviews of these outputs. Each file contains 24 samples across the same six quality dimensions. Reviewers should score each sample from 1–5 using its displayed anchors, enter a short note only where useful, and return their completed JSON without discussing scores first. These forms are for the updated character-guidance replay only. Do not copy scores from the earlier pre-update form or from the T05 output-limit replay.

## Replay verification

- 44 scenarios / 176 generated turns; no provider errors.
- Initial and final read-only state digest match: `181dbe28b6d31e38ab69ef8e0fb3975d552ac18610c0baf463d9ab8d5f4ff24a`.
- Denominators: directness 44, coverage 12, continuity 16, character consistency 44, grounding 44, naturalness 88.
- Turn latency: p50 4.60 s, p95 8.24 s.
- Output ceiling: 600 characters; 13 replies reached the cap, and 12 of those 13 did not end with sentence-final punctuation. Treat them as likely cutoffs during review; the replay has measured the cap but has not solved it.
- Prompt function hash: see `prompt_template_sha256` in `configured-replay-results.json`; profile source and shared-direction hashes are included in `character_guidance` there and in both reviewer forms.

The exact invocation was `PYTHONPATH=backend .venv/bin/python docs/evidence/conversation-redesign-release/t01/configured_replay.py --updated-character-guidance-600` from the repository root. The replay is measurement evidence and does not select a shipping model or dialogue limit.
