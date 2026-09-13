from __future__ import annotations

import logging
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.conversation import Conversation
from app.models.npc import NPC
from app.models.player import Player
from app.models.quest import Quest
from app.schemas.chat import ChatResponse, StructuredNPCOutput
from app.schemas.memory import MemoryRead
from app.schemas.npc import NPCRead
from app.services.context.builder import ContextBuilder
from app.services.llm.service import GenerationResult, LLMService
from app.services.memory.service import MemoryService
from app.services.memory.importance import classify
from app.services.npc.conditioning import RoleConditioningService
from app.services.prompts.builder import PromptBuilder
from app.services.rule_engine.service import RuleEngine
from app.services.state.service import StateService
from app.services.validation.models import LLMResponse, StateUpdate
from app.services.validation.service import KnowledgeBoundaryError, ValidationError, ValidationService
from app.services.validation.knowledge import unfamiliar_topic_response
from app.services.validation.items import requested_transfer, transfer_answer
from app.services.validation.knowledge import outside_world
from app.services.validation.control import (
    authorize_action,
    bow_related_request,
    classify_player_affect,
    make_validation_context,
    refusal_response,
    smooth_emotions,
)
from app.services.quests.bow import dialogue as bow_dialogue, maybe_start, get_quest, snapshot as bow_snapshot, reply

logger = logging.getLogger(__name__)


class ConversationPipeline:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._settings = get_settings()
        self._prompt_builder = PromptBuilder()
        self._validation_service = ValidationService()
        self._rule_engine = RuleEngine()
        self._role_conditioning = RoleConditioningService()
        self._memory_service = MemoryService(db)
        self._llm_service = LLMService()

    def chat(self, npc_id: int, player_message: str) -> ChatResponse:
        player = self._require_player()
        npc = self._require_npc(npc_id)
        quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id))

        context_builder = ContextBuilder(self._db, memory_service=self._memory_service)
        context = context_builder.build(npc=npc, player=player, player_input=player_message)
        validation_context = make_validation_context(npc=npc, player=player, player_input=player_message, quest=quest)
        prompt = self._prompt_builder.build(context)

        quest_before = get_quest(self._db, player.id).phase
        pending_before = npc.pending_item
        self._output_rejected = False
        grounded = None
        if not outside_world(player_message):
            request = requested_transfer(player_message)
            if request == ('give_item', 'bow') and not npc.pending_item and 'bow' not in (npc.inventory or []):
                grounded = bow_dialogue(self._db, npc, player_message, player)
            if grounded is None:
                grounded = transfer_answer(
                    player_message,
                    list(validation_context.npc_inventory),
                    list(validation_context.player_inventory),
                    validation_context.pending_item,
                )
            if grounded is None:
                grounded = bow_dialogue(self._db, npc, player_message, player)
            if grounded is None and any(phrase in player_message.lower() for phrase in ('inventory', 'what do you have', 'what are you carrying')):
                stock = ', '.join(npc.inventory or []) or 'nothing'
                grounded = reply(f"I currently carry {stock}. Select an item in my supplies to request it.")
        try:
            if grounded is not None or requested_transfer(player_message) is not None or npc.pending_item:
                # Ownership and explicit transfer requests are game rules, not LLM decisions.
                generation = GenerationResult(raw_text="", raw_json={})
            else:
                generation = self._llm_service.generate(prompt, context.as_dict())
        except Exception:
            logger.exception("LLM generation failed for NPC %s (model=%s)", npc.id, self._settings.llm_model)
            generation = GenerationResult(raw_text="{}", raw_json={})
        validated_output = grounded or self._validate_or_repair(generation.raw_json, npc, validation_context, player_message)
        conditioned_output = self._role_conditioning.apply(npc, validated_output)
        affect = classify_player_affect(player_message)
        emotion_computation = smooth_emotions(npc, affect, conditioned_output.state_update)
        action_decision = authorize_action(npc, conditioned_output, emotion_computation.next, player_message)
        if not action_decision.allowed:
            logger.info(
                "NPC action blocked",
                extra={
                    "npc_id": npc.id,
                    "npc_role": npc.role,
                    "affect_category": affect.category,
                    "previous_emotion": asdict(emotion_computation.previous),
                    "next_emotion": asdict(emotion_computation.next),
                    "requested_action": action_decision.requested_action,
                    "effective_action": action_decision.effective_action,
                    "refusal_reason": action_decision.reason_code,
                    "quest_phase_before": quest_before,
                },
            )
            get_quest(self._db, player.id).phase = quest_before
            conditioned_output = refusal_response(action_decision)
        _rules = self._rule_engine.evaluate(npc)

        state_service = StateService(self._db)
        snapshot = state_service.apply(
            npc=npc,
            player=player,
            quest=quest,
            output=conditioned_output,
            emotion_snapshot=emotion_computation.next,
        )

        may_start_bow = action_decision.allowed and grounded is not None and bow_related_request(player_message, conditioned_output)
        maybe_start(self._db, player, npc, conditioned_output, allowed=may_start_bow)

        decision = classify(
            player_message, conditioned_output, grounded=grounded is not None,
            quest_before=quest_before, quest_after=get_quest(self._db, player.id).phase,
            pending_before=pending_before, pending_after=npc.pending_item,
            rejected=self._output_rejected,
        )
        stored = None
        if decision.important:
            stored = self._memory_service.store_memory(
                npc=npc, event=decision.event, importance=decision.importance,
                emotion=conditioned_output.emotion, event_type=decision.category,
                quest_id="get_bow" if decision.category.startswith("quest_") else None,
            )
        memory_classification = decision.payload() | {'stored': stored is not None}

        conversation = Conversation(
            npc_id=npc.id,
            player_input=player_message,
            llm_output=generation.raw_json,
            validated_output=conditioned_output.model_dump() | {"memory_classification": memory_classification},
            final_dialogue=conditioned_output.dialogue,
        )
        self._db.add(conversation)
        self._db.commit()

        refreshed_npc = self._db.scalar(select(NPC).where(NPC.id == npc.id)) or npc
        memories = self._memory_service.retrieve_relevant_memories(refreshed_npc, player_message, self._settings.memory_top_k)
        current_quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id))
        current_player = self._db.scalar(select(Player).where(Player.id == player.id)) or player

        return ChatResponse(
            memory_classification=memory_classification,
            bow_quest=bow_snapshot(get_quest(self._db, player.id)),
            npc=NPCRead.model_validate(refreshed_npc),
            validated_output=StructuredNPCOutput.model_validate(conditioned_output.model_dump()),
            final_dialogue=conditioned_output.dialogue,
            player_inventory=list(current_player.inventory or []),
            quest_status=current_quest.status if current_quest else snapshot.quest_status,
            quest_progress=current_quest.progress if current_quest else snapshot.quest_progress,
            memories=[MemoryRead.model_validate(memory) for memory in memories],
        )

    def _validate_or_repair(self, raw_json: dict, npc: NPC, context, player_message: str) -> LLMResponse:
        try:
            return self._validation_service.validate(raw_json, npc, context).output
        except KnowledgeBoundaryError as exc:
            self._output_rejected = True
            logger.warning("NPC %s knowledge boundary: %s", npc.id, exc)
            return unfamiliar_topic_response(npc.role)
        except ValidationError as exc:
            self._output_rejected = True
            logger.warning("NPC %s output rejected: %s", npc.id, exc)
            return self._fallback_output(npc=npc, context=context, player_message=player_message)

    def _fallback_output(self, npc: NPC, context, player_message: str) -> LLMResponse:
        if npc.role == "gatherer":
            return LLMResponse(
                intent="assist",
                emotion="friendly",
                dialogue="I can tell you about the forest. Ask me about the supplies I have.",
                action="speak",
                reasoning="Fallback response after validation rejected the raw output.",
                state_update=StateUpdate(trust=0.03, fear=0.0, aggression=0.0, curiosity=0.02),
            )

        return LLMResponse(
            intent="assist",
            emotion="calm",
            dialogue="I can help with workshop supplies. Open Quests if you would like me to make a bow.",
            action="speak",
            reasoning="Fallback response after validation rejected the raw output.",
            state_update=StateUpdate(trust=0.03, fear=0.0, aggression=0.0, curiosity=0.02),
        )

    def _require_npc(self, npc_id: int) -> NPC:
        npc = self._db.scalar(select(NPC).where(NPC.id == npc_id).with_for_update())
        if npc is None:
            raise ValueError(f"NPC {npc_id} does not exist")
        return npc

    def _require_player(self) -> Player:
        player = self._db.scalar(select(Player).where(Player.id == 1).with_for_update())
        if player is None:
            raise ValueError("Seed player does not exist")
        return player
