# UI rework validation — 2026-10-13

Godot 4.5.1, macOS, Metal rendering. All mutation checks use disposable SQLite
worlds; the player's database and port 8000 were not used.

- `backend-tests.log`: 424 backend tests passed. From `backend`:
  `PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -v`
- `ui-rework.log`: 29/29 rendered assertions passed for focus, menu, recipient, inventory, history, paging,
  fallback and failure checks. Screenshots use true 960×540, 1280×720 and
  1920×1080 root content sizes, plus larger text at 960×540.
- `bow-quest.log`: complete actual HTTP quest, purpose-confirmed wood, pickup,
  gifts, crafting delay and exactly one reward. `crafting-1280.png` and
  `completed-1280.png` show the authoritative crafting/completion states.
- `persistence.log`: scene relaunch restores position, items, quest and history;
  confirmed restart clears them. Existing assertions are retained through the
  stable `conversation_text()` presentation accessor.
- `shutdown-*.log`: real process exits for pending gift + repeated Quit/window
  close, initial loading, normal window close, and actual failed save + Retry.
  Read-only SQLite verification after exit confirmed position `{x:73,y:83}`;
  the pending-gift case had exactly one food in Craftsman's inventory and only
  water remaining in the player's inventory. Failed save stayed open until retry.
- `grounded-live/summary.json`: **301/301** checks passed against llama3:latest,
  including backend/Godot relaunch, grounded history, authoritative effects,
  source-linked decision traces and explicit restart. Runner owns its endpoint,
  temporary project and database; the recorded SHA256s identify that test snapshot.
- `provider-failure/summary.json`: **22/22** checks passed against an unreachable
  provider, with rendered fallback and zero unauthorized effects.

The preliminary mock-provider grounding run was not suitable for provider-dependent
fact assertions. The subsequent configured live-provider run above passed every
assertion; the mock run is not presented as grounding evidence.

## Reproduce

Start a fresh backend on port 8001 from the repository root (choose an unused
SQLite filename; never use the player's save):

```sh
DATABASE_URL=sqlite:////tmp/willowbrook-ui-disposable.db LLM_BASE_URL='' \
  PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --port 8001
```

Import with Godot `--headless --path frontend/godot --editor --import`, then run:

```sh
Godot --path frontend/godot --script res://tests/ui_rework_smoke.gd
Godot --path frontend/godot --script res://tests/bow_quest_smoke.gd
Godot --path frontend/godot --script res://tests/persistence_smoke.gd
Godot --path frontend/godot --script res://tests/ui_shutdown_smoke.gd -- --mode=pending
Godot --path frontend/godot --script res://tests/ui_shutdown_smoke.gd -- --mode=failure
Godot --path frontend/godot --script res://tests/ui_shutdown_smoke.gd -- --mode=loading
Godot --path frontend/godot --script res://tests/ui_shutdown_smoke.gd -- --mode=close
```

Run these sequentially: they reset the disposable world. The UI test writes
screenshots to `/tmp/willowbrook-ui`; the bow check writes `/tmp/npc-bow-*.png`.
For the separate live-provider and failure suites (each owns its own database):

```sh
.venv/bin/python backend/tests/run_godot_grounding.py --godot /path/to/Godot \
  --output /tmp/ui-live-new --rendered
.venv/bin/python backend/tests/run_godot_grounding.py --godot /path/to/Godot \
  --output /tmp/ui-failure-new --rendered --provider-failure
```

Visual review confirmed readable font/punctuation, visible focused/selected slots,
wrapping and local dialogue pages, distinct portraits, short speaker tails,
above-dialogue overlays, preserved reply area, and visible save recovery. Font
fallback coverage beyond the bundled face depends on installed OS fonts. Existing
SVG item artwork is intentionally retained; bespoke pixel item art and typewriter
reveal remain optional follow-ups, not unfinished gameplay work.
