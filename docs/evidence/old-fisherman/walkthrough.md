# Rowan encounter implementation — 13 October 2026

Implements [the encounter specification](../../old-fisherman-dialogue-tree.md).

## Play

Start the backend and Godot as described in the README. Walk north from the
wreck along the existing southern path. Rowan sits on the fallen log at
(250, 2250), east of the path. Entering 320 world units (10 meters at 32 units
per meter) starts an automatic approach followed by a 1.8-second introduction: the seated fisherman looks up,
the camera cuts to a shared framing, and F00 opens. Later, approach within
100 world units and press E. Close / Back or Escape releases movement.

For the specified demo, choose Can you help me? → My boat crashed on the rocks.
→ Is there anyone in the village who could help? Read E08, then Continue.
The dialogue closes; press E to hear F00 and its original choices again. Continue into the village to
compare against the existing AI villagers.

## Implementation

- `resources/fisherman_dialogue.json` contains the exact seven authored branch
  nodes and eight final replies. No generated dialogue, conversational memory,
  rewards, inventory changes, or backend calls are part of this encounter.
- `scripts/fisherman_encounter.gd` owns the fixed panel, introduction and original
  pixel-grid Rowan artwork. It uses the existing theme and nearest filtering.
  Rowan's rendering origin is two units in front of the log for Y sorting;
  the artwork compensates by two units so his hips rest on the seat.
- The fallen-log family and its source generator now provide a broad level seat,
  bark grain, an end stub and foliage behind the ends. The grounded collision
  footprint is 116 × 28 world units; the front approach remains clear.
- The introduction flag is presentation-only, stored locally in
  `user://fisherman-presentation.cfg`, keyed by the backend's saved `game_scope`.
  Relaunching the same save keeps it; Restart Game creates a new scope. Moving
  the save to another device does not carry this local presentation flag.
- World Camera2D already used zoom (0.75, 0.75) when this work began. Retained it,
  updated the obsolete 0.5 graphics assertion, and reviewed 10 opening samples
  at both 960 × 540 and 1920 × 1080. The coast-reveal shot intentionally frames
  the approaching shore with the boat entering from below.

## Verification

Godot 4.5.1, the installed runtime:

```sh
GODOT=/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot
"$GODOT" --headless --log-file /tmp/fisherman.log --path frontend/godot \
  --script res://tests/fisherman_smoke.gd
"$GODOT" --headless --log-file /tmp/fisherman-integration.log --path frontend/godot \
  --script res://tests/fisherman_integration_smoke.gd
FISHERMAN_RENDER=1 "$GODOT" --log-file /tmp/fisherman-render.log \
  --path frontend/godot --script res://tests/fisherman_integration_smoke.gd
```

Both fisherman suites pass, including all eight three-selection paths, exact
opening on reinteraction, explicit Continue/close, Close/reopen, no free-form field, radius
boundary, saved presentation flag, new-run reset, menu pause/stack order, Escape,
movement ownership, clear approach and required camera zoom. Integration uses
a test subclass that suppresses HTTP loading; it never touches the player's save.
Rendered checks pass at 960 × 540 and 1280 × 720. Original source art is authored
in this repository, with no external image sources.

Also passed: graphics layout; beach layout; island layout, mask and world;
south approach, corner and route; opening clock, effects, crash, ownership,
recovery and lifecycle. The full backend unittest suite passed 432 tests.
Sandboxed headless Godot prints a macOS system-certificate diagnostic; rendered
runs complete without it. Live AI conversation quality and gamepad interaction
were not evaluated as part of this encounter implementation.

Screenshots: [dialogue at 960](rowan-960.png), [dialogue at 1280](rowan-1280.png),
[seat and approach](seat-1280.png), [opening coast reveal](opening-coast-960.png),
[opening recovery](opening-recovery-1920.png).

## Fullscreen and automatic approach update

The HUD, menus, inventory and both dialogue styles now scale from a 1280 × 720
logical UI canvas. At 1920 × 1080 they are 1.5×, at 2560 × 1440 2×, and at
3840 × 2160 3×. Short or ultrawide windows retain enough logical space for the
panels. NPC labels, dialogue pointers and history/supplies overlays use the
appropriate logical or screen coordinates. Opening hints/captions and the
restart confirmation scale as well. World-camera magnification is unchanged.

The first proximity introduction now takes control and walks the player at normal
speed to (250, 2310), in front of the log. A local collision-aware grid routes
approaches from behind and either end of the trunk. Dialogue waits for arrival
and the look-up; the menu pauses the walk and Escape cancels it. Unexpected
physical obstructions cancel movement instead of teleporting the player.
Repeat E interactions retain the direct F00 opening.

`res://tests/fullscreen_rowan_smoke.gd` checks scaling and fit at small, 1080p,
1440p, 4K and ultrawide sizes; AI dialogue/history and menu placement; walking,
arrival clearance, menu pause, cancellation and routes around the log. Use
`FISHERMAN_RENDER=1` to capture the same checks. macOS limits oversized native
windows to its available screen height, so native captures verify the actual
viewport size; headless checks cover the full requested 4K canvas.

Final rendered checks also passed in actual fullscreen mode.
[Fullscreen dialogue](rowan-fullscreen.png) · [enlarged 1080p menu](menu-1080p.png).

Final Continue now closes Rowan’s dialogue. E reopens F00 on a new interaction.
All eight endings and the real E interaction path are covered by the updated tests.
