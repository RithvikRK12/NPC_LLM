# Gatherer First Encounter Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development for independent backend/combat tasks and integrate in the current workspace. Steps use checkbox syntax for tracking.

**Goal:** Implement the approved forest rescue, local retry, refusal return, and durable social consequences.

**Architecture:** A run-scoped backend state machine owns story transitions and atomic outcome memories. A dedicated Godot encounter owns staging, UI, routes and gateway recovery; separate player combat and boar controllers own moment-to-moment combat. Main only arbitrates and wires systems.

**Tech Stack:** Existing FastAPI/SQLAlchemy, Godot 4 GDScript, JSON staging resources.

**Spec:** docs/superpowers/specs/2026-10-14-gatherer-first-encounter-design.md

## Global Constraints
- Preserve all existing uncommitted craftsman and other work; work in this checkout without commits or resets.
- Three hearts, two three-hit boars; J attacks, WASD moves; borrowed knife never enters inventory.
- Explicit Help/Decline only; pause remains available and freezes encounter simulation.
- ActorRouter handles visible automatic walks; no visible teleport through scenery.
- Exactly one authoritative outcome memory and relationship mutation per run.
- New scope invalidates callbacks; lost responses retry the same request ID.

## Review Focus
- Lost command responses and revision conflicts must reconcile authoritative branch state.
- Reload in each durable state must reconstruct the right scene without repeating rewards.
- Overlay-delayed forest entry and alternate approaches must not bypass introduction.
- Pausing, held input, simultaneous final damage and stale callbacks must not produce duplicate outcomes.
- Refusal hostility must preserve unrelated quests and normal post-encounter chat.

### Task 1: Durable encounter and dialogue grounding
Files: new backend models/schemas/services/routes gatherer modules and tests/test_gatherer_encounter.py; integrate router, world, seed, model registry, context and chat guard.
Interfaces: POST /gatherer/command accepts game_scope, command, request_id, expected_revision, payload; returns game_scope and gatherer_encounter {revision,status,checkpoint,attempt_id,accepted_attempt_id}. Commands: begin_intro, accept, restart_attempt, victory, decline, complete_retreat, begin_confrontation, finish_presentation. Payload attempt_id for accept/victory/restart; begin_intro uses authored fixed checkpoint. World includes identical snapshot.
- [x] Write and observe failing tests for legal branches, invalid transitions/stale attempts/scope, exact-once outcomes, every reload state, new-game reset and explicit context grounding.
- [x] Implement atomic commands, supported memory provenance/cache invalidation, snapshot and reset.
- [x] Run targeted tests and full backend suite; correct regressions.

### Task 2: Focused combat controllers
Files: scripts/player_combat.gd, scripts/boar.gd, tests/gatherer_combat_smoke.gd; melee_attack input map.
Interfaces: player_combat Node2D configure(player,boars,layout,bounds); reset(); start(); stop(); advance(delta); attack(); take_damage(direction); properties hearts, enabled, facing; signals health_changed, defeated. Boar CharacterBody2D configure(player,combat,layout,bounds); reset_at(at); set_dead(); advance(delta,can_attack); take_hit(direction); properties health,state,active; shared attack permission coordinated by player_combat. All updates manually advanced by encounter for pause and deterministic defeat precedence.
- [x] Write failing headless checks for three-hit death, immunity, per-swing deduplication, token release, defeat priority and reset.
- [x] Implement collision-aware movement/stagger, readable warning, slash, hit feedback and compact audio.
- [x] Run headless checks with actual installed Godot.

### Task 3: Encounter, gateway and integration
Files: scripts/gatherer_encounter.gd, scripts/gatherer_gateway.gd, resources/gatherer_encounter.json, resources/gatherer_dialogue.json; surgical changes main.gd.
Interfaces: configure(main,gateway); restore(world); advance(delta); owns_input(); allows_movement(); camera_target(); blocks_chat(); dispose(); gateway updated/failed signals, send_command(command,payload), retry(), restore(world), state/busy.
- [x] Author and test clear marks, forest entry region and arena using actual layout and router.
- [x] Implement latched trigger, approach/threat/choice, handoff/tutorial/release gate, fight/defeat/retry, thanks, retreat and angry return.
- [x] Implement fixed-ID save retry, conflict refresh/recovery and every durable load state.
- [x] Integrate input arbitration, pause/focus loss, camera, interaction suppression, shutdown/new-game cleanup.
- [x] Add headless state/route/recovery integration checks and update forest smoke.

### Task 4: End-to-end verification and review
- [x] Run backend regressions and Godot import/headless encounter, fisherman, opening, craftsman, inventory/quest checks where available.
- [x] Use disposable backend/database for rendered help, death/retry, refusal/return at 960x540 and 1280x720; inspect saved screenshots and collision/readability evidence.
- [x] Review Gatherer changes against spec, fix concrete issues, rerun affected checks; report limitations honestly.

## Execution record
- Plan approved by user's execution request. No additional design approval needed.
- Existing dirty checkout retained because it contains required encounter foundations; no commits will mix unrelated work.

- Task 1 complete: 462 backend tests pass, including nine Gatherer cases.
- Task 2 complete: combat headless checks cover token/immunity/swing/death/retry/direction/boundary and simultaneous lethal damage.
- Task 3 complete: full integration verifies both branches, local retry, input ownership, save failure retry and durable-state reloads.
- Task 4 complete: 22 Godot regression scripts pass gameplay assertions; rendered checks pass at both required resolutions and all four physical approaches. Separate review completed and relationship tooltip finding fixed.
- Verification details, screenshots and logs: docs/evidence/gatherer/verification.md.
- Existing exit-time resource cleanup warnings in legacy Godot tests are documented; unrelated opening/audio work was not modified.

## Follow-up: compatibility, deeper forest, larger boars
User requested fixing the missing encounter data error, expanding the forest, moving the Gatherer deeper, and larger threatening boars. Existing authorization permits routine implementation choices.
- [x] Reproduce missing backend state trapping controls; recover capability automatically without inventing story state. Run a refreshed local backend without resetting the player's save.
- [x] Extend the shaded forest/trail and add collision-backed forest scenery. Move the Gatherer from (-650,70) to (-1800,70), author a wider clearing, move encounter marks/entry region and persist checkpoints from the shared resource.
- [x] Migrate pending staging metadata without changing outcomes or applying social effects again. Keep legacy resolved saves intact.
- [x] Enlarge boar art 1.8x with matching trunk collision and readable 0.7-second warning; retain three-hit deaths and small encounter scope.
- [x] Update coordinate-dependent tests; verify backend, headless full flows, physical routes and rendered views at both supported sizes.

Follow-up implementation record:
- Missing backend capability no longer captures player input. An automatic authoritative refresh retries until encounter data is available; real end-to-end tests exercise recovery from an empty frontend snapshot.
- Updated the normal port-8000 backend with --reload without resetting the player's database; /world now returns gatherer_encounter.
- Forest uses shared forest_layout.json: shaded ground, an extended trail and 211 collision-backed trees. Gatherer moved to (-1800,70); all encounter marks, entry, routes and recovery marker moved accordingly.
- Existing pending staging migrates to version 2; status, attempt, relationship outcomes and memory remain intact. Backend reads encounter marks from the same JSON as Godot.
- Boar art scales 1.8x; trunk collision is 36x20, warnings 0.70 seconds, forward reach 58 with a matching telegraph. Boars approach at 85 units/s and recover for 1.0 seconds.
- Follow-up checks: 463 backend tests and 27 Godot regression scripts pass gameplay assertions. Rendered verification and evidence are recorded in docs/evidence/gatherer/forest-expansion/verification.md.
