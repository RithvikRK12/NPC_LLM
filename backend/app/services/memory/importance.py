"""Explainable memory selection. Player claims are remembered as claims, not world facts."""
from dataclasses import asdict, dataclass
import re

from app.services.validation.knowledge import outside_world

MIN_IMPORTANCE = 0.65


@dataclass(frozen=True)
class MemoryDecision:
    importance: float
    category: str
    reason: str
    event: str = ''

    @property
    def important(self):
        return self.importance >= MIN_IMPORTANCE

    def payload(self):
        return {**asdict(self), 'important': self.important, 'version': 1}


def classify(player_input, output, *, grounded=False, quest_before=None, quest_after=None,
             pending_before=None, pending_after=None, rejected=False):
    if quest_before != quest_after:
        return MemoryDecision(.95, 'quest_progress', 'The authoritative quest phase changed.',
                              f'Bow quest changed from {quest_before} to {quest_after}.')
    if grounded and output.action in {'give_item', 'receive_item'}:
        direction = 'NPC gave player' if output.action == 'give_item' else 'Player gave NPC'
        return MemoryDecision(.9, 'item_transfer', 'An ownership-checked transfer succeeded.',
                              f'{direction} one {output.item}. Player explanation: {player_input[:300]}')
    if rejected or outside_world(player_input) or outside_world(output.dialogue):
        return MemoryDecision(0, 'excluded', 'Rejected, unavailable-model or outside-world exchange.')
    if pending_before != pending_after:
        return MemoryDecision(.7, 'item_request', 'The pending request changed.',
                              f'Pending item request changed from {pending_before or "none"} to {pending_after or "none"}.')
    # Deliberately inspect player statements, not invented NPC facts or model emotion labels.
    text = player_input.strip()
    if '?' not in text and not re.match(r'(?i)^(what|why|how|when|where|can|could|would|do|is)\b', text):
        for category, pattern in (
            ('commitment', r"\bi (?:promise|will help|will bring|will return|owe you)\b"),
            ('preference', r"\bi (?:prefer|like|love|dislike|hate|am afraid of|don't like|do not like)\b"),
            ('personal_fact', r"\b(?:my name is|i live in|i come from|i work as)\b"),
        ):
            if re.search(pattern, text, re.I):
                return MemoryDecision(.75, category, 'Explicit player statement with potential future relevance.',
                                      f'Player stated (unverified {category}): {text[:430]}')
    return MemoryDecision(.1, 'routine', 'No durable player statement or authoritative event; kept in chat history only.')
