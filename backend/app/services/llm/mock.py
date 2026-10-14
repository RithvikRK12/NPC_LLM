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
            encounter = context.get('encounter', {})
            relationship = context.get('npc_state', {})
            if encounter.get('status') == 'resolved_declined' and relationship.get('trust', .5) < .3:
                return json.dumps({'intent': 'speak', 'emotion': 'wary', 'action': 'speak',
                    'dialogue': "You left when I needed help. I haven't forgotten. What do you want?",
                    'reasoning': 'The recorded refusal still shapes this relationship.', 'state_update': {}})
            if encounter.get('status') == 'resolved_helped':
                return json.dumps({'intent': 'assist', 'emotion': 'grateful', 'action': 'speak',
                    'dialogue': "I'm glad you stayed to help. How are you doing?",
                    'reasoning': 'The recorded rescue shapes this relationship.', 'state_update': {}})
            has_wood = "wood" in inventory
            response = {
                "intent": "assist",
                "emotion": "friendly",
                "dialogue": "The forest is peaceful today. How are you doing?",
                "action": "speak",
                "reasoning": "The Gatherer shares resources and talks about the forest.",
                "state_update": {"trust": 0.05, "fear": -0.02, "aggression": 0.0, "curiosity": 0.02},
            }
            return json.dumps(response)

        from app.services.context.social import is_social_message
        if is_social_message(player_input):
            from app.services.context.craftsman_profile import character_fallback
            return json.dumps({'answer_kind':'chat','fact_ids':[],'dialogue':character_fallback(player_input)})
        import re
        facts={f['id']:f for f in context.get('facts',[])}
        identity=None
        if 'bow' in player_input and any(w in player_input for w in ('need','material','why')): identity='quest.bow.requirements'
        elif 'bow' in player_input: identity='quest.bow.phase'
        elif 'where' in player_input:
            identity='person.gatherer.location' if 'gatherer' in player_input else 'person.craftsman.location' if 'craftsman' in player_input else None
        if identity in facts:
            return json.dumps({'answer_kind':'answer','fact_ids':[identity],'dialogue':''})
        response = {
            "intent": "assist",
            "emotion": "calm",
            "dialogue": "Welcome to my workshop. It is a fine day in the village.",
            "action": "speak",
            "reasoning": "The Craftsman offers safe trade and crafting support.",
            "state_update": {"trust": 0.04, "fear": -0.01, "aggression": 0.0, "curiosity": 0.01},
        }
        return json.dumps(response)