"""Ground common quest questions in authoritative inventory, not generated memory."""
import re

from app.services.validation.models import LLMResponse, StateUpdate


def quest_answer(role: str, question: str, inventory: list[str], npc_inventory: list[str] | None = None) -> LLMResponse | None:
    text = ' '.join(re.findall(r"[a-z]+", question.lower()))
    needs = text in {
        'what do you want', 'what do you need', 'what do you want from me',
        'what do you need from me', 'what should i bring', 'what materials do you need',
    }
    component_request = bool(re.fullmatch(r'(?:can|could|will|would) you (?:please )?(?:give|share) (?:me )?(?:a |some )?circuit board(?: please)?', text))
    if not needs and not component_request:
        return None
    if role == 'craftsman':
        if component_request:
            dialogue = "I don't stock spare circuit boards. Ask the Data Broker in Byte Alley, then bring it to my neon bench."
        elif 'circuit_board' in (npc_inventory or []):
            dialogue = "I have the circuit board you brought. I still need fiber cable from the power junction before assembly."
        elif 'circuit_board' in inventory:
            dialogue = "You already have the circuit board I need. Bring it to me after you collect fiber cable."
        elif 'pulse_blaster' in inventory:
            dialogue = "You already have your Pulse Blaster. Keep it synced and stay sharp in the grid."
        else:
            dialogue = "I need a circuit board and fiber cable to assemble the Pulse Blaster. Ask the Data Broker for the board and check the power junction for cable."
    elif role == 'gatherer' and needs:
        dialogue = "I don't need payment. I can share a circuit board for the Techsmith's build; just ask me for it."
    else:
        return None
    return LLMResponse(intent='inform', emotion='calm', dialogue=dialogue, action='speak',
                       reasoning='Quest requirements are grounded in current player inventory and NPC role.',
                       state_update=StateUpdate())
