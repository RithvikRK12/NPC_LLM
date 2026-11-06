# Current-turn, grounding, and 600-character replay

This separate replay applies `context/T05` prompt guidance to the frozen 44-scenario / 176-turn fixture. It keeps the T06 `llama3:latest` model, settings, and 600-character policy constant. The guidance asks NPCs to answer the current player turn first, avoid unrequested recaps, use prior NPC speech only as conversation context, and ground activity or mechanic claims in supplied current facts and capabilities. It retains the existing character profiles and game mechanics.

## Human review

Reviewer 1 has completed 24/24 scores in `human-calibration-reviewer_1-completed.json`; Reviewer 2 can use `human-calibration-reviewer_2.json` for an independent review of this same replay. Score each sample using the displayed 1–5 anchors. The completed form matches all 24 replay candidates and the replay provenance. The paired one-reviewer comparison is summarized in [reviewer-1-analysis.md](reviewer-1-analysis.md); do not treat it as independent reviewer agreement.

## Replay results

- 176/176 turns generated; no provider errors.
- Frozen fixture SHA-256: `a76b3c16c8be6a535af708544ad5c1ea9b3fcb7ef27ef06524c56b63f427e3bc`.
- Initial/final read-only state digests match: `181dbe28b6d31e38ab69ef8e0fb3975d552ac18610c0baf463d9ab8d5f4ff24a`.
- Denominators unchanged: directness 44, coverage 12, continuity 16, character consistency 44, grounding 44, naturalness 88.
- Turn latency: p50 4.55 s, p95 8.45 s.
- Ceiling remains 600 characters. Four replies reached 600, and all four lacked sentence-final punctuation. This is down from 13 cap hits in T06, but those four remain likely cutoffs.
- A raw exact-adjacent-repeat check counted 21 cases, compared with 17 in T06. This count includes reminder answers and repeated fixture stress turns, so it does not isolate unwanted repetition. Reviewer scoring is needed to assess whether current-turn focus improved in natural conversation.
- The output, model, profile, shared direction, and policy hashes are recorded in `configured-replay-results.json` and the reviewer forms. Reviewer 1’s scores show a mixed result: continuity increased from 2.75 to 4.00 on the same 24 sample references, while the overall mean decreased from 4.00 to 3.29. This remains a single reviewer’s assessment.

The exact invocation was `PYTHONPATH=backend .venv/bin/python docs/evidence/conversation-redesign-release/t01/configured_replay.py --improved-character-guidance-600`. This is measurement evidence; it does not select a production model or raise the dialogue ceiling.
