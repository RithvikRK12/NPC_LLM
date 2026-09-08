from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.npc import NPC
from app.models.player import Player
from app.models.quest import Quest
from app.services.validation.models import LLMResponse
from app.utils.math_utils import clamp


@dataclass(slots=True)
class WorldStateSnapshot:
    inventory: list[str]
    quest_status: str
    quest_progress: int


class StateService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def apply(self, npc: NPC, player: Player, quest: Quest | None, output: LLMResponse) -> WorldStateSnapshot:
        npc.trust = clamp(npc.trust + output.state_update.trust)
        npc.fear = clamp(npc.fear + output.state_update.fear)
        npc.aggression = clamp(npc.aggression + output.state_update.aggression)
        npc.curiosity = clamp(npc.curiosity + output.state_update.curiosity)
        npc.current_state = output.action

        inventory = list(player.inventory or [])
        quest_status = quest.status if quest else "unknown"
        quest_progress = quest.progress if quest else 0

        if npc.role == "gatherer" and output.action in {"give_item", "help_player"} and "wood" not in inventory:
            inventory.append("wood")
            quest_status = "active"
            quest_progress = max(quest_progress, 50)

        if npc.role == "craftsman" and output.action == "craft_axe" and "wood" in inventory:
            inventory.remove("wood")
            if "axe" not in inventory:
                inventory.append("axe")
            quest_status = "completed"
            quest_progress = 100

        player.inventory = inventory

        if quest is not None:
            quest.status = quest_status
            quest.progress = quest_progress

        self._db.add(npc)
        self._db.add(player)
        if quest is not None:
            self._db.add(quest)
        self._db.commit()
        self._db.refresh(npc)
        self._db.refresh(player)
        if quest is not None:
            self._db.refresh(quest)

        return WorldStateSnapshot(inventory=inventory, quest_status=quest_status, quest_progress=quest_progress)