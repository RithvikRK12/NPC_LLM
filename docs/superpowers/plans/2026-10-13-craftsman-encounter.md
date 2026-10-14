# Craftsman Encounter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if explicitly selected. Track steps with the checkboxes below.

**Goal:** Deliver playable slices 1–5: workshop life, first meeting, broader conversation, a physical outing, ship inspection, “A Way Home,” and independent return.

**Architecture:** Keep backend story outcomes and frontend physical activity separate. Add dedicated Craftsman activity and encounter controllers, a bounded actor router, and actor-aware portals; integrate them through small hooks in Main. Use dedicated encounter and ship-quest tables with run-scoped, idempotent writes, while retaining authoritative bow and inventory services.

**Tech stack:** Existing Godot/GDScript (local runtime 4.5.1), FastAPI, Pydantic, SQLAlchemy; no new runtime dependencies or engine migration.

**Spec:** `docs/superpowers/specs/2026-10-13-craftsman-character-and-ship-repair-design.md` (approved by the user; proposed defaults accepted).

## Global constraints

- Keep the name “Craftsman,” the five authored character anchors, and the supplied introduction, inspection, and farewell beats.
- Ambient speed 75; pauses 5–12 seconds. Follow stops within 64, resumes beyond 96, travels at 180, and catches up at up to 210 beyond 160. Repath around 0.4 seconds; warn after sustained separation beyond 240.
- World collisions use the existing 24×16 foot box. Player and Craftsman may overlap physically; navigation provides visible spacing. Do not apply foot clearance twice.
- Only explicit authored portal crossings relocate actors. Navigation failure never teleports them. Invalid saved positions may recover to documented safe points on load.
- Introduction completes after its final beat or deliberate skip. Inspection skip commits only after valid staging. Success notifications follow confirmed transactions.
- `ship_repair` / “A Way Home” starts at `gathering_materials`, with `ship_plank:12`, `rope:3`, `sailcloth_bundle:2`, `pitch_pot:2` and zero contributions.
- Reserve `not_started → gathering_materials → ready_for_repair → repairing → completed` and durable, deduplicated `main_story_completed` semantics. Do not implement deliveries, acquisition, repair, sailing, or ending, or expose a completion operation in this scope.
- Dialogue never authorizes inventory changes or quest completion. Existing string-list inventory representation and bow progression remain compatible.
- Use disposable test databases; preserve the user's existing database, approved spec, and unrelated code. Current checkout is clean except the user's untracked `docs/superpowers/specs/` directory.

## Verified assumptions and integration points

- `npc.gd` is an `Area2D`; `person.gd` already animates from a physical parent's velocity. Main types `current_npc` as `Area2D` and builds actors dynamically: update those integration points when adding the physical Craftsman.
- `world_layout.gd.is_walkable()` already includes foot clearance, furniture, hull, scenery, and coast. Workshop origin is `(10000,10000)`; portals currently move only the player.
- Rowan provides physical local-grid approach and input ownership, but marks his introduction seen before arrival. Preserve Rowan's behavior; give the Craftsman the stronger completion semantics in the spec.
- Social classification and validation are restrictive. Factual questions already select server-rendered fact IDs. `bow.dialogue()` is currently called for particular bow requests, rather than every ordinary materials question; the axe helper in `validation/quest_dialogue.py` has no discovered callers. Do not introduce another broad quest-word intercept.
- `StateService.apply()` overwrites `NPC.current_state` with dialogue actions; bow completion sets it to `available`. New movement mode must live separately. Bow availability must consult that mode before starting hands-on work away from the workshop.
- Chat has a revision check during generation, but its request lacks game scope. Add a backward-compatible scope field and enforce it for the game client; reject stale encounter/checkpoint responses too.
- The legacy Quest row is unique per player. Add separate tables rather than repurposing it. Startup uses `Base.metadata.create_all()` plus explicit upgrades for changed existing tables.

## Review focus

Each condition below is covered by the owning task's tests:

1. Reply lost after a committed inspection: retry/read returns the same outcome and never duplicates a quest.
2. New Game or a newer activity checkpoint races an old reply: reject stale scope/revision without restoring old position or phase.
3. Bow completion coincides with departure or return: reward once, retain movement mode, and defer new crafting until workshop arrival.
4. Player is close through a wall, or enters a cottage: use reachable distance and portal state; never remotely inspect or drag the camera after the NPC.
5. Quoted/hypothetical/negated help and two-turn agreement: accept contextual player intent without interpreting quoted requests as commands.

## Task 1: Durable encounter and ship-quest contracts

**Files:** Create `backend/app/models/craftsman_encounter.py`, `backend/app/models/ship_repair_quest.py`, `backend/app/services/craftsman.py`, `backend/app/services/quests/ship_repair.py`, `backend/app/schemas/craftsman.py`, `backend/app/api/routes/craftsman.py`, and `frontend/godot/resources/craftsman_encounter.json`. Modify model imports, API router, database initialization/seed, and world response. Test in `backend/tests/test_craftsman_encounter.py`.

**Interfaces:** `encounter_snapshot(db, player) -> dict`; `ship_snapshot(db, player) -> dict`; `apply_command(db, player, npc, command, request_id, expected_revision, payload) -> dict`. Expose `POST /craftsman/command`, `PUT /craftsman/checkpoint`, plus `craftsman_encounter` and `ship_repair` in `/world`. Requests carry `game_scope`; responses carry scope and monotonic encounter revision. The resource supplies stable activity/inspection/return marker IDs; the backend recipe supplies quantities and formatted requirement text to all UI/dialogue consumers.

- [x] Write failing tests for default/legacy world creation, independent bow state, scope rejection, duplicate command IDs, invalid NPC/phase/position, out-of-order checkpoints, and atomic inspection activation.
- [x] Run `cd backend && PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -p 'test_craftsman_encounter.py' -v`; confirm failures exercise missing behavior.
- [x] Implement encounter storage for intro status, report/offer context, outing, activity, navigation space/position, wait reason, return index, inspection presentation checkpoint/outcome ID, revision and processed command results. Store ship phase, recipe version and contribution ledger separately. Validate legal transitions, finite/collision-clear locations and both actors' staging eligibility using shared authored geography. Command processing and checkpoint writes lock in the established player-first order.
- [x] Implement `complete_inspection` as one transaction setting inspected state, creating the single quest, recording verified inspection evidence, and scheduling return. Replay returns its persisted result. Store durable story-event schema/uniqueness for the future completion boundary, without a callable repair/completion implementation.
- [x] Initialize old worlds without changing inventory or bow progress; reset encounter, quest, events and idempotency state with New Game. Verify isolated tests pass and review the slice diff.

## Task 2: Physical actor, routing, workshop routine, and portals (slice 1)

**Files:** Create `frontend/godot/scripts/actor_router.gd`, `craftsman_activity.gd`, `actor_portals.gd`, and `tests/craftsman_navigation_smoke.gd`. Modify `npc.gd`, `main.gd`, `world_layout.gd`, and the encounter resource as necessary. Keep Gatherer stationary and Rowan unchanged.

**Interfaces:** Router `find_path(from: Vector2, to: Vector2, layout: Resource) -> Array[Vector2]`, `advance(actor: CharacterBody2D, delta: float, speed: float) -> String` returning moving/arrived/blocked. Activity `configure(actor, player, layout, portals)`, `restore(snapshot: Dictionary)`, `set_conversation_open(open: bool)`, `advance(delta: float, paused: bool)`, `checkpoint() -> Dictionary`. Portal service `traverse_actor(actor, portal_id: String, entering: bool) -> bool`; explicit shared departure uses Main's fade, solo NPC crossing never changes player/camera.

- [x] Write and run failing physical navigation tests: blocked direct segments, furniture and corner clearance, unreachable targets, bounded search, and portal positions validated in both spaces.
- [x] Give the Craftsman a `CharacterBody2D` root and separate interaction area, with world collision mask excluding the player. Retain identity, label, art and existing interaction APIs; update Main's actor type assumptions. Use existing directional animation and real physics movement.
- [x] Implement bounded local AStar searches and a coarse exterior landmark graph. Validate segment clearance, choose reachable endpoints, detect lack of progress, retry a bounded number of times, then wait safely with feedback. Never grid-search across interior/exterior coordinate gaps.
- [x] Author reachable bench/shelf/timber standing points and return-route landmarks. Implement weighted nonrepeating routine destinations, 5–12 second idle, speed 75, facing work points, and conversation/global-pause suspension. NPC travel continues off camera.
- [x] Run the navigation smoke test with real physics, then observe two rendered workshop minutes. Confirm multiple walks/pauses, no clipping and a clear doorway; record evidence before accepting the slice.

## Task 3: First-entry introduction and presentation ownership (slice 2)

**Files:** Create `frontend/godot/scripts/craftsman_encounter.gd`, `craftsman_gateway.gd`, `resources/craftsman_dialogue.json`, and `tests/craftsman_intro_smoke.gd`. Modify Main's ready/load, travel-finished, input/camera ownership, pause, shutdown and restart hooks.

**Interfaces:** Gateway `send_command(command: String, payload: Dictionary, request_id: String)`, `save_checkpoint(snapshot: Dictionary)`, and scoped success/failure signals. Encounter `try_introduction() -> bool`, `owns_input() -> bool`, `camera_target() -> Vector2`, `advance(delta: float)`, `skip()`, `cancel()`, `restore(snapshot: Dictionary)`. Dialogue resource uses stable beat IDs and separate text.

- [x] Write/run failing tests for first entry during ambient walking, no launch under another modal, final-Continue handoff, skip, failed approach, pause, interrupted reload, and second entry without replay.
- [x] Pause the routine, route the player toward a clear conversation position (or first route the Craftsman to the greeting mark), face both actors, and present the approved two beats with Continue/Skip. Use one owner for player motion/camera and restore both on every exit. Final Continue/skip persists seen and opens normal Craftsman chat; failed staging leaves pending.
- [x] Include gateway operations in restart/shutdown pending-operation handling. Preserve request IDs across retries and discard replies with old scope/revision. If persistence fails, release control and expose retry without falsely announcing success.
- [x] Run intro and existing fisherman integration checks; inspect rendered framing and UI at 960×540 and 1280×720.

## Task 4: Character conversation and contextual actions (slice 3)

**Files:** Create `backend/app/services/context/craftsman_profile.py` and `backend/app/services/craftsman_intent.py`. Modify `context/social.py`, context models/builder/grounding, prompts, validation, LLM mock/fallback, pipeline, chat schemas/routes, and frontend chat/gateway. Modify bow service and inventory route only where availability requires it. Test in `backend/tests/test_craftsman_dialogue.py` and existing grounding/bow tests.

**Interfaces:** `resolve_craftsman_intent(message, recent_context, encounter, focus) -> dict`; trusted intents are report/accept/begin inspection, wait, resume, postpone/return, or clarify. Pipeline validates and executes allowed commands in its transaction and returns encounter/quest snapshots; generated text cannot supply command authority. Persist accepted focus for bow versus ship across short follow-ups.

- [x] Write/run failing tests for the spec's interests/loneliness messages, mixed fear/help, direct and two-turn requests, report followed by agreement, hypotheticals/quotes/negation, repeated requests, explicit topic switching and ambiguous materials questions.
- [x] Add the five stable character anchors, voice limits, authored fallback and report/agreement/firsthand knowledge distinctions. Broaden generated conversation to work/values/home/uncertainty without inventing biography. Coordinate classification, recent-context retention, prompt and validation; permit harmless craft language while rejecting unsupported possession, transfer, delivery, movement and completion claims.
- [x] Resolve action and quest focus before bow routing. Commit acceptance before showing “Lead the way”; report alone offers and waits. Finish existing five-second bow work before departure, and prevent new hands-on bow work while away. Keep movement mode independent from dialogue/current_state writes and bow reward completion.
- [x] Add optional run scope to chat for compatibility, require the current scope from Godot, and test rejection before generation and after concurrent reset. Store separate verified agreement evidence and unverified wreck-report memory; inspection knowledge comes only from Task 1's outcome.
- [x] Pass new dialogue tests plus grounding, memory provenance, inventory and bow regressions. Demonstrate provider-failure acceptance using authored text only after a successful command.

## Task 5: Follow, waiting, doorway detours, and independent return (slice 4)

**Files:** Extend activity, portal, gateway and Main integration from Tasks 2–3. Add `frontend/godot/tests/craftsman_outing_smoke.gd` and backend checkpoint/availability tests.

**Interfaces:** Activity `apply_encounter(snapshot: Dictionary)`, `on_player_portal(portal_id: String, entering: bool)`, `whereabouts() -> String`; the encounter controller may temporarily override activity for staging. Navigation uses recent reachable player breadcrumbs, reachable path length and the accepted tuning band.

- [x] Write/run failing tests for following around bench/tree/rock/coast, close-through-wall pursuit, catch-up and failed routing, wait/resume, cancelled departure, workshop re-entry, cottage wait/resume, conversation during return, and off-camera solo arrival.
- [x] Start pursuit after response presentation and chat close. Shared workshop departure routes both actors to distinct exit positions before fade; NPC later traverses independently. Unrelated interiors suspend pursuit outside their entrance, preserving outing and previous wait reason.
- [x] Add trailing-target smoothing, 0.4-second repath, 180/210 speed, 64/96 hysteresis, sustained 240 separation hint, and blocked-route safe wait with return-to-NPC guidance. Explicit return follows the authored landmark chain and resumes routine only after physical workshop arrival.
- [x] Persist activity checkpoints on mode/portal/landmark changes and throttled movement, including when the player stands still. On load validate safe positions and recompute paths. Update actor labels, journal whereabouts and grounded location facts from reported checkpoints.
- [x] Run rendered outing tests and observe actual obstacle detours, shared fade, cottage waiting and solo return. Verify talking pauses/resumes the same return segment and bow completion leaves activity intact.

## Task 6: Inspection, journal, recovery, and full verification (slice 5)

**Files:** Extend encounter/dialogue resource, ship beach markers, quest panel, Main world/chat update handlers and gateway. Create `frontend/godot/tests/craftsman_inspection_smoke.gd`, `craftsman_integration_smoke.gd`, and `docs/evidence/craftsman/walkthrough.md`; update README play instructions.

**Interfaces:** Encounter `try_inspection() -> bool`, `retry_outcome()`, and gateway `complete_inspection` command using Task 1's contract. Quest panel `set_ship_state(state: Dictionary, encounter: Dictionary)` augments the existing bow API. Both requirement dialogue and UI consume backend recipe/remaining quantities.

- [x] Write/run failing tests for player-only arrival, two reachable distinct marks, obstructed staging, Continue beats, skip before/after valid staging, activation failure, commit with lost response, and reload during staging/dialogue/committed return.
- [x] Author and collision-check `InspectionArrival`, `InspectionPlayerMark`, `InspectionCraftsmanMark`, `ReturnRouteStart` against the current southern hull. Play recognition before physical approach; wait for both arrivals, then inspection, hope, requirements, confirmed activation and farewell. Keep retry at the pending outcome beat. Release camera/player after farewell and resume independent return.
- [x] Present main quest alongside the bow, zero/required material counts, escort/wait/return whereabouts and a success notification only after confirmation. Explain deferred acquisition/repair in journal copy without claiming existing sources. No delivery button or repair-completion trigger.
- [x] Run the full backend suite: `cd backend && PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -v`; require all applicable tests passing. Run Godot import/parse and new navigation/intro/outing/inspection/integration tests, plus existing bow, interiors, fisherman, opening lifecycle and persistence regressions against an isolated SQLite backend on port 8001 with mock generation.
- [x] Use `/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot --headless --log-file /tmp/craftsman-godot.log --path frontend/godot --script res://tests/<test>.gd` for headless checks. Use rendered runs for visual acceptance; inspect saved frames/video of workshop motion, approach, obstacles, shared portal, both actors/hull framing, and complete independent return. Headless assertions alone do not establish those visual outcomes.
- [x] Exercise all 21 spec scenarios, including reload during follow/inspection/return, pending-request New Game, duplicate requests, claimed deliveries and bow overlap. Record commands/results, screenshots and any unverified limitations. Review the final diff and provide concrete playthrough instructions; claim only what was observed or checked.

## Plan review and execution

The approved design is unchanged. Recommended execution is native, in manageable tasks above: routing, story transactions and presentation share interfaces, so keeping their implementation in one session reduces coordination overhead. Any required independent final review can use the applicable review skill. Do not begin product implementation until the user reviews this plan and selects/confirms execution.

Execution evidence and verification limits are recorded in `docs/evidence/craftsman/walkthrough.md`. All scoped gameplay tasks are implemented; the existing baseline 1920px UI failures remain outside this change.
