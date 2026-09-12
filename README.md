# Willowbrook NPC quest demo

A Godot 4 village backed by FastAPI, SQLAlchemy, and a local or compatible LLM. Godot resumes the saved world on launch, including position, inventories, NPC states, chats, memories and quest progress. Use Restart Game to begin a fresh run.

## Run

1. Copy `backend/.env.example` to `backend/.env` if needed. Set `LLM_BASE_URL=http://localhost:11434/v1` and `LLM_MODEL=llama3:latest` for Ollama.
2. Start Ollama (`open -a Ollama` on macOS). Install the model once with `ollama pull llama3`.
3. If your `DATABASE_URL` uses PostgreSQL, start Docker Desktop and run `docker compose up -d`. SQLite also works for local use.
4. Install `backend/requirements.txt` in a Python virtual environment.
5. From `backend`, run `../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
6. Open `frontend/godot/project.godot` in Godot 4 and press F5, or run the Godot executable with `--path frontend/godot` from the project root.

The backend loads `backend/.env` regardless of working directory. Relative SQLite paths are still relative to the working directory. An empty LLM base URL selects the mock provider. Generation and validation failures are logged in the backend terminal.

## Get a bow

1. Click **Quests → Begin • Get a bow**.
2. Approach the Craftsman, press **E**, and ask for a bow. He needs **wood and string**.
3. Request wood from the Gatherer. He asks why; answer with a purpose such as “I need wood to make a bow.”
4. Find the fallen string near the well. Walk close and press **F** to pick it up.
5. Return to the Craftsman. Open your satchel with **I** or its button, select each material, and click **Give [item] to Craftsman**.
6. He consumes one wood and one string and crafts for **five seconds**, with a progress bar. A bow is added to your satchel, completing the quest.

Use WASD to walk and Escape to close panels. Each NPC has a separate chat and supplies panel. Item cards show names, icons and stack counts. Click an NPC item and Request to begin its purpose-confirmation conversation. Say “cancel” to cancel. Player gifts transfer immediately and receive a thank-you.

Clear chat removes that NPC's transcript, dialogue memories and pending request. It does not reset inventory or quest progress.

## New runs and validation

Each run starts with Craftsman: saw, hammer, rope; Gatherer: axe, wood, fruits; Player: water, food. Existing worlds receive the inventory upgrade once, without resetting existing items. The bow quest is stored separately from legacy axe progress. Starting it repeatedly never resets it or replenishes materials.

Transfers check current ownership and save both inventories with the conversation. PostgreSQL requests lock the player row to serialize world mutations. String is a single-use pickup, available only at the gather step; its endpoint validates the game-reported position against a 64-unit pickup radius. This is a local demo, not a server-simulated multiplayer movement system.

The backend controls quest steps, crafting deadlines, material consumption, and the one-time bow reward. Deadlines survive backend and game restarts; elapsed crafting completes when the game resumes. The model cannot trigger crafting or grant rewards. Known inventory and quest questions use authoritative replies; generated small talk is checked for unsupported actions, inventory/quest claims, and a curated set of outside-world technology topics. This reduces hallucinations but does not guarantee every unrestricted natural-language sentence is factual.

## Tests

From `backend`:

```bash
../.venv/bin/python -m unittest discover -s tests -v
```

For the full Godot quest check, start a **fresh disposable SQLite backend on port 8001**, then run Godot from the project root with:

```bash
Godot --path frontend/godot --script res://tests/bow_quest_smoke.gd
```

This uses game HTTP handlers, tests the pickup and real crafting delay, and saves preview images under `/tmp`. Do not point the test backend at your saved world.

## API

- `GET /world`, `/health`, `/npc/{id}`, `/memory/{npc_id}`
- `POST /chat`, `DELETE /chat/{npc_id}`
- `POST /inventory/transfer`
- `POST /quests/bow/start`, `/quests/bow/pickup-string`, `/quests/bow/advance`

The game calls `advance` only while crafting. Context, prompts, validation, role conditioning, state updates and memory are organized under `backend/app/services`.

Godot loads `GET /world` before enabling gameplay. Player position autosaves once per second through `PUT /world/player-position` and saves again on normal window close; gameplay transactions save immediately. A forced process termination can lose the most recent unsaved movement. The Restart Game button asks for confirmation and calls `POST /world/new-game`, clearing chats and memories and resetting inventories, position, NPC states, pending requests, pickups and crafting timers without changing NPC IDs. Pending operations finish before restart is allowed. On save failure, normal close keeps the window open to let you retry. This demo still uses one shared save, not separate player profiles; restart affects that shared world.
