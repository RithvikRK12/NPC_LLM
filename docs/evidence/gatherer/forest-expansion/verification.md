# Forest expansion and encounter-data recovery

The screenshot error is the frontend's missing Gatherer snapshot condition. It previously entered a modal encounter before checking backend capability. The controller now keeps exploration available and automatically refreshes authoritative world data until the updated backend returns the encounter. This does not fabricate a local branch or award social changes.

The normal local backend was started on port 8000 with `--reload`, using the existing database without resetting it. A read-only `/world` request confirmed `gatherer_encounter` is present and the opening remains complete. Close and reopen the running game to load the new map and scripts; existing saves remain valid.

## Forest and boars

- Added `forest_layout.json`, a shaded forest spanning 2700×2160 world units, a longer westward trail and **211 additional collision-backed trees**. Terrain and scenery retain the existing art style and collision conventions.
- Moved the Gatherer from **(-650,70) to (-1800,70)**. The entry region, staging positions, recovery marker, combat clearing and retreat route moved together. Camera framing follows the longer approach/retreat and fits the arena at minimum resolution.
- Backend checkpoint positions now come from the same authored JSON as Godot. Old pending staging migrates from version 1 to 2 without changing the branch, attempt, inventory, relationship or outcome memory. Resolved saves retain progress.
- Boar artwork is **1.8× larger**, with a matching 36×20 trunk collider. Forward attack reach is 58 units, warning width 52 units and warning time 0.70 seconds. The telegraph matches that strike area. Approach speed is 85 units/s and recovery 1.0 second; three-hit deaths and shared damage immunity remain intact.

## Verification

- **463 backend tests pass**, including old refusal checkpoint migration without duplicate penalties/memories.
- **27 Godot regression scripts pass gameplay assertions**, including forest scenery/layout, physical approaches, automatic missing-data recovery, combat, pause/input, local retry, both outcomes, save/reload, fisherman/opening/craftsman, persistence and bow progression after refusal.
- Rendered **960×540 and 1280×720** help/victory, death/retry, refusal/return, missing frontend snapshot recovery, save failure/retry and pending-scene reloads pass. Screenshots were inspected for the forest border, larger boars, readable warnings, corpse visibility and HUD clearance.
- All four physical approaches pass with actual scenery collisions. The arena grid and authored marks pass collision clearance checks.
- `git diff --check` passes.

Gameplay tests used only the disposable database `/tmp/gatherer-expanded-verification.db` on port 8001. The normal port-8000 save was not reset. Existing craftsman and other uncommitted work was preserved.

The previously documented exit-time ObjectDB/resource cleanup warnings in older Godot regression scripts remain. External LLM generation was not exercised during these local tests.

A separate read-only review found no important correctness defects in capability recovery, staging migration, forest collision integration, camera framing or the enlarged boar art/collision/attack telegraphs.
