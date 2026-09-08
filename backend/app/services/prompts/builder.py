from __future__ import annotations

from app.services.context.models import ConversationContext


class PromptBuilder:
    def build(self, context: ConversationContext) -> str:
        return (
            "You are the dialog brain for a modular closed-loop NPC controller. "
            "Return ONLY strict JSON. No markdown. No code fences. No commentary.\n\n"
            "Schema:\n"
            "{\n"
            '  "intent": "",\n'
            '  "emotion": "",\n'
            '  "dialogue": "",\n'
            '  "action": "",\n'
            '  "reasoning": "",\n'
            '  "state_update": {"trust": 0, "fear": 0, "aggression": 0, "curiosity": 0}\n'
            "}\n\n"
            "Rules:\n"
            "- Output JSON only.\n"
            "- Do not include unsupported actions.\n"
            "- Keep dialogue under 240 characters.\n"
            "- Stay consistent with the NPC role, memories, quest, and inventory.\n"
            "- Never attack when role constraints forbid it.\n\n"
            f"Context: {context.as_dict()}"
        )