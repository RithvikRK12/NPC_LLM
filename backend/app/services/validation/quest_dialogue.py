"""Ground common quest questions in authoritative inventory, not generated memory."""
import re

from app.services.validation.models import LLMResponse, StateUpdate


def quest_answer(role: str, question: str, inventory: list[str], npc_inventory: list[str] | None = None) -> LLMResponse | None:
    text = ' '.join(re.findall(r"[a-z]+", question.lower()))
    needs = text in {
        'what do you want', 'what do you need', 'what do you want from me',
        'what do you need from me', 'what should i bring', 'what materials do you need',
    }
    wood_request = bool(re.fullmatch(r'(?:can|could|will|would) you (?:please )?(?:give|share) (?:me )?(?:some )?wood(?: please)?', text))
    if not needs and not wood_request:
        return None
    if role == 'craftsman':
        if wood_request:
            dialogue = "I don't supply wood. Ask the Gatherer by the forest, then bring the wood to me and I can craft an axe."
        elif 'wood' in (npc_inventory or []):
            dialogue = "I have the wood you brought. Ask me to craft an axe when you're ready."
        elif 'wood' in inventory:
            dialogue = "You already have the wood I need. Ask me to craft an axe when you're ready."
        elif 'axe' in inventory:
            dialogue = "You already have your axe. I don't need anything else for it, but I can help with tool repairs."
        else:
            dialogue = "I need wood to craft an axe. Ask the Gatherer by the forest for some, then bring it to my workshop."
    elif role == 'gatherer' and needs:
        dialogue = "I don't need anything in return. I can share wood for the Craftsman's axe; just ask me for some."
    else:
        return None
    return LLMResponse(intent='inform', emotion='calm', dialogue=dialogue, action='speak',
                       reasoning='Quest requirements are grounded in current player inventory and NPC role.',
                       state_update=StateUpdate())
