# Conversation memory retrieval evidence

Run date: 2026-10-20

## Environment brought online

The local Ollama binary and `llama3:willowbrook` / `nomic-embed-text:latest` models were already installed. The service was running, but sandboxed commands could not access its localhost API. With approved local access, the configured endpoint responded normally.

Godot was absent, so Godot 4.7.2 was installed with Homebrew. PostgreSQL client/server tools were absent, so PostgreSQL 18.6 and pgvector 0.8.7 were installed. Acceptance checks used a separate, trust-authenticated cluster under `/private/tmp/npc-faiss-postgres` on port 5433; it never used the app database or personal save. The temporary cluster and default PostgreSQL service were stopped after verification. Godot and PostgreSQL tooling remain installed.

## Paired local Llama trial

Run `PYTHONPATH=backend:backend/tests .venv/bin/python docs/evidence/conversation-memory-retrieval/run_paired_live.py` to repeat the disposable experiment. The runner uses a fresh temporary SQLite world for each condition and never opens the personal save.

The same source statements, intervening turn and memory-recall question ran for Craftsman and Gatherer under retrieval off, retrieval on, and an embedding endpoint outage. Each NPC had 20 attributed memories sourced from a finalized player turn. The source turn was outside the one-turn visible-history window. Each condition used an identical 2,000-token context budget, 256-token generation reserve, 240-character output limit and 120-character beat limit; model and generation settings were unchanged between conditions.

Results are in [paired-live-results.json](paired-live-results.json). Both queries reached Llama in all three conditions. FAISS produced 40 reusable vectors (20 per NPC) and ranked the target preference first in both provider prompts. Deterministic retrieval-off and embedding-outage prompts placed it twentieth. The outage logged `degraded` and both NPCs still returned generated dialogue. The captured semantic answers framed the preference as what the player had told the NPC.

This is one controlled memory-recall scenario across two NPCs, not a broad dialogue-quality evaluation. Every mode included the memory in the prompt, and all six target-query replies used identical wording even though the target ranked first with FAISS and twentieth off/outage. That verifies production wiring and ranking order, but shows no user-visible difference in this sample. In some captured turns the NPC repeated the previous answer when asked a different personal question; that remains a dialogue-quality issue to investigate. The local retrieval switch remains `false` pending larger paired cases covering promises, completed inspection, mechanical-state conflicts, corrections/retractions and human review.

## Additional verification

- Full backend suite: 1,173 tests passed.
- Seven isolated PostgreSQL acceptance runners passed against disposable `npc_test_*` databases.
- Godot 4.7.2 `conversation_gateway_smoke`, `craftsman_post_inspection_smoke`, and `gatherer_integration_smoke` passed. The Craftsman regression passed after correcting prompt/schema token accounting.
- The existing temporary-world local Llama pilot passed ordinary questions for both NPCs, bow/gift/wood routes, exact retry behavior, and real provider-outage fallback.
- No personal save was reset or modified.

The context estimator now counts serialized prompt text and a bounded 128-token structured-output control reserve. Ollama's JSON schema travels separately in `response_format`; charging its entire schema serialization as model prompt tokens caused false context-budget overflows. Token counting remains a lexical estimate, not an exact Llama tokenizer count.
