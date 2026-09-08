from __future__ import annotations

from dataclasses import dataclass

from app.models.npc import NPC


def bucket(value: float) -> str:
    if value < 0.3:
        return "LOW"
    if value < 0.7:
        return "MEDIUM"
    return "HIGH"


@dataclass(slots=True)
class RuleEvaluation:
    trust_label: str
    fear_label: str
    aggression_label: str
    curiosity_label: str
    relationship_mode: str


class RuleEngine:
    def evaluate(self, npc: NPC) -> RuleEvaluation:
        trust_label = bucket(npc.trust)
        fear_label = bucket(npc.fear)
        aggression_label = bucket(npc.aggression)
        curiosity_label = bucket(npc.curiosity)

        if trust_label == "HIGH" and fear_label == "LOW":
            relationship_mode = "friendly"
        elif aggression_label == "HIGH" and trust_label == "LOW":
            relationship_mode = "hostile"
        else:
            relationship_mode = "neutral"

        return RuleEvaluation(
            trust_label=trust_label,
            fear_label=fear_label,
            aggression_label=aggression_label,
            curiosity_label=curiosity_label,
            relationship_mode=relationship_mode,
        )