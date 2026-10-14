# Willowbrook NPC quest demo

A Godot 4 village backed by FastAPI, SQLAlchemy, and a local or compatible LLM. Godot resumes the saved world on launch, including position, inventories, NPC states, chats, memories and quest progress. Use Restart Game to begin a fresh run.

## Run

1. Copy `backend/.env.example` to `backend/.env` if needed. Set `LLM_BASE_URL=http://localhost:11434/v1` and `LLM_MODEL=llama3:latest` for Ollama.
2. Start Ollama (`open -a Ollama` on macOS). Install the model once with `ollama pull llama3`.
3. If your `DATABASE_URL` uses PostgreSQL, start Docker Desktop and run `docker compose up -d`. SQLite also works for local use.
4. Install `backend/requirements.txt` in a Python virtual environment.
5. From `backend`, run `../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`. Automatic reload keeps encounter APIs in sync while developing.
6. Open `frontend/godot/project.godot` in Godot 4 and press F5, or run the Godot executable with `--path frontend/godot` from the project root.

Before launching directly from the command line on a fresh checkout, import the
assets once from the project root:

```sh
/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot \
  --headless --path frontend/godot --editor --import
```

Wait for import to finish, then launch normally. This builds the local `.godot`
texture cache required by SVG preloads. Opening the project in the editor also
imports assets; direct game launch alone can fail with a missing `.ctex` error.

The backend loads `backend/.env` regardless of working directory. Relative SQLite paths are still relative to the working directory. An empty LLM base URL selects the mock provider. Generation and validation failures are logged in the backend terminal.

## Get a bow

1. Click **Quests → Begin • Get a bow**.
2. Walk into the workshop doorway (or press **E** at the door), approach the Craftsman inside, and press **E** to ask for a bow. He needs **wood and string**.
3. Follow the path west into the forest to find the Gatherer in a clearing. Request wood from him. He asks why; answer with a purpose such as “I need wood to make a bow.”
4. Find the fallen string near the well. Walk close and press **F** to pick it up.
5. Return to the Craftsman. Open your satchel with **I** or its button, select each material, and click **Give [item] to Craftsman**.
6. He consumes one wood and one string and crafts for **five seconds**, with a progress bar. A bow is added to your satchel, completing the quest.

Use WASD to walk and Escape to close panels. Each NPC has a separate chat and supplies panel. Item cards show names, icons and stack counts. Click an NPC item and Request to begin its purpose-confirmation conversation. Say “cancel” to cancel. Player gifts transfer immediately and receive a thank-you.

The workshop and both cottages have furnished interiors. Walk up into a front door
to enter, then walk down through the marked exit to return outside. You can also
press **E** at an exterior doorway. Saved games resume inside the room you left.

UI text, buttons and item slots are enlarged for readability; the menu's
**Larger text** option increases text further. NPC location answers give brief
approximations such as “I think the Craftsman is in the workshop.”

Clear chat removes that NPC's transcript, dialogue memories and pending request. It does not reset inventory or quest progress.

## New runs and validation

Each run starts with Craftsman: saw, hammer, rope; Gatherer: axe, wood, fruits; Player: water, food. Existing worlds receive the inventory upgrade once, without resetting existing items. The bow quest is stored separately from legacy axe progress. Starting it repeatedly never resets it or replenishes materials.

Transfers check current ownership and save both inventories with the conversation. PostgreSQL requests lock the player row to serialize world mutations. String is a single-use pickup, available only at the gather step; its endpoint validates the game-reported position against a 64-unit pickup radius. This is a local demo, not a server-simulated multiplayer movement system.

The backend controls quest steps, crafting deadlines, material consumption, and the one-time bow reward. Deadlines survive backend and game restarts; elapsed crafting completes when the game resumes. The model cannot trigger crafting or grant rewards. Known inventory and quest questions use authoritative replies; generated small talk is checked for unsupported actions, inventory/quest claims, and a curated set of outside-world technology topics. This reduces hallucinations but does not guarantee every unrestricted natural-language sentence is factual.

## Tests

From `backend`:

```bash
PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -v
```

For the full Godot quest check, start a **fresh disposable SQLite backend on port 8001**, then run Godot from the project root with:

```bash
Godot --path frontend/godot --script res://tests/bow_quest_smoke.gd
```

This uses game HTTP handlers, tests the pickup and real crafting delay, and saves preview images under `/tmp`. Do not point the test backend at your saved world.

With the same disposable backend, run `res://tests/building_interiors_smoke.gd`
to check all three doorways, walls, furniture, interior saves and workshop
interaction. A rendered run also saves previews under `/tmp/willowbrook-interiors`.

## API

- `GET /world`, `/health`, `/npc/{id}`, `/memory/{npc_id}`
- `POST /chat`, `DELETE /chat/{npc_id}`
- `POST /inventory/transfer`
- `POST /quests/bow/start`, `/quests/bow/pickup-string`, `/quests/bow/advance`

The game calls `advance` only while crafting. Context, prompts, validation, role conditioning, state updates and memory are organized under `backend/app/services`.

Godot loads `GET /world` before enabling gameplay. Player position autosaves once per second through `PUT /world/player-position` and saves again on normal window close; gameplay transactions save immediately. A forced process termination can lose the most recent unsaved movement. The Restart Game button asks for confirmation and calls `POST /world/new-game`, clearing chats and memories and resetting inventories, position, NPC states, pending requests, pickups and crafting timers without changing NPC IDs. Pending operations finish before restart is allowed. On save failure, normal close keeps the window open to let you retry. This demo still uses one shared save, not separate player profiles; restart affects that shared world.

## Shipwreck opening and island

Fresh games begin with a 60-second opening on the island's southern coast. Hold
**Space** for 2× playback and release for normal speed; press **L** to skip
straight to the beach, or **Esc** for pause/settings.
Older saves resume without replaying it. Offshore legacy positions recover to
reachable land while preserving progress. After arrival, inspect the hull with
**E**, collect the nearby rope with **F**, and follow the path north.

Preview any shot/effect without a backend or real save:

```sh
/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot \
  --path frontend/godot res://scenes/cutscenes/opening/OpeningPreview.tscn
```

Import assets first as described above. The preview supports shot/effect selection,
seek, restart, pause, 2×, reduced motion/flashes, captions and markers.
[Implementation, launch/test instructions and recorded evidence](docs/evidence/starting-cutscene/walkthrough.md)
include the island capacity review, save migration and remaining review items.

## Old fisherman

Rowan sits on the fallen log east of the southern approach path. Within 10 meters,
the player automatically walks to the front of the log, then a one-time look-up
introduction opens his fixed dialogue. On later visits,
approach and press **E**. Each branch has three selections, then a final response;
**Continue** closes the dialogue. Press **E** again to hear the opening. **Close / Back** or **Esc** releases movement.
HUD, dialogue and menu controls scale up automatically on larger fullscreen
displays. [Implementation and verification](docs/evidence/old-fisherman/walkthrough.md).

At the first gameplay handoff, a large controls card pauses movement until you
select **Let's go** (or press **Esc**). “Find someone to get help.” then appears
near the center before shrinking into the upper-left HUD. The card is shown once
per saved run; later launches resume with the objective already docked.
[Onboarding behavior and verification](docs/evidence/onboarding/walkthrough.md).

The help objective displays a check mark and fades away when Rowan's introduction
starts. Press **E** near the broken hull or the north-pointing wooden sign to
open an inspection text panel; the sign reads **Willowbrook**. Use **Close** or
**Esc** to return to play.

## Craftsman and A Way Home

Enter the workshop for a one-time introduction: the player walks toward the
Craftsman, then **Continue** opens normal conversation. **Skip** finishes the
introduction; **Esc** interrupts it without marking it complete. He otherwise
walks between his benches, shelf and timber, pausing to work. Talking pauses his
routine or travel.

Tell him “The storm broke my ship,” then “Could you help me fix it?” (or ask for
wreck help in one message). He responds sympathetically and follows after you
close chat. A report alone waits for agreement. Use “wait here,” “let's go,”
“not now,” or “go back to your workshop” to manage the outing. He walks to the
workshop exit before your shared fade, waits outside unrelated cottages, and
follows the southern path around obstacles. If blocked, return to him and ask
him to resume; he does not teleport to catch up.

Lead him to the southern wreck. Both actors must arrive before the inspection
starts. Continue through recognition, a closer physical approach, damage,
hope, requirements and farewell. After staging, **Skip** saves the same outcome.
The confirmed inspection starts **A Way Home**: 12 sound timber planks, 3 coils
of rope, 2 bundles of sailcloth and 2 pots of pitch. The quest panel shows it
alongside the independently playable bow quest. The Craftsman walks back to the
workshop without the player and resumes his routine.

The quest currently stops at material gathering: acquisition of the new
materials, deliveries, actual repair, sailing and the ending remain future
work. Conversation cannot contribute materials or complete either quest.
Encounter flags, physical checkpoints, waiting/return modes and inspection
beats survive reload; Retry is available if an outcome cannot be confirmed.
Restart Game resets this story with the existing world reset.

[Verification, limitations and captured gameplay](docs/evidence/craftsman/walkthrough.md).
