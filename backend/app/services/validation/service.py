from __future__ import annotations

from dataclasses import dataclass
import re

from app.config.settings import get_settings
from app.services.context.social import is_social_message
from app.models.npc import NPC
from app.services.validation.models import LLMResponse, FactualProposal
from app.services.context.grounding import render_answer, resolve_location_reference
from app.services.validation.knowledge import outside_world
from app.services.validation.items import transfer_answer, ITEMS


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

    def validate(self, raw_output: dict, npc: NPC, context: object | None = None) -> ValidationResult:
        if npc.role in {"craftsman", "gatherer"}:
            player_input = getattr(context, "player_input", "")
            if outside_world(player_input) or outside_world(str(raw_output.get("dialogue", ""))):
                raise KnowledgeBoundaryError("Modern technology is outside the NPC's world knowledge")
        transfer = transfer_answer(getattr(context, "player_input", ""), list(npc.inventory or []),
                                   list(getattr(context, "inventory", []) or []), npc.pending_item)
        if transfer is not None:
            return ValidationResult(output=transfer)
        try:
            if raw_output.get('answer_kind') in {'answer', 'clarify'}:
                proposal = FactualProposal.model_validate(raw_output)
                output = LLMResponse(
                    answer_kind=proposal.answer_kind, fact_ids=proposal.fact_ids,
                    intent='inform' if proposal.answer_kind == 'answer' else 'clarify',
                    emotion='calm', dialogue='Pending factual rendering.', action='speak',
                    reasoning='Server-rendered permitted fact selection.', state_update=proposal.state_update,
                )
            elif raw_output.get('answer_kind') == 'chat' and set(raw_output) == {'answer_kind', 'fact_ids', 'dialogue'}:
                # Compact conversational proposals have no authority to propose
                # relationship changes or game operations. Legacy full proposals
                # still pass the existing independent action/range checks.
                output = LLMResponse.model_validate(raw_output | {
                    'intent': 'assist', 'emotion': 'calm', 'action': 'speak',
                    'item': None, 'reasoning': 'Social dialogue proposal.', 'state_update': {},
                })
            else:
                output = LLMResponse.model_validate(raw_output)
        except Exception as exc:
            raise ValidationError("Malformed structured JSON") from exc

        if len(output.dialogue) > self._settings.max_dialogue_chars:
            raise ValidationError("Dialogue exceeds maximum length")

        if output.action in {"give_item", "receive_item"}:
            raise ValidationError("Item transfers require an explicit player request naming an owned item")
        if output.action not in {"speak", "idle", "ask_question", "share_memory"}:
            raise ValidationError("The model cannot trigger crafting, transfers, or quest rewards")
        if output.answer_kind in {'answer', 'clarify'}:
            if output.action != 'speak' or output.item is not None or any(output.state_update.model_dump().values()):
                raise ValidationError("Factual answers cannot propose effects or state rewards")
            if output.answer_kind == 'clarify' and output.fact_ids:
                raise ValidationError("Clarification cannot assert facts")
            facts = getattr(context, 'facts', [])
            if any(identity not in {fact['id'] for fact in facts} for identity in output.fact_ids):
                raise ValidationError("Unknown or private fact reference")
            binding = resolve_location_reference(getattr(context, 'player_input', ''),
                                                 getattr(context, 'conversation_focus', {}), facts)
            if binding is False:
                output.answer_kind, output.fact_ids, output.intent = 'clarify', [], 'clarify'
            elif binding:
                output.answer_kind, output.fact_ids, output.intent = 'answer', [binding], 'inform'
                output.reasoning = 'Server resolved a catalog entity and locative facet.'
            try:
                output.dialogue = render_answer(output, facts)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
            if len(output.dialogue) > self._settings.max_dialogue_chars:
                raise ValidationError("Select fewer facts: rendered answer exceeds dialogue limit")
            return ValidationResult(output=output)
        player_input = getattr(context, 'player_input', '')
        # Free prose is limited to social exchanges. A model cannot disguise an
        # outcome announcement as chat in response to a game request ("Done!").
        # This classifies messages; it does not select canned dialogue.
        social = is_social_message(player_input)
        if getattr(context, 'facts', []) and not social:
            raise ValidationError("World questions require a constrained answer or clarification")
        ownership_claim = re.search(r"\b(?:i|we) (?:already )?(?:own|have|gave|delivered|finished|completed|possess|brought)\b", player_input, re.I)
        if ownership_claim and any(output.state_update.model_dump().values()):
            raise ValidationError("Unverified player claims cannot award relationship changes")
        if output.fact_ids:
            raise ValidationError("References require a constrained factual answer")
        # Permit only a complete self-introduction clause naming the exact
        # current speaker. This is supplied identity, not permission to add job,
        # location, possession or outcome claims to otherwise social prose.
        speaker = getattr(context, 'npc_name', '')
        social_prose = output.dialogue
        if speaker:
            introduction = r"(?:^|(?<=[.!?,]))\s*I(?: am|'m|’m) (?:the |a )?" + re.escape(speaker) + r"(?=[,.!?](?:\s|$)|$)"
            social_prose = re.sub(introduction, '', social_prose, flags=re.I)
        if re.search(r"\b(?:gatherer|craftsman|castle|north|south|east|west|opening|opens|axe|bow|food|fruits|hammer|rope|saw|string|water|wood|quest|reward|crafted|crafting|completed|finished|inventory)\b|\bi (?:have|own|carry|give|gave|made)\b|\byou (?:have|received|earned)\b", social_prose, re.I):
            raise ValidationError("Inventory and quest claims must come from authoritative game rules")
        self._validate_ranges(output)
        self._validate_action(output.action, npc, context)
        self._validate_contradictions(output)
        return ValidationResult(output=output)

    def validate_control(self, output: LLMResponse, npc: NPC, player, *, authoritative: bool) -> None:
        """Final hard boundary after role conditioning, before FSEC selection."""
        LLMResponse.model_validate(output.model_dump())
        self._validate_ranges(output)
        allowed = {'speak', 'idle', 'ask_question', 'share_memory'}
        if authoritative and npc.role in {'craftsman', 'gatherer'}:
            allowed |= {'give_item', 'receive_item'}
        if output.action not in allowed:
            raise ValidationError('Final control rejected an unsupported or role-denied action')
        if output.action in {'give_item', 'receive_item'}:
            source = npc.inventory if output.action == 'give_item' else player.inventory
            if not output.item or output.item not in (source or []):
                raise ValidationError('Final control rejected unavailable resources')

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

        allowed_actions = {
            "speak",
            "idle",
            "trade",
            "give_item",
            "receive_item",
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
