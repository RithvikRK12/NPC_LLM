# Fresh-save greeting: undisclosed ship knowledge

2026-10-20. User reproduction: restart the save, approach the Craftsman and say `hello`. The original saved turn was sequence 1 in the current scope, with no earlier chat, no receipt and `wreck_reported=false`. It made one provider proposal attempt; the generated expressive segment incorrectly offered to help with the player’s ship inspection. The game reset was successful. No personal save data was copied into these evidence artifacts or altered by the diagnostic read.

## Cause and change

The provider received all mechanical facts and command descriptors, including the global ship-repair quest recipe and inspection capabilities. The old prompt called those supplied facts authoritative but did not distinguish game availability from facts learned by the character. The generated free prose had no cited mechanical slot, so structural validation did not catch the assumed shared knowledge. Passing mechanical tests had not established this narrative boundary.

`prompts/knowledge.py` now projects speaker-facing context separately from the authoritative packet. Before the Craftsman has received a wreck report, ship activity/quest data and related capabilities are withheld from proposal generation. The original packet is retained for deterministic request authorization, revision checks and execution. Reporting the wreck still uses the existing deterministic durable command; subsequent contextual questions can use the learned state.

Whole-message greetings receive a compact voice/profile projection, no mechanical catalog, and a constrained subset of the same proposal contract. The reply remains model-generated and passes the existing strict decoder. Mixed greetings containing an action request retain ordinary context. No canned greeting, model substitution or decoder relaxation was introduced. The prompt version is `conversation-prompt-v7`.

## Verification

Five new behavioral regression tests reproduce the source leak and verify unknown/known state, immutable authority context, the greeting schema and mixed-message routing. Red and green logs are retained. Full backend: **1,134 tests pass**, exit 0. No schema/storage/client code was changed by this fix, so the previous PostgreSQL and Godot gate results are historical evidence rather than claimed fresh reruns.

Four fresh-world turns used real local Llama (`llama3:willowbrook`), the normal enabled application and temporary SQLite worlds. Every turn returned generated speech, zero game effects, no ship/inspection or prior-acquaintance assumption, and identical exact retries. Provider usage and measured timings are in `live-samples.json`. The scripted assertions are supporting checks, not a semantic quality benchmark.

Measured end-to-end greetings: **5.34–6.79 seconds**. The Craftsman’s `hello` reply was: “Ah, hello there! Nice to meet you. What brings you to our village today?” Prompt usage was 292 tokens for that call; provider time was 6.69 seconds. This improves this small greeting sample relative to the user-reported roughly 15 seconds; it does not prove ordinary dialogue latency is solved.

The original incorrect line remains in the user’s historical transcript; this fix does not rewrite accepted history, clear conversations or reset the save. The local game was saved/closed normally and relaunched to activate the updated backend, preserving the same scope and workshop location. All acceptance requests were run against disposable worlds.

Reproduce: `PYTHONPATH=backend .venv/bin/python docs/evidence/conversation-redesign-release/greeting-knowledge/run_live.py`.
