from __future__ import annotations

from dataclasses import dataclass
import re

from app.config.settings import get_settings
from app.models.npc import NPC
from app.services.validation.control import SUPPORTED_ACTIONS, ValidationContext
from app.services.validation.models import LLMResponse
from app.services.validation.knowledge import outside_world
from app.services.validation.items import transfer_answer


class ValidationError(RuntimeError):
    pass


class KnowledgeBoundaryError(ValidationError):
    pass


@dataclass(slots=True)
class ValidationResult:
    output: LLMResponse


class ValidationService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def validate(self, raw_output: dict, npc: NPC, context: ValidationContext | None = None) -> ValidationResult:
        if npc.role in {"craftsman", "gatherer"}:
            player_input = context.player_input if context is not None else ""
            if outside_world(player_input) or outside_world(str(raw_output.get("dialogue", ""))):
                raise KnowledgeBoundaryError("Modern technology is outside the NPC's world knowledge")
        transfer = transfer_answer(
            getattr(context, "player_input", "") if context is not None else "",
            list(getattr(context, "npc_inventory", npc.inventory or []) if context is not None else npc.inventory or []),
            list(getattr(context, "player_inventory", getattr(context, "inventory", [])) if context is not None else []),
            getattr(context, "pending_item", npc.pending_item) if context is not None else npc.pending_item,
        )
        if transfer is not None:
            return ValidationResult(output=transfer)
        try:
            output = LLMResponse.model_validate(raw_output)
        except Exception as exc:
            raise ValidationError(f"Malformed structured JSON: {exc}") from exc

        if len(output.dialogue) > self._settings.max_dialogue_chars:
            raise ValidationError("Dialogue exceeds maximum length")

        if output.action in {"give_item", "receive_item"}:
            raise ValidationError("Item transfers require an explicit player request naming an owned item")
        if output.action not in {"speak", "idle", "ask_question", "share_memory"}:
            raise ValidationError("The model cannot trigger crafting, transfers, or quest rewards")
        if re.search(r"\b(?:quest|reward|crafted|crafting|completed|finished|inventory)\b|\bi (?:have|own|carry|give|gave|made)\b|\byou (?:have|received|earned)\b", output.dialogue, re.I):
            raise ValidationError("Inventory and quest claims must come from authoritative game rules")
        self._validate_ranges(output)
        self._validate_action(output.action, npc, context)
        self._validate_contradictions(output)
        return ValidationResult(output=output)

    def _validate_ranges(self, output: LLMResponse) -> None:
        for field_name in ("trust", "fear", "aggression", "curiosity"):
            value = getattr(output.state_update, field_name)
            if not -1.0 <= value <= 1.0:
                raise ValidationError(f"{field_name} delta must be between -1 and 1")

    def _validate_action(self, action: str, npc: NPC, context: object | None) -> None:
        forbidden_by_role = {
            "craftsman": {"attack", "declare_war"},
            "gatherer": {"attack", "declare_war"},
        }
        if action in forbidden_by_role.get(npc.role, set()):
            raise ValidationError(f"Action '{action}' is forbidden for role '{npc.role}'")

        if action not in SUPPORTED_ACTIONS:
            raise ValidationError(f"Unsupported action '{action}'")

        if action == "craft_axe":
            inventory = []
            if context is not None:
                inventory = list(getattr(context, "player_inventory", getattr(context, "inventory", [])) or [])
            if "wood" not in inventory and "wood" not in (npc.inventory or []):
                raise ValidationError("Crafting an axe requires wood in the inventory")

    def _validate_contradictions(self, output: LLMResponse) -> None:
        hostile_tokens = {"kill", "attack", "destroy", "burn", "war"}
        friendly_tokens = {"friend", "help", "safe", "gift", "repair", "craft"}
        dialogue_tokens = set(output.dialogue.lower().replace(".", " ").replace(",", " ").split())

        if output.emotion in {"friendly", "calm"} and hostile_tokens.intersection(dialogue_tokens):
            raise ValidationError("Friendly dialogue cannot threaten")
        if output.emotion in {"hostile", "angry"} and friendly_tokens.intersection(dialogue_tokens) and output.action in {"attack", "declare_war"}:
            raise ValidationError("Hostile output cannot be framed as friendly help")
