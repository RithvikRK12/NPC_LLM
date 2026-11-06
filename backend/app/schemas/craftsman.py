from pydantic import BaseModel, Field
class CraftsmanCommand(BaseModel):
    game_scope: str
    npc_id: int = 1
    command: str
    request_id: str = Field(min_length=1,max_length=100)
    expected_revision: int = Field(ge=0)
    payload: dict = Field(default_factory=dict)
class CraftsmanCheckpoint(BaseModel):
    game_scope: str
    expected_revision: int = Field(ge=0)
    checkpoint: dict
