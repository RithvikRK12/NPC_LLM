from pydantic import BaseModel, Field

from app.schemas.memory import MemoryRead
from app.schemas.npc import NPCRead


class ChatRequest(BaseModel):
    game_scope: str | None = None
    npc_id: int = Field(ge=1)
    player_message: str = Field(min_length=1, max_length=500)


class StateUpdatePayload(BaseModel):
    trust: float = 0.0
    fear: float = 0.0
    aggression: float = 0.0
    curiosity: float = 0.0


class StructuredNPCOutput(BaseModel):
    answer_kind: str = "chat"
    fact_ids: list[str] = Field(default_factory=list)
    intent: str
    emotion: str
    dialogue: str
    action: str
    item: str | None = None
    reasoning: str
    state_update: StateUpdatePayload


class ChatResponse(BaseModel):
    game_scope: str = ""
    craftsman_encounter: dict = Field(default_factory=dict)
    ship_repair: dict = Field(default_factory=dict)
    decision_trace: dict = Field(default_factory=dict)
    behavior_trace: dict = Field(default_factory=dict)
    grounding_trace: dict = Field(default_factory=dict)
    memory_classification: dict = Field(default_factory=dict)
    bow_quest: dict = Field(default_factory=dict)
    npc: NPCRead
    validated_output: StructuredNPCOutput
    final_dialogue: str
    player_inventory: list[str]
    quest_status: str
    quest_progress: int
    memories: list[MemoryRead]