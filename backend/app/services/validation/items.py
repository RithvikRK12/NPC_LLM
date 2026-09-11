"""Resolve explicit item requests and validate ownership before any transfer."""
import re
from app.services.validation.models import LLMResponse, StateUpdate

ITEMS = {'saw', 'hammer', 'rope', 'axe', 'wood', 'fruits', 'water', 'food', 'string', 'bow'}


def requested_transfer(question: str) -> tuple[str, str] | None:
    text = question.lower().strip().rstrip('.!?')
    if re.search(r"\b(?:don't|do not|never|not|if)\b", text):
        return None
    # Requests transfer exactly one named item. Ambiguous/multiple-item requests need clarification.
    words = set(re.findall(r'\b[a-z]+\b', text))
    items = words & ITEMS
    if len(items) != 1:
        return None
    item = items.pop()
    if re.search(r"\b(?:i give you|i offer you|take my|here is|here's|give you)\b", text):
        return 'receive_item', item
    if re.search(r"\b(?:give me|give us|share|can i have|could i have|may i have|i need|i want|please give|give some|give wood|give fruits)\b", text):
        return 'give_item', item
    return None


def transfer_answer(question: str, npc_inventory: list[str], player_inventory: list[str], pending_item: str | None = None) -> LLMResponse | None:
    transfer = requested_transfer(question)
    text = question.lower().strip().rstrip('.!?')
    has_purpose = bool(re.search(r"\b(?:for|to|because|so)\b", text)) and len(text.split()) >= 3 and '?' not in question
    explaining_same_item = pending_item and transfer == ('give_item', pending_item) and has_purpose
    if pending_item and (transfer is None or explaining_same_item):
        text = question.lower().strip().rstrip('.!?')
        if text in {'cancel', 'never mind', 'nevermind', 'no thanks', 'forget it'}:
            return LLMResponse(intent='cancel_transfer', emotion='calm', dialogue="All right, I'll keep it for now.",
                               action='speak', reasoning='Player cancelled the item request.', state_update=StateUpdate())
        # Require a purpose, not a repeated request, greeting, bare yes, or another question.
        purpose = bool(re.search(r"\b(?:for|to|because|so|need it|need them)\b", text))
        if not purpose or len(text.split()) < 3 or '?' in question:
            return LLMResponse(intent='confirm_transfer', emotion='calm',
                               dialogue=f"What will you use the {pending_item} for? Tell me why you need it, or say cancel.",
                               action='ask_question', item=pending_item, reasoning='Waiting for a purpose before giving the item.', state_update=StateUpdate())
        transfer = ('give_item', pending_item)
        confirmed = True
    else:
        confirmed = False
    if transfer is None:
        return None
    action, item = transfer
    source = npc_inventory if action == 'give_item' else player_inventory
    if item not in source:
        dialogue = f"I don't have any {item} left to give you." if action == 'give_item' else f"You don't have {item} to give me."
        action = 'speak'
    elif action == 'give_item' and not confirmed:
        return LLMResponse(intent='confirm_transfer', emotion='calm',
                           dialogue=f"Before I give you the {item}, why do you need it?",
                           action='ask_question', item=item, reasoning='Ask the player for a purpose before transferring stock.', state_update=StateUpdate())
    else:
        dialogue = f"Thanks for explaining. Here, take my {item}. It's yours now." if action == 'give_item' else f"Thank you for the {item}. I'll keep it with my supplies."
    return LLMResponse(intent='transfer' if action != 'speak' else 'unavailable_item', emotion='calm',
                       dialogue=dialogue, action=action, item=item if action != 'speak' else None,
                       reasoning='Item ownership checked against current inventories.', state_update=StateUpdate())
