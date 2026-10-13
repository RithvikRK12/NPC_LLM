# Starting cutscene — Shipwreck on the southern shore

**Status:** Implemented with verification and evidence recorded. Remaining subjective audio review, exhaustive asset-failure handling and extended GPU profiling are explicitly unchecked below.<br>
**Created:** 2026-10-13. Revised to use a fog-only voyage and a larger, fully water-surrounded island.<br>
**Confirmed duration:** 60 seconds of cinematic time. Hold a keyboard key to play at 2× speed; release it to return to 1×.<br>
**Technology:** Godot 4, GDScript, 2D top-down pixel art. Confirm the project's installed Godot minor version before implementation.<br>
**Goal:** Deliver a deliberately directed shipwreck opening that establishes the island's mystery and ends with the player freely exploring the beach.

## 1. Creative brief and boundaries

The player arrives from the south by wooden sailing ship through an apparently endless, fog-covered ocean. The ship continues through dense mist with no visible land or external communication. Just before the wreck, the fog suddenly dissipates and clouds part, exposing the island’s southern coastline directly ahead. The vessel cannot turn in time, runs aground, and breaks apart. After darkness and silence, the player awakens in the wreck, climbs onto the southern beach, and gains control. The playable landmass is an island surrounded by water on every side.

The emotional sequence is fixed:

**Isolation → Growing Unease → Sudden Danger → Disaster → Survival → Curiosity and Exploration.**

Success means the player understands three things without exposition: they are stranded on an unfamiliar island; the wreck lies on its southern shore; and the inland environment invites exploration. Mystery comes from isolation, the abrupt weather change, and the unknown island. The scene does not imply that someone summoned or deliberately guided the ship.

### Confirmed requirements

- A scripted opening with no player movement, inventory use, dialogue interactions, or steering.
- Animated ocean, ship, and dense fog, followed by sudden fog dissipation immediately before the wreck.
- The crash beach is on the actual southern coastline, with inland to the north and open sea to the south.
- The entire exterior map is one coherent island surrounded by water, with space reserved for future content.
- A readable coastline reveal before the collision, with a visibly unsuccessful turn.
- Hull impact, splintering timber, falling mast, water over the deck, and the player losing balance.
- Fade to black, a short silence, then a calmer wrecked beach.
- Recovery and ship-exit animation before normal gameplay begins.
- Control transfers at the moment the player finishes stepping onto the beach.
- The visual language remains consistent with the existing 2D pixel-art RPG.
- Individual shots and effects can be built, previewed, reset, and tested independently.
- A 60-second normal playback and hold-to-play-at-2× keyboard control.

### Proposed defaults, open to revision

| Decision | Working default | Reason |
| --- | --- | --- |
| Fast-forward key | Space, via `cutscene_fast_forward` Input Map action | Easy to discover; not a toggle or an instant skip |
| Dialogue | No spoken lines, narration, or explanatory text | The staging and sound carry the mystery |
| Crew | No clearly identifiable crew shown in this opening | Avoid accidentally confirming the player was alone or that others died |
| Music | Restrained atmospheric texture; no large melodic score | Leaves room for water, timber, wind, and silence |
| Recovery location | Visible within the broken hull near a reachable exit | Makes survival and the journey onto the beach legible |
| Island connection | Beach connects inland to the existing Willowbrook area | Preserves the current NPC and quest content while establishing an arrival point |
| Resume policy | Restart an unfinished opening from its beginning; completed saves resume normally | No fragile mid-shot save restoration in the first implementation |
| Instant skip | Not included in the first implementation | The requested acceleration is continuous 2× playback |

These defaults allow the design to proceed. They are not additional confirmed story facts. The player's prior voyage, crew fate, cause of the sudden weather change, and the island's larger plot remain unwritten. Map dimensions and future-region allocations below are planning defaults, not claims that every future feature has been specified.

### Scope

Deliver the cinematic, playable southern wrecked beach, nearby inspectable wreckage and collectible supplies, a clear inland route, save continuity, and a dependable gameplay handoff. Also establish the complete island outline, surrounding ocean, collision boundary, region reservations, and chunk layout so future content fits without moving the starting coast. The first delivery needs a complete geographic blockout, not fully detailed content in every region. Ship steering, simulated sailing, global dynamic weather, procedural destruction, swimming, and combat are outside this opening’s scope.

## 2. The 60-second shot plan

All times below are **cinematic seconds**, not wall-clock seconds. They also serve as stable preview anchors. The intervals are consecutive and total exactly 60 seconds.

| ID / time | Emotion and image | Camera and animation | Sound / exit cue |
| --- | --- | --- | --- |
| S01 · 0–6 · 6 s | Already underway in dense fog; retained original shot S03 at local time 8. | Continue bow/deck framing from the previous time-30 state. | Wind, water and creaks already looping; discarded cues never replay. |
| S02 · 6–22 · 16 s | Growing unease, overlapping fog banks close around the vessel. | Measured track and closer deck view; player braces. | Stronger wind and stressed rigging. |
| S03 · 22–28 · 6 s | Suspense; wind softens, land remains concealed. | Bow aimed into opaque mist. | Water and timber become exposed. |
| S04 · 28–30 · 2 s | Sudden coastal reveal. | Banks break apart at 28; coastline fully readable at 29.5. | Surf becomes distinct. |
| S05 · 30–33 · 3 s | Evasive turn fails. | Authored heading changes while momentum carries the ship north. | Keel contact at 33. |
| S06 · 33–39 · 6 s | Disaster. | Splinters 33.3, mast 34.2, wash 35, fall 35.4; fade 37.5–39. | Ordered impact, timber, mast and water cues. |
| S07 · 39–43 · 4 s | Blackout. | Swap to the persistent beach under black. | Impact tail to 40.5; silence 40.5–42; surf resumes at 42. |
| S08 · 43–49 · 6 s | Survival. | Recovery fade-in 43–45; settle toward the player in the wreck. | Calm surf and seabirds. |
| S09 · 49–57 · 8 s | Resolve. | Recover, brace 51, stand 53, climb from 54. | Cloth, timber and steps. |
| S10 · 57–60 · 3 s | Exploration. | Checkpoint request 57; camera aligned and readiness barrier 59.8; handoff 60. | Ambient surf retains its playing voice. |

Boundaries: `0,6,22,28,30,33,39,43,49,57,60`. Shared named sampling times live in `opening_times.gd`. Opening save version stays **1**; map version is **2**. This is removal of the first 30 seconds, not a rescaled 90-second sequence.

### Directing rules

- Start already sailing through fog with the retained deck composition; preserve ocean negative space around the vessel.
- Use changing ship/deck framing, fog movement, and environmental sound to sustain the voyage; the ship continues blindly until the abrupt reveal.
- Keep land hidden until 28, make it readable by 29.5, and strike at 33. This gives 3.5 cinematic seconds of readable danger while keeping the fog clearing immediately before the wreck. At 2×, retain a continuous, clear coast-and-bow composition through this short interval.
- The weather change is sudden and unexplained; no character or device is shown causing it.
- Crash energy comes from multiple ordered events, not continuous maximum shake.
- Preserve a real silence between disaster and survival.
- Do not interrupt the first free step with a quest popup or NPC conversation.
- At 2×, preserve every beat and event in the same order; do not substitute a shortened edit.

## 3. Making the sequence cinematic in top-down pixel art

A top-down scene has no literal distant horizon. Create the impression of endless water through repeating ocean detail, fog occlusion, reduced contrast toward the frame edges, and negative space around the ship. Before the reveal there is no visible coastal silhouette. Once the mist clears, the southern shoreline enters the forward composition at the same scale and orientation as the persistent beach.

Use framing, tracking, lead space, occlusion, and timed reveals rather than changing into a side-view illustration or attempting a 3D orbit. Wide-to-player shots should primarily reframe and move the ship through the composition. Keep the existing `Camera2D` zoom at `Vector2(0.5, 0.5)` for the first implementation. Fractional animated zoom would disturb the established pixel scale. A closer shot, if necessary after the animatic review, needs separately authored framing or a deliberate shot cut and visual QA.

Keep a consistent screen direction: the ship progresses generally upward toward land; its unsuccessful turn bends the bow without reversing the scene's geography. In the crash set, the coast is above the ship. In the beach set, inland remains upward and the sea remains below. Broken mast, hull shape, and shoreline rocks provide continuity across the blackout.

### Pixel and layer rules

The existing art standard uses one source pixel per two world units, 16×16 source terrain tiles, 24×32 actor frames, nearest-neighbor sampling, and integer enlargement of a low-resolution world viewport. Preserve it. See [the current pixel-art standard](../../frontend/godot/assets/PIXEL_ART.md).

- Draw all weather, spray, and destruction effects inside the low-resolution world viewport.
- Keep UI and the full-window fade in the parent viewport so they cover resize margins too.
- Keep physics, path positions, and save coordinates as floats; quantize only their visual presentation.
- Snap the composed camera position, including shake, to the two-world-unit render grid once per frame.
- Prefer alternate ship frames to rotating a large detailed pixel sprite through many arbitrary angles. Subtle rotation is a prototype option requiring visual review.
- Use a limited palette with dithered/clustered edges for mist, light, and spray; avoid smooth high-resolution effects pasted over the pixel scene.
- Explicitly layer sea → wake/foam → ship/deck → player and rail occluders → spray → foreground fog. Keep scenery intended to share actor ground sorting as sibling nodes in the world's Y-sort hierarchy.

The minimal supported window is currently 960×540; compose mandatory action inside its safe frame. At 1280×720 and 1920×1080, extra visibility should reveal ocean or scenery rather than unfinished set edges. Resize must not expose the hidden shore before S06.

## 4. Architecture and alternatives

| Approach | Strength | Cost or limitation |
| --- | --- | --- |
| **Recommended: a small director, shot AnimationPlayers, and a shared cinematic clock** | Editable timing, independent previews, deterministic 2× playback, clear save/handoff boundaries | Requires explicit ownership and reset contracts |
| One large 60-second AnimationPlayer | Fast first animatic; all keyframes visible together | Cross-scene paths become fragile; debug entry, loading, cancellation, and persistence become awkward |
| GDScript-only coroutine with timers and tweens | Easy to sketch and customize | Timing is scattered; parallel effects and fast-forward become difficult to synchronize |

Use GDScript for state, cue scheduling, input ownership, loading, and lifecycle. Use `AnimationPlayer` for authored property changes within each shot. Godot recommends it for complex timed animation; its inherited manual processing mode supports advancing animation explicitly. These are the engine capabilities behind the proposed single-clock design. [AnimationPlayer](https://docs.godotengine.org/en/stable/classes/class_animationplayer.html), [AnimationMixer](https://docs.godotengine.org/en/stable/classes/class_animationmixer.html).

Do not build a universal dialogue/cutscene framework for this first sequence. A focused `OpeningDirector`, a small shot interface, and a few reusable effect scenes are sufficient.

### Proposed scene ownership

```text
Main                                  existing application/session owner
├── WorldView                         existing pixel viewport presenter
│   └── WorldViewport
│       └── World                     existing Y-sorted Node2D
│           ├── WorldCamera           one actual Camera2D
│           ├── IslandWorld           ocean, coastline and streamed exterior chunks
│           ├── Village / interiors   hidden or inactive during opening
│           ├── OpeningStage          temporary cinematic set
│           │   ├── OceanBackdrop
│           │   ├── CoastReveal
│           │   ├── SailingShip
│           │   │   ├── Hull / rigging / mast / rails
│           │   │   └── PlayerVisualProxy
│           │   ├── WeatherFX
│           │   └── CrashFX
│           ├── ShipwreckBeach        survives handoff as gameplay scenery
│           └── Player                existing authoritative gameplay body
├── OpeningDirector                   state, clock, cue dispatch, cleanup
├── OpeningAudio                      ambience and event voices
├── Gameplay UI                       existing UI, gated during cinematic
└── TransitionOverlay                 fade, pause and speed hint
```

`OpeningStage` and `ShipwreckBeach` are distinct. Swap their visibility under black; do not rebuild the entire application scene. Keep `Main`, requests, UI, and the existing world viewport alive.

For the voyage and crash, use a visual player proxy under the ship. It has no inventory, physics authority, or save position. This avoids moving the real body into cinematic ocean coordinates and avoids parenting a gameplay collider to a rocking ship.

During black, place the real player at the beach recovery marker with gameplay control locked. Use its visual component in scripted animation mode for recovery. Hide the proxy before revealing the beach. At handoff there is already one real player on the sand, so no visible replacement is necessary.

### Components and proposed public contracts

These are planned project interfaces, not claims that these methods already exist.

| Component | Responsibility and proposed interface |
| --- | --- |
| `OpeningDirector` | `start()`, `set_paused(value: bool)`, `cancel()`, `preview_shot(id: StringName)`; emits `shot_changed(id: StringName)` and `completed`; owns the only cinematic clock |
| `OpeningShot` | `enter(context: OpeningContext)`, `advance(delta: float)`, `exit()`, `reset()`; one non-looping property animation plus explicit initial state |
| `OpeningContext` | Typed references to stage, camera rig, real player, effects, audio, and transition overlay; no service locator or direct database access |
| `CinematicCamera` | Stores authored `base_position` and visual `shake_offset`; `sample_at(time: float)`; submits one combined target through `WorldView` |
| `WeatherFX` | `sample_at(time: float)` and `reset()`; fog coverage/drift, cloud shadow, sea tint, and daylight |
| `CrashFX` | `trigger(cue_id: StringName)` and `reset()`; repeat-safe bursts and ship damage stage changes |
| `OpeningAudio` | `trigger(cue_id: StringName)`, `sample_mix(time: float)`, `set_paused(value: bool)`, `reset()`; owns playback voices and state-boundary fades |
| `ShipwreckBeach` | Exposes `RecoveryStart`, `HullExit`, `ControlHandoff`, `SafeFallback`, and `InlandRoute` markers; supplies colliders and interaction anchors |
| `IslandLayout` | `is_exterior_walkable(at: Vector2) -> bool`, `recover_exterior_position(at: Vector2) -> Vector2`, and `chunk_id_at(at: Vector2) -> Vector2i`; owns exterior geography and region reservations |
| `IslandWorld` | `prepare_region(region_id: StringName)` and `update_active_chunks(at: Vector2)`; loads terrain and keeps coastline collision available independently of decorative chunks |
| Player visual adapter | `set_scripted_mode(enabled: bool)`, `play_scripted(animation: StringName)`, `set_facing(direction: StringName)`; suspends automatic idle/walk selection |

The director accepts a fake persistence adapter in preview/test mode. Effect scenes never access the backend, grant items, unlock input, or change global scenes.

### State and ownership

```text
PREPARING → FOG_TRANSIT → DEEP_FOG
          → STILLNESS → WEATHER_REVEAL → APPROACH → CRASH → BLACKOUT
          → BEACH_REVEAL → RECOVERY → EXIT → GAMEPLAY
```

`PAUSED` and `WAITING_FOR_DATA` are overlays on the current state, not extra story shots. Cancellation is a lifecycle operation. Each state has explicit entry values, a bounded duration, and cleanup. There must be one owner per property: shot animation owns the camera base; shake owns an additive offset; the camera presenter owns the final transform. Do not have a Tween and an AnimationPlayer writing the same property.

## 5. Time, held-key 2× playback, pause, and cues

### The timing contract

- Normal: cinematic time advances by real frame delta.
- Space held: cinematic time advances by twice real frame delta.
- Space released: return to 1× on the next update, with no restart or seek.
- Paused, unfocused, or waiting for required data: cinematic time does not advance.
- All 60 cinematic seconds played at 2× take approximately 30 wall-clock seconds, excluding readiness waits and explicit pauses.
- The main game, backend deadlines, network timeouts, and menus remain on their own normal clocks.
- Completion occurs exactly once when cinematic time reaches 60.0; the final state is evaluated before input is unlocked.

**Do not use `Engine.time_scale` for fast-forward.** It would affect unrelated systems, and changing it alone would not define how audio and shader animation should behave.

Use an Input Map action rather than hardcoding the physical key in director logic. Show `Hold Space · 2×` quietly near the beginning, using the actual binding label. While held, show a small `2×` indicator except during intentional blackout. No tap-to-skip behavior. Consume fast-forward during the cutscene; do not deliver it as a gameplay action at handoff.

The input mode is `CINEMATIC` until handoff. Escape may open pause/settings; the cinematic itself remains non-interactive. On focus loss, pause and clear the effective speed. On focus return, require a fresh key press before resuming acceleration so a missed key-release event cannot leave it stuck at 2×.

### One clock for every visual system

The director computes the desired time once. Split its advance at shot boundaries and cue timestamps, dispatch each crossed event in chronological order, and apply any remaining delta to the next shot. A frame that crosses several boundaries must not lose events or discard the leftover time.

Use manual processing for registered `AnimationPlayer`s and advance them with director-scaled delta at speed scale 1.0. Do not also set their speed to 2.0, which would double-count acceleration. Sprite frames, fog withdrawal, and ocean loops derive from cinematic time or are advanced through the same adapter. Pass explicit `cinematic_time` into shaders; shader `TIME` is not the cutscene clock.

Prefer sampled curves and animations over free-running Tweens for story effects. If a Tween is necessary, stop its automatic processing and advance it only through the director's adapter; never let it advance twice. Godot exposes explicit Tween stepping, but it still needs lifecycle ownership. [Tween](https://docs.godotengine.org/en/stable/classes/class_tween.html).

Use a sorted cue list with stable IDs such as `keel_contact`, `mast_break`, and `deck_wash`. Fire events over `(previous_time, current_time]`, with entry cues handled explicitly at time zero. Store the IDs already fired during that run. Animation property tracks control poses and intensity; the cue dispatcher controls side effects. This avoids duplicate effects when previews seek or states restart.

### Audio policy at 2×

The **sequence plays twice as fast**; this does not require doubling the pitch of water and breaking timber. Schedule audio starts and mix envelopes on cinematic time. Keep ambient loops and short effect samples at their authored pitch, and fade/truncate outgoing sounds at their defined state boundaries. Author impact samples short enough to remain intelligible when cues are closer together at 2×. Crossfade ocean ambience into shore ambience instead of seeking a long mixed soundtrack.

This is a deliberately event-based soundtrack, not a promise of pitch-preserving time stretching. Avoid spoken dialogue and long beat-synchronized music in this delivery. If either is added, an explicit accelerated audio mix or time-stretch solution needs a separate decision. `AudioStreamPlayer.pitch_scale` changes both pitch and playback rate, so it is not the default solution here. [AudioStreamPlayer](https://docs.godotengine.org/en/stable/classes/class_audiostreamplayer.html).

Pause all opening voices when the cinematic pauses, then resume them; ensure the blackout silence remains silent even after switching rates repeatedly. Use non-positional players for the main cinematic mix, with optional spatial accents, so camera motion does not accidentally attenuate the crucial crash.

## 6. Environment and effects implementation

### Ocean and ship movement

Build an inexpensive repeating ocean layer with a small animated wave atlas or low-resolution UV-scrolling shader. Use separate foam/wake sprites to make travel obvious even when fog hides environmental landmarks. Keep the ship near its cinematic staging origin during the early voyage; relative water motion sells distance without constructing miles of sea.

Combine two low-amplitude, different-period bob curves on the ship visual group. Keep feet, railings, mast, and deck attached to the same group. Avoid moving individual deck pieces independently before the crash. Increase foam and lateral drift during the attempted turn, not arbitrary ship speed changes.

For the approach, move a bounded authored shoreline set relative to the ship or move the ship along a short authored path. Choose one approach transform as the owner; do not scroll the shore and move the ship by the full approach distance simultaneously. Prototype contact around a bow marker and a beach-contact marker, then lock the shot's path. Visual impact does not depend on a physics collision callback.

### Fog and weather reveal

Use two or three slow-moving fog layers: background haze, a middle veil obscuring coast detail, and foreground banks passing over the vessel. Expose `coverage`, `opacity`, `drift`, and an authored reveal mask. Sample drift from cinematic time. Keep the offshore coastline concealed at all supported viewport sizes.

Fog disappearance is spatial: banks pull apart and dissolve during 28–30, with the coast readable by 29.5. Do not begin gradually exposing land earlier in the voyage. Simultaneously lift cloud-shadow modulation and shift the sea from dark slate toward daylight blue-green. The land already exists behind the masking, so it emerges rather than popping into existence. A simplified initial mask may conceal its silhouette entirely until the release cue.

Use explicit local modulation or a scoped world lighting setup; do not accidentally brighten the UI or village while the opening is active. Animate the cloud-shadow layer and world color treatment together, with a lower-contrast daylight transition for the reduced-flash setting. Daylight is the only lighting reveal.

### Crash and damage staging

Use authored stages: intact → grounded/deck torn → mast fallen → final wreck. Stage changes, splash bursts, and camera jolts are repeatable cues. Hull breakup can use a few animated fragments with authored trajectories; a rigid-body destruction simulation is unnecessary and makes repeatable framing harder.

Start shake with a short displacement at contact, then a smaller irregular decay during secondary failures. Proposed maximum: six low-resolution render pixels for the principal impact, falling below two pixels by the mast aftermath. Normal voyage bob should be much smaller. Quantize shake only after composing it with the camera path. Set shake to zero in reduced-motion mode.

The mast should fall across readable deck space and settle into the same orientation used by the beach wreck. Spray can briefly cover the player fall and conceal an art swap, but should not obscure the entire impact. Do not use a full-screen white flash. No violent camera rotation is needed.

## 7. Island map, southern beach, recovery, and exploration

### Whole-island geography and capacity

The exterior map must read as **one substantial island completely enclosed by ocean**. This is a map-wide requirement, not just a water backdrop behind the opening beach. Build an irregular closed shoreline with bays, rocky edges, and headlands; no mainland connection or land extending through the map boundary. The southern arrival coast must belong to this same outline in the cinematic, gameplay scene, and any future map UI.

Use this provisional layout budget before detailed terrain production:

| Measure | Planning target |
| --- | --- |
| Exterior authoring envelope, including ocean margin | **16,384 × 12,288 world units**; X `-8192..8192`, Y `-6144..6144` |
| Terrain grid | 32-world-unit tiles; **512 × 384 tiles** in the envelope |
| Maximum land envelope | X `-7168..7168`, Y `-5120..5120`; the irregular island occupies less than this bounding rectangle |
| Surrounding water | At least 1,024 world units between the maximum land envelope and each authoring edge; ocean rendering continues beyond it as needed |
| Existing village | Retain the origin near `(0, 0)` and existing building/quest anchors |
| Southern wreck staging | Approximately `(0, 3840)` on the actual south-facing shoreline; safe exit and route lead north |
| Terrain chunk | 32 × 32 tiles = **1,024 × 1,024 world units**; 16 × 12 potential chunk slots |
| Expansion allowance | Reserve at least **35% of usable land** after coast/cliff exclusions for future locations and connecting routes; do not fill it with permanent obstacles |

The maximum land width is about 79.6 seconds of straight walking at the current 180-world-unit/second speed; maximum north–south span is about 56.9 seconds. Real routes will be longer because paths bend around terrain. The central southern bay is inset 960 units while the outer coastline and village anchors retain their scale. Handoff `(0,3600)` to village follows 3,662.307 world units, or 20.346 seconds at the unchanged 180 wu/s.

These dimensions are a starting capacity decision, not a guarantee that unspecified future content fits. Before finalizing the coastline, list every planned location's footprint, approach area, NPC activity space, and route connections. Validate their combined fit plus the 35% reserve on a blockout overview. Enlarge the envelope at this early stage if necessary; avoid compressing buildings or losing routes to keep the proposed numbers. Preserve village anchors and the southern arrival relationship when adjusting the outline.

### Region reservations

These regions reserve space; they do not require implementing every suggested future system as part of the opening.

| Region | Spatial role and content allowance |
| --- | --- |
| Central settlement | Willowbrook, workshop/cottages/interiors, market lane, well, existing quest anchors, and room for additional buildings and NPC gathering spaces |
| Southern coast and approach | Wreck, beach supplies, coastal exploration, and a readable inland path; space for later shore encounters without blocking arrival |
| Western woodland | Existing Gatherer/forest connection, larger woodland paths, clearings, resource areas, and future exploration sites |
| Eastern expansion land | Reserved space for additional settlement or other planned locations, with several approach routes |
| Northern interior | Space for later substantial exploration areas and landmarks; high ground or cave entrances are possibilities, not confirmed content |
| Coastal perimeter and buffers | Varied shoreline, headlands, route connections, and undeveloped space between regions; not every cliff edge must be walkable |

Build an overview showing region extents, current content footprints, routes, coastline, and expansion reserves. Prove that all launch-accessible regions connect to the southern spawn. Future regions may remain lightly detailed or intentionally gated; they still need a believable land footprint and an entrance reservation. Current buildings, NPC interactions, and the bow quest must fit before adding speculative locations.

### Rendering, collision, and chunk ownership

- Introduce `IslandWorld` and an `IslandLayout` resource as the source of truth for the closed land outline, shallow/deep water, region bounds, chunk IDs, routes, and recovery markers. Village and beach scenes own local scenery and consume shared geography.
- Replace the effectively infinite green exterior background with an ocean base and authored land chunks. Blue beyond a rectangular grass patch does not satisfy the closed, irregular island requirement.
- Use tiled/chunked terrain, not one giant image of the island. Preserve existing village art as an initial local chunk group where practical.
- Load visible chunks plus an adjacent ring. Pin the player/collision neighborhood and active NPC or quest regions; stop unnecessary decorative animation elsewhere. Distant scenery unloading must not discard authoritative NPC state.
- Preload the southern coast and first inland chunks before recovery. Preserve coverage until required neighboring chunks are ready; the player must not cross into an unloaded seam.
- Derive shoreline visuals and collision from the same land/water data. Deeper water is impassable until a separate swimming/boat feature exists. Validate the full player footprint, including diagonal approaches.
- Keep the global coastline boundary independent of decorative chunk loading so unloading cannot open a passage into the sea. Test every coastline segment and chunk seam.
- Render ocean beyond the authoring envelope when a large viewport looks outward. No green fallback, void, or abrupt rectangular water cutoff may appear.
- Keep cinematic staging separate from playable geography. The crash set matches the southern beach; the voyage does not require an enormous walkable ocean map.

### Interior coordinates and older saves

Existing interior origins are `(10000, 10000)`, `(12000, 10000)`, and `(14000, 10000)`, outside the proposed exterior envelope. These are logical rooms, not extra land beyond the island. Validate recognized interiors before applying island bounds, and exclude them from exterior chunk rendering and island overviews. Ocean boundaries must never relocate a valid indoor save.

The old map allowed arbitrary exterior coordinates. A bounded island cannot preserve all those positions as walkable land. Preserve valid floating-point positions exactly. For saves now in water, cliffs, or outside the island, choose the nearest valid authored recovery marker on connected playable land, with a stable marker-ID tie break and a safe village marker as fallback. Explain the relocation once and persist it with the map version; preserve inventory, quests, histories, and NPC state. This supersedes the older unbounded-map behavior only where geography invalidates a position. Opening completion and geographic validity are separate checks.

### Southern beach and recovery

The beach is a real gameplay location, not a cinematic-only matte. Its persistent scene must contain shallow-water visuals, impassable deeper water, walkable sand, wreck collision, debris footprints, inspectable objects, supply interaction points, and an inland route. Water must not become walkable simply because the cutscene used visual sprites.

Use named markers in the beach layout rather than magic coordinates in shot scripts:

| Marker | Purpose |
| --- | --- |
| `RecoveryStart` | Feet position for the recovering player inside the broken hull |
| `HullExit` | Clear breach/ramp that visually supports climbing out |
| `ControlHandoff` | Safe sand where the final scripted step lands |
| `SafeFallback` | Valid nearby sand used if final placement validation fails |
| `SupplyApproach` | Reachable interaction point outside wreck colliders |
| `InlandRoute` | Walkable route toward existing island/NPC content |

Place the wreck on the island’s southern perimeter, not merely below the village inside the landmass. Proposed beach staging origin: world `(0, 3840)`, with dry sand and the exit route north of the wreck and open ocean south of it. Shape the local shoreline around these anchors; the map’s southernmost land tips may extend to Y 5120 elsewhere. Derive final recovery and handoff coordinates from the beach resource, validate them against the island land/water mask, and share the authoritative handoff position with the backend. The complete island plan below supersedes the earlier smaller beach placement.

Author a minimum 64-world-unit-wide recovery exit and inland path for the existing 24×16 foot collider. Keep debris out of the route and provide enough sand for the first movement input in any direction. The recovery body follows an authored, collision-checked path; disable user input, not the ability to advance scripted movement. Use a swept movement check in physics updates or an equivalent validated path, with a bounded fallback if a collider unexpectedly blocks the exit.

Add dedicated `recover`, `brace`, `stand`, and `climb_out` frames using the existing player palette and foot pivot. The prototype may use timed idle/walk poses, but that is not final recovery animation. Avoid squashing the full sprite to simulate every pose.

### First free actions

1. Move freely on the sand and look back at the damaged ship.
2. Inspect a hull breach or recognizable piece of wreckage for a short factual description.
3. Collect a nearby salvage supply through a real pickup interaction.
4. Follow an obvious but unforced inland route toward future NPC encounters and help.

Keep existing starting food and water in inventory for compatibility; do not remove them merely to stage a pickup tutorial. Proposed extra salvage is one rope bundle, using the existing item vocabulary, subject to validating current inventory behavior. Pickup state and inventory addition must be persisted together and replay-safe. A repeated request or reload must not duplicate the supply. Keep pickup labels and prompts hidden until gameplay is active.

Environmental text describes observable facts: splintered timber, washed-up supplies, or the sudden clearing of the mist. The cause of the wreck remains unexplained. The first objective may read `Explore the shore`, but should appear unobtrusively after the player is already in control.

## 8. Exact handoff and loading contract

The handoff is an ordered transition, not simply setting a boolean:

1. While black, activate beach colliders and real player; place the player at `RecoveryStart`, reset velocity, and enable scripted visual mode.
2. Reveal the beach and run recovery/exit while normal interactions remain locked.
3. During S10, move the gameplay camera target into alignment with its normal follow target. Its zoom remains the normal 0.5 throughout.
4. Prepare a durable completion checkpoint before the final frame, as described below. Pause the cinematic at 59.8 if that required acknowledgment is not ready.
5. At 60.0, evaluate the final pose and place/check the player's feet at `ControlHandoff`. If validation failed earlier, resolve to `SafeFallback` before showing the final step.
6. Clear residual shake, scripted velocity, and cinematic-only visibility/modulation. Set normal facing and idle; disable scripted visual mode.
7. Transfer the one camera to gameplay follow and enable normal movement and interaction on the next physics update. There must be no intervening camera snap.
8. Reveal HUD and movement guidance. Release cinematic input ownership; any held fast-forward key has no effect on gameplay speed.
9. Emit completion once; dispose of the opening stage and cinematic audio voices, retaining beach scenery and its ambient audio.

The user gains control at the visible final step onto sand. There is no extra cinematic pan after that point.

Request beach resources during `PREPARING` and load as early as practical. If background loading is used, poll threaded load status and only retrieve the resource when ready; Godot notes that retrieving it too early can block. Instantiation and adding nodes to the tree still need to be staged and measured. [ResourceLoader](https://docs.godotengine.org/en/stable/classes/class_resourceloader.html).

Ideally both sets are ready before the opening starts, so the designed blackout lasts exactly four cinematic seconds. If a required load fails, stop advancing at the safe black boundary, show a small actionable retry/return message after a short real-time delay, and avoid an indefinite silent black screen. Such waits are operational interruptions, not part of the 60-second authored duration. Holding Space must not accelerate loading, network retries, or their timeout.

## 9. Integration with this repository

The following findings come from the current working tree on 2026-10-13, including its existing uncommitted changes. The plan must be reconciled with those changes before implementation; it does not replace them.

| Existing location | Current behavior | Required opening integration |
| --- | --- | --- |
| `frontend/godot/scenes/Main.tscn` | A `Node2D` using `main.gd`; world and UI are built at runtime | Retain application ownership; attach a focused director instead of replacing the entry scene |
| `frontend/godot/scripts/main.gd` | `_process()` enables player physics and follows the player every frame | Add an explicit cinematic mode to all input, movement, interaction, follow, and HUD paths; a one-time physics disable will be overwritten |
| Same file | `_input`, `_unhandled_input`, `_physics_process`, UI callbacks and save timer act independently | Gate all gameplay entry points; allow pause/quit and ongoing network servicing |
| `frontend/godot/scripts/world_view.gd` | Owns `SubViewport`, integer enlargement, one camera, and snapped follow | Reuse its presenter; expose explicit camera ownership without adding competing active cameras |
| `frontend/godot/scripts/player.gd` | Reads WASD directly in `_physics_process()` | Separate manual-input movement from scripted recovery movement; clear velocity on ownership changes |
| `frontend/godot/scripts/person.gd` | Re-selects idle/walk from parent velocity every frame | Add scripted animation ownership so recovery frames are not immediately overwritten |
| `frontend/godot/scripts/village.gd` | Uses its own terrain plus a very large green background; props are world siblings | Replace the unbounded green exterior fallback with island land and ocean ownership; preserve interior floors and hide village NPC labels during the opening |
| `frontend/godot/scripts/world_layout.gd` | Validates village/interior positions and recovers blocked saves | Check interiors first, then island land/water and local obstacles; migrate exterior saves newly stranded in water to safe land |
| `frontend/godot/scripts/main.gd` | Existing fade at CanvasLayer 20 handles building travel | Share a transition owner or prohibit concurrent fades; cinematic and travel must not race |
| Same file | Reduced scenery motion currently only calls the village | Route the preference to ship bob, fog drift, particles and shake as well |
| `backend/app/api/routes/world.py` | World snapshot, new game, and position PUT; no opening checkpoint | Add explicit opening progression scoped to the existing run |
| `backend/app/models/player.py` | Has `game_scope`, inventory, position, and location | Use `game_scope` to reject stale opening writes after New Game |

The opening should have no dependency on LLM output. Network-generated NPC behavior is not responsible for shot timing, fog withdrawal, crash outcomes, or unlocking movement.

### Save model and migration

Proposed new player state:

- `opening_version: int = 1` for this authored sequence.
- `opening_state: String` with values `pending` or `complete`.
- `map_version: int` recording the island-boundary migration separately from opening playback.
- Persisted salvage collection IDs, owned by the beach pickup service.
- Expose existing `game_scope` with the world snapshot for run-scoped writes.

For **existing saves**, opening migration assigns `complete`. Preserve every valid exterior or interior position exactly, along with inventory, quest state, histories, and NPC state. The new closed-island boundary additionally requires a map-version migration for exterior positions now in water or outside the island: recover those to a deterministic reachable land marker, explain the move, and persist it once. Do not replay the opening or reset progress. See the island compatibility rules in section 7. Missing opening metadata from an older server must not make an existing save replay the crash. Only newly seeded games and explicit New Game reset use `pending`. The frontend must detect an older backend's missing capability and keep its existing gameplay path rather than invoking unsupported checkpoint requests.

During a pending opening, suppress ordinary player-position autosaves. Cinematic/proxy coordinates are never persisted. Quit before completion leaves `pending`; the next launch starts the opening at S01. Do not force the user to watch the sequence merely to quit.

Proposed completion endpoint: `POST /world/opening/complete`, accepting `{game_scope, opening_version}`. The server validates the current run, locks the player, and atomically sets `complete`, the authored safe beach spawn, and `current_location = "shipwreck_beach"`. Repeating the request for the same completed run is harmless and **must not teleport a player who has since walked away**. A stale run gets a conflict response and cannot mutate the new game.

Send this request once the final beach/path state is ready, during S10, so acknowledgment can arrive before handoff. If the app closes after it succeeds but before the last step, the next launch resumes at the safe beach spawn; it does not attempt to restore a partially animated character. If it fails, hold at the pre-handoff readiness barrier, retain the locked final approach, and offer retry/return. Do not claim a save succeeded or silently allow progression that will disappear on reload.

This small acknowledgment window is the deliberate tradeoff between an uninterrupted normal handoff and crash-safe persistence. At normal local-server latency the opening remains 60 seconds; outages can extend wall-clock time. Error UI appears outside the story clock and is never sped up.

On New Game, reset opening state and salvage together with the existing run reset. Cancel old requests/timelines using a per-run generation guard. Update new-game tests that intentionally expect the old village spawn, while retaining legacy-save regression coverage.

## 10. Previewability, accessibility, and failure recovery

### Independent preview harness

Create `OpeningPreview.tscn` with controls for shot ID, restart, 1×/2×, pause, reduced motion, reduced flashes, and collision/marker overlays. It uses fake backend state and cannot mutate a real save. Every shot enters from its own complete initial snapshot, including ship damage stage, fog coverage, audio mix, camera position, and player pose.

Seeking a preview applies visual state without replaying side-effect cues or writing persistence. Playing forward from the selected point dispatches future cues only. Restart clears fired cue IDs, pooled particles, sound voices, and elapsed time. A saved debug screenshot must identify the shot and cinematic time.

### Pause and cancellation

Use local cinematic pause rather than pausing the whole application by default. Freeze the director and audio together; keep menu and network timeout processing active. If implementation uses `SceneTree.paused`, assign and test process modes explicitly, since pause behavior depends on node process mode. [Godot pause behavior](https://docs.godotengine.org/en/stable/tutorials/scripting/pausing_games.html).

Cancellation invalidates a generation token checked by pending asynchronous callbacks, stops all effect/audio players, clears camera offsets and overlays, and releases ownership only to the intended next application mode. Returning to a menu must not briefly unlock a hidden beach player. Avoid unbounded chains of `await animation_finished`; a cancelled or replaced animation may never provide the awaited transition.

### Accessibility and resilience

- Reduced motion disables shake, reduces bob, stops decorative drift, and uses restrained camera tracking. It preserves the coastline reveal, damage stages, and player recovery.
- Reduced flashes softens the sudden daylight contrast change without delaying land visibility. Test the fog reveal at 2× and keep the crash free of full-screen flashes.
- Offer optional concise environmental captions for key sounds such as hull impact and rushing water.
- No essential clue depends exclusively on sound or color.
- Handle window resize, focus loss, held-key release while paused, missing optional audio, and repeated preview playback.
- Missing required scene/marker data stops preparation with a useful error. Missing optional ambience logs the omission and allows the sequence to continue.
- Make preview crash effects seeded/repeatable. Use a modest capped particle budget and a low-effects variant on weaker hardware.

## 11. Asset and audio checklist

Final art should be approved together at the actual game pixel scale before individual assets are polished.

| Asset group | Minimum deliverable |
| --- | --- |
| Ship | Intact hull/deck, bow/stern, mast, sail, rigging, rail occluders, turning appearance, damaged stages, final wreck |
| Ocean | Dark and daylight palette treatment, wave loop, forward wake, turning wake, shallow-water foam |
| Fog / clouds | Layered pixel fog textures/masks, cloud-shadow mask, controlled withdrawal effect |
| Island and coast | Closed island silhouette, ocean on every side, reusable shoreline transitions in every orientation, southern beach, cliffs, rocks, inland connections, and region blockout tiles |
| Crash | Timber fragments, broken sail/rope details, mast fall frames, spray and deck-wash frames |
| Player | Existing voyage idle/look poses plus brace, fall, recover, stand and climb-out animation |
| Beach props | Persistent mast/hull pieces, debris, one inspectable anchor, one supply container/pickup |
| Audio loops | Open-sea wind and water, stressed rigging, quiet beach surf, sparse distant seabirds |
| Audio one-shots | Creaks, grounding impact, hull crack, mast break/fall, splash, footing loss, recovery and steps |
| UI | Binding-aware speed hint, active 2× indicator, pause/retry state, handoff movement hint |

Track asset origin and licensing in `assets/cutscene/opening/README.md`. Do not produce a photorealistic ship or smooth painted fog that conflicts with the established kit. Temporary blockout art and missing recovery frames must remain clearly marked as prototype assets.

## 12. Implementation checklist

**Goal:** Implement the specified opening and beach handoff within a spacious, water-surrounded island while preserving current village gameplay and migrating saves safely.<br>
**Architecture:** A run-scoped opening director advances independent shots and effects through one cinematic clock; the existing viewport renders the opening and a chunked island with a persistent southern beach. Backend-owned progression provides a durable endpoint.<br>
**Spec:** Sections 1–11 of this document. All listed new paths are proposed; existing files must be re-read before changing them.

Each task has an independently reviewable deliverable. Checkboxes describe future work; none imply implementation has occurred. Implement the graybox and timing foundation before commissioning final animation or polishing destruction.

### Task CUT-01 — Build the 60-second graybox animatic

**Create:** `frontend/godot/scenes/cutscenes/opening/OpeningPreview.tscn`, `OpeningStage.tscn`, `opening_preview.gd`, `opening_timeline.gd`, and `frontend/godot/resources/cutscenes/opening_timing.tres`.

**Depends on:** This design. **Produces:** A visual timing reference and authoritative S01–S10 durations, shot IDs, and cue timestamps.

- [x] Record the actual Godot executable/minor version and confirm manual animation APIs work in it.
- [x] Define the 10 shot intervals and named cues as data; assert no gaps, overlaps, or total other than 60.0 seconds.
- [x] Block out ship, player, dense fog, southern coast, wreck, and exit path using simple shapes.
- [x] Play the full sequence at the current pixel scale at 960×540 and 1280×720.
- [x] Capture an animatic showing sustained fogbound travel, abrupt clearing at 28, a visible late turn, impact at 33, silence, recovery, and final free-control location.
- [x] Review pacing against the emotional sequence; adjust within the fixed 60-second total and update this table if timing changes.

**Done when:** The fogbound voyage sustains tension, the sudden coast reveal reads immediately before the wreck, and the southern-shore arrival is clear without dialogue.

### Task CUT-02 — Implement the shared clock and held-key acceleration

**Create:** `opening_director.gd`, `opening_shot.gd`, `opening_context.gd` under `frontend/godot/scenes/cutscenes/opening/`; `frontend/godot/tests/opening_clock_smoke.gd`.<br>
**Modify:** `frontend/godot/project.godot` for `cutscene_fast_forward`.

**Depends on:** CUT-01. **Produces:** The director/shot contracts from section 4, 1×/2×/paused progression, and repeat-safe cue dispatch.

- [x] Write clock checks for 60 seconds at 1×, 30 seconds at 2×, and a mixed run: 20 real seconds at 1× plus 20 at 2× reaches 60 cinematic seconds.
- [x] Test short press/release changes, pause during acceleration, focus loss, and reaching several cue/shot boundaries in one update.
- [x] Implement a single time owner with manual AnimationPlayer advancement and explicit shader/effect time.
- [x] Add Space binding, binding-aware hint, and active 2× display; clear the effective hold on focus loss.
- [x] Test that each crash cue and completion fire exactly once; preview seeking must not fire past cues.
- [x] Verify `Engine.time_scale` remains unchanged and no gameplay timer or timeout is accelerated.

**Done when:** Both normal and accelerated playback reach the same endpoint and event log, with no skipped or duplicate events.

### Task CUT-03 — Add gameplay, camera, and animation ownership

**Create:** `frontend/godot/scenes/cutscenes/opening/cinematic_camera.gd`; `frontend/godot/tests/opening_ownership_smoke.gd`.<br>
**Modify:** `scripts/main.gd`, `scripts/world_view.gd`, `scripts/player.gd`, and `scripts/person.gd` under `frontend/godot/`.

**Depends on:** CUT-02. **Produces:** Explicit cinematic/gameplay ownership and scripted player visual mode.

- [x] Add tests proving held WASD, E, F, I, and clickable gameplay controls cannot move, interact, transfer items, or start travel during the opening.
- [x] Route camera updates through one owner; test that `main.gd` no longer overwrites cinematic framing every frame.
- [x] Suspend automatic idle/walk selection during scripted recovery and restore it afterward.
- [x] Separate visual voyage proxy from the real body; verify only the real body can be saved or receive gameplay input.
- [x] Suppress NPC labels, inventory/quest prompts, building detection, and regular position saves during cinematic mode.
- [x] Keep pause and quit available; clear velocity and shake on every ownership change.

**Done when:** The cutscene can run for multiple frames without existing game loops reclaiming its camera, actor animation, or input.

### Task CUT-04 — Build ocean, ship, and dense fog

**Create:** `OceanBackdrop.tscn`, `SailingShip.tscn`, `WeatherFX.tscn` and their focused scripts under `frontend/godot/scenes/cutscenes/opening/`; assets under `frontend/godot/assets/cutscene/opening/`; `frontend/godot/tests/opening_effects_smoke.gd`.

**Depends on:** CUT-01–03. **Produces:** Independently previewable `sample_at(time)` effects and a sustained, visually varied fogbound voyage.

- [x] Author a shared art scale/palette sample containing ship, player, fog, and southern coast.
- [x] Implement scrolling ocean, wake, restrained ship bob, and layered fog using director time.
- [x] Stage distinct deck, bow, wake and tracking compositions across the voyage without adding an external story event.
- [x] Confirm all land stays concealed until second 28 at every supported viewport size, including during resize.
- [x] Add reduced-motion and reduced-flash variants without changing shot duration or coast-reveal timing.
- [x] Visually inspect each effect standalone and the combined sequence at 1× and 2×.

**Done when:** The first 28 seconds establish isolation and growing unease while remaining readable pixel art, with no premature glimpse of land.

### Task CUT-05 — Choreograph reveal, turn, crash, and sound

**Create:** `CoastReveal.tscn`, `CrashFX.tscn`, `OpeningAudio.tscn`, `opening_audio.gd`; shot animation resources under `frontend/godot/resources/cutscenes/opening/`; `frontend/godot/tests/opening_crash_smoke.gd`.

**Depends on:** CUT-02–04. **Produces:** Repeatable S06–S09 and event-based audio behavior at both rates.

- [x] Animate spatial fog withdrawal, lifting cloud shadow, daylight, and fully readable southern coast by cinematic second 29.5; begin clearing only at 28.
- [x] Author a failed turn that preserves forward momentum and makes collision unavoidable.
- [x] Implement ordered hull contact, splinter, mast, deck-wash, and player-fall cues with matching damage stages.
- [x] Compose bounded camera shake with the camera path and zero it for reduced motion.
- [x] Add separated ambience and effect voices, pause handling, 2× boundary fades, and silence from 70.5–72.
- [x] Test cancellation/restart after every crash cue; no debris, sound, or shake may leak into the next run.
- [ ] Capture and listen to 1×, 2×, and rapid rate changes during impact; check timing and peak levels.

**Done when:** The danger is understandable before impact, destruction is dramatic and reproducible, and the blackout contains an intentional quiet interval.

### Task MAP-01 — Block out the complete island and reserve expansion space

**Create:** `frontend/godot/resources/island_layout.json`, `frontend/godot/resources/island_layout.tres`, `frontend/godot/scripts/island_layout.gd`, `frontend/godot/tests/island_layout_smoke.gd`, and an annotated overview under `docs/evidence/starting-cutscene/`.

**Depends on:** Section 7 and the existing village/interior resources. **Produces:** Authoritative island outline, region/chunk definitions, recovery anchors, and a content-capacity review.

- [x] Inventory existing and planned locations with footprints, clear approaches, routes, and NPC activity space; distinguish confirmed content from reserved possibilities.
- [x] Block out the 16,384 × 12,288 exterior envelope and closed irregular shoreline with ocean on all sides.
- [x] Retain village/quest anchors, place the wreck on the southern perimeter near `(0, 3840)`, and keep logical interior rooms outside exterior geography.
- [x] Allocate the six region groups from section 7 and verify at least 35% of usable land remains available for future locations and routes.
- [x] Prove connected paths from the south spawn to all launch-accessible locations with collider clearance; measure travel time rather than relying only on map dimensions.
- [x] Check the land mask does not touch any authoring edge and that every exterior edge remains water; sample the complete coast as well as the four cardinal directions.
- [x] Review an annotated island overview and expand the envelope before detailed art if content plus reserve does not fit.

**Done when:** The whole island has a coherent, water-enclosed shape, a southern arrival beach, connected current content, and measurable expansion capacity.

### Task MAP-02 — Implement chunked island terrain, water boundaries, and save recovery

**Create:** `frontend/godot/scenes/world/IslandWorld.tscn`, `frontend/godot/scripts/island_world.gd`, `frontend/godot/tests/island_world_smoke.gd`.<br>
**Modify:** `scripts/main.gd`, `scripts/village.gd`, `scripts/world_layout.gd`, and `scripts/world_view.gd` under `frontend/godot/`; map migration persistence integrates with CUT-07.

**Depends on:** MAP-01. **Produces:** Rendered ocean/land chunks, stable coast collision, and deterministic recovery for geographically invalid older saves.

- [x] Implement the section 4 island interfaces and 1,024-world-unit chunk layout; replace the infinite green exterior fallback.
- [x] Render surrounding ocean beyond the authoring envelope and derive land/water edges and collision from shared layout data.
- [x] Load visible/adjacent chunks, pin active player/NPC/quest regions, and keep global coast collision independent of decorative loading.
- [x] Test walking and diagonal movement along the entire coast, crossing every chunk seam, and delayed chunk readiness; no path may lead into deep water or unloaded ground.
- [x] Preserve exact valid exterior/interior positions; test old water/out-of-bounds/cliff saves recover deterministically while all unrelated progress remains intact.
- [x] Preload the southern beach and inland corridor for the opening; verify logical interiors never render as distant land or trigger exterior recovery.
- [x] Capture north/east/south/west coasts and a zoomed-out debug overview; profile active chunk count and memory at both normal and large window sizes.

**Done when:** The island is surrounded by visible, impassable ocean, chunk transitions remain seamless, and older saves recover safely where the new geography requires it.

### Task CUT-06 — Author the persistent beach and recovery route

**Create:** `frontend/godot/scenes/world/ShipwreckBeach.tscn`, `frontend/godot/scripts/shipwreck_beach.gd`, `frontend/godot/resources/shipwreck_beach.json`, `frontend/godot/resources/shipwreck_beach.tres`, `frontend/godot/tests/beach_layout_smoke.gd`.<br>
**Modify:** `scripts/world_layout.gd`, `scripts/main.gd`, and player art/frame definitions.

**Depends on:** MAP-01, MAP-02, CUT-01 and CUT-03; final wreck appearance from CUT-05. **Produces:** Beach markers, real collision, safe recovery path, and connected inland exploration.

- [x] Place the wreck on the actual southern coastline near `(0, 3840)`, reconcile land/water boundaries, and finalize named marker coordinates.
- [x] Integrate the beach with island chunks and surrounding ocean; ensure no green fallback, coastline seams, or premature island visibility.
- [x] Create wreck, water, rock and debris collision footprints; retain a clear 64-unit exit and inland route.
- [x] Add real recovery/climb frames and scripted movement through the validated markers.
- [x] Check every marker and swept path using the full player collider, including at accelerated playback.
- [x] Verify continued walking reaches existing NPC content and valid older saves retain their coordinates and newly invalid exterior saves use the documented safe recovery.
- [x] Add one factual wreck inspection point and the supply interaction anchor, disabled until handoff.

**Done when:** The beach supports normal movement and exploration independently of the opening, and recovery never crosses a solid hull or deep water.

### Task CUT-07 — Persist opening progression and salvage safely

**Create:** `backend/app/database/opening_migration.py`, `backend/app/services/opening.py`, `backend/tests/test_opening.py`, `frontend/godot/scenes/cutscenes/opening/opening_session.gd`.<br>
**Modify:** `backend/app/models/player.py`, `backend/app/database/init_db.py`, `backend/app/database/seed.py`, `backend/app/api/routes/world.py`, frontend world-snapshot handling, and relevant existing new-game tests.

**Depends on:** CUT-06 final marker data. **Produces:** Run-scoped pending/complete state, atomic checkpoint, salvage persistence, and frontend readiness signals.

- [x] Test that migration treats all pre-feature saves as complete, preserves valid positions/inventory/quests/history, and recovers only exterior positions invalidated by the island boundary.
- [x] Test that fresh seed and explicit New Game produce pending state in a new `game_scope`.
- [x] Implement the atomic completion endpoint and expose state/capability in the world snapshot.
- [x] Persist map-version recovery separately from opening state; test reloads do not repeatedly relocate valid players or affect valid indoor saves.
- [x] Share the finalized authoritative beach spawn between layout validation and server checkpoint logic; add a check that they agree.
- [x] Test repeated completion after the player has moved: it cannot reset their position or duplicate rewards.
- [x] Test stale run completion, lost response/retry, quitting before completion, and restarting during a pending request.
- [x] Add the rope pickup with server-validated location, one-time collection ID, atomic inventory update, and reload/double-request tests.
- [x] Verify fallback to existing gameplay against an older backend without opening capability.

**Done when:** Replays/retries cannot corrupt saves or duplicate supplies, and unfinished/new/completed games enter the correct mode.

### Task CUT-08 — Integrate blackout loading and seamless handoff

**Create:** `frontend/godot/tests/opening_handoff_smoke.gd`.<br>
**Modify:** Director, session adapter, `main.gd`, transition overlay, beach and audio ownership.

**Depends on:** CUT-03, CUT-05–07. **Produces:** Complete S01–S10 → gameplay flow with one durable checkpoint and one control transfer.

- [x] Prepare both sets early; perform visibility and real-player placement changes entirely under black.
- [ ] Guard required-load failure and delayed checkpoint acknowledgment with explicit paused readiness states and actionable retry/return UI.
- [x] Align gameplay camera before the final step, validate endpoint, and execute the ordered handoff in section 8.
- [x] Test no one-frame player duplication, camera jump, velocity burst, leftover shake, or transparent fade swallowing gameplay clicks.
- [x] Test held Space and held WASD through the boundary: speed stays normal afterward and WASD acts only once gameplay begins.
- [x] Check normal, fully accelerated, mixed-speed, paused, and retried runs reach the same playable beach state.
- [x] Confirm HUD appears at handoff and no pickup, quest, or dialogue activates automatically.

**Done when:** The final cinematic step lands exactly where normal player-controlled movement begins.

### Task CUT-09 — Finish preview tools, regression checks, and delivery evidence

**Create:** `frontend/godot/tests/opening_render_smoke.gd`, `docs/evidence/starting-cutscene/walkthrough.md`.<br>
**Modify:** Preview harness, asset manifest, and this checklist as work completes.

**Depends on:** CUT-01–08. **Produces:** Repeatable verification and reviewable capture evidence.

- [x] Expose individual-shot entry, reset, seek, rate, reduced motion, reduced flashes, and debug markers in the preview harness.
- [x] Ensure the harness uses only fake persistence and never resets or writes a real user's game.
- [x] Run island boundary/chunk, clock, ownership, effects, crash, layout, persistence and handoff checks; record actual results.
- [x] Run relevant existing graphics, building, persistence, quest and UI checks against a disposable backend.
- [x] Capture representative frames for S01, S03, S04, S06, S08, S10 and the frame immediately after handoff.
- [x] Record full 1× and 2× playback with audio, plus a mixed-speed run and reduced-motion run.
- [ ] Inspect supported window sizes and resizing mid-shot; profile fog fill cost, crash particle peak, and hidden-scene processing on the target machine.
- [x] Confirm resource loading introduces no visible hitch at impact or beach reveal on the measured target; record hardware and observations rather than claiming a universal frame rate.
- [x] Update asset attribution, controls, debugging instructions, known limitations, and checked tasks only after evidence exists.

**Done when:** The opening is narratively legible, independently testable, and does not regress normal RPG gameplay or saves.

### Critical path

`CUT-01 → CUT-02 → CUT-03 → CUT-04 → CUT-05 → CUT-08 → CUT-09`.

Map work follows `MAP-01 → MAP-02 → CUT-06 → CUT-07 → CUT-08`. Beach work (`CUT-06`) also requires the animatic and ownership work; persistence (`CUT-07`) follows finalized beach markers. Both must finish before integrated handoff (`CUT-08`). Final artwork follows approved blockout composition; it should not block clock and ownership testing.

## 13. Verification commands and acceptance matrix

The test files are implemented; current second-pass results and native captures are recorded in the walkthrough. Use the actual installed Godot executable; README currently references a local macOS bundle, and there is no `godot` executable on the inspected shell PATH.

```bash
# From the repository root; substitute the actual installed executable if different.
GODOT_BIN=/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot
"$GODOT_BIN" --headless --path frontend/godot --editor --import
"$GODOT_BIN" --headless --path frontend/godot --script res://tests/island_layout_smoke.gd
"$GODOT_BIN" --headless --path frontend/godot --script res://tests/island_world_smoke.gd
"$GODOT_BIN" --headless --path frontend/godot --script res://tests/opening_clock_smoke.gd
"$GODOT_BIN" --headless --path frontend/godot --script res://tests/opening_ownership_smoke.gd
"$GODOT_BIN" --headless --path frontend/godot --script res://tests/opening_effects_smoke.gd
"$GODOT_BIN" --headless --path frontend/godot --script res://tests/opening_crash_smoke.gd
"$GODOT_BIN" --headless --path frontend/godot --script res://tests/beach_layout_smoke.gd
# Handoff checks require the disposable backend fixture documented in the test.
"$GODOT_BIN" --headless --path frontend/godot --script res://tests/opening_handoff_smoke.gd
"$GODOT_BIN" --path frontend/godot res://scenes/cutscenes/opening/OpeningPreview.tscn
```

Backend unittest command, from `backend/`, following the repository's existing test setup:

```bash
PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -p 'test_opening.py' -v
```

Test scripts should print labeled PASS/FAIL checks and exit nonzero on failure, matching the existing Godot smoke-test convention. Headless tests prove state and timing; they do not prove composition, audio quality, or pixel clarity. Use a normal rendered session for those.

| Acceptance case | Required result | Primary task |
| --- | --- | --- |
| Full normal playback | Exactly 60 cinematic seconds, within one update tolerance in synthetic clock tests | CUT-02 |
| Space held throughout | Approximately 30 real seconds excluding waits/pauses; all events retained | CUT-02 |
| Rate changes during fog reveal or impact | Continuous weather transition; no missed/duplicate crash events | CUT-02/04/05 |
| Pause/focus loss while holding Space | Frozen story/audio; no stuck acceleration after focus return | CUT-02/05 |
| Player input during every shot | No gameplay movement, interaction, travel, or inventory mutation | CUT-03 |
| Wide/narrow window before reveal | Shore remains hidden until second 28; no resize exposes land early | CUT-04/09 |
| Coast reveal and crash | Fog clears at 28–30; coast readable by 29.5; failed turn precedes contact at 33 | CUT-05 |
| Reduced motion and flashes at 2× | No shake; mystery and danger remain legible | CUT-04/05/09 |
| Slow/missing load or failed checkpoint | Clear retry/return state; no endless black screen or false completion | CUT-07/08 |
| Southern arrival | Wreck sits on the actual south coast; open sea is south and the playable inland route is north | MAP-01/CUT-06 |
| Complete island perimeter | Closed irregular coast; ocean on every side; no land reaches an authoring edge or permits walking into deep water | MAP-01/02 |
| Content capacity | Current/planned footprints and connections fit with at least 35% usable land reserved for expansion | MAP-01 |
| Chunk transitions and large windows | No missing terrain, collision gaps, rectangular ocean cutoff, or distant interior rooms visible | MAP-02 |
| Legacy saved game | Valid positions remain exact; newly invalid exterior positions recover to safe land with all progress preserved | MAP-02/CUT-07 |
| App closes before checkpoint | Opening remains pending and restarts from S01 | CUT-07 |
| App closes after checkpoint before final frame | Resumes safely on beach with normal controls | CUT-07/08 |
| Duplicate completion or stale callback | No teleport, duplicate reward, or new-run corruption | CUT-07 |
| Recovery at either rate | Body remains on valid route; no collision tunneling or stuck exit | CUT-06/08 |
| Handoff frame | One player, normal speed, aligned camera, cleared effects, responsive controls | CUT-08 |
| Supply pickup then reload/retry | Exactly one persisted pickup; no duplicated item | CUT-07 |
| Walk inland after opening | Existing NPC, inventory, building and quest flows still work | CUT-06/09 |

## 14. Definition of done

- [x] The complete emotional progression reads in a normal-speed capture without explanatory dialogue.
- [x] The ship sails through dense fog until it suddenly dissipates immediately before the wreck.
- [x] Normal duration is 60 cinematic seconds; held-key 2× works throughout, including recovery and fades.
- [x] Ocean, fog, weather, crash, audio, and recovery can be previewed independently.
- [x] The coastline reveal provides enough time to understand the approaching disaster.
- [x] Blackout, silence, calm beach reveal, and recovery preserve the intended contrast.
- [x] At the final step onto sand, the camera is already aligned and movement becomes responsive.
- [x] The player crashes on the southern shoreline, can investigate wreckage, collect supplies once, and walk north inland.
- [x] A closed coastline surrounds the complete island, with visible ocean on all sides and no walkable land bridge to a map edge.
- [x] The region budget accommodates current content and documented expansion reserves; loaded chunks do not expose seams or gaps.
- [x] Legacy saves and current village gameplay remain usable; new runs receive the opening.
- [x] Timing/state tests pass and rendered/audio review evidence is recorded for both playback rates.


## 15. Historical first-pass implementation record — 2026-10-13

The existing working-tree edits to this specification and untracked skill files were retained. Implementation follows the two dependency chains in section 12. Installed runtime: **Godot 4.5.1 stable** at `/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot`; the skills' 4.7 examples were adapted to this installed runtime.

- CUT-01/02/03: graybox captures preceded original pixel assets. Twelve shot intervals total 90 seconds. Manual AnimationPlayers own shot framing; one director splits advancement at every boundary/cue. Space affects only this clock. Input, player visuals, camera, HUD, autosaves and building travel have explicit cinematic ownership.
- MAP-01: retained the proposed envelope. Usable mask area after the coast exclusion is 108,856,320 world units². Conservatively budgeting all three launch regions consumes 34,051,840, leaving **68.7%** uncommitted. North/east/perimeter remain reservations, not promised feature sets. Village props/approaches and logical interiors retain their anchors. The south route bends around the existing well; measured length is 4,622 world units (~25.7 seconds at 180 units/s). See `docs/evidence/starting-cutscene/island-overview.png`.
- MAP-02: shared 32-unit land-cell mask drives terrain and independent global coast collision. Chunks are populated synchronously in bounded batches, with a visible/adjacent ring and pinned village/forest NPC regions. This implementation deliberately avoids asynchronous decorative loading and its seam readiness race. It does not implement streaming authoritative NPC state.
- CUT-06/07: marker JSON is shared by backend and Godot. Legacy rows migrate to complete; geographic migration is separate and preserves valid floats/interiors. Completion is run-scoped and idempotent, and rope salvage commits its collection ID with inventory. Failed completion holds at 89.8. The main application and request deadlines remain alive.
- CUT-04/05/08: original integer-grid ship/damage/mast/recovery art, sampled ocean/fog/crash effects and synthesized separate audio voices replace the graybox. Both sets prepare before playback; the real body is introduced under black. Final control transfers at the shared `(0,4560)` handoff marker.
- Verification so far: 429 backend tests pass. Clock, ownership, effects, lifecycle, beach, island layout and integrated checkpoint/salvage/reload checks pass. Coast physics checked 4,962 outward straight/diagonal sweeps and 13,462 land seam sweeps. Remaining delivery evidence and any limitations are recorded in the walkthrough as verification finishes.

Implementation decisions: focused absolute-time effect samplers supplement manually advanced property animations; no generic cutscene framework or `Engine.time_scale` changes. No external artwork or sampled audio is introduced. Optional sound captions, reduced motion and soft daylight are available in preview and pause settings. Full production recording/listening and target-machine observations must be distinguished from headless state checks; unchecked acceptance items are not implied complete.

Final validation refinements: source review identified and resolved replacement-opening HUD loss, completed-run reconnect ownership, and stale beach location in NPC context. Their regressions failed before the fixes and passed afterward. Surf remains attached to the persistent beach from preparation, with ownership transferred at handoff without restarting playback; native checks verified the same playing voice and full 88,200-sample WAV loops. A full **196,608-cell** cross-language mask comparison found eight exact-edge disagreements in Python's polygon rule; the backend now follows Godot's closed-edge rule and both match the shared SHA-256 contract. Recovery obstruction fault injection uses a single latched safe fallback, with later ordinary saving covering a fallback position distinct from the checkpoint marker.


Final evidence and exact launch instructions: [walkthrough](../evidence/starting-cutscene/walkthrough.md). Normal native playback measured **90.006 s**; held-action native 2× measured **45.015 s**. Backend full suite: **431 tests**. Current Godot regression/physics, real-backend handoff/reload, lifecycle, obstruction fallback and native pixel-render checks are recorded in that directory. The island mask contract checks every authoring cell against both languages. Remaining unchecked items concern subjective listening, compiled-resource fault injection and extended GPU/hidden-scene profiling; objective audio levels/silence, full captures and static chunk memory/counts are available. Small loose planks are walk-over dressing; authored larger hull/mast/rock solids provide the wreck/debris collision footprints.


## 16. Approved second visual and pacing pass — 2026-10-13

The user approved implementation directly. The first 30 seconds were removed; ten shots retain the later pacing and causal order. Start pose, camera offset and periodic sailing phase continue the original time-30 state. Cue IDs `creak_1` and `creak_2` are removed; all later cues move earlier by 30 seconds. Clock/seek selectors derive the shot count from boundary data. Named times are shared across stage, camera, weather, audio, crash and recovery. Existing completed runs retain `opening_version=1` and never replay because of this presentation change.

Seven opaque, individual source-grid fog formations have different dimensions and irregular clustered silhouettes, shaded undersides and restrained highlights. Uneven overlap and slow relative drift form deep banks. A matching opaque distant field buries its edge beneath the formations; stage coast/scenery also remain concealed until release at 28, covering extra-wide windows. Reduced motion suppresses drift while retaining the same reveal.

The persistent southern beach and cinematic coast use the same surface and scenery definitions. Original warm sand/wet sand, turquoise shallow shelves, broken foam lines, palms, broadleaf canopies, shrubs, flowers, shells, stones, driftwood and landmarks are encoded as exact source-pixel runs. No reference pixels, watermark or pencil graphic were copied. All source pixels occupy two world units. Palette and density derive from the supplied image; island orientation remains north inland / south sea.

The central bay shoreline and wreck move from Y4800 to Y3840, with handoff Y3600 and all beach markers/solids rebased together. Village, quest, interior and NPC anchors are unchanged. Map version 2 migrates newly offshore version-1 positions once using the shared recovery policy, preserving run state and inventory. All 106,187 land cells connect to the new spawn. Usable land after coast exclusion is 106,363,904 wu²; 67.99% remains uncommitted.

Scenery is deterministic from global cell coordinates, with a single owner chunk at each trunk/prop origin. Whole nodes, shadows and collision footprints can cross seams; nothing is clipped into terrain textures. A full adjacent loaded ring exceeds the largest formation's extent. Props share the actor Y-sort hierarchy; trunks, landmark rocks, fallen log and marker have narrow ground footprints. Loose stones, shells, flowers and shrubs are walk-over dressing. The full camera footprint plus margin is dressed up to 2,200 units either side, without occupying future northern/eastern reserves. Exclusion zones keep the recovery corridor, salvage and route clear. Older saves inside new trunks recover through the existing world-layout validator.

Progression: wreck/open sand → palms/scrub → shaded broadleaf stretch (Y1900–2650) → fallen-log composition and flowering clearing (Y1580) → trail marker (Y940) → established village approach. The route remains optional to follow and requires no new interactions.

### Second-pass acceptance checklist

- [x] 60/30-second clocks, retained cue order, immediate release, mixed rate, focus/pause, safe seek/restart and 59.8 readiness barrier.
- [x] Shared coast relocation, map-v2 migration, completed/pending run compatibility, recovery and salvage clearance.
- [x] 3,662.307-wu / 20.346-second direct route, deterministic scenery after unload/reload, collidable trunks/landmarks and clear path.
- [x] Original overlapping formations, persistent coastal art and full-footprint route dressing.
- [x] Final native capture review, complete recordings and full regression results — see walkthrough for current evidence.

Section 15 and files outside `second-pass/` are historical 90-second evidence and must not be interpreted as validation of this revision.
