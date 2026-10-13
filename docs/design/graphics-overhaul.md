# Willowbrook graphics and village expansion

Status: GFX-01–GFX-07 implemented and validated on 2026-10-13. See sections 14–16 for the final placements, commands, rendered evidence and review. Earlier proposed coordinates remain as design history; the layout resource is authoritative.
Created: 2026-10-13.
Related work: [UI rework](ui-rework.md). The completed UI remains the starting point.

## 1. What we want to achieve

Give Willowbrook a more detailed, deliberately pixelated appearance while keeping it bright, charming, and easy to read. Make the village feel arranged by people who live and work there: buildings face paths, people stand on the ground, tools belong beside workstations, and items are reachable rather than scattered arbitrarily.

Confirmed direction:

- Use the three supplied images as visual references for the overhaul.
- Increase environmental and character detail while making the art more pixelated.
- Keep the world colorful and inviting rather than dull.
- Pay closer attention to actual game coordinates, scale, and placement.
- Expand the world modestly, with **more village buildings and a market lane** as the preferred addition.
- Discuss the proposal in Markdown before implementing it.

The dimensions, asset counts, coordinates, and rollout below describe the original proposal. The implementation follows the shared scale and gameplay protections, with placement refinements recorded below.

## 2. Reading the references

| Supplied reference | What to bring into Willowbrook |
| --- | --- |
| Outdoor character gathering | Readable small character silhouettes, distinct clothing and hair, consistent human scale, lively greens, flower accents, and enough open ground for people to stand comfortably |
| Character portrait sheet | Expressive faces, recognizable differences between villagers, rich but controlled shading, and matching identity between the walking sprite and dialogue portrait |
| Farm and buildings | Layered roof and wall materials, believable fence gates and paths, trees with clustered leaves, small gardens, and work areas with purposeful props |

The strength of these images comes from composition as much as detail. Paths and fences organize the space; flowers and warm wood break up the greens; busy areas sit beside quieter walking surfaces. Adopt those principles with original Willowbrook artwork, characters, and architecture. The portrait sheet demonstrates character individuality; it does not imply adding that many NPCs.

## 3. Art direction: a lively timber village

Recommended direction: a sunny woodland settlement, with warm timber buildings, mossy stone, tiled roofs, small cottage gardens, and a cheerful market lane. Keep the Craftsman and Gatherer visually central to the village's identity.

Other approaches considered:

| Approach | Benefit | Trade-off |
| --- | --- | --- |
| **Village and market lane — recommended and user-selected** | More places that feel inhabited; clear opportunity for cottages, stalls, signage, and gardens | Needs a coordinated building kit and careful street layout |
| Woodland-first expansion | Strong atmosphere around the Gatherer; fewer building assets | Adds less village life and can become visually repetitive |
| Garden and pond expansion | Color, water animation, and a quieter destination | Does less to address the requested buildings and market lane; defer the pond |

### Color and material rules

- Use several greens: warm sunlit grass, cooler woodland shade, deeper leaf clusters, and brighter new growth. Avoid one flat green across the whole map.
- Ground paths in honey-brown soil and sandy edges. Use muted purple/brown shadows rather than covering everything with black or gray.
- Give buildings readable material changes: warm plaster, timber beams, individual roof rows, stone foundations, doors, and window recesses.
- Introduce flowers, painted stall cloth, vegetables, and warm windows as concentrated accents. Proposed stall colors: faded coral and golden ochre, with cream trim.
- Keep grass detail low contrast. Reserve sharper outlines and stronger contrast for characters, building edges, quest items, and interactable objects.
- Texture should form clusters and patches. Do not replace the current sparse strokes with uniform high-contrast noise.
- Use a consistent upper-left light direction and small, stepped ground shadows. Avoid smooth blurred shadows and gradients in the world artwork.

The desired result is richer at close inspection and clear at a glance. Every open tile does not need a flower, rock, or tuft.

## 4. Current world and placement problems to solve

The current world is primarily drawn with rectangles, circles, lines, and polygons. It has a recognizable layout, but changing texture filtering alone will not turn those shapes into detailed pixel art.

| Current area | Source and observed baseline | Proposed treatment |
| --- | --- | --- |
| Ground and paths | `scripts/village.gd`: large flat background, seeded grass strokes, thick path polylines | Authored terrain tiles with edge transitions, quieter path centers, and clustered detail |
| Workshop | Geometry drawn separately from its collision in `scripts/main.gd` | One reusable building scene containing art, footprint, ground anchor, and approach marker |
| Trees, well, work props, fence | Drawn together in the village's single `_draw()` | Separate placed scenes where overlap/collision matters; terrain decoration can stay in ground layers |
| Characters | `scripts/person.gd`: rounded procedural figures and a sinusoidal stride | Original pixel sprite sheets with directional idle/walk animation |
| Camera | Player child, smoothing enabled, horizontal offset `(290, 0)` | Explore a player-centered composition with a small facing look-ahead; verify dialogue does not cover the speaker |
| Pickup | Frontend placement and backend quest constant both use `(-70, 240)` | Preserve this authoritative location and place surrounding artwork around it |
| Dialogue portraits and items | Block portrait drawings; SVG inventory icons | Matching character portraits and original pixel item icons using the existing UI components |

The painted background currently spans `(-1400, -1100)` to `(1400, 1100)`. That is not a fully authored, collision-bounded playable map. A larger background rectangle alone would not be a useful expansion. The proposal adds a coherent district within and around the existing scenery, with more reasons to walk east.

## 5. A consistent pixel and scale standard

Use one source-pixel scale for world assets. Proposed starting specification:

| Asset | Source artwork | World footprint or display |
| --- | --- | --- |
| Terrain tile | 16 × 16 px | 32 × 32 world units |
| Human animation frame | 24 × 32 px, including transparent breathing room | 48 × 64 world units; visible body fits within the frame |
| Small props | Multiples of 8 or 16 px | Same scale: 1 source pixel = 2 world units |
| Tree | Approximately 48 × 64 px; controlled variants | Approximately 96 × 128 world units; collision only around trunk |
| Workshop | Modular facade/roof assembled on the terrain grid | Approximately 256 units wide; larger than cottages |
| Cottage | Modular parts, roughly 64–80 px wide | Approximately 128–160 world units wide |
| Dialogue portrait | 48 × 48 px | 96 × 96 UI pixels at integer 2× display; adjust layout to preserve reply space |
| Inventory icon | 24 × 24 px | 48 × 48 UI pixels inside the existing 64 px slot |

These sizes need a combined art sample before production. A character, doorway, tree, bench, and cottage must be reviewed together; a beautiful asset at an incompatible scale is not ready to use.

### Rendering and camera proposal

Render the world into a lower-resolution viewport and enlarge it with nearest-neighbor filtering at integer scale. Keep the existing UI in a separate full-resolution layer so text, input, and larger-text accessibility remain readable.

A concrete starting configuration, preserving world units:

| Window | World render size | Integer enlargement | World camera zoom | Visible world span |
| --- | --- | --- | --- | --- |
| 960 × 540 | 480 × 270 | 2× | 0.5 | 960 × 540 units |
| 1280 × 720 | 640 × 360 | 2× | 0.5 | 1280 × 720 units |
| 1920 × 1080 | 640 × 360 | 3× | 0.5 | 1280 × 720 units |

At zoom 0.5, two world units become one render pixel, matching the asset scale above. Increasing the output size does not change saved positions, movement speed, or interaction distances. Compact windows show less scenery, rather than squeezing the world into uneven pixels.

For other window sizes, calculate an integer enlargement and an appropriate render size; center any unavoidable remainder of at most a few pixels. Test resizing and high-DPI displays. Do not stretch a fixed world image by a fractional scale.

Keep simulation positions as floats. Snap the final rendered camera and sprite positions consistently to the render grid; do not round the player's saved position or physics movement. Check slow movement, diagonals, and camera follow for shimmer and jitter. If the current camera smoothing causes uneven pixel steps, replace it with a follow method that produces stable final pixels.

## 6. Coordinates, grounding, and overlap

### One coordinate system

Keep the existing world origin and unit scale. Positive X is east/right; positive Y is south/down. Tile coordinates are for terrain authoring, not a replacement for saved world coordinates.

For the proposed grid, `tile (column, row)` has top-left world position `(column × 32, row × 32)`. Its center is 16 units farther along each axis. Exact gameplay anchors may sit between grid points; do not move existing quest locations just to make their numbers divisible by 32.

### Every placed object has an intentional anchor

| Anchor or shape | Meaning |
| --- | --- |
| Ground/foot origin | Where the object or person touches the ground; use this for placement and depth sorting |
| Visual bounds | Full artwork, including hair, roof, canopy, shadows, and overhangs |
| Collision footprint | Solid ground area that blocks movement; usually much smaller than visual bounds |
| Interaction point | Where the player should approach an NPC, sign, or pickup |
| Approach space | Clear walkable area around that point, connected to a path |

Character frame origin should be at a consistent foot position, for example source pixel `(12, 30)` in a 24 × 32 frame. Drawing offsets then place the head above the origin. Frame changes must not move the feet or collider.

Proposed actor foot collision begins around 24 × 16 world units, adjusted after movement checks. The current player collider is 36 × 36 and NPC shapes are 44 × 44; changing these is a deliberate collision adjustment to validate, not a silent unit conversion. A character's head and shoulders should not block an entire doorway.

Trees collide at their trunks, not across their entire canopies. Separate roof/canopy artwork from the ground footprint when needed. Sort people and objects by their foot/ground Y, so walking behind a tree hides the appropriate part of the person and walking in front draws the person in front. A single background drawing cannot provide this overlap for individual objects.

### Placement rules

- Main paths: generally 96 units wide. Secondary paths: at least 64. Keep the traversable width after props and collisions are placed.
- Decorative cottage doorways: visually around 32–48 units wide, with at least a 64-unit clear apron. These are closed exteriors in this pass; do not suggest a working entrance that the player can only partly enter.
- Keep workshop and Gatherer approach positions connected to the square. Preserve the current 96-unit talk distance and 64-unit string-pickup distance.
- NPCs stand beside their work, not inside a bench or in the center of through-traffic. Tools should sit on surfaces; baskets should sit on the ground.
- Keep flower clusters and grass tufts away from pickup silhouettes and the center of walking paths.
- Snap repeated structural parts to the grid. Allow deliberate smaller offsets for planted areas and irregular rocks, using a fixed authored layout or a reproducible seed.
- Place and review collision overlays alongside artwork. Do not tune coordinates solely until a screenshot looks plausible.

## 7. Proposed village layout

Preserve the workshop–square–forest relationship. Develop the eastward road into a small market lane, with two cottages set back to the north and a few household details around them.

Conceptual arrangement, not a scaled collision map:

```text
                              NORTH (-Y)

       Woodland           Workshop yard       Cottage A       Cottage B
       and Gatherer       Craftsman           small garden    fenced yard
            |                  |                    |              |
            +-------- Village square ------- Market lane ----------+
                           |                 two stalls / noticeboard
                          Well                       |
                     String clearing            eastward exit

                              SOUTH (+Y)
```

### Anchors to preserve

These coordinates are read from the current implementation. They remain fixed in the first pass.

| Element | Existing world anchor | Reason |
| --- | --- | --- |
| New-game player position | `(0, 0)` | Save and restart continuity |
| Craftsman | `(180, -20)` | Existing talk/transfer flow and test approach at `(110, -20)` |
| Gatherer | `(-170, 35)` | Existing talk/transfer flow and test approach at `(-100, 35)` |
| Well stone base | `(-15, 172)` | Established landmark beside the quest pickup |
| String pickup | `(-70, 240)` | Backend validates against this exact location |
| Workshop collision center | `(195, -160)` | Existing footprint is 230 × 125 units; first art pass should fit around it |

### New and refined placements

Coordinates below are proposed ground anchors or path centerline points, not sprite top-left positions.

| Element | Proposed world placement | Spatial intent |
| --- | --- | --- |
| Market path | `(210, 0)` → `(384, 32)` → `(576, 64)` → `(800, 128)` | A readable eastward continuation from the current workshop/square route |
| Cottage A facade ground anchor | `(496, -96)` | Suggested footprint X `432..560`, Y `-224..-96`; door/yard faces south toward the lane |
| Cottage B facade ground anchor | `(720, -128)` | Suggested footprint X `656..784`, Y `-256..-128`; stagger the frontage for a less rigid street |
| Produce stall | `(480, -16)` | Ground footprint approximately X `448..512`, Y `-48..-16`; south-facing front beside the lane |
| Cloth/general-goods stall | `(624, 0)` | Ground footprint approximately X `592..656`, Y `-32..0`; leave a clear browsing strip to the south |
| Noticeboard | `(384, -32)` | At the lane entrance, outside the main walking corridor; decorative initially |
| Cottage garden | Around `(416, -160)` | Small enclosed planted area beside Cottage A, with a visible gate toward its yard |
| Refined workshop bench | Around `(280, -24)` | Grounded beside the Craftsman, with the working surface above its ground origin |
| Logs and tool storage | Around `(352, -64)` | Outside the workshop's current solid footprint and away from the main route |
| String approach | Keep `(-70, 288)` clear | A reachable point 48 units south of the pickup, inside its 64-unit interaction radius |

The lane has a proposed 96-unit width. At the produce stall, its nearby center is approximately Y 48, giving a north edge near Y 0; the stall's ground footprint ends at Y -16. This leaves separation between the solid stall and through-route. Verify the entire bent path against all footprints, not just these sample points. Art can overhang farther than its collision.

The two cottage footprints have a gap between them for a short side path or planted strip. Their frontage aprons must connect to the lane without fencing the player out. Keep the west side of the workshop clear so the existing quest route remains direct.

### What “a little bigger” means

First expansion: **one short district, two cottage exteriors, two stalls, a noticeboard, and small gardens/fences**. Improve the existing woodland edge and well area as part of the art pass rather than adding a second large biome.

Aim for a route that reveals the market naturally from the square and takes only a few seconds of walking beyond the workshop. At the existing 180-unit/second speed, a roughly 600-unit route is about 3.3 seconds before turns and stops. Evaluate the actual walk in-game; do not add long empty roads to inflate map size.

Do not introduce hard world boundaries merely to match a new rectangular art map. Existing saves may contain positions outside the currently detailed center. Any future boundary or collision migration needs a safe recovery rule for players who load inside new geometry, preserving their inventory, quest, and history.

## 8. Characters, portraits, and animation

Create original, coordinated art for the existing cast first:

| Character | World silhouette | Portrait cues |
| --- | --- | --- |
| Player | Teal/blue outerwear, practical boots, small satchel | Same hair, clothing, and accent colors as the world sprite |
| Craftsman | Ochre shirt, leather apron, broad working stance | Warm face, apron strap, distinctive hair or beard; visibly a craftsperson |
| Gatherer | Green clothing, hood or cap, basket/shoulder bag | Different face and hair from the Craftsman; woodland clothing and friendly expression |

Proposed baseline animation: four directions, one idle pose and four walk frames per direction. Author consistent foot contact and avoid stretching sprites between frames. A diagonal move can use the dominant direction initially; do not add eight directions unless the four-direction sample looks inadequate.

Use restrained ambient motion: two-frame leaf movement, a small chimney-smoke cycle, and two-frame cloth movement. Differentiate static and animated foliage so the whole scene does not twitch in unison. Keep a reduced-motion path available if ambient movement becomes distracting.

Portraits start with one expressive neutral face per character. A small optional expression set can follow, but select expressions only from existing, trustworthy state. Do not invent relationship changes or emotional gameplay effects from the artwork.

## 9. Environment asset kit

Build a small reusable kit before filling the map:

- **Terrain:** grass base variants, dirt path centers/edges/corners, worn ground, darker woodland ground, and garden soil. Blend transitions around the path's actual shape.
- **Buildings:** workshop and cottage wall/roof modules, stone footing, closed doors, lit windows, chimney, eaves, and readable signage.
- **Market:** two original stall designs, baskets, crates, produce displays, folded cloth, noticeboard, and a few small pennants.
- **Nature:** two or three tree silhouettes, bushes, grass clusters, flowers, small rocks, and stump/log variants.
- **Work and well:** bench, anvil, tools, stacked wood, well stonework, posts, roof, bucket, and rope.
- **Ground contact:** consistent stepped shadows and small worn patches beneath frequently used objects.
- **Items:** matching pixel icons for existing items, especially wood, string, bow, food, water, and NPC supplies. String needs a readable world-pickup sprite as well as its inventory icon.

Production counts should follow the approved sample, not become an invitation to generate hundreds of unrelated assets. Keep source sheets, slicing specifications, anchors, and any licenses together. Use original art or assets whose redistribution terms are explicitly documented.

## 10. Integration and gameplay protections

Proposed Godot organization:

- Terrain layers for ground and path transitions.
- Individual building, tree, stall, and prop scenes where depth or collisions matter.
- A shared character sprite presentation driven by the existing player/NPC nodes.
- A village layout resource recording stable IDs, scenes, world anchors, visual offsets, footprints, and approach markers.
- A world-render viewport plus the existing full-resolution UI layer. Convert speaker coordinates through the actual world-to-screen transform before drawing dialogue tails.

Suggested resource locations: `assets/world/`, `assets/characters/`, `assets/portraits/`, `assets/items/pixel/`, `scenes/world/`, and a village layout resource under `resources/`. These are proposals, not files created by this document.

Keep simulation and presentation separate:

1. Preserve NPC IDs, inventories, transfers, quest phases, crafting deadlines, and reward rules.
2. Preserve free-text dialogue, per-NPC histories, pinned recipients, UI movement blocking, and the Esc menu.
3. Retain save-before-exit and loaded player positions in existing world units. Do not reset a world to install new graphics.
4. Keep the frontend pickup at the backend's authoritative `string_position`. The frontend currently also hardcodes the same value; consume the snapshot value or share a validated definition when implementing the layout so future visual moves cannot cause drift.
5. Audit any new solid props against saved positions. If a saved player is trapped by new geometry, relocate only the position to a tested nearby walkable point, explain the adjustment, and save it; do not clear other state.
6. New cottages and stalls are scenic in this pass. No interiors, purchasing, extra inventories, quests, or new NPC schedules are implied.
7. If the market becomes a named location NPCs can discuss, explicitly update the static village context and grounding checks after the map exists. New artwork does not automatically give the model knowledge of a place or imply a trading capability.

## 11. Proposed work sequence

All seven phases are implemented. The combined concept and measured art sample were inspected before full asset generation; see the review ledger and rendered evidence below.

- [x] **GFX-01 — Combined art and scale sample.** One character, portrait, terrain patch, tree, workshop frontage, stall, and bench together. Include foot origins and collision overlays. Review charm, pixel size, contrast, and proportions.
- [x] **GFX-02 — Rendering and coordinate foundation.** Establish integer world scaling, separate UI, camera behavior, and world-to-screen conversion. Document pivots and layout data. Prove existing saved coordinates still work.
- [x] **GFX-03 — Existing village art pass.** Replace core terrain, workshop, well, trees, and work props. Keep all existing quest anchors and approach points. Validate layering and collisions before adding density.
- [x] **GFX-04 — Character and item art.** Replace the player/NPC world figures, portraits, and inventory/world-pickup icons. Add four-direction idle/walk animation with stable feet.
- [x] **GFX-05 — Market lane expansion.** Add the eastward lane, two cottages, two stalls, gardens, and purposeful details. Keep the core quest journey short and clear. Audit every approach corridor and new solid footprint.
- [x] **GFX-06 — Atmosphere and polish.** Add a limited set of ambient animations, shadows, terrain variation, and concentrated color accents. Remove clutter that competes with characters or quest items.
- [x] **GFX-07 — Rendered and gameplay validation.** Capture the core and market at supported sizes; exercise saved-world loading, collisions, interactions, the full bow quest, and shutdown/recovery. Record evidence and remaining issues here.

## 12. Review and acceptance criteria

### Visual quality

- [x] The world visibly uses authored pixel detail, with consistent pixel size across characters, buildings, vegetation, and items.
- [x] Grass and paths are pleasant rather than noisy; varied greens and localized color accents keep the village lively.
- [x] Character sprites and portraits look like the same people and remain distinct at normal playing size.
- [x] Doors, stalls, benches, trees, and people have believable relative proportions and contact shadows.
- [x] Integer scaling remains crisp at 960 × 540, 1280 × 720, and 1920 × 1080, including native macOS 2× DPI and an odd-size resize check. Other operating systems and DPI factors have not been exercised.
- [x] Slow movement, diagonal movement, animation, and camera follow produce no visible pixel shimmer or foot sliding.
- [x] The bottom dialogue, larger-text mode, inventory, and Esc menu remain readable over the richer world.

### Spatial quality

- [x] Foot anchors, art bounds, collision footprints, and interaction points are inspectable in a debug view.
- [x] Players can walk in front of and behind tall props with correct overlap.
- [x] Main routes, cottage aprons, NPC approaches, and the pickup clearing remain connected and comfortably traversable.
- [x] No character floats, stands inside a prop, or appears to walk across a roof or solid well.
- [x] The market reads as one compact extension of the village, with no long empty connector road.

### Gameplay and persistence

- [x] The current 96-unit talk and 64-unit pickup checks still match what the player sees.
- [x] Request wood, explain purpose, pick up string, give both materials, wait for crafting, and receive exactly one bow.
- [x] Existing inventory, quest progress, histories, position, and crafting deadlines survive the art update and relaunch.
- [x] Loading representative older positions, including near new buildings and outside the detailed core, remains usable.
- [x] Dialogue tails track actual screen positions after the rendering/camera change.
- [x] Resume, Restart Game, Quit Game, window close, save failure, and pending transfer behavior retain their existing protections.

Use disposable backends for mutation checks. Revisit `bow_quest_smoke.gd`, `persistence_smoke.gd`, `grounded_chat_smoke.gd`, `ui_rework_smoke.gd`, and `ui_shutdown_smoke.gd`. Add focused layout checks for reachable quest approaches, collision overlap, and saved-position recovery. Rendered captures should include the same location before/after, core square, forest edge, market lane, character overlap, dialogue portraits, and a coordinate/collision debug view. Headless success alone cannot establish art quality.

## 13. Decisions to review together

| Decision | Proposed default |
| --- | --- |
| Main expansion | Confirmed preference: more village buildings and a market lane |
| First district size | Two cottage exteriors, two stalls, noticeboard, and small gardens |
| World mood | Bright woodland village, warm timber, colorful cloth and flowers |
| Pixel density | 16 px terrain tiles, 24 × 32 px human frames, 2 world units per source pixel |
| Character identity | Original player, Craftsman, and Gatherer designs; no new NPCs initially |
| Building access | Scenic exteriors; interiors and shop mechanics deferred |
| Camera | Player-centered baseline with modest facing look-ahead; approve in the scale sample |
| Art production | Original, coordinated asset kit; choose the production method after reviewing the sample brief |
| Deferred additions | Pond, larger forest, interiors, active shops, new villagers, seasons, and day/night simulation |

Initial review priority was the village/market composition and shared sprite scale. The completed GFX-01 sample review is recorded below.

## 14. Implementation ledger — 2026-10-13

User authorized implementation of GFX-01–07 with the three references above. Work proceeds in this checkout to preserve the existing, uncommitted UI rework; a baseline copy of touched UI scripts and the original diff is retained in `/tmp/willowbrook-gfx-baseline`. No backend gameplay changes are planned.

Execution plan (native, sequential):

1. GFX-01: produce and inspect a combined concept and an exact-grid sample, including character/portrait, cottage, workshop, tree, stall, bench, terrain and footprint overlays. Review before expanding assets.
2. GFX-02: add a dedicated integer-scaled world viewport, a snapped camera, separate full-resolution UI, and an explicit world-to-screen transform. Test 960×540, 1280×720, 1920×1080 and odd window sizes. Keep simulation coordinates floating point.
3. GFX-03: introduce one placed-object scene and a stable layout resource. Replace core art; retain workshop collision and all quest anchors. Test physical traversal and depth ordering.
4. GFX-04: integrate coordinated original four-direction sprite sheets, portraits and item icons. Retain NPC IDs and interaction radii. Test stable feet across frames and snapshot-controlled pickup position.
5. GFX-05: add two cottages, two stalls, board, gardens and fences. Use the shared layout for collision, debug display and safe recovery from newly solid props. Test connected approaches and old positions.
6. GFX-06: add restrained, independently phased ambient smoke/cloth/leaf motion with a reduced-motion toggle. Keep paths and quest clearing quiet.
7. GFX-07: run rendered captures and movement/layout checks, the backend suite, bow quest, persistence, grounded chat, UI rework and process-level shutdown against a unique disposable SQLite database. Review the complete diff and record exact results and limitations here.

Review focus: odd-size viewport remainders; saved positions inside new footprints; path width at bends; dialogue tails across viewport transforms; repeated shutdown during pending transfers. Tests will exercise these conditions, rather than testing only asset existence.

Art-production decision: the generated [concept sample](../evidence/graphics-overhaul/concept-sample.png) guides palette, timber/shingle detail and character identity. Its illustrative overlay is not engineering evidence. Production uses reproducible, original integer-grid pixel sources with no filtered resampling, so animation frames, pivots and pixel density are exact. The exact-grid sample must be inspected before the full set is produced.

GFX-01 review: inspected [exact-grid rendered sample](../evidence/graphics-overhaul/exact-grid-sample.png) in Godot at 1280×720 before running full asset generation. Shared square pixels and (12,30) character feet are consistent; character height fits the cottage doorway, workbench top is at hand height, workshop exceeds cottage scale, tree trunk footprint excludes canopy. Portrait shares player hair/teal palette. Proceeding with this production scale. The concept is a richer mood target; source-pixel sample is the engineering authority. Baseline backend suite: 424 tests passed with `PYTHONPATH=..`; unqualified discovery initially failed importing `backend.tests`, a test invocation issue corrected without code changes.


## 15. Final implementation and spatial decisions

| Phase | Delivered and verified |
| --- | --- |
| GFX-01 | Generated concept plus exact-grid sample inspected in a rendered Godot window before production. Sample contains character, portrait, workshop, cottage, tree, stall, bench, terrain and footprint overlays. |
| GFX-02 | `world_view.gd`: separate SubViewport at 0.5 zoom, integer 2×/3× presentation, centered remainder pixels, snapped camera and sprite presentation, explicit speaker projection. Simulation and saves retain float world coordinates. Full-resolution UI and NPC labels remain readable. |
| GFX-03 | Original pixel terrain, shingle/timber workshop, stone well, clustered woodland and work props. One reusable `PlacedProp.tscn` owns art and ground collision. Original workshop footprint is retained exactly. |
| GFX-04 | Three coordinated 24×32 character sheets, four idle/walk directions with four walk frames each; stable (12,30) pivots. Three 48×48 portraits and ten 24×24 item icons. Pickup placement consumes `bow_quest.string_position`. |
| GFX-05 | Compact market, two cottage exteriors, two stalls, board, gardens, fences, barrel/crate details. Stable IDs, pivots, footprints and approaches reside in `resources/village_layout.json` through `village_layout.tres`. No shop transactions, interiors or new NPCs were added. |
| GFX-06 | Three tree silhouettes, quiet grass/path variants, curved moss/woodland transition, stepped shadows, window flowers, garden beds and warmer path edges. Independently phased leaf/cloth animation and chimney smoke; reduced scenery motion freezes leaves/cloth and hides smoke. |
| GFX-07 | Rendered core/market/dialogue at 960×540, 1280×720, 1920×1080 and 1001×701; exact pixel-block checks; native 2× DPI; actual keyboard walking/collision; disposable-backend gameplay, persistence, grounding and shutdown validation. |

Final spatial refinements from the proposed defaults:

- Produce stall moved to **(576,-16)** and cloth stall to **(704,16)**. The original produce placement blocked Cottage A’s approach; the failing layout test demonstrated the conflict. Cottage anchors remain **(496,-96)** and **(720,-128)**. Their 64-unit aprons connect to the lane.
- Bench moved to **(280,-40)** to keep the path’s usable central width clear. The square-to-workshop path passes through **(210,32)**, placing the fixed Craftsman beside its northern edge. The pickup path bends through **(-112,128)** so it passes beside the well rather than through the stone base.
- Camera remains player-centered without smoothing or extra look-ahead. This keeps its final source pixels stable and keeps speakers above the compact dialogue panel.
- Props and actors are direct siblings under one Y-sorted world node. Trees use trunk-only collision; actor feet use **24×16 world units**. Main and pickup routes are sampled every eight units, including lateral offsets and actor-foot clearance, in addition to actual physics sweeps.
- A loaded position intersecting scenery is moved only to nearby clear ground, explained onscreen and saved through the existing position-save path. Inventory, histories, quests, deadlines and NPC IDs are untouched. Tests cover cottage/stall overlap, valid fractional coordinates, and a save outside the detailed district.
- The market remains scenery. Backend village grounding and gameplay rules were not modified, and no trading capability is implied.

Use **F3** to inspect visual bounds, collisions, foot origins and approach markers. Asset dimensions, slicing and provenance are documented in [PIXEL_ART.md](../../frontend/godot/assets/PIXEL_ART.md). The reproducible source is [build_pixel_art.py](../../frontend/godot/tools/build_pixel_art.py).

## 16. Validation and evidence

All gameplay mutation used `/tmp/willowbrook-graphics-20261013.db` on port 8001 or the grounding runner’s own temporary database/random port. Neither the normal port-8000 world nor the repository’s saved database was used. The temporary backend was stopped after validation.

| Check | Result / evidence |
| --- | --- |
| Backend suite | **424 passed**. From `backend`: `PYTHONPATH=.. PYTHONWARNINGS=ignore ../.venv/bin/python -m unittest discover -s tests -q`. [Log](../evidence/graphics-overhaul/logs/backend-tests.log). Existing dependency deprecation warnings and expected validation/fallback diagnostics are unrelated. |
| Layout and physics | **All checks passed**: shared art/collision resource, connected NPC/pickup/cottage/stall approaches, continuous path clearances, original workshop rectangle, actual collision sweeps, recovery, stable sprite pivots, camera projection, ambient/reduced-motion behavior. [Log](../evidence/graphics-overhaul/logs/layout.log). |
| Rendered graphics | **All checks passed**: integer 2×/3× pixel blocks at all requested sizes plus odd resize; terrain visibility, retained portraits, dialogue projection, keyboard-driven slow diagonal with fractional physics and integer rendered feet, all four walk frames/directions and cottage collision. Metal / Apple M5 / native display scale **2.0**. [Log](../evidence/graphics-overhaul/logs/rendered.log). |
| Bow quest | **Passed**: purpose-confirmed wood → F pickup → both gifts → real crafting delay → exactly one bow. [Log](../evidence/graphics-overhaul/logs/bow-quest.log). |
| Persistence | **Passed**: position, inventory, quest and histories across relaunch; explicit restart resets only when requested. [Log](../evidence/graphics-overhaul/logs/persistence.log). |
| Graphics state integration | **Passed**: actual old-save recovery and resave while preserving inventory/history/quest, snapshot pickup coordinates, unchanged 96-unit talk threshold, exact outside-world float position. [Log](../evidence/graphics-overhaul/logs/graphics-state.log). |
| Grounded dialogue | **295/295 passed** with configured local `llama3:latest`, including runner-owned backend/frontend relaunch, memory provenance and decision trace links. [Summary](../evidence/graphics-overhaul/logs/grounding-live-summary.json), [checks](../evidence/graphics-overhaul/logs/grounding-live.log), [resume](../evidence/graphics-overhaul/logs/grounding-resume.log). |
| Existing UI regression | **All checks passed**, rendered: movement blocking, recipient pinning, histories/supplies, late responses, pagination, compact/large text, satchel, menu focus, restart confirmation and save-error recovery. [Log](../evidence/graphics-overhaul/logs/ui.log). |
| Process-level shutdown | **4/4 modes passed**: pending gift/repeated quit/window close; real connection failure and Retry; window close; quit during loading. Backend inspection confirmed saved **(73,83)** after each process and exactly one pending food gift. [Summary](../evidence/graphics-overhaul/logs/shutdown-summary.json). |
| Shared Godot contracts | `contract_fixture_smoke.gd` and `gateway_contract_codec_smoke.gd` passed. [Regression log](../evidence/graphics-overhaul/logs/regressions.log). |
| Independent review | No critical or important implementation bugs found. Reviewer independently ran layout checks and inspected market/debug/overlap/compact-dialogue captures. Its evidence gaps were addressed with real keyboard motion and native DPI recording. No merge, push or commit performed. |

Rendered gallery:

- [Before: core at player (0,0)](../evidence/graphics-overhaul/before-core-1280.png) → [after: same world position](../evidence/graphics-overhaul/core-1280.png). Camera composition intentionally changes from the prior horizontal offset to player-centered.
- Core: [960](../evidence/graphics-overhaul/core-960.png), [1280](../evidence/graphics-overhaul/core-1280.png), [1920](../evidence/graphics-overhaul/core-1920.png), [odd resize](../evidence/graphics-overhaul/core-1001.png).
- Market: [960](../evidence/graphics-overhaul/market-960.png), [1280](../evidence/graphics-overhaul/market-1280.png), [1920](../evidence/graphics-overhaul/market-1920.png), [odd resize](../evidence/graphics-overhaul/market-1001.png), [coordinate/collision overlay](../evidence/graphics-overhaul/market-debug-1280.png).
- [Forest edge](../evidence/graphics-overhaul/forest-1280.png), [atmosphere](../evidence/graphics-overhaul/atmosphere-1280.png), tree overlap [behind](../evidence/graphics-overhaul/overlap-behind.png) / [front](../evidence/graphics-overhaul/overlap-front.png), [cottage collision](../evidence/graphics-overhaul/cottage-collision.png).
- Dialogue portraits: [960](../evidence/graphics-overhaul/dialogue-960.png), [1280](../evidence/graphics-overhaul/dialogue-1280.png), [1920](../evidence/graphics-overhaul/dialogue-1920.png). [Larger-text dialogue](../evidence/graphics-overhaul/ui-dialogue-960-large.png), [compact menu](../evidence/graphics-overhaul/ui-menu-960-large.png), [inventory during dialogue](../evidence/graphics-overhaul/ui-inventory-dialogue-960.png).
- Slow keyboard diagonal: [frame 0](../evidence/graphics-overhaul/slow-diagonal-0.png), [30](../evidence/graphics-overhaul/slow-diagonal-30.png), [60](../evidence/graphics-overhaul/slow-diagonal-60.png), [89](../evidence/graphics-overhaul/slow-diagonal-89.png). Rendered foot coordinates were sampled after `frame_post_draw`, rather than before `_process` had updated presentation.

Re-run the Godot checks with `Godot --path frontend/godot --script res://tests/<name>.gd`; add `--headless` only for non-rendered checks. Use a fresh disposable port-8001 backend for bow/persistence/state/UI/shutdown checks. Run grounding through `backend/tests/run_godot_grounding.py --godot <executable> --output <new-evidence-directory>`; it creates its own backend and database.

Validation history: initial graphics regression exposed hidden terrain and white portraits; both received failing rendered checks and were fixed (layer order and retained texture lifetime). The first grounding run used the mock provider and failed **36 fact-selection checks (259/295)**, because that provider does not perform constrained fact selection; it was superseded by the configured-provider **295/295** run, without backend changes. [Initial mock summary](../evidence/graphics-overhaul/logs/grounding-mock-summary.json). The first custom recovery test attempted a transfer through a closed conversation; correcting the test to use the existing open-chat flow verified preservation without changing transfer behavior.

Limitations: validation covers macOS Metal at native 2× DPI and the stated window sizes. Windows/Linux, other DPI factors and extremely large arbitrary window sizes were not exercised. Scenic exteriors remain closed; no new shopping or dialogue knowledge was added. The concept board is mood guidance; production artwork is the exact-grid original kit. No known failing checks remain in the final tree.

Existing unrelated changes were left intact: README, quest panel, grounded-chat test, persistence test and the pre-existing UI work. Baseline comparison confirmed those unrelated tracked diffs are byte-for-byte identical to their initial state; graphics edits in main/chat/item-grid are layered over their saved initial versions.
