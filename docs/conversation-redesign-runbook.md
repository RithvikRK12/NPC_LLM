# Conversation redesign: local playtest and rollback

Updated 2026-10-20 (Asia/Kolkata). Local playtest is the adoption target; numerical production dialogue-quality targets are a separate, unaccepted release gate. The user's human-scoring waiver and Llama preference were already recorded in `llm-response-improvement/runbook.md`; no reviewer scores were invented.

## Play

Double-click `Play.command` in the repository, or run `./Play.command` from Terminal. It uses the existing `.venv`, starts the backend on 127.0.0.1:8000, imports assets and opens Godot. It refuses to reuse an occupied port. Closing the game normally saves the world; the launcher then stops its own backend.

The backend runs from `backend/`, so the existing `.env` setting `sqlite:///./mvp.db` resumes `backend/mvp.db`. Nothing resets or deletes that save. A configured absolute SQLite or PostgreSQL URL in `.env` remains effective. Use the game's confirmed Restart Game action only when you want a fresh run. Do not point acceptance runners at this save.

Godot resolves from `GODOT_BIN`, `/Applications/Godot.app`, `~/Downloads/Godot.app`, then `godot` on PATH. This machine has Godot 4.7.2 in Downloads. Start Ollama first if it is not running. The playtest explicitly uses local Ollama structured output and Llama 3. `config/Modelfile.playtest` creates `llama3:willowbrook`, reusing installed `llama3:latest` weights with 8192 context; it does not replace the original tag or download a different model. A missing alias is created by the launcher.

WASD moves, E inspects/talks/uses doors, F picks up, I opens the bag, Esc opens the menu. L skips the opening. The controls card must be dismissed before walking. Both the bow quest and Craftsman's wreck inspection are playable. Reporting the wreck offers an inspection; accepting with `yes`, `follow me`, or a natural affirmation such as `Sure! That would be helpful.` automatically closes chat and shows the animated “Lead the Craftsman to the boat.” objective. The prompt docks in the corner, stays nonblocking, and completes on arrival. Accepting the Gatherer’s forest help choice shows “Help the Gatherer defeat both boars.” with the same objective animation; its checkmark plays when both boars die. Declining shows no objective. Retrying clears it until help is chosen again. A Way Home still ends at material gathering, as documented in README; ship repair/sailing/ending are outside this conversation redesign.

## Explicit pilot bounds

`config/playtest.env` selects policy `local-playtest-v1`: 500 input characters; 600 complete reply characters; readable beats of 300; 8192 context budget; 2048 generated tokens; 16384 serialized output characters; 60-second provider stages; 180-second complete turn deadline; 240-second leases; eight queued turns per NPC; two workers; one-second HTTP delivery wait; summary trigger 20 turns; diagnostic retention policy seven days. Cold model/context processing can take tens of seconds. These are provisional pilot limits, not product acceptance of latency, language quality or retention enforcement.

Speaker generation withholds undisclosed ship state and capabilities until the Craftsman receives the wreck report. Plain greetings use a compact voice-only projection and remain model-generated. The original authoritative context remains available to deterministic game checks. See `evidence/conversation-redesign-release/greeting-knowledge/` for the fresh-save regression and measured greeting latency.

Composition, repair and bounded social conversation use a strict provider-only `SpeechDraft` containing `dialogue`. The server constructs provenance, policy metadata and structural references before strict public-contract validation. Canonical action receipts are appended by the assembler, with their length reserved in the provider speech budget. Non-social semantic proposals keep their typed contract. See `evidence/conversation-redesign-release/validation-contract/` for the exact rejection, final wire format and fresh live matrix.

Prompt v9 routes whole-message gratitude through dialogue-only generation, projects completed inspection separately from the damaged hull and unfinished repair, and avoids feeding old offer transcripts into acknowledgements. Narrow validation findings catch perspective reversal, copied offers, inspection reoffers and false repair completion; speech repair receives those findings. See `evidence/conversation-redesign-release/post-inspection-dialogue/` for live generated variants, real provider correction, and full post-inspection game verification.

The compact prompt excludes redundant server fingerprints and, for schema-capable transport, does not repeat the full response schema in the system message. The provider schema restricts operations to the offered command/argument shapes. All output still passes the strict public decoder and game rechecks. Existing deterministic request parsers adapt explicit bow/item/Craftsman requests; generated guesses cannot authorize a different action. Stock requests persist an exact purpose question before transfer. Gifts use the same durable request identity as chat.

## Mechanical verification

See `evidence/conversation-redesign-release/t02/` for logs and the §5.4/§8 coverage map. Backend tests use temporary SQLite. PostgreSQL runners create only `npc_test_*` databases and remove them. `run_godot_checks.py` copies the client and fixtures, reserves port 8001, uses a temporary SQLite world, and gives each test a separate client cache. Never start a personal backend on port 8001 for these runners.

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
PYTHONPATH=backend CONVERSATION_TEST_ADMIN_URL=postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/postgres \
  .venv/bin/python docs/evidence/conversation-redesign-release/t02/run_postgres_checks.py
.venv/bin/python docs/evidence/conversation-redesign-release/t02/run_godot_checks.py
```

Godot integration checks permit bounded cold provider processing; this does not turn their timeouts into a latency-quality claim. The API/client checks include real durable reply delivery, inventory/quest revision envelopes, clear sequence continuation, confirmed stock transfer, gifts, crafting, save/reload, and room/encounter state.

## Staged adoption

Only this local pilot is enabled by `Play.command`. Ordinary manual backend launch reads `backend/.env`/Settings defaults. This Mac’s ignored `.env` is now configured with the same local pilot values after a terminal launch without them caused NPC chat 503s. Fresh checkouts must still explicitly export `config/playtest.env` as described in README; global defaults remain disabled. Keep both NPCs in the same explicit policy cohort. Before widening adoption, run the frozen evaluation on the final prompt/model configuration, preserve all six denominators, and demonstrate relevance ≥90%, mixed coverage ≥90%, canon consistency ≥95%, healthy-provider fallback <5%, accidental repetition <2%, and accepted route latency/readability. Human scoring was waived; it is not evidence these thresholds passed. Generated canon remains fail-closed without a trusted semantic claim producer. No broad release is approved by this handoff.

## Receipt-safe rollback

1. Close the game normally and let the launcher stop the backend. Preserve the database and all conversation tables. Do not clear/reset as a rollback technique.
2. Keep **every** policy setting from `config/playtest.env`, changing only `CONVERSATION_ENABLED=false`. For a terminal-only maintenance run, source/export the profile, override that flag, and run uvicorn from `backend/`. Do not use Play.command during maintenance; it selects the enabled pilot profile again.
3. Startup resumes pending streams. The periodic worker scan revisits recoverable queues and expired leases; status GET remains read-only. New versioned identities receive 503, while existing identities remain replayable. A committed receipt is recovered before any attempt to execute. Committed effects are never reversed or executed again. Generated canon may remain stored but inactive.
4. Verify `/health` and inspect pending counts using a read-only query against the selected database. Do not omit policy while any admitted work remains. The application deliberately rejects startup if pending turns exist without the complete policy.
5. Re-enable only after recovery/receipt tests and the desired cohort checks pass. Restore the enabled profile and relaunch the game. Scope/epoch invalidation suppresses obsolete delivery; durable request IDs survive ordinary client restarts.

The deterministic suite exercises rollback of new admission, recovery of a committed receipt with generation disabled, exact final HTTP replay, and provider-failure fallback. Local pilot authorization does not authorize a shared deployment, database deletion, schema downgrade, or automatic model replacement.
