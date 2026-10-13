# Starting cutscene — The signal in the fog

**Status:** Design and implementation checklist; gameplay implementation has not started.  
**Created:** 2026-10-13.  
**Confirmed duration:** 90 seconds of cinematic time. Hold a keyboard key to play at 2× speed; release it to return to 1×.  
**Technology:** Godot 4, GDScript, 2D top-down pixel art. Confirm the project's installed Godot minor version before implementation.  
**Goal:** Deliver a deliberately directed shipwreck opening that establishes the island's mystery and ends with the player freely exploring the beach.

## 1. Creative brief and boundaries

The player arrives by wooden sailing ship through an apparently endless, fog-covered ocean. A distant lighthouse appears and signals deliberately. The fog and clouds clear with unsettling speed, exposing land directly ahead. The vessel cannot turn in time, runs aground, and breaks apart. After darkness and silence, the player awakens in the wreck, climbs onto the beach, and gains control.

The emotional sequence is fixed:

**Isolation → Curiosity → Unease → Sudden Danger → Disaster → Survival → Exploration.**

Success means the player understands three things without exposition: they are stranded; the island is explorable; and something about the lighthouse was unusual. The opening must not establish who signaled, what the signal means, or whether it caused the crash.

### Confirmed requirements

- A scripted opening with no player movement, inventory use, dialogue interactions, or steering.
- Animated ocean, ship, fog, lighthouse beam and signaling, followed by a rapid weather change.
- A readable coastline reveal before the collision, with a visibly unsuccessful turn.
- Hull impact, splintering timber, falling mast, water over the deck, and the player losing balance.
- Fade to black, a short silence, then a calmer wrecked beach.
- Recovery and ship-exit animation before normal gameplay begins.
- Control transfers at the moment the player finishes stepping onto the beach.
- The visual language remains consistent with the existing 2D pixel-art RPG.
- Individual shots and effects can be built, previewed, reset, and tested independently.
- A 90-second normal playback and hold-to-play-at-2× keyboard control.

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

These defaults allow the design to proceed. They are not additional confirmed story facts. The signal's true meaning, the player's prior voyage, crew fate, and the island's larger plot remain unwritten.

### Scope

Deliver the cinematic, playable wrecked beach, nearby inspectable wreckage and collectible supplies, a clear inland route, save continuity, and a dependable gameplay handoff. The first delivery does not need ship steering, simulated sailing, a dynamic weather system for the whole island, procedural destruction, swimming, combat, a lighthouse interior, or a complete island map.

## 2. The 90-second shot plan

All times below are **cinematic seconds**, not wall-clock seconds. They also serve as stable preview anchors. The intervals are consecutive and total exactly 90 seconds.

| ID / time | Emotion and image | Camera and animation | Sound / exit cue |
| --- | --- | --- | --- |
| S01 · 0–12 · 12 s | Isolation. A wooden ship crosses dark, restless water surrounded by pale-gray fog. No land is readable. | Begin with substantial empty ocean around the ship. Track slowly; scroll wave texture and wake to establish forward travel. Small, irregular visual bobbing. | Wind, hull creaks, wave wash; establish space before any musical tension. Ship remains underway. |
| S02 · 12–22 · 10 s | Isolation becomes personal. Reveal the player standing on deck, watching the mist. | Drift toward the deck and reframe around the player's position. A subtle head/body turn makes the character recognizable. Keep the same top-down art perspective. | Closer rope and plank sounds. No dialogue. Hold long enough to register the player. |
| S03 · 22–32 · 10 s | Curiosity. A faint point of light resolves into a lighthouse silhouette on an otherwise hidden headland. | Player notices the light; reframe toward the upper portion of the image. A broad, ordinary sweep briefly catches water and mist. | A restrained tonal layer may enter. No audible electronic beeping from a distant lighthouse. |
| S04 · 32–46 · 14 s | Unease. The light stops behaving like a simple rotating beacon and repeats an intentional motif twice. | Keep lighthouse and part of the ship/player in the composition. Let the sweep settle toward the ship; gate the lamp and visible beam with the motif. The player turns toward it. | Reduce incidental creaks enough to focus attention. Signal recognition comes from repeated timing, not explanatory text. |
| S05 · 46–50 · 4 s | Uncertainty. The player keeps watching; the sea continues carrying the ship forward. | Hold the unanswered look. The beacon returns to a faint ordinary sweep. | Leave an uncomfortable gap. Avoid a musical cue that declares the lighthouse evil. |
| S06 · 50–56 · 6 s | False relief becomes danger. Fog tears away and clouds part; sunlight reveals the coastline. | Main fog withdrawal occurs during 50–53. Light opens across water during 51–54. By 54, beach, rocks, and high coastal terrain are clearly readable. Hold the realization through 56. | Wind changes, water sharpens, then tension rises. Brightness initially feels welcome. |
| S07 · 56–63 · 7 s | Sudden danger. Shore advances too quickly. The ship attempts to turn. | Lead the bow toward looming sand and rocks. Change heading, sail tension, wake direction, and drift; the hull still slides toward shore. Never imply the player could have steered. | Rigging strain, increasing surf, stressed timber. End at first grounding contact. |
| S08 · 63–69 · 6 s | Disaster. The keel strikes, the hull tears, mast falls, water crosses the deck, and the player loses footing. | Choreographed contact at 63; splinter burst near 63.3; mast collapse near 64.2; deck wash near 65; player fall near 65.4. Fade starts at 67.5 and reaches black at 69. | Low impact, cracking timber, ropes, falling mast, rushing water. Prioritize distinct layers over sheer loudness. |
| S09 · 69–73 · 4 s | Disorientation. Black screen. | Stay fully black; exchange the intact set for the persistent wrecked beach. | Impact tail ends by 70.5; silence from 70.5–72; gentle surf begins at 72. No speed-status text over this intentional blackout. |
| S10 · 73–79 · 6 s | Survival. The wreck rests partly in shallow water; debris is scattered over sand. | Fade in during 73–75. Establish the same coastline and recognizable broken ship. Settle toward the motionless player. | Calm surf and distant seabirds; no fog, no continuing storm or collapse. |
| S11 · 79–87 · 8 s | Survival becomes resolve. The player stirs, braces, stands, and climbs through the hull breach. | Use authored recovery/climb frames and a short scripted path. Camera begins returning to normal gameplay framing. | Breathing/cloth if available, hands on timber, footsteps. No automatic inventory collection. |
| S12 · 87–90 · 3 s | Exploration. Final steps carry the player onto safe sand. | Camera completes its alignment by 89.8. At 90 the final step lands, recovery pose becomes normal idle, and control transfers. | Beach ambience continues uninterrupted. Reveal the movement hint and normal HUD at handoff. |

### Directing rules

- Establish the ocean before centering the player; isolation needs visible negative space.
- Let the player notice the lighthouse before its signaling becomes strange.
- Show the land clearly for several seconds before impact. The audience must understand the danger rather than infer it from shake.
- The weather change is unnaturally abrupt, but its cause is never shown.
- Crash energy comes from multiple ordered events, not continuous maximum shake.
- Preserve a real silence between disaster and survival.
- Do not interrupt the first free step with a quest popup or NPC conversation.
- At 2×, preserve every beat and event in the same order; do not substitute a shortened edit.

## 3. Making the sequence cinematic in top-down pixel art

A top-down scene has no literal distant horizon. Create distance through placement toward the top of the frame, fog occlusion, reduced contrast, simplified silhouettes, and a small apparent lighthouse. The distant lighthouse is a cinematic backdrop representation; a future explorable lighthouse would use normal gameplay scale.

Use framing, tracking, lead space, occlusion, and timed reveals rather than changing into a side-view illustration or attempting a 3D orbit. Wide-to-player shots should primarily reframe and move the ship through the composition. Keep the existing `Camera2D` zoom at `Vector2(0.5, 0.5)` for the first implementation. Fractional animated zoom would disturb the established pixel scale. A closer shot, if necessary after the animatic review, needs separately authored framing or a deliberate shot cut and visual QA.

Keep a consistent screen direction: the ship progresses generally upward toward land; its unsuccessful turn bends the bow without reversing the scene's geography. In the crash set, the coast is above the ship. In the beach set, inland remains upward and the sea remains below. Broken mast, hull shape, and shoreline rocks provide continuity across the blackout.

### Pixel and layer rules

The existing art standard uses one source pixel per two world units, 16×16 source terrain tiles, 24×32 actor frames, nearest-neighbor sampling, and integer enlargement of a low-resolution world viewport. Preserve it. See [the current pixel-art standard](../../frontend/godot/assets/PIXEL_ART.md).

- Draw all weather, beam, spray, and destruction effects inside the low-resolution world viewport.
- Keep UI and the full-window fade in the parent viewport so they cover resize margins too.
- Keep physics, path positions, and save coordinates as floats; quantize only their visual presentation.
- Snap the composed camera position, including shake, to the two-world-unit render grid once per frame.
- Prefer alternate ship frames to rotating a large detailed pixel sprite through many arbitrary angles. Subtle rotation is a prototype option requiring visual review.
- Use a limited palette with dithered/clustered edges for mist, light, and spray; avoid smooth high-resolution effects pasted over the pixel scene.
- Explicitly layer sea → wake/foam → ship/deck → player and rail occluders → spray/beam → foreground fog. Keep scenery intended to share actor ground sorting as sibling nodes in the world's Y-sort hierarchy.

The minimal supported window is currently 960×540; compose mandatory action inside its safe frame. At 1280×720 and 1920×1080, extra visibility should reveal ocean or scenery rather than unfinished set edges. Resize must not expose the hidden shore before S06.

## 4. Architecture and alternatives

| Approach | Strength | Cost or limitation |
| --- | --- | --- |
| **Recommended: a small director, shot AnimationPlayers, and a shared cinematic clock** | Editable timing, independent previews, deterministic 2× playback, clear save/handoff boundaries | Requires explicit ownership and reset contracts |
| One large 90-second AnimationPlayer | Fast first animatic; all keyframes visible together | Cross-scene paths become fragile; debug entry, loading, cancellation, and persistence become awkward |
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
│           ├── Village / interiors   hidden or inactive during opening
│           ├── OpeningStage          temporary cinematic set
│           │   ├── OceanBackdrop
│           │   ├── CoastReveal
│           │   ├── SailingShip
│           │   │   ├── Hull / rigging / mast / rails
│           │   │   └── PlayerVisualProxy
│           │   ├── LighthouseSignal
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
| `LighthouseSignal` | `sample_at(time: float)` and `reset()`; computes angle, pulse envelope, lamp intensity, beam visibility, and water highlight together |
| `WeatherFX` | `sample_at(time: float)` and `reset()`; fog coverage/drift, cloud shadow, sea tint, and daylight |
| `CrashFX` | `trigger(cue_id: StringName)` and `reset()`; repeat-safe bursts and ship damage stage changes |
| `OpeningAudio` | `trigger(cue_id: StringName)`, `sample_mix(time: float)`, `set_paused(value: bool)`, `reset()`; owns playback voices and state-boundary fades |
| `ShipwreckBeach` | Exposes `RecoveryStart`, `HullExit`, `ControlHandoff`, `SafeFallback`, and `InlandRoute` markers; supplies colliders and interaction anchors |
| Player visual adapter | `set_scripted_mode(enabled: bool)`, `play_scripted(animation: StringName)`, `set_facing(direction: StringName)`; suspends automatic idle/walk selection |

The director accepts a fake persistence adapter in preview/test mode. Effect scenes never access the backend, grant items, unlock input, or change global scenes.

### State and ownership

```text
PREPARING → VOYAGE → PLAYER_REVEAL → LIGHTHOUSE_APPEARS → SIGNAL
          → UNEASE → WEATHER_REVEAL → APPROACH → CRASH → BLACKOUT
          → BEACH_REVEAL → RECOVERY → EXIT → GAMEPLAY
```

`PAUSED` and `WAITING_FOR_DATA` are overlays on the current state, not extra story shots. Cancellation is a lifecycle operation. Each state has explicit entry values, a bounded duration, and cleanup. There must be one owner per property: shot animation owns the camera base; shake owns an additive offset; the camera presenter owns the final transform. Do not have a Tween and an AnimationPlayer writing the same property.

## 5. Time, held-key 2× playback, pause, and cues

### The timing contract

- Normal: cinematic time advances by real frame delta.
- Space held: cinematic time advances by twice real frame delta.
- Space released: return to 1× on the next update, with no restart or seek.
- Paused, unfocused, or waiting for required data: cinematic time does not advance.
- All 90 cinematic seconds played at 2× take approximately 45 wall-clock seconds, excluding readiness waits and explicit pauses.
- The main game, backend deadlines, network timeouts, and menus remain on their own normal clocks.
- Completion occurs exactly once when cinematic time reaches 90.0; the final state is evaluated before input is unlocked.

**Do not use `Engine.time_scale` for fast-forward.** It would affect unrelated systems, and changing it alone would not define how audio and shader animation should behave.

Use an Input Map action rather than hardcoding the physical key in director logic. Show `Hold Space · 2×` quietly near the beginning, using the actual binding label. While held, show a small `2×` indicator except during intentional blackout. No tap-to-skip behavior. Consume fast-forward during the cutscene; do not deliver it as a gameplay action at handoff.

The input mode is `CINEMATIC` until handoff. Escape may open pause/settings; the cinematic itself remains non-interactive. On focus loss, pause and clear the effective speed. On focus return, require a fresh key press before resuming acceleration so a missed key-release event cannot leave it stuck at 2×.

### One clock for every visual system

The director computes the desired time once. Split its advance at shot boundaries and cue timestamps, dispatch each crossed event in chronological order, and apply any remaining delta to the next shot. A frame that crosses several boundaries must not lose events or discard the leftover time.

Use manual processing for registered `AnimationPlayer`s and advance them with director-scaled delta at speed scale 1.0. Do not also set their speed to 2.0, which would double-count acceleration. Sprite frames, beam pulses, and ocean loops derive from cinematic time or are advanced through the same adapter. Pass explicit `cinematic_time` into shaders; shader `TIME` is not the cutscene clock.

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

Fog disappearance is spatial: banks pull apart and dissolve over roughly three cinematic seconds. Simultaneously lift cloud-shadow modulation and shift the sea from dark slate toward daylight blue-green. The land already exists behind the masking, so it emerges rather than popping into existence. A simplified initial mask may conceal its silhouette entirely until the release cue.

Use explicit local modulation or a scoped world lighting setup; do not accidentally brighten the UI or village while the opening is active. A `PointLight2D` can provide the lighthouse lamp's local light, while a textured beam sprite/polygon supplies the visible shaft through mist. Godot's 2D lights illuminate canvas items; the volumetric-looking beam is an authored visual effect. [2D lights and shadows](https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html).

### The lighthouse motif

The beam initially sweeps normally. During S04 its orientation settles toward the ship and its light deliberately pulses. Proposed motif, repeated exactly twice:

| Part | State | Cinematic duration |
| --- | --- | --- |
| 1 | Short illumination | 0.8 s |
| 2 | Dark | 0.8 s |
| 3 | Short illumination | 0.8 s |
| 4 | Dark | 0.8 s |
| 5 | Longer illumination | 1.6 s |
| 6 | Dark pause | 2.2 s |
| Total | One motif | 7.0 s |

The repetitions occupy 32–39 and 39–46. The lamp, beam, and water highlight share one envelope so they cannot disagree. Use eased intensity edges and a small illuminated area, not full-screen flashes. At 2×, each part halves in real duration without changing the motif's proportions.

Do not label this as a translated message, add subtitles that decode it, randomize the timing, or reveal a person operating the lamp. The short-short-long visual motif is a narrative seed; its eventual interpretation remains a story decision. A reduced-flash setting can retain the timing through low-contrast intensity changes.

### Crash and damage staging

Use authored stages: intact → grounded/deck torn → mast fallen → final wreck. Stage changes, splash bursts, and camera jolts are repeatable cues. Hull breakup can use a few animated fragments with authored trajectories; a rigid-body destruction simulation is unnecessary and makes repeatable framing harder.

Start shake with a short displacement at contact, then a smaller irregular decay during secondary failures. Proposed maximum: six low-resolution render pixels for the principal impact, falling below two pixels by the mast aftermath. Normal voyage bob should be much smaller. Quantize shake only after composing it with the camera path. Set shake to zero in reduced-motion mode.

The mast should fall across readable deck space and settle into the same orientation used by the beach wreck. Spray can briefly cover the player fall and conceal an art swap, but should not obscure the entire impact. Do not use a full-screen white flash. No violent camera rotation is needed.

## 7. Beach, recovery, and exploration

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

Proposed blockout: place the beach south of the village in the existing continuous coordinate space, with its local origin around world `(0, 2304)`. Keep sea to the south and inland to the north. This is a layout starting point, not a finalized spawn coordinate; derive final absolute marker positions from the authored beach resource and share the authoritative handoff position with the backend. Verify the region against existing interior locations and older saved positions before finalizing it.

Author a minimum 64-world-unit-wide recovery exit and inland path for the existing 24×16 foot collider. Keep debris out of the route and provide enough sand for the first movement input in any direction. The recovery body follows an authored, collision-checked path; disable user input, not the ability to advance scripted movement. Use a swept movement check in physics updates or an equivalent validated path, with a bounded fallback if a collider unexpectedly blocks the exit.

Add dedicated `recover`, `brace`, `stand`, and `climb_out` frames using the existing player palette and foot pivot. The prototype may use timed idle/walk poses, but that is not final recovery animation. Avoid squashing the full sprite to simulate every pose.

### First free actions

1. Move freely on the sand and look back at the damaged ship.
2. Inspect a hull breach or recognizable piece of wreckage for a short factual description.
3. Collect a nearby salvage supply through a real pickup interaction.
4. Follow an obvious but unforced inland route toward future NPC encounters and help.

Keep existing starting food and water in inventory for compatibility; do not remove them merely to stage a pickup tutorial. Proposed extra salvage is one rope bundle, using the existing item vocabulary, subject to validating current inventory behavior. Pickup state and inventory addition must be persisted together and replay-safe. A repeated request or reload must not duplicate the supply. Keep pickup labels and prompts hidden until gameplay is active.

Environmental text can describe facts such as splintered timber or signs of an unnatural light. It must not assert sabotage or tell the player the correct interpretation. The first objective may read `Explore the shore`, but should appear unobtrusively after the player is already in control.

## 8. Exact handoff and loading contract

The handoff is an ordered transition, not simply setting a boolean:

1. While black, activate beach colliders and real player; place the player at `RecoveryStart`, reset velocity, and enable scripted visual mode.
2. Reveal the beach and run recovery/exit while normal interactions remain locked.
3. During S12, move the gameplay camera target into alignment with its normal follow target. Its zoom remains the normal 0.5 throughout.
4. Prepare a durable completion checkpoint before the final frame, as described below. Pause the cinematic at 89.8 if that required acknowledgment is not ready.
5. At 90.0, evaluate the final pose and place/check the player's feet at `ControlHandoff`. If validation failed earlier, resolve to `SafeFallback` before showing the final step.
6. Clear residual shake, scripted velocity, and cinematic-only visibility/modulation. Set normal facing and idle; disable scripted visual mode.
7. Transfer the one camera to gameplay follow and enable normal movement and interaction on the next physics update. There must be no intervening camera snap.
8. Reveal HUD and movement guidance. Release cinematic input ownership; any held fast-forward key has no effect on gameplay speed.
9. Emit completion once; dispose of the opening stage and cinematic audio voices, retaining beach scenery and its ambient audio.

The user gains control at the visible final step onto sand. There is no extra cinematic pan after that point.

Request beach resources during `PREPARING` and load as early as practical. If background loading is used, poll threaded load status and only retrieve the resource when ready; Godot notes that retrieving it too early can block. Instantiation and adding nodes to the tree still need to be staged and measured. [ResourceLoader](https://docs.godotengine.org/en/stable/classes/class_resourceloader.html).

Ideally both sets are ready before the opening starts, so the designed blackout lasts exactly four cinematic seconds. If a required load fails, stop advancing at the safe black boundary, show a small actionable retry/return message after a short real-time delay, and avoid an indefinite silent black screen. Such waits are operational interruptions, not part of the 90-second authored duration. Holding Space must not accelerate loading, network retries, or their timeout.

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
| `frontend/godot/scripts/village.gd` | Uses its own terrain plus a very large green background; props are world siblings | Give beach terrain explicit layering; do not leave green beneath ocean or village NPC labels over the opening |
| `frontend/godot/scripts/world_layout.gd` | Validates village/interior positions and recovers blocked saves | Dispatch validation to the beach layout within its bounds; preserve old exterior/interior saves elsewhere |
| `frontend/godot/scripts/main.gd` | Existing fade at CanvasLayer 20 handles building travel | Share a transition owner or prohibit concurrent fades; cinematic and travel must not race |
| Same file | Reduced scenery motion currently only calls the village | Route the preference to ship bob, fog drift, particles and shake as well |
| `backend/app/api/routes/world.py` | World snapshot, new game, and position PUT; no opening checkpoint | Add explicit opening progression scoped to the existing run |
| `backend/app/models/player.py` | Has `game_scope`, inventory, position, and location | Use `game_scope` to reject stale opening writes after New Game |

The opening should have no dependency on LLM output. Network-generated NPC behavior is not responsible for shot timing, lighthouse flashes, crash outcomes, or unlocking movement.

### Save model and migration

Proposed new player state:

- `opening_version: int = 1` for this authored sequence.
- `opening_state: String` with values `pending` or `complete`.
- Persisted salvage collection IDs, owned by the beach pickup service.
- Expose existing `game_scope` with the world snapshot for run-scoped writes.

For **existing saves**, migration assigns `complete`, preserving position, inventory, quest state, histories, and NPC state. Missing opening metadata from an older server must not make an existing save replay the crash. Only newly seeded games and explicit New Game reset use `pending`. The frontend must detect an older backend's missing capability and keep its existing gameplay path rather than invoking unsupported checkpoint requests.

During a pending opening, suppress ordinary player-position autosaves. Cinematic/proxy coordinates are never persisted. Quit before completion leaves `pending`; the next launch starts the opening at S01. Do not force the user to watch the sequence merely to quit.

Proposed completion endpoint: `POST /world/opening/complete`, accepting `{game_scope, opening_version}`. The server validates the current run, locks the player, and atomically sets `complete`, the authored safe beach spawn, and `current_location = "shipwreck_beach"`. Repeating the request for the same completed run is harmless and **must not teleport a player who has since walked away**. A stale run gets a conflict response and cannot mutate the new game.

Send this request once the final beach/path state is ready, during S12, so acknowledgment can arrive before handoff. If the app closes after it succeeds but before the last step, the next launch resumes at the safe beach spawn; it does not attempt to restore a partially animated character. If it fails, hold at the pre-handoff readiness barrier, retain the locked final approach, and offer retry/return. Do not claim a save succeeded or silently allow progression that will disappear on reload.

This small acknowledgment window is the deliberate tradeoff between an uninterrupted normal handoff and crash-safe persistence. At normal local-server latency the opening remains 90 seconds; outages can extend wall-clock time. Error UI appears outside the story clock and is never sped up.

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
- Reduced flashes keeps lighthouse rhythm readable through localized low-contrast changes. Test it at 2×; acceleration affects real flash timing.
- Offer optional concise environmental captions for key sounds; do not decode the signal.
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
| Lighthouse | Distant silhouette, lamp, beam texture, water highlight; all linked to one signal envelope |
| Coast | Sand/wet sand, shallow/deep water edge, rocks, cliff/high terrain shapes, inland connection |
| Crash | Timber fragments, broken sail/rope details, mast fall frames, spray and deck-wash frames |
| Player | Existing voyage idle/look poses plus brace, fall, recover, stand and climb-out animation |
| Beach props | Persistent mast/hull pieces, debris, one inspectable anchor, one supply container/pickup |
| Audio loops | Open-sea wind and water, stressed rigging, quiet beach surf, sparse distant seabirds |
| Audio one-shots | Creaks, grounding impact, hull crack, mast break/fall, splash, footing loss, recovery and steps |
| UI | Binding-aware speed hint, active 2× indicator, pause/retry state, handoff movement hint |

Track asset origin and licensing in `assets/cutscene/opening/README.md`. Do not produce a photorealistic ship or smooth painted fog that conflicts with the established kit. Temporary blockout art and missing recovery frames must remain clearly marked as prototype assets.

## 12. Implementation checklist

**Goal:** Implement the specified opening and beach handoff without breaking current village gameplay or existing saves.  
**Architecture:** A run-scoped opening director advances independent shots and effects through one cinematic clock; the existing viewport renders both the opening and persistent beach. Backend-owned progression provides a durable endpoint.  
**Spec:** Sections 1–11 of this document. All listed new paths are proposed; existing files must be re-read before changing them.

Each task has an independently reviewable deliverable. Checkboxes describe future work; none imply implementation has occurred. Implement the graybox and timing foundation before commissioning final animation or polishing destruction.

### Task CUT-01 — Build the 90-second graybox animatic

**Create:** `frontend/godot/scenes/cutscenes/opening/OpeningPreview.tscn`, `OpeningStage.tscn`, `opening_preview.gd`, `opening_timeline.gd`, and `frontend/godot/resources/cutscenes/opening_timing.tres`.

**Depends on:** This design. **Produces:** A visual timing reference and authoritative S01–S12 durations, shot IDs, and cue timestamps.

- [ ] Record the actual Godot executable/minor version and confirm manual animation APIs work in it.
- [ ] Define the 12 shot intervals and named cues as data; assert no gaps, overlaps, or total other than 90.0 seconds.
- [ ] Block out ship, player, lighthouse, fog, coast, wreck, and exit path using simple shapes.
- [ ] Play the full sequence at the current pixel scale at 960×540 and 1280×720.
- [ ] Capture an animatic showing the repeated signal, visible attempted turn, impact, silence, recovery, and final free-control location.
- [ ] Review pacing against the emotional sequence; adjust within the fixed 90-second total and update this table if timing changes.

**Done when:** The story reads without final art or explanatory dialogue, and the lighthouse feels intentional without explaining its purpose.

### Task CUT-02 — Implement the shared clock and held-key acceleration

**Create:** `opening_director.gd`, `opening_shot.gd`, `opening_context.gd` under `frontend/godot/scenes/cutscenes/opening/`; `frontend/godot/tests/opening_clock_smoke.gd`.  
**Modify:** `frontend/godot/project.godot` for `cutscene_fast_forward`.

**Depends on:** CUT-01. **Produces:** The director/shot contracts from section 4, 1×/2×/paused progression, and repeat-safe cue dispatch.

- [ ] Write clock checks for 90 seconds at 1×, 45 seconds at 2×, and a mixed run: 20 real seconds at 1× plus 35 at 2× reaches 90 cinematic seconds.
- [ ] Test short press/release changes, pause during acceleration, focus loss, and reaching several cue/shot boundaries in one update.
- [ ] Implement a single time owner with manual AnimationPlayer advancement and explicit shader/effect time.
- [ ] Add Space binding, binding-aware hint, and active 2× display; clear the effective hold on focus loss.
- [ ] Test that each crash cue and completion fire exactly once; preview seeking must not fire past cues.
- [ ] Verify `Engine.time_scale` remains unchanged and no gameplay timer or timeout is accelerated.

**Done when:** Both normal and accelerated playback reach the same endpoint and event log, with no skipped or duplicate events.

### Task CUT-03 — Add gameplay, camera, and animation ownership

**Create:** `frontend/godot/scenes/cutscenes/opening/cinematic_camera.gd`; `frontend/godot/tests/opening_ownership_smoke.gd`.  
**Modify:** `scripts/main.gd`, `scripts/world_view.gd`, `scripts/player.gd`, and `scripts/person.gd` under `frontend/godot/`.

**Depends on:** CUT-02. **Produces:** Explicit cinematic/gameplay ownership and scripted player visual mode.

- [ ] Add tests proving held WASD, E, F, I, and clickable gameplay controls cannot move, interact, transfer items, or start travel during the opening.
- [ ] Route camera updates through one owner; test that `main.gd` no longer overwrites cinematic framing every frame.
- [ ] Suspend automatic idle/walk selection during scripted recovery and restore it afterward.
- [ ] Separate visual voyage proxy from the real body; verify only the real body can be saved or receive gameplay input.
- [ ] Suppress NPC labels, inventory/quest prompts, building detection, and regular position saves during cinematic mode.
- [ ] Keep pause and quit available; clear velocity and shake on every ownership change.

**Done when:** The cutscene can run for multiple frames without existing game loops reclaiming its camera, actor animation, or input.

### Task CUT-04 — Build ocean, ship, fog, and lighthouse

**Create:** `OceanBackdrop.tscn`, `SailingShip.tscn`, `LighthouseSignal.tscn`, `WeatherFX.tscn` and their focused scripts under `frontend/godot/scenes/cutscenes/opening/`; assets under `frontend/godot/assets/cutscene/opening/`; `frontend/godot/tests/opening_effects_smoke.gd`.

**Depends on:** CUT-01–03. **Produces:** Independently previewable `sample_at(time)` effects and a legible lighthouse motif.

- [ ] Author a shared art scale/palette sample containing ship, player, coast, and lighthouse.
- [ ] Implement scrolling ocean, wake, restrained ship bob, and layered fog using director time.
- [ ] Implement the seven-second motif and verify the exact lamp/beam on/off intervals over both repetitions.
- [ ] Confirm the lighthouse appears before land is readable and the same region remains concealed at every supported viewport size.
- [ ] Add reduced-motion and reduced-flash variants without changing shot duration or clue order.
- [ ] Visually inspect each effect standalone and the combined sequence at 1× and 2×.

**Done when:** The first 50 seconds establish isolation and intentional signaling while remaining readable pixel art.

### Task CUT-05 — Choreograph reveal, turn, crash, and sound

**Create:** `CoastReveal.tscn`, `CrashFX.tscn`, `OpeningAudio.tscn`, `opening_audio.gd`; shot animation resources under `frontend/godot/resources/cutscenes/opening/`; `frontend/godot/tests/opening_crash_smoke.gd`.

**Depends on:** CUT-02–04. **Produces:** Repeatable S06–S09 and event-based audio behavior at both rates.

- [ ] Animate spatial fog withdrawal, lifting cloud shadow, daylight, and fully readable coast by cinematic second 54.
- [ ] Author a failed turn that preserves forward momentum and makes collision unavoidable.
- [ ] Implement ordered hull contact, splinter, mast, deck-wash, and player-fall cues with matching damage stages.
- [ ] Compose bounded camera shake with the camera path and zero it for reduced motion.
- [ ] Add separated ambience and effect voices, pause handling, 2× boundary fades, and silence from 70.5–72.
- [ ] Test cancellation/restart after every crash cue; no debris, sound, or shake may leak into the next run.
- [ ] Capture and listen to 1×, 2×, and rapid rate changes during impact; check timing and peak levels.

**Done when:** The danger is understandable before impact, destruction is dramatic and reproducible, and the blackout contains an intentional quiet interval.

### Task CUT-06 — Author the persistent beach and recovery route

**Create:** `frontend/godot/scenes/world/ShipwreckBeach.tscn`, `frontend/godot/scripts/shipwreck_beach.gd`, `frontend/godot/resources/shipwreck_beach.json`, `frontend/godot/resources/shipwreck_beach.tres`, `frontend/godot/tests/beach_layout_smoke.gd`.  
**Modify:** `scripts/world_layout.gd`, `scripts/main.gd`, and player art/frame definitions.

**Depends on:** CUT-01 and CUT-03; final wreck appearance from CUT-05. **Produces:** Beach markers, real collision, safe recovery path, and connected inland exploration.

- [ ] Block out the beach south of the village, reconcile interior/world bounds, and finalize named marker coordinates.
- [ ] Layer beach and ocean above the village's fallback green background; ensure no visual seams or premature island visibility.
- [ ] Create wreck, water, rock and debris collision footprints; retain a clear 64-unit exit and inland route.
- [ ] Add real recovery/climb frames and scripted movement through the validated markers.
- [ ] Check every marker and swept path using the full player collider, including at accelerated playback.
- [ ] Verify continued walking reaches existing NPC content and older saved positions retain their previous behavior.
- [ ] Add one factual wreck inspection point and the supply interaction anchor, disabled until handoff.

**Done when:** The beach supports normal movement and exploration independently of the opening, and recovery never crosses a solid hull or deep water.

### Task CUT-07 — Persist opening progression and salvage safely

**Create:** `backend/app/database/opening_migration.py`, `backend/app/services/opening.py`, `backend/tests/test_opening.py`, `frontend/godot/scenes/cutscenes/opening/opening_session.gd`.  
**Modify:** `backend/app/models/player.py`, `backend/app/database/init_db.py`, `backend/app/database/seed.py`, `backend/app/api/routes/world.py`, frontend world-snapshot handling, and relevant existing new-game tests.

**Depends on:** CUT-06 final marker data. **Produces:** Run-scoped pending/complete state, atomic checkpoint, salvage persistence, and frontend readiness signals.

- [ ] Test that migration treats all pre-feature saves as complete and preserves their position/inventory/quests/history.
- [ ] Test that fresh seed and explicit New Game produce pending state in a new `game_scope`.
- [ ] Implement the atomic completion endpoint and expose state/capability in the world snapshot.
- [ ] Share the finalized authoritative beach spawn between layout validation and server checkpoint logic; add a check that they agree.
- [ ] Test repeated completion after the player has moved: it cannot reset their position or duplicate rewards.
- [ ] Test stale run completion, lost response/retry, quitting before completion, and restarting during a pending request.
- [ ] Add the rope pickup with server-validated location, one-time collection ID, atomic inventory update, and reload/double-request tests.
- [ ] Verify fallback to existing gameplay against an older backend without opening capability.

**Done when:** Replays/retries cannot corrupt saves or duplicate supplies, and unfinished/new/completed games enter the correct mode.

### Task CUT-08 — Integrate blackout loading and seamless handoff

**Create:** `frontend/godot/tests/opening_handoff_smoke.gd`.  
**Modify:** Director, session adapter, `main.gd`, transition overlay, beach and audio ownership.

**Depends on:** CUT-03, CUT-05–07. **Produces:** Complete S01–S12 → gameplay flow with one durable checkpoint and one control transfer.

- [ ] Prepare both sets early; perform visibility and real-player placement changes entirely under black.
- [ ] Guard required-load failure and delayed checkpoint acknowledgment with explicit paused readiness states and actionable retry/return UI.
- [ ] Align gameplay camera before the final step, validate endpoint, and execute the ordered handoff in section 8.
- [ ] Test no one-frame player duplication, camera jump, velocity burst, leftover shake, or transparent fade swallowing gameplay clicks.
- [ ] Test held Space and held WASD through the boundary: speed stays normal afterward and WASD acts only once gameplay begins.
- [ ] Check normal, fully accelerated, mixed-speed, paused, and retried runs reach the same playable beach state.
- [ ] Confirm HUD appears at handoff and no pickup, quest, or dialogue activates automatically.

**Done when:** The final cinematic step lands exactly where normal player-controlled movement begins.

### Task CUT-09 — Finish preview tools, regression checks, and delivery evidence

**Create:** `frontend/godot/tests/opening_render_smoke.gd`, `docs/evidence/starting-cutscene/walkthrough.md`.  
**Modify:** Preview harness, asset manifest, and this checklist as work completes.

**Depends on:** CUT-01–08. **Produces:** Repeatable verification and reviewable capture evidence.

- [ ] Expose individual-shot entry, reset, seek, rate, reduced motion, reduced flashes, and debug markers in the preview harness.
- [ ] Ensure the harness uses only fake persistence and never resets or writes a real user's game.
- [ ] Run clock, ownership, effects, crash, layout, persistence and handoff checks; record actual results.
- [ ] Run relevant existing graphics, building, persistence, quest and UI checks against a disposable backend.
- [ ] Capture representative frames for S01, S03, S04, S06, S08, S10 and the frame immediately after handoff.
- [ ] Record full 1× and 2× playback with audio, plus a mixed-speed run and reduced-motion run.
- [ ] Inspect supported window sizes and resizing mid-shot; profile fog fill cost, crash particle peak, and hidden-scene processing on the target machine.
- [ ] Confirm resource loading introduces no visible hitch at impact or beach reveal on the measured target; record hardware and observations rather than claiming a universal frame rate.
- [ ] Update asset attribution, controls, debugging instructions, known limitations, and checked tasks only after evidence exists.

**Done when:** The opening is narratively legible, independently testable, and does not regress normal RPG gameplay or saves.

### Critical path

`CUT-01 → CUT-02 → CUT-03 → CUT-04 → CUT-05 → CUT-08 → CUT-09`.

Beach work (`CUT-06`) follows the animatic and ownership work; persistence (`CUT-07`) follows finalized beach markers. Both must finish before integrated handoff (`CUT-08`). Final artwork follows approved blockout composition; it should not block clock and ownership testing.

## 13. Verification commands and acceptance matrix

The proposed test files do not exist yet. Commands below are the intended implementation checks, not tests already run for this documentation task. Use the actual installed Godot executable; README currently references a local macOS bundle, and there is no `godot` executable on the inspected shell PATH.

```bash
# From the repository root; substitute the actual installed executable if different.
GODOT_BIN=/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot
"$GODOT_BIN" --headless --path frontend/godot --editor --import
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
| Full normal playback | Exactly 90 cinematic seconds, within one update tolerance in synthetic clock tests | CUT-02 |
| Space held throughout | Approximately 45 real seconds excluding waits/pauses; all events retained | CUT-02 |
| Rate changes during signal or impact | Continuous phase, no missed/duplicate flashes or crash events | CUT-02/04/05 |
| Pause/focus loss while holding Space | Frozen story/audio; no stuck acceleration after focus return | CUT-02/05 |
| Player input during every shot | No gameplay movement, interaction, travel, or inventory mutation | CUT-03 |
| Wide/narrow window before reveal | Shore remains hidden until S06; lighthouse remains identifiable | CUT-04/09 |
| Coast reveal and crash | Coast visible by 54; failed turn precedes contact at 63 | CUT-05 |
| Reduced motion and flashes at 2× | No shake; mystery and danger remain legible | CUT-04/05/09 |
| Slow/missing load or failed checkpoint | Clear retry/return state; no endless black screen or false completion | CUT-07/08 |
| Legacy saved game | Continues at saved position with prior gameplay state preserved | CUT-07 |
| App closes before checkpoint | Opening remains pending and restarts from S01 | CUT-07 |
| App closes after checkpoint before final frame | Resumes safely on beach with normal controls | CUT-07/08 |
| Duplicate completion or stale callback | No teleport, duplicate reward, or new-run corruption | CUT-07 |
| Recovery at either rate | Body remains on valid route; no collision tunneling or stuck exit | CUT-06/08 |
| Handoff frame | One player, normal speed, aligned camera, cleared effects, responsive controls | CUT-08 |
| Supply pickup then reload/retry | Exactly one persisted pickup; no duplicated item | CUT-07 |
| Walk inland after opening | Existing NPC, inventory, building and quest flows still work | CUT-06/09 |

## 14. Definition of done

- [ ] The complete emotional progression reads in a normal-speed capture without explanatory dialogue.
- [ ] The lighthouse repeats a deliberate signal whose meaning remains unresolved.
- [ ] Normal duration is 90 cinematic seconds; held-key 2× works throughout, including recovery and fades.
- [ ] Ocean, fog, weather, signal, crash, audio, and recovery can be previewed independently.
- [ ] The coastline reveal provides enough time to understand the approaching disaster.
- [ ] Blackout, silence, calm beach reveal, and recovery preserve the intended contrast.
- [ ] At the final step onto sand, the camera is already aligned and movement becomes responsive.
- [ ] The player can investigate wreckage, collect supplies once, and walk inland.
- [ ] Legacy saves and current village gameplay remain usable; new runs receive the opening.
- [ ] Timing/state tests pass and rendered/audio review evidence is recorded for both playback rates.
