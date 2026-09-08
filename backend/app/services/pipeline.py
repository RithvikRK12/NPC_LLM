from __future__ import annotations

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
from app.services.npc.conditioning import RoleConditioningService
from app.services.prompts.builder import PromptBuilder
from app.services.rule_engine.service import RuleEngine
from app.services.state.service import StateService
from app.services.validation.models import LLMResponse, StateUpdate
from app.services.validation.service import ValidationService


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
        npc = self._require_npc(npc_id)
        player = self._require_player()
        quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id))

        context_builder = ContextBuilder(self._db, memory_service=self._memory_service)
        context = context_builder.build(npc=npc, player=player, player_input=player_message)
        prompt = self._prompt_builder.build(context)

        try:
            generation = self._llm_service.generate(prompt, context.as_dict())
        except Exception:
            generation = GenerationResult(raw_text="{}", raw_json={})
        validated_output = self._validate_or_repair(generation.raw_json, npc, context, player_message)
        conditioned_output = self._role_conditioning.apply(npc, validated_output)
        _rules = self._rule_engine.evaluate(npc)

        state_service = StateService(self._db)
        snapshot = state_service.apply(npc=npc, player=player, quest=quest, output=conditioned_output)

        memory_event = self._memory_service.build_interaction_memory(
            npc=npc,
            player_input=player_message,
            dialogue=conditioned_output.dialogue,
            action=conditioned_output.action,
            relationship_mode=_rules.relationship_mode,
        )
        self._memory_service.store_memory(
            npc=npc,
            event=memory_event,
            importance=self._importance_for_output(conditioned_output),
            emotion=conditioned_output.emotion,
        )

        conversation = Conversation(
            npc_id=npc.id,
            player_input=player_message,
            llm_output=generation.raw_json,
            validated_output=conditioned_output.model_dump(),
            final_dialogue=conditioned_output.dialogue,
        )
        self._db.add(conversation)
        self._db.commit()

        refreshed_npc = self._db.scalar(select(NPC).where(NPC.id == npc.id)) or npc
        memories = self._memory_service.retrieve_relevant_memories(refreshed_npc, player_message, self._settings.memory_top_k)
        current_quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id))
        current_player = self._db.scalar(select(Player).where(Player.id == player.id)) or player

        return ChatResponse(
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
        except Exception:
            return self._fallback_output(npc=npc, context=context, player_message=player_message)

    def _fallback_output(self, npc: NPC, context, player_message: str) -> LLMResponse:
        if npc.role == "gatherer":
            return LLMResponse(
                intent="assist",
                emotion="friendly",
                dialogue="I can share wood and tell you where the forest is safest.",
                action="give_item",
                reasoning="Fallback response after validation rejected the raw output.",
                state_update=StateUpdate(trust=0.03, fear=0.0, aggression=0.0, curiosity=0.02),
            )

        return LLMResponse(
            intent="assist",
            emotion="calm",
            dialogue="Bring me wood and I will craft an axe for you.",
            action="speak",
            reasoning="Fallback response after validation rejected the raw output.",
            state_update=StateUpdate(trust=0.03, fear=0.0, aggression=0.0, curiosity=0.02),
        )

    def _importance_for_output(self, output: LLMResponse) -> float:
        if output.action in {"craft_axe", "give_item", "repair_tool"}:
            return 0.9
        if output.emotion in {"friendly", "calm"}:
            return 0.6
        return 0.4

    def _require_npc(self, npc_id: int) -> NPC:
        npc = self._db.scalar(select(NPC).where(NPC.id == npc_id))
        if npc is None:
            raise ValueError(f"NPC {npc_id} does not exist")
        return npc

    def _require_player(self) -> Player:
        player = self._db.scalar(select(Player).where(Player.id == 1))
        if player is None:
            raise ValueError("Seed player does not exist")
        return player