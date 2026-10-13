# Historical first pass — superseded

This records the previous 90-second version. Current evidence is in [walkthrough](walkthrough.md) and `second-pass/`.

# Opening implementation and verification

Implementation date: 2026-10-13. Runtime: Godot **4.5.1 stable**, native Metal on
an **Apple M5**. Existing document edits and unrelated skill files were preserved.

## Launch

From the repository root, use the existing environment and database configuration:

```sh
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal, from the repository root:

```sh
GODOT_BIN=/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot
"$GODOT_BIN" --headless --path frontend/godot --editor --import
"$GODOT_BIN" --path frontend/godot
```

Existing saves resume normally. Fresh databases and **Esc → Restart Game →
confirm** start the opening. Restart Game clears the current run's progress.
The cinematic does not require an LLM. Existing NPC conversations use the backend's
normal provider configuration; set `LLM_BASE_URL=` when starting the backend to use
its mock provider.

The preview is independent and never contacts a backend or mutates a save:

```sh
"$GODOT_BIN" --path frontend/godot res://scenes/cutscenes/opening/OpeningPreview.tscn
```

Hold **Space** for 2×; release for 1×. **Esc** opens the game pause menu. Focus loss
freezes the opening and its audio; acceleration needs a fresh press after focus
returns. There is no instant skip. Pause settings include reduced scenery motion,
soft light and sound captions. After handoff use **WASD**, **E** to inspect the wreck,
**F** beside the rope container, and walk north along the path toward Willowbrook.

Preview controls select S01–S12, restart, seek, pause, 2×, reduced motion/flashes,
markers and captions. Its effect selector isolates ocean, ship, fog, coast, crash
or audio. Seeking applies poses without replaying past effect cues; restarting
resets fired IDs, damage, voices and the clock. The watermark identifies shot/time.

## Evidence

- [Normal playback with audio](normal.mp4)
- [Continuous 2× playback with audio](fast.mp4)
- [Intermittent 2× playback with audio](mixed.mp4)
- [Reduced-motion playback with audio](reduced.mp4)
- [Island capacity overview](island-overview.png)
- [Gameplay immediately after handoff](gameplay-handoff.png)
- `graybox/` preserves pre-polish composition captures.
- `frame-{960,1280,1920}-*.png` covers fog travel, 57.9, reveal at 59.5, crash,
  blackout recovery, climb and endpoint at each supported window size.
- `coast-{north,east,south,west}-{960,1920}.png` covers the surrounding ocean.

The movie harness records at fixed 30 FPS with fake persistence. Story frames:
2,700 normal (90 seconds), 1,350 fast (45 seconds), 1,800 mixed (60 seconds),
2,700 reduced. Mixed alternates two real seconds at 2× and two at 1×. Media includes
short setup/end padding beyond the story (which can vary with desktop focus).
These are offline recordings, not a claim about real-time FPS.

Separate native wall-clock checks measured **90.006 s normal** and **45.015 s
held-action 2×**, both ending at `(0,4560)`. See `realtime-normal.txt` and
`realtime-fast.txt`. PCM analysis of the recorded audio found peaks between
**−16.92 and −16.39 dBFS**, with exact zero samples in the intentional blackout
silence probes. Details: `audio-analysis.json`. Subjective listening approval
has not been asserted; the complete soundtracks are provided for review.

## Geography and implementation decisions

The original 16,384 × 12,288 envelope fits current content and the expansion
allowance. The irregular, closed outline stays at least 1,024 units from all
edges. A shared 32-unit cell mask drives land rendering, full-footprint validation,
backend recovery and global coast collision. Interior rooms are recognized first.
The wreck is at `(0,4800)` on that outline; dry sand is north and open sea is south.

| Content | Allocation / clearance |
| --- | --- |
| Willowbrook props, cottages/workshop, market, well, bow/string anchors | 2,816 × 2,240 current district; original footprint/approach data retained |
| Three logical furnished interiors / Craftsman | Existing 640 × 448 rooms at their original remote origins; excluded from land budget |
| Western woodland / Gatherer and resource approaches | 3,992 × 4,000 reservation; original NPC and paths retained |
| Southern beach, wreck, salvage, inland corridor | 3,200 × 3,680 budget; ≥64-unit exit/corridor; collider 24 × 16 |
| Eastern expansion | 4,000 × 4,000 nominal reservation with an approach route |
| Northern interior | 8,000 × 2,400 nominal reservation clipped by the coast, with a north route |
| Coast/perimeter | Remaining connected land, buffers and future entrances |

After a 64-unit coast exclusion, usable mask area is **108,856,320 wu²**.
Conservatively committing all three launch-region rectangles consumes
**34,051,840 wu²**, leaving **68.7% uncommitted**, exceeding the required 35%.
Future region names reserve geography, not unspecified buildings or systems.
The northbound route bends around the existing well: **4,622 wu / 25.7 s** at
180 wu/s. Current village approach connectivity remains covered by its existing
route tests. Eastern/northern land connects through open land and authored routes.

Chunks are 1,024 units square, with the visible footprint plus one adjacent ring,
and pinned village/forest NPC regions. Population is synchronous and finishes
before a chunk becomes available; there is no delayed async seam to enter.
Coast collision is independent of chunk unloads. At the captured 960/1920 windows,
24–32 decorative chunks were active. Static memory increased about **14.2–20.4
MiB** over the pre-island measurement; RGBA terrain textures budget **24–32 MiB**.
Godot's Metal texture-memory monitor returned an invalid unsigned value, so it is
not used as a measured GPU-memory figure. See `coast-render-log.txt`.

Crash drawing is capped at 32 analytic fragments, reduced to eight with reduced
motion; no rigid-body debris is spawned. One snapped camera presents authored
framing plus additive shake. Two ship headings and five mast-fall frames keep
source pixels intact. Dedicated recovery/brace/stand/climb/fall/look poses use the
existing player palette and foot pivot. All visuals are in the low-resolution
world viewport; full-window fade/menu are outside it.

The backend atomically completes the current run and writes the shared safe
handoff marker. Repeating completion after walking cannot teleport the player.
Salvage collection ID and rope inventory commit together. Position saves update
location context after arrival, including workshop, forest and village. Valid old
floats/interiors persist; only newly offshore positions relocate deterministically.
The relocation notice is acknowledged through a same-position save. Missing
opening capability follows the existing gameplay path without checkpoint calls.

At handoff the already-playing surf voice changes ownership to the beach without
reparenting/restarting it. Completed beach reloads restore ambience; it stops when
the player moves well inland. Normal gameplay UI visibility is restored from its
baseline, including replacement openings and failed reset/reconnect paths.

## Verification

Backend: **431 unittest cases**, including migration, run/version conflict,
idempotent completion after movement, replay-safe salvage, reset and location
context. Godot's 14-script regression set covers clock, island/layout/physics,
beach, ownership, effects and existing graphics, interiors, forest, bow quest,
inventory, persistence and UI/shutdown. Additional lifecycle/crash/handoff and
native render checks are recorded alongside this file.

A flood fill connects all **108,619 land cells** to the southern spawn. The backend and Godot also match a shared SHA-256 contract for **all 196,608 authoring cells**, including exact diagonal-edge centers. Coast physics checked **4,962 outward straight/45° diagonal sweeps** and **13,462
walkable seam sweeps**. Handoff checks use actual HTTP against the disposable DB,
including shared marker agreement, one real actor, camera alignment, control,
HUD, surf ownership, pickup and exact float reload. Lifecycle checks cover focus
notifications, release while paused, cancellation/restart after every crash cue,
the 89.8 readiness barrier/retry, and held WASD/Space across handoff. A physics fault-injection check adds an unexpected blocker to the recovery path and verifies a single latched safe fallback through handoff. Quitting an
unfinished opening left the disposable backend pending at its pre-opening save.
A source review found three restart/context gaps; new failing regressions were
added and the fixes passed. A second source review found no remaining substantive
concerns in those fixes.

Reproduce destructive integration checks against **only a disposable database**:

```sh
cd backend
DATABASE_URL=sqlite:////tmp/starting-cutscene-qa.sqlite LLM_BASE_URL= LLM_MODEL=mock \
  ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

From the repository root in a second terminal:

```sh
GODOT_BIN=/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot
"$GODOT_BIN" --headless --log-file /tmp/opening-clock.log --path frontend/godot --script res://tests/opening_clock_smoke.gd
"$GODOT_BIN" --headless --log-file /tmp/island-world.log --path frontend/godot --script res://tests/island_world_smoke.gd
"$GODOT_BIN" --headless --log-file /tmp/opening-lifecycle.log --path frontend/godot --script res://tests/opening_lifecycle_smoke.gd
"$GODOT_BIN" --path frontend/godot --script res://tests/opening_handoff_smoke.gd
"$GODOT_BIN" --path frontend/godot --script res://tests/opening_render_smoke.gd
```

Backend full suite:

```sh
cd backend
PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -v
```

Godot's headless Dummy audio driver can report retained WAV/playback resources at
process teardown; state checks still exit zero. Native captures do not show that
warning. Deliberate unavailable-server tests log connection errors. In the managed
sandbox, native rendering/local HTTP required tool escalation; none of these tests
used the real save. Explicit `--log-file /tmp/...` avoids a sandboxed user-log path
issue in the installed runtime.

## Remaining review and limits

- Synthetic sound effects are implemented, recorded and level/silence checked;
  subjective listening approval remains unchecked in the design checklist.
- Required marker validity stops preparation with a useful message and quit/menu
  access. Missing/corrupt compiled scene/script resources still use Godot's import
  diagnostics; exhaustive asset-corruption/retry fault injection is not complete.
- Extended GPU fill-cost/hidden-scene trace profiling remains unchecked. The measured chunk/static-memory figures and offline frame/sample logs are provided; no universal frame-rate claim is made.
- North/east/perimeter are intentionally light geographic blockout, with expansion
  space rather than fully dressed future locations. No swimming or sailing controls.
- Art uses deliberately economical discrete poses; no claim of fluid frame-by-frame
  character animation or recorded real-world ship sounds is made.
