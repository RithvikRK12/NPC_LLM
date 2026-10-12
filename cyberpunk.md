# Cyberpunk Theme Conversion Plan and Command Log

## 1. Project Objective

Transform the existing NPC quest demo on branch `cyberpunk-npc` into a polished cyberpunk-themed hackathon presentation build for Gameathon 8.0 by Jyothy Institute of Technology, Information Science Engineering, Bits & Bytes x ACM.

The conversion keeps the current backend architecture, quest workflow, API shape, testability, inventory transfer, pickup, timed crafting, save/resume, and reset behavior. The theme shifts from a village/craftsman/gatherer bow quest to a neon city AI/NPC quest where a Runner assembles a Pulse Blaster in the JIT Cyber Grid.

## 2. Current Repo Inspection Notes

- Backend is a FastAPI app under `backend/app`.
- NPC seed data lives in `backend/app/database/seed.py`.
- The authoritative timed quest logic lives in `backend/app/services/quests/bow.py`; route naming uses `/quests/bow/...`, so this will be preserved for API compatibility while content becomes cyberpunk.
- Inventory transfer validation lives in `backend/app/services/validation/items.py`.
- Dialogue/topic guardrails live in:
  - `backend/app/services/validation/knowledge.py`
  - `backend/app/services/validation/quest_dialogue.py`
  - `backend/app/services/validation/service.py`
- Tests are mostly in `backend/tests/test_npc_pipeline.py`, with contract and validation fixtures elsewhere.
- Godot project is under `frontend/godot`.
- The world is drawn procedurally by `frontend/godot/scripts/village.gd`.
- Main UI/world wiring is in `frontend/godot/scripts/main.gd`.
- Character drawing is in `frontend/godot/scripts/person.gd`.
- Quest panel and item cards are in:
  - `frontend/godot/scripts/quest_panel.gd`
  - `frontend/godot/scripts/item_grid.gd`
- Item SVGs are under `frontend/godot/assets/items`.
- Existing git worktree already contains unrelated modified/untracked backend and docs files; do not revert them.

## 3. Exact Files That Will Be Changed

Planned changes:

- `cyberpunk.md`
- `backend/app/api/routes/inventory.py`
- `backend/app/api/routes/quests.py`
- `backend/app/database/inventory_migration.py`
- `backend/app/database/seed.py`
- `backend/app/models/npc.py`
- `backend/app/models/player.py`
- `backend/app/services/llm/mock.py`
- `backend/app/services/pipeline.py`
- `backend/app/services/prompts/builder.py`
- `backend/app/services/quests/bow.py`
- `backend/app/services/state/service.py`
- `backend/app/services/validation/items.py`
- `backend/app/services/validation/knowledge.py`
- `backend/app/services/validation/quest_dialogue.py`
- `backend/app/services/validation/service.py`
- `backend/tests/test_inventory_migration.py`
- `backend/tests/test_npc_pipeline.py`
- `frontend/godot/scripts/chat_window.gd`
- `frontend/godot/scripts/item_grid.gd`
- `frontend/godot/scripts/main.gd`
- `frontend/godot/scripts/npc.gd`
- `frontend/godot/scripts/person.gd`
- `frontend/godot/scripts/quest_panel.gd`
- `frontend/godot/scripts/village.gd`
- `frontend/godot/tests/bow_quest_smoke.gd`
- `frontend/godot/tests/persistence_smoke.gd`
- `frontend/godot/assets/items/circuit_board.svg`
- `frontend/godot/assets/items/circuit_board.svg.import`
- `frontend/godot/assets/items/data_shard.svg`
- `frontend/godot/assets/items/data_shard.svg.import`
- `frontend/godot/assets/items/diagnostic_tool.svg`
- `frontend/godot/assets/items/diagnostic_tool.svg.import`
- `frontend/godot/assets/items/energy_cell.svg`
- `frontend/godot/assets/items/energy_cell.svg.import`
- `frontend/godot/assets/items/fiber_cable.svg`
- `frontend/godot/assets/items/fiber_cable.svg.import`
- `frontend/godot/assets/items/med_patch.svg`
- `frontend/godot/assets/items/med_patch.svg.import`
- `frontend/godot/assets/items/nano_solder.svg`
- `frontend/godot/assets/items/nano_solder.svg.import`
- `frontend/godot/assets/items/pulse_blaster.svg`
- `frontend/godot/assets/items/pulse_blaster.svg.import`
- `frontend/godot/assets/items/scanner.svg`
- `frontend/godot/assets/items/scanner.svg.import`
- `frontend/godot/assets/items/scrap_alloy.svg`
- `frontend/godot/assets/items/scrap_alloy.svg.import`
- `frontend/godot/assets/backgrounds/cyberpunk_plaza.png`
- `frontend/godot/assets/backgrounds/cyberpunk_plaza.png.import`

## 4. Command Log and Executable Commands

Commands already run:

```bash
pwd
rg --files
git status --short --branch
sed -n '1,240p' backend/app/database/seed.py
sed -n '1,260p' backend/app/services/quests/bow.py
sed -n '1,260p' backend/app/services/validation/items.py
sed -n '1,260p' backend/app/services/validation/knowledge.py
sed -n '1,260p' backend/app/services/validation/quest_dialogue.py
sed -n '1,320p' frontend/godot/scenes/Main.tscn
sed -n '1,320p' frontend/godot/scripts/village.gd
sed -n '1,320p' frontend/godot/scripts/main.gd
sed -n '1,260p' frontend/godot/scripts/npc.gd
sed -n '1,260p' frontend/godot/scripts/quest_panel.gd
sed -n '320,700p' frontend/godot/scripts/main.gd
sed -n '1,280p' frontend/godot/scripts/person.gd
sed -n '1,260p' frontend/godot/scripts/player.gd
sed -n '1,260p' frontend/godot/scripts/item_grid.gd
sed -n '1,300p' backend/tests/test_npc_pipeline.py
sed -n '300,620p' backend/tests/test_npc_pipeline.py
sed -n '1,260p' backend/app/api/routes/quests.py
sed -n '1,300p' backend/app/api/routes/inventory.py
sed -n '1,260p' backend/app/services/llm/mock.py
sed -n '1,340p' backend/app/services/validation/service.py
sed -n '1,260p' backend/app/api/routes/world.py
rg "wood|bow|Craftsman|Gatherer|village|forest|axe|rope|fruits|water|food|string|hammer" backend/tests/test_npc_pipeline.py
perl -0pi -e 's/wood/circuit_board/g; s/string/fiber_cable/g; s/bow/pulse_blaster/g; s/rope/scrap_alloy/g; s/fruits/data_shard/g; s/hammer/nano_solder/g; s/water/energy_cell/g; s/food/med_patch/g; s/axe/scanner/g; s/saw/diagnostic_tool/g; s/Craftsman/Neon Techsmith/g; s/Gatherer/Data Broker/g; s/craftsman/techsmith/g; s/gatherer/broker/g; s/village/grid/g; s/forest/alley/g; s/Get a pulse_blaster/Assemble Pulse Blaster/g; s/pulse_blaster_quest/bow_quest/g; s/test_pulse_blaster/test_bow/g; s/app\.services\.quests\.pulse_blaster/app.services.quests.bow/g' backend/tests/test_npc_pipeline.py
sed -n '1,420p' backend/tests/test_npc_pipeline.py
sed -n '420,760p' backend/tests/test_npc_pipeline.py
sed -n '1,220p' backend/app/services/validation/models.py
rg "quests/pulse|pickup-fiber|techsmith|broker|fiber_cable_collected|NPC\(role='techsmith|NPC\(role='broker|What is AI\?|artificial intelligence|/quests/pulse|craft_scanner|Craftsman|Gatherer|wood|bow|rope|fruits|water|food|string|axe|hammer|saw" backend/tests/test_npc_pipeline.py
rg "village|Village|Craftsman|Gatherer|String|SATCHEL|satchel|wood|bow|Quests|string|water|food|forest|workshop" frontend/godot/scripts/main.gd frontend/godot/scripts/quest_panel.gd frontend/godot/scripts/npc.gd frontend/godot/scripts/item_grid.gd frontend/godot/scripts/person.gd
rg 'Color\("[0-9a-fA-F]+",' frontend/godot/scripts
perl -0pi -e 's/Color\("([0-9a-fA-F]+)", ([^)]+)\)/_ca("$1", $2)/g' frontend/godot/scripts/village.gd frontend/godot/scripts/main.gd frontend/godot/scripts/quest_panel.gd frontend/godot/scripts/person.gd frontend/godot/scripts/item_grid.gd
sed -n '1,320p' frontend/godot/scripts/chat_window.gd
rg "village|Village|Craftsman|Gatherer|forest|wood|string|bow|water|food|axe|rope|fruits|hammer|saw" backend/app frontend/godot/scripts frontend/godot/tests
rg '_ca\(' frontend/godot/scripts
rg "quests/pulse|fiber_cable_available|techsmith|broker|NPC\(role='techsmith|NPC\(role='broker|craft_scanner|pickup-fiber|pulse_blaster/start" backend/tests/test_npc_pipeline.py
sed -n '1,340p' backend/app/services/pipeline.py
sed -n '1,220p' backend/app/services/prompts/builder.py
sed -n '1,220p' backend/app/services/state/service.py
sed -n '1,200p' backend/app/database/inventory_migration.py
sed -n '1,80p' backend/app/models/player.py && sed -n '1,100p' backend/app/models/npc.py
sed -n '1,260p' frontend/godot/tests/bow_quest_smoke.gd
sed -n '1,220p' frontend/godot/tests/persistence_smoke.gd
python -m pytest tests/test_npc_pipeline.py
python3 -m pytest tests/test_npc_pipeline.py
ls -la
ls -la
rg --files -g 'pyproject.toml' -g 'pytest.ini' -g 'tox.ini' -g 'setup.cfg' -g '.venv' -g 'uv.lock' -g 'Pipfile' -g 'poetry.lock'
../.venv/bin/python -m pytest tests/test_npc_pipeline.py
.venv/bin/python -m pytest tests/test_npc_pipeline.py
which pytest
sed -n '1,220p' backend/requirements.txt
backend/.venv/bin/python -m pip list
backend/.venv/bin/python -m pip install pytest
backend/.venv/bin/python -m pytest tests/test_npc_pipeline.py
.venv/bin/python -m pytest tests/test_npc_pipeline.py
.venv/bin/python -m pytest
PYTHONPATH=/Users/rithvik/Desktop/majorprojectimplementation:/Users/rithvik/Desktop/majorprojectimplementation/backend backend/.venv/bin/python -m pytest backend
sed -n '1,160p' backend/tests/test_inventory_migration.py
PYTHONPATH=/Users/rithvik/Desktop/majorprojectimplementation:/Users/rithvik/Desktop/majorprojectimplementation/backend backend/.venv/bin/python -m pytest backend
which godot
which godot4
ls /Applications | rg -i 'godot'
godot --headless --path . --quit
sed -n '1,120p' frontend/godot/assets/items/string.svg.import
godot --headless --path . --quit
godot --headless --path . --import
godot --headless --path . --quit
backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
sed -n '1,180p' backend/app/config/settings.py && sed -n '1,100p' backend/.env.example
DATABASE_URL=sqlite:////private/tmp/cyberpunk-smoke.db .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
godot --headless --path . -s res://tests/bow_quest_smoke.gd
godot --headless --path . -s res://tests/bow_quest_smoke.gd
godot --headless --path . -s res://tests/persistence_smoke.gd
git status --short
git diff --stat
sed -n '1,260p' cyberpunk.md
rg "water|food|wood|string|bow|village|forest|Craftsman|Gatherer|Get a bow|well" backend/app frontend/godot/scripts frontend/godot/tests backend/tests/test_npc_pipeline.py backend/tests/test_inventory_migration.py
sed -n '1,260p' /Users/rithvik/.codex/skills/.system/imagegen/SKILL.md
sed -n '1,260p' frontend/godot/project.godot
sed -n '1,260p' frontend/godot/scripts/village.gd
sed -n '1,220p' frontend/godot/scripts/person.gd
mkdir -p frontend/godot/assets/backgrounds
cp /Users/rithvik/.codex/generated_images/01a10f94-d0bb-7280-9a18-72b94ec00593/call_uoeCfkMYmdHFSulUke8WEUCQ.png frontend/godot/assets/backgrounds/cyberpunk_plaza.png
file frontend/godot/assets/backgrounds/cyberpunk_plaza.png
sed -n '1,260p' frontend/godot/scripts/main.gd
sed -n '1,200p' frontend/godot/scripts/player.gd
godot --headless --path . --import
godot --headless --path . --quit
godot --headless --path . -s res://tests/bow_quest_smoke.gd
DATABASE_URL=sqlite:////private/tmp/cyberpunk-smoke-graphics.db .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
godot --headless --path . -s res://tests/bow_quest_smoke.gd
godot --path .
sed -n '1,360p' frontend/godot/scripts/main.gd
sed -n '1,260p' frontend/godot/scripts/village.gd
sed -n '1,220p' frontend/godot/scripts/npc.gd
sed -n '1,220p' frontend/godot/scripts/quest_panel.gd
godot --headless --path . --quit
DATABASE_URL=sqlite:////private/tmp/cyberpunk-smoke-collision.db .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
godot --headless --path . -s res://tests/bow_quest_smoke.gd
godot --path .
```

Commands needed to run and verify:

```bash
cd /Users/rithvik/Desktop/majorprojectimplementation/backend
./.venv/bin/python -m pytest tests/test_npc_pipeline.py
cd /Users/rithvik/Desktop/majorprojectimplementation
PYTHONPATH=/Users/rithvik/Desktop/majorprojectimplementation:/Users/rithvik/Desktop/majorprojectimplementation/backend backend/.venv/bin/python -m pytest backend
cd /Users/rithvik/Desktop/majorprojectimplementation/frontend/godot
godot --headless --path . --quit
godot --headless --path . -s res://tests/bow_quest_smoke.gd
godot --headless --path . -s res://tests/persistence_smoke.gd
godot --path .
```

Run backend API locally:

```bash
cd /Users/rithvik/Desktop/majorprojectimplementation/backend
./.venv/bin/uvicorn app.main:app --reload
```

Run Godot game manually:

```bash
cd /Users/rithvik/Desktop/majorprojectimplementation/frontend/godot
godot --path .
```

## 5. Step-by-Step Implementation Checklist

- [x] Inspect repository structure and current backend/Godot quest flow.
- [x] Create `cyberpunk.md` before implementation edits.
- [x] Rename and reskin NPCs, player-facing place names, inventory items, quest title/objectives, and authoritative dialogue.
- [x] Preserve the timed quest API and mechanics while making it read as Pulse Blaster assembly.
- [x] Update validation-safe item lists and quest dialogue fallbacks.
- [x] Update mock LLM content so tests and demos stay in-theme.
- [x] Update backend tests for renamed items and cyberpunk dialogue.
- [x] Upgrade Godot world drawing to a neon cyberpunk district with skyline, signs, glowing paths, power junction pickup, and atmospheric accents.
- [x] Upgrade player/NPC appearance to cyberpunk silhouettes with neon accents.
- [x] Update UI labels, quest panel, inventory styling, and pickup hints for the hackathon presentation.
- [x] Add or edit lightweight SVG item icons for cyberpunk items.
- [x] Run focused backend tests.
- [x] Run full backend tests.
- [x] Attempt Godot headless validation if Godot CLI is available.
- [x] Update this file with final changed files, final command log, test results, known limitations, and demo instructions.

## 6. Final Verification Checklist

- [x] Backend tests pass.
- [x] Focused quest flow test passes.
- [x] Quest can start from the UI.
- [x] Techsmith/engineer asks for materials/components.
- [x] Broker/fixer can provide one needed component through validated transfer.
- [x] World pickup appears only in the gather phase and can be collected only nearby.
- [x] Components can be given to the Techsmith.
- [x] Timed crafting/building progresses and grants exactly one reward.
- [x] Reset clears inventories, chats, NPC memories, player position, and active crafting state.
- [x] Validation blocks hallucinated quest rewards and unsafe inventory claims.
- [x] Godot project remains Godot 4 compatible.
- [x] Visual first impression clearly reads as a cyberpunk city demo.

## 7. Hackathon Presentation/Demo Notes

- Demo title: `JIT Cyber Grid`.
- Suggested story beat: the Runner needs a Pulse Blaster to restore signal control in Byte Alley.
- Judge-facing flow:
  1. Open Quests and start `Assemble Pulse Blaster`.
  2. Talk to the Techsmith to show grounded AI/NPC quest context.
  3. Ask the Data Broker for the circuit board to show validated item transfer and purpose confirmation.
  4. Pick up the fiber cable near the power junction to show world-state quest gating.
  5. Give both components to the Techsmith.
  6. Show timed assembly progress and final reward.
  7. Mention memory/context persistence, reset, validation, and hallucination-safe reward handling.

## Final Results

Implemented.

Final verification:

- Focused backend: `31 passed, 178 warnings` with `./.venv/bin/python -m pytest tests/test_npc_pipeline.py`.
- Full backend: `207 passed, 184 warnings` with `PYTHONPATH=/Users/rithvik/Desktop/majorprojectimplementation:/Users/rithvik/Desktop/majorprojectimplementation/backend backend/.venv/bin/python -m pytest backend`.
- Godot import/parse: `godot --headless --path . --quit` ran after `godot --headless --path . --import`; no GDScript parse errors remained.
- Godot quest smoke: passed with `PASS: free roam -> mission -> component dialogue -> confirmed circuit board -> F pickup -> gifts -> timed progress -> one Pulse Blaster`.
- Godot persistence smoke: passed with `PASS persistence across launches and explicit restart`.
- Graphics improvement pass: replaced the mostly procedural rectangle world with a project-local generated raster background at `frontend/godot/assets/backgrounds/cyberpunk_plaza.png`, retained Godot-drawn mission markers/labels, moved NPCs onto the visible workshop/kiosk areas, and upgraded character drawing details. Godot quest smoke passed again after the visual pass.
- Collision/depth pass: removed large in-world presentation text, added expanded map-edge architecture, foreground depth masks, camera bounds, invisible collision walls for rooftops/buildings/map edges, left the workshop/kiosk approaches reachable, shortened NPC labels, and applied a system-font sci-fi label style. Godot quest smoke passed again after these movement and scene-readability changes.

Warnings and limitations:

- Installed `pytest` into `backend/.venv` because no available Python environment had pytest.
- Full backend tests emit existing deprecation warnings from FastAPI/Starlette and `datetime.utcnow`.
- Godot headless runs on this machine emit local environment warnings about log-file/editor-settings writes and macOS CA certificate lookup; these did not block validation.
- The disposable smoke backend used `DATABASE_URL=sqlite:////private/tmp/cyberpunk-smoke.db`.
- During smoke tests, Ollama embeddings were unavailable, so memory saved without semantic vectors and logged `run memory.reindex when Ollama is available`; the quest and persistence smoke tests still passed.
- The public quest route and response key remain `/quests/bow` and `bow_quest` for API compatibility, while all judge-facing title/objective/dialogue content now reads as `Assemble Pulse Blaster`.

Demo instructions:

1. Start the backend:

   ```bash
   cd /Users/rithvik/Desktop/majorprojectimplementation/backend
   ./.venv/bin/uvicorn app.main:app --reload
   ```

2. Start the game:

   ```bash
   cd /Users/rithvik/Desktop/majorprojectimplementation/frontend/godot
   godot --path .
   ```

3. Present the flow:
   - Open Missions and begin `Assemble Pulse Blaster`.
   - Talk to `Neon Techsmith`.
   - Request `circuit board` from `Data Broker`; explain the purpose when asked.
   - Pick up `fiber cable` at the power junction.
   - Give both components to `Neon Techsmith`.
   - Show timed assembly, one `pulse_blaster` reward, memory/context continuity, and restart behavior.

## Native 3D District Conversion (October 6)

### Pause Menu and Shop Patrol Follow-up

### Shop Roof Visibility Follow-up

Plan: add full shop roofs with independent materials; smoothly fade only the occupied shop's roof and upper entrance beam, restoring opacity on exit. Preserve physical walls, patrols, and quest behavior.
Files: `frontend/godot/scripts/district_3d.gd`, `frontend/godot/tests/district_3d_smoke.gd`, and this log.
Commands:
```sh
rg -n 'func shop|func _process|func _physics_process|shop_for|patrols|func box' frontend/godot/scripts/district_3d.gd
cat frontend/godot/tests/district_3d_smoke.gd
sed -n '145,184p' frontend/godot/scripts/district_3d.gd
godot --headless --path frontend/godot -s res://tests/district_3d_smoke.gd
godot --path frontend/godot -s res://tests/district_3d_smoke.gd
git diff --check
godot --path frontend/godot -s res://tests/district_3d_smoke.gd
```

Result: Both shops now have full roofs. Occupied-shop roof, entrance beam, neon trim and sign fade smoothly to 4% opacity in about 0.4 seconds, then restore on exit. Roof shadows are disabled while transparent so NPCs remain visible; the other shop stays opaque. Independent materials prevent changing other architecture. Graphical Godot smoke passed, including gradual fade, full fade, neighboring roof isolation and restoration plus existing collision/patrol/pause checks. Inspected interior screenshots `/tmp/neon-shop-roof-1.png` and `/tmp/neon-shop-roof-2.png`; final pass also fades obstructing signs. Backend code unchanged; backend suite not rerun. Offline visual harness can show connection/save notices because it deliberately uses an unused port rather than the player's save.

Plan: consolidate actions in a pause overlay; stabilize restart during autosave; remove overlapping bank/bridge surfaces; enlarge both shops; synchronize wandering NPCs with interaction positions and freeze them for the entire store visit.
Files: `scripts/main.gd`, `scripts/pause_menu.gd`, `scripts/district_3d.gd`, `scripts/runner_3d.gd`, `tests/district_3d_smoke.gd` (under `frontend/godot/`), and this log.
Inspection commands:
```sh
cat frontend/godot/scripts/runner_3d.gd frontend/godot/scripts/district_3d.gd
rg -n 'func |restart|quests_button|bag_button|help.text|npc_nodes|position = ' frontend/godot/scripts/main.gd frontend/godot/scripts/chat_window.gd
```

Verification commands for this follow-up (repository root except the backend command):
```sh
godot --headless --path frontend/godot -s res://tests/district_3d_smoke.gd
godot --path frontend/godot -s res://tests/district_3d_smoke.gd
# Working directory: backend/
DATABASE_URL=sqlite:////private/tmp/neon-shop-check.db .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
# Working directory: repository root
godot --headless --path frontend/godot -s res://tests/bow_quest_smoke.gd
godot --headless --path frontend/godot -s res://tests/persistence_smoke.gd
git diff --check
# Stopped disposable backend with Ctrl-C.
```

Completed:
- Pause button/Escape opens a centered modal with Resume, Missions, Inventory, Restart, camera-distance slider, fullscreen toggle and Save and Quit. Missions/inventory resume play and open their respective panels. Existing I shortcut remains.
- Restart no longer flickers disabled during autosave/crafting polls. Confirmed restart waits for in-flight operations to finish before resetting. Reset restores NPC patrol starting positions.
- Corrected north-bank geometry ending at z=12 while the bridge began at z=11. Bank now ends at z=11, removing the overlapping surface at the bridge approach.
- Shops are 50% wider and 60% deeper; wall collisions, signs, props and workbenches expand together. Each NPC follows an interior route and its interaction position follows its visible body.
- Store entry freezes that store's NPC immediately, without requiring a conversation first. Closing chat does not restart it. Leaving the store closes its chat and resumes patrol. Pause also freezes both patrols.
- Regression checks passed: bridge/canal collision and non-overlapping approach, enlarged shop walls/doorways, both NPCs' entry/stay/exit behavior, interaction targeting, paused patrols, stable restart during autosave, and queued restart.
- Existing full quest smoke and persistence/reset smoke passed. No backend code changed in this follow-up; full backend suite was not rerun.
- Actual graphical Godot run passed; pause-menu screenshot at `/tmp/neon-district-pause.png` inspected for layout/overlap. Plaza and bridge screenshots regenerated. `git diff --check` passed.

Notes: pause freezes local player/NPC movement, but the authoritative backend crafting deadline continues in real time. Graphics settings apply to the current session. Prior backend embedding-service warnings remain unrelated to these changes. To try the updates, relaunch `godot --path frontend/godot`, press Pause/Escape, and enter/leave each shop.

Objective: replace the image world with an expanded, physically navigable Godot 3D district, guarded bridges, enterable workshops, and animated human-proportioned characters. Preserve API coordinates through a 40-units-per-meter adapter.

Exact files: `frontend/godot/scripts/main.gd`, `frontend/godot/scripts/district_3d.gd`, `frontend/godot/scripts/runner_3d.gd`, `frontend/godot/scripts/human_3d.gd`, `frontend/godot/project.godot`, `frontend/godot/tests/district_3d_smoke.gd`, and this log. Existing 2D scripts remain available but are no longer rendered.

Commands executed during inspection (repository root unless stated):
```sh
pwd
rg --files -g AGENTS.md -g project.godot -g '*.gd' -g '*.tscn' -g cyberpunk.md
cat frontend/godot/scripts/main.gd
cat frontend/godot/scripts/player.gd frontend/godot/scripts/npc.gd frontend/godot/scenes/Main.tscn frontend/godot/project.godot
tail -100 cyberpunk.md
git status --short
cat frontend/godot/tests/persistence_smoke.gd frontend/godot/tests/bow_quest_smoke.gd
which godot
cat frontend/godot/scripts/quest_panel.gd
```

Implementation checklist:
- [x] Native 3D environment, camera, materials, lighting and expanded streets.
- [x] Animated 3D characters and compatibility adapter for quest coordinates.
- [x] Solid architecture, accessible interiors and guarded canal crossings.
- [x] Collision and quest/persistence checks; rendered visual inspection.
- [x] Record results and limitations.

Execution commands, in order (repeated render checks are intentional):
```sh
godot --headless --path frontend/godot --import
godot --headless --path frontend/godot -s res://tests/district_3d_smoke.gd
godot --path frontend/godot -s res://tests/district_3d_smoke.gd
lsof -nP -iTCP:8000 -iTCP:8001 -sTCP:LISTEN
godot --path frontend/godot -s res://tests/district_3d_smoke.gd
# Next command uses backend/ as its working directory:
DATABASE_URL=sqlite:////private/tmp/neon-3d-check.db .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
# Repository root again:
godot --headless --path frontend/godot -s res://tests/bow_quest_smoke.gd
PYTHONPATH=/Users/rithvik/Desktop/majorprojectimplementation:/Users/rithvik/Desktop/majorprojectimplementation/backend backend/.venv/bin/python -m pytest backend
godot --headless --path frontend/godot -s res://tests/persistence_smoke.gd
godot --path frontend/godot -s res://tests/district_3d_smoke.gd
git diff --check
# Disposable backend stopped with Ctrl-C after verification.
open -a Godot --args --path /Users/rithvik/Desktop/majorprojectimplementation/frontend/godot
```

Results:
- Expanded world to 112 by 99 meters, with two canal banks, three traversable bridges, surrounding streets, towers, service props and parked vehicles.
- Main world now renders native 3D meshes, shaded weathered materials, physical shadows, fog, illuminated signs, and animated articulated characters. No background image is used by the active scene.
- Workshop interiors are accessible through open front entrances. Other towers are solid scenery. All bridge sides, canal banks and district boundaries have continuous solid barriers.
- Existing 2D player/NPC nodes are hidden compatibility adapters, not the rendered world or movement physics. Backend x/y maps to 3D x/z at 40 units per meter. Existing quest API and save structure are unchanged.
- Full backend suite: 207 passed, 184 existing deprecation warnings.
- Quest smoke: passed, including pickup, transfers, timed crafting and one reward.
- Persistence smoke: passed for saved position, inventory, quest, chat history and reset.
- 3D collision smoke: passed. Verified canal gap has no floor, bridge has a floor, bridge sides and bank edges block movement, workshop door is open and walls are solid.
- Ran actual graphical Godot on Apple M5/OpenGL, captured and inspected `/tmp/neon-district-3d.png` and `/tmp/neon-district-bridges.png`; screenshot color check passed. Final rendered collision check passed after material and vehicle edits.
- `git diff --check` passed.

Warnings/fixes: Initial sandboxed Godot import could not write user settings/logs; graphical verification ran with permission. An initial smoke-test type-inference parse error was fixed before the passing runs. Ollama embeddings remain unavailable in the disposable backend; memory storage and quest tests still pass without vectors.

Limits: This is a native 3D, stylized procedural district, not photorealistic scanned scenery or motion-captured characters. Upper tower floors are scenery; only the two quest workshops have accessible interiors. The camera follows at a fixed angle with mouse-wheel zoom. Visual review covered the plaza and canal at 1280x720 on this machine, not every camera position or GPU.

Demo: launch the existing backend on port 8000, then `godot --path frontend/godot` from the repository root. Use WASD, E to talk, F to collect, I for inventory; scroll to zoom. Enter the Techsmith and Data Exchange workshops, demonstrate the existing quest, then walk south across the guarded bridge to the expanded second bank. No paid assets or additional asset downloads are required.
