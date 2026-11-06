# Opening second pass — implementation and verification

2026-10-13 · Godot **4.5.1 stable**, native Metal 3.2 on Apple M5.
This is the current **60-second** revision. [First-pass record](first-pass-walkthrough.md)
and captures outside `second-pass/` describe the previous 90-second version.
Unrelated dirty work and the original evidence were preserved.

The first 30 seconds are removed, not compressed. Ten shots use boundaries
`0,6,22,28,30,33,39,43,49,57,60`; retained cues shift by −30. Start camera,
ship/deck pose, bob and water phase continue the original time-30 state.
Fog withdraws at 28, coast is readable at 29.5, turn starts at 30, keel contact
at 33, mast at 34.2, fall at 35.4, black at 39, recovery fade at 43,
checkpoint at 57, handoff at 60. The readiness barrier is 59.8.
Opening save version remains 1, so completed saves do not replay.

Seven individual opaque fog formations replace the stripes: varied dimensions,
irregular clustered silhouettes, shaded undersides, uneven overlap and slow drift.
The opaque far field blends beneath the silhouettes. Stage coast/scenery also
stay concealed until release, protecting extra-wide windows. Reduced motion
freezes drift while preserving the reveal and cue order.

The persistent beach uses the same coastal surface and scenery definitions as
the crash set. Turquoise shelves, broken foam, wet sand, warm textured sand,
irregular grass, palms, broadleaf canopy clusters, shrubs, shells, stones, flowers,
driftwood and grounded shadows use original integer-grid art. Source pixels are
two world units; nearest filtering remains intact. No reference pixels, watermark
or pencil graphic were copied. [Asset provenance](../../../frontend/godot/assets/cutscene/opening/README.md).

The central southern bay is inset by 960 units: wreck `(0,3840)`, handoff
`(0,3600)`. Village/interior/NPC/quest anchors stay unchanged. Shared marker JSON
updates cinematic staging, recovery, salvage and backend handoff together. Map
version 2 migrates newly offshore version-1 saves once while preserving completed
or pending opening state, inventory and valid floats/interiors. New/reset games
use the current map version. The shared mask contract covers all 196,608 authoring
cells; all 106,187 land cells connect to the spawn. Usable area is 106,363,904 wu²,
with **67.99% uncommitted** after the existing launch-region budgets.

The route is **3,662.307 wu / 20.346 s** at the unchanged **180 wu/s**, down from
4,622 wu / 25.7 s. It progresses from open wreck sand through palms, a rock outcrop,
a shaded broadleaf stretch and fallen log, a flowering clearing, a weathered
trail marker, then the established village approach. The village terrain now joins
the shared route visibly. Landmark exclusion areas prevent canopies hiding these
compositions. Full visible gameplay footprints plus a margin are dressed up to
2,200 units either side; future northern/eastern reserves remain open.

Whole formations belong to their trunk-origin chunk and render as nodes in the
actor Y-sort hierarchy. Neighboring loaded rings exceed their visual extents;
shadows and sprites are not clipped into chunk textures. Trunks, large landmarks
and marker have foot colliders, with full-footprint validation including diagonal
chunk owners. Ground details are walk-over. Recovery, salvage and route exclusions
keep navigation clear. Deterministic unload/reload checks compare actual node
identities and positions. Interior transitions hide sibling scenery correctly.

## Current evidence

- [Full normal opening with audio](second-pass/normal.mp4) — 1,800 story frames / 60 s.
- [Full held-Space 2× with audio](second-pass/fast.mp4) — 900 story frames / 30 s.
- [Intermittent 2× with audio](second-pass/mixed.mp4) — 1,200 story frames / 40 s;
  alternates two wall seconds held and two released, including reveal and crash.
- [Reduced motion with audio](second-pass/reduced.mp4).
- [Full 1920×1080 beach-to-village walk](second-pass/walk-large.mp4).
- [Full 960×540 walk](second-pass/walk-small.mp4).
- [New start](second-pass/frame-1280-0000.png), [extra-wide fog before reveal](second-pass/frame-2560-0279.png),
  [withdrawal](second-pass/frame-1280-0285.png), [revealed coast](second-pass/frame-1280-0295.png),
  [impact](second-pass/frame-1280-0335.png), [landing](second-pass/frame-1280-0600.png).
- [Palms](second-pass/route-1920-3200.png), [outcrop](second-pass/route-1920-2900.png),
  [shaded log](second-pass/route-1920-2250.png), [flowering clearing](second-pass/route-1920-1580.png),
  [marker/approach](second-pass/route-1920-940.png), [village](second-pass/route-1920-0.png).
- [Map-v2 capacity overview](second-pass/island-overview.png).

Native stills cover **960×540, 1280×720, 1920×1080 and 2560×720**, including
resize transitions, time 0, dense fog, 27.9, withdrawal, reveal, impact, fall,
recovery and handoff. Individual ocean/ship/fog/coast/crash captures are provided.
Actual native images were inspected for density, layer order, silhouette repetition,
landmark visibility and route continuity. Review caught and fixed a village path
texture gap, hidden landmarks and small beach dressing below the surface layer.

Movie Maker records offline at fixed 30 FPS with fake persistence and short
setup/end padding; its generation rate is not a real-time FPS claim. The walk
uses full collision, the actual village scene and 6-wu steps at 30 FPS; 612 movement
frames reach the village (fractional segment ends account for the difference from
20.346 geometric seconds). No teleport or global speed change is involved.
Separate native wall-clock checks measured **60.018 s normal** and **30.002 s held
Space**, both ending at `(0,3600)`; see [normal log](second-pass/realtime-normal.txt)
and [fast log](second-pass/realtime-fast.txt). Recorded soundtrack analysis measured
−16.89 dBFS normal and −18.12 dBFS fast peaks, with exact-zero PCM silence in
central blackout probes: [analysis](second-pass/audio-analysis.json).

## Verification

**432 backend unittest cases pass**: [full log](second-pass/backend-suite.txt).
**21 Godot regression scripts pass**: [summary](second-pass/regression-summary.txt).
They cover clock/cues, release, pause/focus/fresh press, seeking/restart, ownership,
59.8 readiness barrier/retry, obstruction fallback, island mask/perimeter/seams,
full recovery and route footprint, deterministic scenery reload, diagonal footprint
validation, village approach continuity, graphics state/layout, interiors, forest,
bow quest, inventory/history/persistence, UI and shutdown.

[Native HTTP integration](second-pass/handoff.txt) against a disposable port-8001
database verifies durable completion, one actor, exact shared marker, aligned camera,
normal physics, HUD, seamless surf voice ownership, one rope pickup, exact float
reload and no replay. Existing/pending map-v1 migration, map-v2 new/reset runs,
stale run/version rejection and idempotent completion after movement are covered
by backend tests. The real save database was never reset by these tests. A final independent, read-only
review found no critical or important issues in timing, concealment, scenery
ownership/collision, shared markers or migration. The disposable QA server was
stopped after verification.

The final native walks peak at 24 terrain chunks and 846 scenery props; exact prop count and update-cost
figures are in `second-pass/movie-walk-{large,small}.txt`. Chunk loads are synchronous;
there is no delayed decorative readiness seam. No extended GPU-memory/fill-cost or
universal frame-rate claim is made. Headless Dummy-audio teardown can report retained
WAV resources; native runs do not show those warnings. Initial sandboxed HTTP/native
attempts failed due to access restrictions; reruns with local/native access pass.

## Launch and reproduce

From the repository root, launch the normal configured backend:

```sh
(cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000)
```

In another terminal from the repository root:

```sh
GODOT_BIN=/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot
"$GODOT_BIN" --headless --log-file /tmp/npc-import.log --path frontend/godot --editor --import
"$GODOT_BIN" --path frontend/godot
```

Independent preview, requiring no backend and never modifying saves:

```sh
"$GODOT_BIN" --path frontend/godot res://scenes/cutscenes/opening/OpeningPreview.tscn
```

Hold **Space** for 2×; release for 1×. **Esc** pauses; focus loss freezes the clock
and sound and requires a fresh press after returning. Preview selects **S01–S10**,
seeks 0–60 and isolates fog/coast/crash and other effects. After handoff use **WASD**,
**E** to inspect and **F** beside salvage. Existing saves resume normally; fresh
runs and explicit **Esc → Restart Game → confirm** play the opening.

Use only a disposable database for destructive integration checks:

```sh
(cd backend && DATABASE_URL=sqlite:////tmp/second-pass-qa.sqlite LLM_BASE_URL= LLM_MODEL=mock \
  ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001)
"$GODOT_BIN" --path frontend/godot --script res://tests/opening_handoff_smoke.gd
"$GODOT_BIN" --headless --log-file /tmp/south-route.log --path frontend/godot --script res://tests/south_route_smoke.gd
"$GODOT_BIN" --path frontend/godot --script res://tests/opening_render_smoke.gd
(cd backend && PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -v)
```

Regenerate art with `python3 frontend/godot/tools/build_opening_assets.py` (includes
the southern asset family), then import. For native movies use
`--fixed-fps 30 --write-movie /tmp/opening.avi --script res://tests/opening_movie.gd`
with `-- --fast`, `-- --mixed` or `-- --reduced`; the route harness is
`res://tests/south_walk_movie.gd` with optional `-- --small`. Both use fake persistence.

## Remaining limits

Subjective audio listening approval, exhaustive corrupt compiled-resource failure
injection and extended GPU/hidden-scene profiling remain open from the first pass.
The original synthetic audio and economical discrete actor/ship poses are retained.
Vegetation is a deliberately reusable pixel family; the route is still direct and
calm rather than a new quest or interaction system. North/east/perimeter beyond
this southern delivery remain geographic blockout and expansion reserve.

## L skip shortcut

During the opening, press **L** to skip directly to the shared beach handoff.
The session stops the narrative clock and one-shot audio without firing skipped
crash cues, uses the normal run-scoped arrival checkpoint, then restores the
beach HUD and first-control onboarding. Save failures retain the existing retry
control. Key repeat, gameplay, and the open menu do not trigger skipping.

`res://tests/opening_skip_smoke.gd` passed for voyage, fog, blackout and recovery
skips, exact beach landing, cue suppression, onboarding, menu/key-repeat guards,
and pending-save failure/retry. Opening clock/lifecycle/recovery, onboarding and
inspection regressions and all 432 backend tests also passed.
