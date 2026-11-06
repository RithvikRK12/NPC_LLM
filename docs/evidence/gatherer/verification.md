# Gatherer encounter verification — 2026-10-14

Implemented the approved design in dedicated encounter, gateway, combat and boar controllers, with a transactional backend story record. Existing craftsman and other uncommitted work was retained; no commits or resets were made.

## Checks

- Backend: **462 tests pass** with `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests`. Nine Gatherer tests cover legal branches, stale attempts/revisions/scopes, duplicate request IDs, rollback, relationship clamping, memory revision invalidation, all durable states, reset, explicit dialogue context and refusal-aware mock dialogue.
- Godot: **22 regression scripts pass their gameplay assertions**, including Gatherer combat, routing, gateway recovery, input ownership and full integration; forest chat; fisherman; opening; craftsman; interiors; bow quest; persistence; and contract codec. Engine: Godot 4.5.1.
- Rendered gameplay: help/victory, idle-player defeat/local retry, choosing decline after retry, retreat/return, and reload during combat, retreat, confrontation and thanks pass at **960×540 and 1280×720**. Screenshots were inspected; a minimum-resolution HUD overlap was reproduced and fixed.
- Rendered physical approaches from east, north, south and west pass, using the real scenery collisions and ActorRouter. Every authored staging point and the arena grid also pass walkability checks.
- Disconnected victory save holds both dead boars safely. Retry preserves the request ID and completes thanks after reconnecting. Gateway checks cover lost responses, authoritative revision-conflict refresh, and rejecting old-scope callbacks.
- Pause freezes boar movement and damage; Escape does not choose a branch; Bag/Quests buttons are blocked while the encounter owns interaction. Combat remains movable.
- Bow progression completes after refusal, including real inventory transfers, string pickup, timed crafting and exactly one bow reward.
- `git diff --check` passes.

Tests use a disposable SQLite database at `/tmp/gatherer-verification.db` and local backend port 8001. The user's normal database is untouched. Backend tests use in-memory databases. The live external LLM was not exercised; provider behavior and dialogue grounding are tested locally.

## Review and fixes

A separate read-only review found no important correctness defects. Its stale relationship-tooltip finding was reproduced and fixed by including the NPC state in command responses. Additional checks fixed a clickable Quests overlay bypass, empty failed-response JSON parsing, and minimum-resolution HUD occlusion. Cutscene pacing, warning poses/audio and angry confrontation cues were checked in rendered gameplay.

## Remaining limitation

Several existing regression scripts emit exit-time ObjectDB/resource cleanup warnings despite zero failed gameplay assertions. A verbose fisherman run identifies the existing opening `surf.wav` playback resource as one source. These unrelated cleanup warnings are retained in test output rather than changing the opening/audio systems.

## Reproduce

Start a disposable backend:

```sh
DATABASE_URL=sqlite:////tmp/gatherer-verification.db LLM_BASE_URL='' LLM_API_KEY='' \
  .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

Then use the installed Godot executable:

```sh
Godot --headless --log-file /tmp/gatherer-test.log --path frontend/godot \
  --script res://tests/gatherer_integration_smoke.gd
Godot --log-file /tmp/gatherer-render.log --path frontend/godot --resolution 960x540 \
  --script res://tests/gatherer_integration_smoke.gd
Godot --log-file /tmp/gatherer-approaches.log --path frontend/godot \
  --script res://tests/gatherer_approaches_smoke.gd
```

Rendered screenshots go to `/tmp/gatherer-evidence` by default; set `GATHERER_EVIDENCE` to choose another directory. Test scripts reset only the disposable port-8001 world.
