# Willowbrook pixel kit

Original project artwork, authored as integer pixel grids by `tools/build_pixel_art.py`.
No pixels were extracted from the supplied game screenshots. Those references inform
composition, clustered materials, scale and character individuality. The generated
concept board was reviewed for mood; it was not sliced into production assets.
SVG sources encode exact pixel-color runs, with no gradients or curves. No external
asset license is required for this original kit. Existing font licensing is in `fonts/OFL.txt`.

Regenerate with `python3 frontend/godot/tools/build_pixel_art.py` from the repository
root, then run Godot editor import. `--sample` emits the combined-scale sample sources.
All source pixels occupy two world units. Godot renders at 0.5 camera zoom and enlarges
the world viewport by an integer. UI remains separate at full window resolution.

| Asset | Source dimensions | Source pivot / slicing |
| --- | --- | --- |
| Terrain | 16×16 | top-left; 32×32 world tile |
| Actors | 120×128 sheet | 24×32 frames; columns idle, walk 1–4; rows down, left, right, up; feet (12,30) |
| Portraits | 48×48 | 96×96 UI display |
| Items | 24×24 | 48×48 UI display; string also used in the world |
| Workshop | 128×120 | (64,115); original 230×125 collision retained |
| Cottages | 80×96 | (40,91); enter through front door aprons |
| Interior floors | 320×224 | top-left; 640×448 world rooms with north wall and south exit |
| Interior furniture | 48×64 or 64×48/64 | foot pivots and footprints in `building_interiors.json` |
| Trees | 48×72 | (24,68); three silhouettes, two restrained leaf frames |
| Stalls | 48×48 | (24,44); two cloth frames |
| Bench | 48×32 | (24,28) |
| Well, board, household/nature props | 48×56 | normally (24,50); smoke shares workshop sort origin with a visual offset |

`resources/village_layout.json`, loaded through `village_layout.tres`, is the sole
exterior placement/footprint/approach source. `resources/building_interiors.json`
defines furnished rooms, actor spawns and furniture footprints. The original
`interior-*.svg` art is authored directly on integer grids using the same palette;
the exterior generator does not overwrite these files. Rooms occupy separate world
coordinates so existing position saves resume indoors without a new save format.
`scenes/world/PlacedProp.tscn` pairs each sprite
with its collider and ground origin. Terrain sits beneath Y-sorted prop/actor siblings.
Actor foot collisions are 24×16 world units. Talk distance remains 96; string pickup
remains 64 and consumes the exact quest-snapshot location.

Press **F3** to inspect visual bounds (pale green), collisions (coral), ground origins
(cyan), and approach markers (yellow). The Esc menu offers **Reduced scenery motion**,
which freezes cloth/leaves and hides chimney smoke. New solids recover trapped older
positions to nearby clear ground without changing inventory, quest, histories or deadlines.
Outside positions retain their floats and have no artificial rectangular map boundary.
