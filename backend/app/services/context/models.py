from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ConversationContext:
    player_input: str
    npc_state: dict[str, Any]
    memories: list[dict[str, Any]] = field(default_factory=list)
    quest: dict[str, Any] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    location: str = ""
    time: str = ""
    npc_name: str = ""
    npc_role: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "player_input": self.player_input,
            "npc_state": self.npc_state,
            "memories": self.memories,
            "quest": self.quest,
            "inventory": self.inventory,
            "location": self.location,
            "time": self.time,
            "npc_name": self.npc_name,
            "npc_role": self.npc_role,
        }