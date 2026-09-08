# Modular Closed-Loop Control Architecture MVP

This project demonstrates a closed-loop NPC control architecture inspired by the paper "Modular Closed-Loop Control Architecture for LLM-Driven NPC Behavior".

The backend is the primary system. Godot is only a thin visualization layer that forwards player interaction to FastAPI.

## What is included

- Two NPCs: Craftsman and Gatherer
- FastAPI backend with SQLAlchemy models and modular services
- Context builder, prompt builder, LLM abstraction, validation, rule engine, role conditioning, state updates, and memory storage
- PostgreSQL + pgvector ready database layer
- Godot 4 top-down frontend with placeholder visuals

## Run backend

1. Copy `.env.example` to `.env` and update values if needed.
2. Start PostgreSQL with `docker compose up -d`.
3. Install Python dependencies from `backend/requirements.txt`.
4. Run the app with `uvicorn app.main:app --reload` from the `backend` folder.

## Run frontend

Open `frontend/godot` in Godot 4 and run the `Main` scene.

## API

- `POST /chat`
- `GET /npc/{id}`
- `GET /memory/{npc}`
- `GET /health`

## Architecture notes

The interaction pipeline is:

Player -> Context Builder -> LLM -> Structured JSON -> Validation -> Rule Engine -> Role Conditioning -> State Update -> Memory Storage -> Response -> Game Engine -> Memory Feedback