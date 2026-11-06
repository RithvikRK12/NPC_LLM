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
    claim_text: str | None = None
    retracts_claim: str | None = None

    @property
    def important(self):
        return self.importance >= MIN_IMPORTANCE

    def payload(self):
        from app.memory.reconcile import EpistemicStatus, EvidenceAuthority
        verified = self.category in {'quest_progress', 'quest_completion', 'item_transfer', 'item_request'}
        status = EpistemicStatus.RETRACTION if self.retracts_claim else (EpistemicStatus.FACT if verified else EpistemicStatus.CLAIM)
        authority = EvidenceAuthority.AUTHORITATIVE if verified else EvidenceAuthority.REPORTED
        if not self.important:
            status, authority = EpistemicStatus.INTERPRETATION, EvidenceAuthority.INFERRED
        return {**asdict(self), 'important': self.important, 'version': 2,
                'epistemic_status': status.value,
                'authority': authority.value}


def classify(player_input, output, *, grounded=False, quest_before=None, quest_after=None,
             pending_before=None, pending_after=None, rejected=False):
    if rejected or outside_world(player_input) or outside_world(output.dialogue):
        return MemoryDecision(0, 'excluded', 'Rejected, unavailable-model or outside-world exchange.')
    if quest_before != quest_after:
        return MemoryDecision(.95, 'quest_progress', 'The authoritative quest phase changed.',
                              f'Bow quest changed from {quest_before} to {quest_after}.')
    if grounded and output.action in {'give_item', 'receive_item'}:
        direction = 'NPC gave player' if output.action == 'give_item' else 'Player gave NPC'
        return MemoryDecision(.9, 'item_transfer', 'An ownership-checked transfer succeeded.',
                              f'{direction} one {output.item}.')
    if pending_before != pending_after:
        return MemoryDecision(.7, 'item_request', 'The pending request changed.',
                              f'Pending item request changed from {pending_before or "none"} to {pending_after or "none"}.')
    retraction = re.fullmatch(r"I no longer (prefer|like|love) (.+?)[.!]?", player_input.strip(), re.I)
    if retraction:
        target = f'I {retraction[1].lower()} {retraction[2]}'
        return MemoryDecision(.75, 'preference', 'Explicit retraction of an exact earlier preference.',
                              f'Player retracted (unverified preference): {target}',
                              claim_text=player_input[:500], retracts_claim=target)
    if '?' not in player_input and re.match(r"(?i)^\s*i (?:already )?(?:gave|delivered) you\b", player_input):
        return MemoryDecision(.7, 'player_claim', 'Player delivery statement without a verified transfer.',
                              f'Player stated (unverified delivery claim): {player_input[:430]}', claim_text=player_input[:500])
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
                                      f'Player stated (unverified {category}): {text[:430]}', claim_text=text[:500])
    return MemoryDecision(.1, 'routine', 'No durable player statement or authoritative event; kept in chat history only.')
