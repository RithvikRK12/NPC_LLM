from __future__ import annotations

from app.models.npc import NPC
from app.services.validation.models import LLMResponse, StateUpdate
from app.utils.math_utils import clamp


ROLE_CONSTRAINTS = {
    "craftsman": {"max_aggression": 0.20, "forbidden_actions": {"attack", "declare_war"}},
    "gatherer": {"max_aggression": 0.10, "forbidden_actions": {"attack", "declare_war"}},
}


class RoleConditioningService:
    def apply(self, npc: NPC, output: LLMResponse) -> LLMResponse:
        constraints = ROLE_CONSTRAINTS.get(npc.role, {"max_aggression": 1.0, "forbidden_actions": set()})
        sanitized_action = output.action if output.action not in constraints["forbidden_actions"] else "speak"
        aggression_delta = min(output.state_update.aggression, constraints["max_aggression"])
        state_update = StateUpdate(
            trust=clamp(output.state_update.trust),
            fear=clamp(output.state_update.fear),
            aggression=clamp(aggression_delta),
            curiosity=clamp(output.state_update.curiosity),
        )
        return output.model_copy(update={"action": sanitized_action, "state_update": state_update})