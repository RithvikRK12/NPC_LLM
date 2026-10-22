# Conversation redesign baseline: current contracts and authority

Task: `baseline/T01`, inspection on 2026-10-14. Source revision: `83af36d1541fce21a546b058ef69df591741ec7a`, branch `master-progress`. This is an inventory of existing behavior, not verification of redesigned runtime modules. No application was started, provider contacted, player database opened, or runtime source changed. Numeric values below describe current source defaults; they are **not shipping policy recommendations**.

Reproduce with `.venv/bin/python docs/evidence/conversation-redesign-baseline/inspect_inventory.py` from repository root. [Manifest and exit codes](evidence/conversation-redesign-baseline/inspection-manifest.json), [numbered source snapshot](evidence/conversation-redesign-baseline/source-snapshot.txt), [limit search](evidence/conversation-redesign-baseline/inspection-05.txt), [writer search](evidence/conversation-redesign-baseline/inspection-06.txt), and [test inventory](evidence/conversation-redesign-baseline/inspection-07.txt) preserve the inspection. Source snapshots intentionally exclude `.env`, credentials and databases.

Read scope: baseline packet T01; Proposal §§2,16,19,21; Detailed design §§9–10; master shared implementation rules. Earlier diagnosis does not supersede current source: current Craftsman permits selected 600-character stories and Gatherer already has an encounter-aware fallback, while Gatherer prompt character data is still `{}`.

## Live HTTP and ordinary path

`api/routes/chat.py:chat` accepts `ChatRequest`, injects `ConversationPipeline` through `api/deps.py`, calls `chat(npc_id, player_message, game_scope)`. Missing NPC/player becomes 404; stale game/conversation/encounter becomes 409. No submission/status endpoint, durable admission queue, client turn ID or receipt-based chat retry exists here.

Ordinary example by inspection: Craftsman, no pending item, `Hello` (opening/encounter permits chat). `services/pipeline.py:chat` reads Player 1 and NPC, checks optional game scope and Gatherer gate, records `memory_revision`, builds context/prompt and Craftsman intent, then rolls back the read transaction. With no interception it calls `LLMService.generate`; a configured base URL selects `OpenAICompatibleProvider`, otherwise `MockLLMProvider`. Provider/decode exceptions become empty JSON plus a diagnostic generation status. It then locks Player, checks scope, CAS-updates the NPC memory token to a decision UUID, locks/reloads NPC, rechecks encounter eligibility, and refreshes inventory/quest/facts from current state. Grounded handlers run first even after generation. Otherwise validator constructs a speak proposal, conditioning and final control validation run, behavior selector runs, and `StateService.apply` applies accepted output. Rejected output takes a zero-effect snapshot. Conversation is flushed, accepted memory is stored, diagnostics assembled, and pipeline commits; post-commit memory retrieval and response assembly follow.

Important transaction boundary: pre-generation context may retrieve/query-embed memories; `MemoryService.store_memory` may embed while the post-generation transaction holds the player writer lock. This is existing coupling, not conformance to the redesign prohibition on provider/embedding under transactions. Post-commit retrieval can also call embeddings and delay response after effects are durable.

`ChatResponse` contains game_scope, NPC snapshot, structured output and final_dialogue, player inventory, legacy quest status/progress, bow quest, Craftsman encounter/ship repair, memories and grounding/behavior/decision/classification traces. `StructuredNPCOutput` carries legacy intent/emotion/action/item/reasoning/state_update and fact IDs. Neither HTTP response model bounds dialogue length; response contains no conversational epoch, per-resource inventory/quest revision, stable chat turn ID, beats or operation receipt. Gatherer encounter is provided by `/world` and its command endpoint, not the chat response schema.

## Action path and deterministic rule owners

Transfer example by inspection: Gatherer has wood, player says `give me wood`, no pending request. `requested_transfer` recognizes exactly one supported item, causing generation bypass. Under the writer lock `transfer_answer` checks current ownership and produces `confirm_transfer`/`ask_question`; `StateService.apply` persists `npc.pending_item='wood'`. On subsequent `I need it for a bow`, pending-item interception again bypasses generation, broad purpose matching selects the pending wood, final control rechecks ownership and StateService removes one wood from NPC and appends one to Player, clears pending, and updates legacy Quest active/progress at least 50. The pipeline records before/after counts and commits conversation/memory with effects. This is an illustrative path, not a newly executed behavioral test. Pending unrelated text containing purpose words can still enter this route; no exact consent binding or suspended interaction exists.

`POST /inventory/transfer` synthesizes `give me {item}` or `I give you {item}` and calls the same pipeline; it is not a second inventory executor. Supported items are saw, hammer, rope, axe, wood, fruits, water, food, string and bow. Generated transfers are denied by `ValidationService.validate`; authoritative deterministic outputs may transfer after `validate_control`. `StateService` owns movement of one actual owned item, pending item transitions, relationship clamping and legacy quest updates. `RoleConditioningService` and `rule_engine/behavior.py` alter/select behavior before this effect boundary; their outputs still require the final checks already in the pipeline.

Craftsman action example: `craftsman_intent.py:dialogue` resolves a wreck report/help/wait/resume/return/postpone, calls `craftsman.apply_command` with a fresh server UUID, then returns authored reply text. The command owner enforces opening completion, encounter revision, allowed physical state and inspection staging. Accepted outing is distinct from `complete_inspection`; only the latter validates both actors' marks and creates `ShipRepairQuest(gathering_materials)`. It does not repair the ship. Command IDs/results exist for encounter endpoints; chat's fresh UUID does not supply stable client retry identity.

| Rule owner | Authoritative responsibility / limit |
| --- | --- |
| `validation/items.py`, `state/service.py` | Explicit named-item recognition, current ownership and pending purpose flow; mutation is StateService, not prose |
| `services/quests/bow.py` | available → meet → gather → crafting → completed; consumes wood/string held by Craftsman, 5-second ready_at, grants one bow only when ready; workshop routine gate |
| `api/routes/quests.py` | Explicit start, nearby string pickup (64 units), timed advance; can restore Gatherer wood when start would otherwise lack it |
| `services/craftsman.py` | Authored outing modes/checkpoints, inspection completion, outcome memory, ship quest creation and command replay |
| `services/quests/ship_repair.py` | Snapshot/material rendering only: 12 timber, 3 rope, 2 sailcloth, 2 pitch; no acquisition/contribution/repair executor |
| `services/gatherer.py` | Legal story transitions, attempts/acceptance, victory/decline relationship outcomes and authoritative memory; local combat reported through trusted command boundary, not chat generation |
| `services/opening.py`, `island.py`, `scenery_geometry.py` | Run/opening/proximity/walkability checks; one salvage rope, opening handoff and valid position recovery |
| `services/context/grounding.py`, authored JSON catalogs | Current public fact views only; inventory/delivery/completion authority stays in game services |

## Input, output, context and operational limits

| Layer | Existing bound or absence | Source |
| --- | --- | --- |
| Chat request | npc_id ≥1, message 1–500 Python characters; optional unbounded scope string | `schemas/chat.py` |
| Client input | LineEdit max_length 500; trimmed empty messages rejected locally | `scripts/chat_window.gd` |
| Transfer request | npc_id ≥1; item enum; direction enum; optional scope | `api/routes/inventory.py` |
| Ordinary dialogue | settings max_dialogue_chars=240, validator rejects longer; prompt says under 240 | `config/settings.py`, `validation/service.py`, `prompts/builder.py` |
| Craftsman story | regex story/explain/tell me more permits 600 in validator and decoder; prompt's story allowance is not role restricted but decoder/validator are | same plus `llm/openai_compatible.py` |
| Model response | LLMResponse dialogue 1–600, fact_ids at most 2; state deltas each [-1,1]; intent/emotion/action/reasoning nonempty, no maxima | `validation/models.py` |
| Factual decoder | strict schema selects chat/answer/clarify; social permits only chat and 0 fact IDs, world ≤2 IDs; dialogue maxLength 240 or Craftsman story 600 | `llm/openai_compatible.py` |
| Factual rendering | one/two known unique selected IDs; clarification no IDs; rendered final text checked against settings 240 even for story request | `context/grounding.py`, `validation/service.py` |
| HTTP output | no Pydantic max for final_dialogue/StructuredNPCOutput dialogue or total response size; authored grounded outputs bypass ordinary semantic/240 check but final LLMResponse still caps 600 | `schemas/chat.py`, `pipeline.py` |
| Separate pure composer | DialogueText 1–300; DialoguePolicy max_text_chars 1–300; rejects overflow, never truncates | `app/dialogue/compose.py`; not wired into live pipeline |
| Recent context | latest 6 Conversation rows by NPC only, chronological after selection; rejected and outside-world turns removed; ≤12 message entries; social_history further strips action/factual turns | `context/builder.py`, `context/social.py` |
| Memories | top_k default 5 clamped to candidate count default 40 (settings 20–50); ≤40 semantic + ≤40 lexical ORM rows by default, final ≤5; full eligible vector-pair index build on cache miss is unbounded | `memory/service.py`, `config/settings.py` |
| Memory text/search/cache | stored event slices to 512; claim text 500 / report text 430; lexical query first 500, ≤12 distinct ASCII terms of 2–32 chars; malformed vector sample ≤50; index cache ≤32 entries | `memory/service.py`, `memory/importance.py`, `memory/index.py` |
| Catalog shape | ≤8 people, ≤12 places/routes, route directions 1–140 chars; no total assembled prompt/fact/token cap | `context/grounding.py` |
| World history | latest 50 turns per NPC, NPC-only predicate; no epoch/scope filter | `api/routes/world.py` |
| Memory HTTP / maintenance | GET memory list has no row bound; search query 1–500 nonblank chars and retrieval defaults above; reindex batches default 32, allowed 1–256 | `api/routes/memory.py`, `memory/reindex.py` |
| Generation config | temperature .2; default model gpt-4.1-mini in Settings; runtime env overrides deliberately not read for this static inventory; structured output default true; no max_tokens/max_completion_tokens or explicit context token budget | `settings.py`, `llm/openai_compatible.py` |
| Provider deadline | HTTP timeout default 120 seconds, connect 5; no overall pipeline deadline or stage/repair policy | same |
| Embedding | timeout default 30 seconds, connect 3; dimensions default 768, model nomic-embed-text, revision v1; fallback lexical/vectorless storage on embedding unavailable | `settings.py`, `memory/embedding.py` |
| Client timeout | chat/transfer/clear 160 seconds; Craftsman/Gatherer gateways 10; world/quest 10; position 5; salvage 8 | `chat_window.gd`, gateways, `main.gd` |
| Client display | whole string retained in log/bubbles; TextParagraph font-shaped line pagination, no character ceiling or silent truncation; local pages are not durable server beats | `chat_window.gd:paginate` |
| Retry/repair/retention | `_validate_or_repair` immediately falls back, no generation repair; no durable chat retry/queue capacity/lease/summary trigger/retention policy; histories/memories persist until explicit lifecycle/reset/clear | `pipeline.py`, models/services |
| Shared pure contracts | opaque nonempty ASCII Identifier, exact integer Revision 0–2^53−1, schema version 1; collection bounds intentionally belong to owners | `contracts/core.py` |

Keep the 500-character input bound in redesign. New `ConversationPolicy` must supply explicit tuning values; this inventory does not select defaults for output/beats/tokens/deadlines/queues/leases/summaries/retention. Baseline/T02–T03 and release product acceptance own measurements and final budgets.

## Renderer contracts and client state application

`context/grounding.py:render_answer` emits fixed clarification or joins selected catalog fact text; unknown/duplicate/no IDs raise rather than accepting generated prose. `build_facts` renders live inventory, role/location, bow requirements/progress/verified deliveries, encounter knowledge and ship materials with source/status/as_of. `validation/items.py:transfer_answer`, `quests/bow.py:reply/dialogue/maybe_start/finish_if_ready`, and `craftsman_intent.py:dialogue` return authored LLMResponse text and exact mechanical terms. There is no pluggable renderer registry in this live path. Fallbacks are Gatherer encounter-aware branches and `context/craftsman_profile.py:character_fallback`; no provider repair occurs.

Separate `app/dialogue/compose.py` offers immutable ApprovedDialogue/DialoguePolicy/DialogueEvent: expression/commitment needs approved_text, verified events need identity/kind and required template fields; templates cover quest reward, item transfer, interaction failure. It checks game/timeline/NPC/policy compatibility, rejects overflow and replaces substring success claims in non-outcome text. It is reusable only via an explicit adapter and revised policy, not as proof of redesigned whole-reply validation.

Godot `chat_window.gd:_completed` displays final_dialogue, adds system transfer line from validated action, applies NPC inventory, and emits world_changed. It rejects responses from a different *sent* scope, but chat carries no independent inventory revision. `main.gd:_apply_chat_state`, `_quest_completed`, `_salvage_completed`, world hydration and Gatherer/Craftsman handlers apply overlapping snapshots through different handlers. Craft/Gather gateways gate their encounter states by scope/revision; that does not order inventory/quest snapshots from every handler. Preserve pagination, then centralize future resource-revision application under godot-adapters/T03.

## Complete live writer inventory and transaction ownership

These are runtime writer entry points found by source inspection, including helpers that appear read-only. Pure domain/port fakes also model revisions and effects but are not SQL/game writers. Seed/schema migration paths are included because they mutate persistent state.

| Entry path | Mutations / helper owner | Commit and revision behavior |
| --- | --- | --- |
| `/chat`, `/inventory/transfer` | StateService inventory/pending/relationship/current_state/legacy Quest; bow dialogue phase, maybe_start materials/timer; Craftsman intent commands/topic; Conversation and memory | pipeline commits once after flushes; NPC memory CAS token advances; memory listeners may rotate it again; no inventory/quest revision |
| `/quests/bow/start` | phase meet; replenishes Gatherer wood if absent everywhere | routes/quests payload commits; no resource revision |
| `/quests/bow/pickup-string` | string_collected + one Player string, proximity gate | same; no scope argument or inventory revision |
| `/quests/bow/advance` | finish_if_ready grants bow, completes phase/current_state, Conversation/memory | payload commits; memory listener can rotate NPC token; no quest/inventory revision or request ID |
| `/craftsman/command` | intro/player position, wreck/outing/wait/return modes, inspection, ShipRepairQuest creation, event Memory and cached command results | endpoint commits; apply_command flushes and increments encounter revision, replays by request_id+command (not full payload) |
| `/craftsman/checkpoint` | physical position/navigation/activity/presentation checkpoint plus NPC location | endpoint commits; checkpoint flushes/increments encounter revision |
| `/gatherer/command` | story/checkpoint/attempt/position, relationship outcome, authoritative memory and command result | endpoint commits; service flushes/increments Gatherer revision; replay checks command and payload |
| `/world/player-position` | recovered position/location/recovery notice | endpoint commits under player lock; no spatial/resource revision |
| `/world/opening/complete` | opening state, position, location/map version | **service internal commit**; no aggregate revision |
| `/world/beach/salvage` | salvage IDs + rope inventory | **service internal commit**; salvage ID prevents repeated pickup; no inventory revision |
| `/world/new-game` | reset_world deletes conversations/memories/story/encounters/ship quest; resets Player/NPC inventories/state, bow and legacy Quest; new game_scope and memory tokens | reset flushes; endpoint obtains world snapshots then commits |
| `craftsman.record`, `gatherer.record`, `bow.get_quest` | lazy row creation; stale-scope encounter reset; Gatherer staging migration can move player | flushes/assignments, caller owns commit; `/world`, context/fact/snapshot reads can invoke record; not intrinsically read-only |
| `craftsman_intent.dialogue` | remembers ship/bow topic directly in encounter state even without command | caller pipeline commit; **no encounter revision increment for topic** |
| `gatherer.record` staging migration | checkpoint version/state and applicable Player position | **no encounter revision increment**; commit depends on caller |
| database initialization | seed_world creates Player/NPC/legacy Quest inventory/state; inventory migration initializes legacy inventories; opening migration repairs positions/schema; memory migration adds scope/provenance schema with conservative legacy defaults | seed_world internal commit; migration engine.begin transactions; startup-owned, not receipt boundary |
| Memory persistence/reindex/lifecycle | store_conversation/store_memory, explicit preference retraction, encounter Memory inserts, reindex updates embedding metadata | memory service/provenance flush; reindex CLI commits; ORM Memory insert/update/delete listener rotates NPC memory_revision; SQL bulk deletions bypass mapper listener so clear/reset rotate explicitly |
| `/chat/{npc_id}` DELETE | clears pending, deletes NPC conversations/memories, rotates memory_revision | endpoint commit; no game_scope argument/epoch or tombstone; clears all NPC rows regardless scope |

`services/state/locking.py:lock_player` acquires SQLite writer lock via no-op Player UPDATE and PostgreSQL row lock; lock order is Player then NPC. Encounter services participate in caller transaction; StateService/bow helpers flush, not commit. Existing internal service commits in opening/salvage and seed must be isolated/adapted for future receipt transactions. Conversation effects and final speech currently share one commit, but no durable pre-effect operation receipt/admission recovery exists; do not equate this with the redesign's two publication phases.

Revision writers: pipeline CAS; clear/reset explicit UUID; Memory mapper listener UUID (including encounter/reindex/retraction writes); Craftsman command/checkpoint +1 and record reset 0; Gatherer command +1 and record reset 0. No Player inventory revision, legacy/bow/ship quest revision, shared activity revision or persisted conversational epoch is modeled. NPC memory_revision is both cache invalidation and optimistic conversation fence, not ordered numeric state revision.

## Explicit ID mapping decisions for handoff

1. Live identity is single Player 1 plus stable integer NPC IDs and run UUID `Player.game_scope`; Conversation/Memory and encounter/ship records retain scope. New game changes scope while preserving NPC IDs. Clear changes NPC memory token, not game_scope.
2. Existing pure `ContractEnvelope` requires opaque string `game_id`, `timeline_id`, `npc_id`. The actual local bridge `services/memory/provenance.py:_retract` sets **game_id='single-player', timeline_id=Memory.game_scope, npc_id=str(NPC.id), actor_id='player:1'**. Record this as an existing preference-reconciliation convention, not a global redesign mapping.
3. Do **not** relabel game_id→scope and timeline_id→epoch. Pure timeline currently means run in that bridge; current memory_revision changes on ordinary chat/memory edits and cannot represent a clear-only epoch. No source establishes a persisted redesign epoch. contracts/T03 and persistence-adapters/T01 must define an explicit semantic adapter/new epoch field and handle the legacy `game_scope='legacy'` case; unknown scope/provenance is excluded unless established.
4. Reuse integer NPC IDs only through string encoding/resolution at typed boundaries; do not use display names as identity. Preserve origin UUIDs for continuity evidence, but a Conversation source_event_id is not an idempotent client turn or operation receipt ID.

## Regression commands and reproducibility

Resolved local Python: repository `.venv/bin/python`, Python 3.12.14. `python3` resolves `/usr/bin/python3`; use the venv for backend dependencies. `godot`/`godot4` were absent from PATH; installed executable is `/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot`, version **4.5.1.stable.official.f62fdbde1**. Skills mentioning later Godot versions do not change this installed version. No application database is needed for this inspection command. Its eight subprocesses all exited 0; the earlier exploratory `rg` using guessed `scripts/ui/chat_window.gd`/`api_client.gd` paths exited 2, then was corrected to observed paths; it is not verification evidence.

Current backend regression entry point from root:

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_craftsman_encounter.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_gatherer_encounter.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_world_inventory.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'
```

Last pattern is a redesign packet convention, currently no matching tests; a zero-test success must not satisfy redesign acceptance. Existing mechanical coverage includes validation_items, craftsman_dialogue/encounter, gatherer_encounter, quest_recovery, grounded_chat, npc_pipeline, control_fallback, behavior_pipeline, memory_provenance/lifecycle/semantic_memory, inventory_migration, world_eligibility/inventory, read/write ports and dialogue_compose. Full filenames are in evidence; source-only T01 does not certify all suites. Main Agent independently recorded current Craftsman 6/6, Gatherer 10/10 and world inventory 14/14, exit 0, in [main verification](evidence/conversation-redesign-schedule/main-verification.json). Existing `datetime.utcnow()` deprecation warnings remain. These results are mechanical foundations, not redesign completion or quality scores.

Godot command shape (choose an existing test with its declared prerequisites):

```sh
/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot --headless --path frontend/godot --script res://tests/contract_fixture_smoke.gd
/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot --headless --path frontend/godot --script res://tests/craftsman_activity_smoke.gd
/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot --headless --path frontend/godot --script res://tests/gatherer_encounter_smoke.gd
```

Integration tests such as bow_quest_smoke, grounded_chat_smoke, craftsman_backend_compatibility_smoke and gatherer_integration_smoke require their disposable backend/fixture setup; consult test source, README and evidence walkthroughs before running. `backend/tests/run_godot_grounding.py` orchestrates temporary backend/client grounding checks. Live scripts named run_*_live.py / semantic_smoke.py contact providers and are outside this task. No Godot gameplay/integration or live replay was run in T01. SQLite/PostgreSQL receipt/concurrency acceptance remains for adapter packets; static inventory cannot certify it.

## Reuse and next ownership

Reusable foundations: exact current-fact catalog and rendering, count/ownership checks, deterministic quest/encounter owners, writer-lock order, scoped memory/provenance/retraction checks, diagnostic sink, immutable contract/port doubles, shared fixture codec and client font pagination. They need explicit adapters/conformance tests; none grants redesign completion.

T01 supplies the ordinary/action traces, limit/renderer/authority/commit/writer inventories and ID decisions requested by acceptance. Main Agent owns final review and task ledger updates. contracts/T01 may freeze new values using these distinctions; contracts/T03 owns legacy ID semantics; game-adapters/T01–T03 own transaction participation and every revision gap; composition/T01, proposal/T02 and godot-adapters/T02 own compatible response budgets; godot-adapters/T03 owns ordered snapshot application. baseline/T02 must identify actual configured provider/model and response origins on isolated fixtures, and T03 freezes scenarios/policy candidates. No live proportions, latency numbers, shipping limits, model replacement or redesigned durability are claimed here.
