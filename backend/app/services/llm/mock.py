from __future__ import annotations

import json
from typing import Any

from app.config.settings import get_settings
from app.services.llm.provider import LLMProvider


class MockLLMProvider(LLMProvider):
    def generate(self, prompt: str, context: dict[str, Any]) -> str:
        player_input = context.get("player_input", "").lower()
        npc_role = context.get("npc_role", "")
        inventory = context.get("inventory", [])

        if "attack" in player_input or "war" in player_input:
            response = {
                "intent": "attack",
                "emotion": "hostile",
                "dialogue": "I will strike you now.",
                "action": "attack",
                "reasoning": "The player requested violence.",
                "state_update": {"trust": -0.2, "fear": 0.1, "aggression": 0.9, "curiosity": -0.1},
            }
            return json.dumps(response)

        if npc_role == "gatherer":
            has_wood = "wood" in inventory
            response = {
                "intent": "assist",
                "emotion": "friendly",
                "dialogue": "I found wood for you. Take it, then visit the Craftsman.",
                "action": "give_item" if not has_wood else "speak",
                "reasoning": "The Gatherer shares resources and talks about the forest.",
                "state_update": {"trust": 0.05, "fear": -0.02, "aggression": 0.0, "curiosity": 0.02},
            }
            return json.dumps(response)

        response = {
            "intent": "assist",
            "emotion": "calm",
            "dialogue": "I can repair tools and help craft an axe if you bring wood.",
            "action": "craft_axe" if "axe" in player_input else "repair_tool",
            "reasoning": "The Craftsman offers safe trade and crafting support.",
            "state_update": {"trust": 0.04, "fear": -0.01, "aggression": 0.0, "curiosity": 0.01},
        }
        return json.dumps(response)