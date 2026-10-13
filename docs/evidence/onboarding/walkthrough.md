# First-control onboarding

At the shipwreck opening's gameplay handoff, a large parchment controls card
pauses player movement. It explains WASD movement, E to talk/inspect/enter, F
to pick up nearby items, I for the bag, and Escape for menus/closing panels.
Click **Let's go**, activate the focused button with the keyboard, or press
Escape to dismiss it. Holding the opening's fast-forward key cannot
immediately activate the dismissal button.

After dismissal, **Find someone to get help.** appears near screen center for
1.6 seconds, then smoothly moves to (24, 100) under the village heading and
shrinks to 65% over 1.1 seconds. Gameplay remains active during the objective
animation; opening the menu pauses it. Reduced motion holds the text centrally,
then docks it without the travel animation. Both presentations inherit the
fullscreen UI scaling.

Acknowledgment is saved locally in `user://onboarding-presentation.cfg`, keyed
by the backend's `game_scope`. Reloading restores the objective in its docked
position. A new game gets the controls card again after its opening. Existing
saves receive the card once on their first launch with this feature. This is
presentation state, separate from quests, inventory and NPC memory.

Implementation: `frontend/godot/scripts/onboarding.gd`, integrated with the
world-load, opening handoff, input ownership and restart paths in `main.gd`.

Validation on Godot 4.5.1:

```sh
/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot \
  --headless --log-file /tmp/onboarding.log --path frontend/godot \
  --script res://tests/onboarding_smoke.gd
```

Set `ONBOARDING_RENDER=1` and omit `--headless` to capture controls at 960 × 540
and 1920 × 1080 plus centered/docked objective views. Tests cover modal input,
movement release, layout, sequencing, menu pause, local persistence, new-run
reset, actual cinematic completion through the real session with a fake
checkpoint adapter, resumed world loading, and reduced motion. No real saved
world or backend is touched by this test.

Also passed: fisherman graph and integration, fullscreen UI/automatic Rowan
walking, graphics layout, opening lifecycle, and all 432 backend unittest tests.
Review found no critical or important issues. Headless runs have the existing
macOS system-certificate diagnostic; rendered runs complete cleanly.

[Controls card, small window](controls-960.png) ·
[Controls card, fullscreen size](controls-1920.png) ·
[Centered objective](objective-center.png) ·
[Docked objective](objective-docked.png).

The help objective now completes when Rowan's introduction starts: a brief green
check mark draws, then the label fades out permanently for that run.
[Completion and inspection verification](../inspections/walkthrough.md).
