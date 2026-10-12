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

        if output.intent == 'confirm_transfer' and output.action == 'ask_question':
            npc.pending_item = output.item
        elif output.intent in {'cancel_transfer', 'unavailable_item'} or output.action in {'give_item', 'receive_item'}:
            npc.pending_item = None
        npc_inventory = list(npc.inventory or [])
        if output.action in {"give_item", "receive_item"}:
            source, destination = (npc_inventory, inventory) if output.action == "give_item" else (inventory, npc_inventory)
            if not output.item or output.item not in source:
                raise ValueError("The requested item is no longer available")
            source.remove(output.item)
            destination.append(output.item)
            if output.action == "give_item" and output.item == "wood" and quest_status != "completed":
                quest_status = "active"
                quest_progress = max(quest_progress, 50)
        npc.inventory = npc_inventory


        player.inventory = inventory

        if quest is not None:
            quest.status = quest_status
            quest.progress = quest_progress

        self._db.add(npc)
        self._db.add(player)
        if quest is not None:
            self._db.add(quest)
        self._db.flush()
        self._db.refresh(npc)
        self._db.refresh(player)
        if quest is not None:
            self._db.refresh(quest)

        return WorldStateSnapshot(inventory=inventory, quest_status=quest_status, quest_progress=quest_progress)