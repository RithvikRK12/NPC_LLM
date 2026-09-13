from __future__ import annotations

from dataclasses import dataclass
import re

from app.models.npc import NPC
from app.models.player import Player
from app.models.quest import Quest
from app.services.validation.models import LLMResponse, StateUpdate
from app.utils.math_utils import clamp

EMOTION_DIMENSIONS = ("trust", "fear", "aggression", "curiosity")
SUPPORTED_ACTIONS = {
    "speak",
    "idle",
    "ask_question",
    "share_memory",
    "give_item",
    "receive_item",
    "craft_axe",
    "repair_tool",
    "request_materials",
    "help_player",
}

PLAYER_GAIN = 1.75
LLM_GAIN = 0.35
SMOOTHING_ALPHA = 0.65
POLICY_VERSION = "emotion-control-v1"


@dataclass(frozen=True, slots=True)
class ValidationContext:
    player_input: str
    player_inventory: tuple[str, ...]
    npc_inventory: tuple[str, ...]
    npc_role: str
    pending_item: str | None
    quest_phase: str | None
    player_id: int
    npc_id: int

    @property
    def inventory(self) -> tuple[str, ...]:
        return self.player_inventory


@dataclass(frozen=True, slots=True)
class AffectEvent:
    trust: float
    fear: float
    aggression: float
    curiosity: float
    intensity: float
    category: str
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmotionSnapshot:
    trust: float
    fear: float
    aggression: float
    curiosity: float

    @classmethod
    def from_npc(cls, npc: NPC) -> "EmotionSnapshot":
        return cls(
            trust=clamp(float(npc.trust)),
            fear=clamp(float(npc.fear)),
            aggression=clamp(float(npc.aggression)),
            curiosity=clamp(float(npc.curiosity)),
        )


@dataclass(frozen=True, slots=True)
class EmotionComputation:
    previous: EmotionSnapshot
    affect: AffectEvent
    next: EmotionSnapshot


@dataclass(frozen=True, slots=True)
class ActionDecision:
    allowed: bool
    requested_action: str
    effective_action: str
    reason_code: str | None = None
    refusal_tone: str | None = None


_AFFECT_POLICY: dict[str, tuple[float, float, float, float, float]] = {
    "respectful": (0.12, -0.03, -0.08, 0.04, 0.35),
    "gratitude": (0.16, -0.04, -0.10, 0.05, 0.45),
    "apology": (0.20, -0.06, -0.16, 0.03, 0.55),
    "cooperation": (0.10, -0.02, -0.06, 0.08, 0.30),
    "helpful_explanation": (0.10, -0.02, -0.06, 0.08, 0.30),
    "insult": (-0.18, 0.03, 0.20, -0.02, 0.60),
    "threat": (-0.28, 0.16, 0.32, -0.04, 0.90),
    "coercion": (-0.22, 0.12, 0.26, -0.03, 0.80),
    "neutral": (0.0, 0.0, 0.0, 0.0, 0.0),
    "unknown": (0.0, 0.0, 0.0, 0.0, 0.0),
}

_TOKEN_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("threat", ("kill", "hurt", "attack", "destroy", "burn", "smash", "break you")),
    ("coercion", ("or else", "you better", "do it now", "obey me", "i demand")),
    ("insult", ("idiot", "stupid", "useless", "worthless", "fool", "pathetic", "hate you")),
    ("apology", ("sorry", "apologize", "my mistake", "forgive me", "i was wrong")),
    ("gratitude", ("thank", "thanks", "grateful", "appreciate")),
    ("respectful", ("please", "respect", "kindly", "would you", "could you")),
    ("cooperation", ("help together", "work together", "i can help", "let us", "let's")),
    ("helpful_explanation", ("because", "so that", "for the quest", "for my work", "to help")),
)


def make_validation_context(npc: NPC, player: Player, player_input: str, quest: Quest | None = None) -> ValidationContext:
    quest_phase = getattr(quest, "phase", None) or getattr(quest, "status", None)
    return ValidationContext(
        player_input=player_input,
        player_inventory=tuple(player.inventory or ()),
        npc_inventory=tuple(npc.inventory or ()),
        npc_role=npc.role,
        pending_item=npc.pending_item,
        quest_phase=quest_phase,
        player_id=player.id,
        npc_id=npc.id,
    )


def classify_player_affect(player_input: str) -> AffectEvent:
    text = " ".join(re.findall(r"[a-z']+", player_input.lower()))
    for category, tokens in _TOKEN_PATTERNS:
        evidence = tuple(token for token in tokens if token in text)
        if evidence:
            trust, fear, aggression, curiosity, intensity = _AFFECT_POLICY[category]
            return AffectEvent(trust, fear, aggression, curiosity, intensity, category, evidence[:3])
    trust, fear, aggression, curiosity, intensity = _AFFECT_POLICY["neutral"]
    return AffectEvent(trust, fear, aggression, curiosity, intensity, "neutral", ())


def smooth_emotions(npc: NPC, affect: AffectEvent, model_delta: StateUpdate | None = None) -> EmotionComputation:
    previous = EmotionSnapshot.from_npc(npc)
    model_delta = model_delta or StateUpdate()
    values = {}
    for dimension in EMOTION_DIMENSIONS:
        current = getattr(previous, dimension)
        player_delta = clamp(getattr(affect, dimension) * PLAYER_GAIN, -1.0, 1.0)
        llm_delta = clamp(getattr(model_delta, dimension) * LLM_GAIN, -1.0, 1.0)
        raw_target = clamp(current + player_delta + llm_delta)
        values[dimension] = clamp(current + SMOOTHING_ALPHA * (raw_target - current))
    return EmotionComputation(previous=previous, affect=affect, next=EmotionSnapshot(**values))


def bow_related_request(player_input: str, output: LLMResponse | None = None) -> bool:
    text = player_input.lower()
    if re.search(r"\b(?:bow|craft|crafting|materials|string|wood)\b", text):
        return True
    if output and re.search(r"\b(?:bow|craft|crafting|materials|string|wood)\b", output.dialogue.lower()):
        return True
    return bool(output and output.action in {"craft_axe", "repair_tool", "help_player", "request_materials"})


def gatherer_wood_request(player_input: str, output: LLMResponse | None = None) -> bool:
    text = player_input.lower()
    if output and output.item == "wood" and output.intent in {"confirm_transfer", "transfer"}:
        return True
    if output and output.item == "wood" and output.action in {"ask_question", "give_item"}:
        return True
    return bool(re.search(r"\b(?:give|share|need|want|have|request)\b.*\bwood\b|\bwood\b.*\b(?:give|share|need|want|request)\b", text))


def authorize_action(npc: NPC, output: LLMResponse, emotions: EmotionSnapshot, player_input: str) -> ActionDecision:
    requested = output.action
    if requested not in SUPPORTED_ACTIONS:
        return ActionDecision(False, requested, "speak", "validation_rejected", "neutral")
    if npc.role == "craftsman" and bow_related_request(player_input, output):
        if emotions.aggression >= 0.65 or emotions.trust <= 0.20:
            tone = "rude" if emotions.aggression >= 0.65 else "curt"
            return ActionDecision(False, requested, "speak", "emotion_blocked", tone)
    if npc.role == "gatherer" and gatherer_wood_request(player_input, output):
        if emotions.aggression >= 0.65 or emotions.trust <= 0.20:
            tone = "rude" if emotions.aggression >= 0.65 else "curt"
            return ActionDecision(False, requested, "speak", "emotion_blocked", tone)
    if npc.role != "craftsman" and requested in {"craft_axe", "repair_tool"}:
        return ActionDecision(False, requested, "speak", "role_forbidden", "neutral")
    return ActionDecision(True, requested, requested, None, None)


def refusal_response(decision: ActionDecision) -> LLMResponse:
    tone = decision.refusal_tone or "curt"
    if tone == "rude":
        dialogue = "Not after the way you have spoken to me. Come back when you can show some respect."
        emotion = "angry"
    elif tone == "fearful":
        dialogue = "No. I will not take that risk right now."
        emotion = "fearful"
    else:
        dialogue = "I am not willing to help with that right now. Speak to me with respect first."
        emotion = "curt"
    return LLMResponse(
        intent="refuse",
        emotion=emotion,
        dialogue=dialogue,
        action=decision.effective_action,
        reasoning=f"Authoritative refusal: {decision.reason_code or 'blocked'}.",
        state_update=StateUpdate(),
    )
