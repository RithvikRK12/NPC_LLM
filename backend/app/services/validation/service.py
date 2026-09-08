from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import get_settings
from app.models.npc import NPC
from app.services.validation.models import LLMResponse


class ValidationError(RuntimeError):
    pass


@dataclass(slots=True)
class ValidationResult:
    output: LLMResponse


class ValidationService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def validate(self, raw_output: dict, npc: NPC, context: object | None = None) -> ValidationResult:
        try:
            output = LLMResponse.model_validate(raw_output)
        except Exception as exc:
            raise ValidationError(f"Malformed structured JSON: {exc}") from exc

        if len(output.dialogue) > self._settings.max_dialogue_chars:
            raise ValidationError("Dialogue exceeds maximum length")

        self._validate_ranges(output)
        self._validate_action(output.action, npc, context)
        self._validate_contradictions(output)
        return ValidationResult(output=output)

    def _validate_ranges(self, output: LLMResponse) -> None:
        for field_name in ("trust", "fear", "aggression", "curiosity"):
            value = getattr(output.state_update, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValidationError(f"{field_name} must be between 0 and 1")

    def _validate_action(self, action: str, npc: NPC, context: object | None) -> None:
        forbidden_by_role = {
            "craftsman": {"attack", "declare_war"},
            "gatherer": {"attack", "declare_war"},
        }
        if action in forbidden_by_role.get(npc.role, set()):
            raise ValidationError(f"Action '{action}' is forbidden for role '{npc.role}'")

        allowed_actions = {
            "speak",
            "idle",
            "trade",
            "give_item",
            "repair_tool",
            "craft_axe",
            "request_materials",
            "ask_question",
            "share_memory",
            "help_player",
        }
        if action not in allowed_actions:
            raise ValidationError(f"Unsupported action '{action}'")

        if action == "craft_axe":
            inventory = []
            if context is not None and hasattr(context, "inventory"):
                inventory = list(getattr(context, "inventory") or [])
            if "wood" not in inventory:
                raise ValidationError("Crafting an axe requires wood in the inventory")

    def _validate_contradictions(self, output: LLMResponse) -> None:
        hostile_tokens = {"kill", "attack", "destroy", "burn", "war"}
        friendly_tokens = {"friend", "help", "safe", "gift", "repair", "craft"}
        dialogue_tokens = set(output.dialogue.lower().replace(".", " ").replace(",", " ").split())

        if output.emotion in {"friendly", "calm"} and hostile_tokens.intersection(dialogue_tokens):
            raise ValidationError("Friendly dialogue cannot threaten")
        if output.emotion in {"hostile", "angry"} and friendly_tokens.intersection(dialogue_tokens) and output.action in {"attack", "declare_war"}:
            raise ValidationError("Hostile output cannot be framed as friendly help")