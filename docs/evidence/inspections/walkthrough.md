# Objective completion and inspections

- Entering Rowan's introduction radius starts the automatic approach and completes
  **Find someone to get help.** A green check mark draws over 0.28 seconds,
  holds fully drawn for 1.5 seconds, then fades out over 0.45 seconds; the full
  presentation lasts 2.23 seconds.
  It stays hidden across reloads. Fresh games reset it. Existing saves whose
  Rowan introduction already played also hide the objective.
- Press **E** near the broken hull to read its description in a parchment text
  panel. **Close**, keyboard activation of the focused button, or **Escape**
  dismisses it. Movement and background interaction hints pause while reading.
- Press **E** near the wooden sign at (150, 940) to read **Willowbrook**. Its
  original pixel-grid arrow artwork now points up/north, toward the village.
  The same reusable panel presents both inspections and scales with the HUD.

Implementation: `inspection_popup.gd` and the inspection lookup in `main.gd`;
objective presentation/persistence in `onboarding.gd`; sign source artwork in
`tools/build_south_assets.py`, using the shared position in `south_scenery.gd`.
Only presentation state changes; inventory, quest and NPC memory stay unchanged.

Validation:

```sh
/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot \
  --headless --log-file /tmp/inspection.log --path frontend/godot \
  --script res://tests/inspection_objective_smoke.gd
```

Set `INSPECTION_RENDER=1` and omit `--headless` for rendered captures at
960 × 540 and 1920 × 1080. The check covers hull/sign interactions, text,
input ownership, Close/Escape, layout, objective completion, saved-run reload,
and fresh-run reset. Rendered checks pass. Also passed: onboarding, fisherman
graph/integration, fullscreen UI/automatic approach, graphics layout, south
approach/route, opening lifecycle, and 432 backend unittest tests.

[Sign inspection at 960](sign-960.png) ·
[Sign inspection at 1920](sign-1920.png) ·
[Completed objective check mark](objective-checkmark.png).
