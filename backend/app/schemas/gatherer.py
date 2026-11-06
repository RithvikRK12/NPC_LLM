from typing import Literal
from pydantic import BaseModel, Field


class GathererCommand(BaseModel):
    game_scope: str
    command: Literal['begin_intro', 'accept', 'restart_attempt', 'victory', 'decline',
                     'complete_retreat', 'begin_confrontation', 'finish_presentation']
    request_id: str = Field(min_length=1, max_length=100)
    expected_revision: int = Field(ge=0)
    payload: dict = Field(default_factory=dict)
