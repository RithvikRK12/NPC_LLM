# Final local pilot screen — 2026-10-20

This is a ten-turn functionality screen against the real enabled application and local Llama transport in a temporary SQLite world. It is not the frozen 44-scenario semantic benchmark. All ten submissions finalized, partitioned complete dialogue into beats, and returned byte-equivalent JSON on exact identity retry. Both deliberate provider outages returned classified fallback and no receipt. Three explicit actions each committed exactly one receipt. Ordinary messages did not change inventory.

The final screen used `llama3:willowbrook` (same installed Llama 3 weights), temperature 0.2, 8192 context, 2048 generation tokens, 16384 JSON characters and 600 dialogue characters. Model digests/settings are in `live-route-summary.json`; messages/origins are in `live-route-samples.json`. Earlier runs are preserved in `pre-social-schema/` and `pre-personal-ease-fix/`.

| Route | n | p50 seconds | p95 seconds |
| --- | ---: | ---: | ---: |
| action | 3 | 17.1044 | 19.1794 |
| ordinary | 4 | 14.6607 | 16.2909 |
| provider_outage | 2 | 0.0746 | 0.0821 |
| purpose_question | 1 | 0.0453 | 0.0453 |

Three of four ordinary samples returned generated dialogue; one returned a safe INTERNAL_FAILURE fallback (25% ordinary fallback in this small screen). All three action narration attempts fell back to exact server-rendered receipt speech. The deterministic purpose question is separately classified; outages and intentional mechanical repeats are excluded from any healthy-language quality claim. No repair samples were measured. These figures do not meet or establish the <5% release fallback threshold, and no semantic quality percentages are available. The user waived human scoring; this does not waive or prove numerical shipping quality.

**Decision:** local playtest ready; broad release gate T03 remains open. Do not infer product acceptance of 14–20 second provider turns. No new model was selected, no human scores were invented, and no legacy receipt-unaware route was used to repair a pending turn.

Reproduce: `PYTHONPATH=backend .venv/bin/python docs/evidence/conversation-redesign-release/t03/run_live_acceptance.py` with local Ollama available. It never uses the personal save.
