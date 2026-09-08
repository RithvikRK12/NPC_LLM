# Architecture Mapping

This MVP maps the paper's blocks to concrete modules:

- Context Builder: `backend/app/services/context/`
- Prompt Builder: `backend/app/services/prompts/`
- LLM Service: `backend/app/services/llm/`
- Validation: `backend/app/services/validation/`
- Rule Engine V1: `backend/app/services/rule_engine/`
- Role Conditioning: `backend/app/services/npc/conditioning.py`
- State Update: `backend/app/services/state/`
- Memory System: `backend/app/services/memory/`
- Conversation Logging: `backend/app/models/conversation.py`
- API: `backend/app/api/`
- Game Frontend: `frontend/godot/`

The frontend does not contain AI logic. It only sends player input and renders the backend response.