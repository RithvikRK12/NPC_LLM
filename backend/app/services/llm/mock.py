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
            response = {
                "intent": "assist",
                "emotion": "friendly",
                "dialogue": "Byte Alley is humming tonight. What signal are you chasing?",
                "action": "speak",
                "reasoning": "The Data Broker shares street resources and grid rumors.",
                "state_update": {"trust": 0.05, "fear": -0.02, "aggression": 0.0, "curiosity": 0.02},
            }
            return json.dumps(response)

        response = {
            "intent": "assist",
            "emotion": "calm",
            "dialogue": "Welcome to the neon bench. Keep your comms clean and your gear grounded.",
            "action": "speak",
            "reasoning": "The Neon Techsmith offers safe trade and assembly support.",
            "state_update": {"trust": 0.04, "fear": -0.01, "aggression": 0.0, "curiosity": 0.01},
        }
        return json.dumps(response)
