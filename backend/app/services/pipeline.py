from __future__ import annotations

import logging
from time import monotonic
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.conversation import Conversation
from app.models.npc import NPC
from app.models.player import Player
from app.models.quest import Quest
from app.schemas.chat import ChatResponse, StructuredNPCOutput
from app.schemas.memory import MemoryRead
from app.schemas.npc import NPCRead
from app.services.decision_trace import build_decision_trace
from app.services.context.builder import ContextBuilder
from app.services.llm.service import GenerationResult, LLMService
from app.services.memory.service import MemoryService
from app.services.memory.importance import classify
from app.services.npc.conditioning import RoleConditioningService
from app.services.prompts.builder import PromptBuilder
from app.services.rule_engine.behavior import select_behavior
from app.services.context.grounding import build_facts
from app.models.bow_quest import BowQuest
from datetime import datetime, timezone
from app.services.state.service import StateService, WorldStateSnapshot
from app.services.validation.models import LLMResponse, StateUpdate
from app.services.validation.service import KnowledgeBoundaryError, ValidationError, ValidationService
from app.services.validation.knowledge import unfamiliar_topic_response
from app.services.semantic_routing import ROUTING_VERSION
from app.services.validation.items import transfer_interpretation
from app.services.validation.knowledge import outside_world
from app.services.quests.bow import maybe_start, get_quest, snapshot as bow_snapshot, reply

logger = logging.getLogger(__name__)


class StaleConversationError(RuntimeError):
    """The reset/clear/conversation revision changed while generation ran."""


class ConversationPipeline:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._settings = get_settings()
        if self._settings.conversation_routing_version != ROUTING_VERSION:
            raise RuntimeError('Unsupported conversation routing version; refusing phrase-router fallback.')
        self._prompt_builder = PromptBuilder()
        self._validation_service = ValidationService()
        self._role_conditioning = RoleConditioningService()
        self._memory_service = MemoryService(db)
        self._llm_service = LLMService()

    def chat(self, npc_id: int, player_message: str, game_scope: str | None = None,
             structured_operation: dict | None = None) -> ChatResponse:
        started = monotonic()
        # Snapshot only: no row locks or game mutations while providers run.
        player = self._db.get(Player, 1)
        npc = self._db.get(NPC, npc_id)
        if player is None or npc is None:
            raise ValueError("Player or NPC does not exist")
        if game_scope is not None and game_scope != player.game_scope:
            raise StaleConversationError("This game has been replaced. Reload the current game.")
        from app.services.gatherer import chat_blocked
        if chat_blocked(self._db, player, npc):
            raise StaleConversationError("Finish the Gatherer encounter before talking or transferring items.")
        requested_scope = player.game_scope
        revision = npc.memory_revision
        context_builder = ContextBuilder(self._db, memory_service=self._memory_service)
        context = context_builder.build(npc=npc, player=player, player_input=player_message)
        capabilities = [
            {'id': 'give_item', 'kind': 'transfer', 'targets': list(npc.inventory or [])},
            {'id': 'receive_item', 'kind': 'transfer', 'targets': list(player.inventory or [])},
        ]
        if npc.role == 'craftsman':
            capabilities.extend({'id': 'craftsman.' + command, 'kind': 'encounter', 'targets': ['ship']} for command in
                                 ('report_wreck', 'begin_inspection', 'resume', 'wait', 'return', 'postpone'))
            capabilities.append({'id': 'craftsman.request_bow', 'kind': 'quest', 'targets': ['bow']})
        from app.services.semantic_routing import InterpretationContext
        interpretation_context = InterpretationContext(
            message=player_message, history=context.recent_dialogue, facts=context.facts,
            capabilities=capabilities,
            pending_question=({'id': 'purpose:' + npc.pending_item, 'kind': 'item_purpose', 'item': npc.pending_item}
                              if npc.pending_item else
                              {'id': 'craftsman:ship-inspection', 'kind': 'ship_inspection_consent'}
                              if npc.role == 'craftsman' and context.encounter.get('offer_pending') else None),
            pending_item=npc.pending_item,
            focus=context.conversation_focus, encounter=context.encounter,
            npc_name=npc.name, npc_role=npc.role)
        structured_interpretation = None
        if structured_operation is not None:
            from app.services.semantic_routing import AcceptedInterpretation
            operation = structured_operation.get('operation')
            target = structured_operation.get('target')
            evidence = player_message
            structured_interpretation = AcceptedInterpretation(version=1, concerns=[{
                'id': 'c1', 'kind': 'operation_request', 'evidence': evidence,
                'start': 0, 'end': len(evidence), 'modality': 'direct', 'target': target,
                'fact_ids': [], 'pending_question_id': None, 'answer_type': None,
                'operation': operation}], clarification=None)
            AcceptedInterpretation.validate_for_context(structured_interpretation.model_dump(), interpretation_context)
        # Detached validation snapshot: provider calls must
        # not refresh ORM rows and reopen a transaction after rollback.
        validation_npc = NPC(id=npc.id, role=npc.role, inventory=list(npc.inventory or []),
                             pending_item=npc.pending_item)
        self._db.rollback()  # release the read transaction before generation
        context_seconds = monotonic() - started
        generation_started = monotonic()
        generation_status = 'succeeded'
        interpretation_seconds = 0.0
        interpretation_calls = 0
        span_repairs = 0
        interpretation_failed = False
        speech_calls = 0
        try:
            if structured_interpretation is not None:
                interpretation = structured_interpretation
                generation_status = 'structured_ui_operation'
            else:
                interpretation, interpretation_seconds = self._llm_service.interpret(interpretation_context)
            interpretation_calls = interpretation_context.provider_calls
            span_repairs = interpretation_context.span_repairs
            context.accepted_interpretation = interpretation.model_dump()
            context.interpretation_seconds = interpretation_seconds
            kinds = {c.kind for c in interpretation.concerns}
            speech_required = bool(kinds & {'social', 'player_report'}) or len(kinds) > 1
            if speech_required:
                prompt = self._prompt_builder.build(context)
                generation = self._llm_service.generate(prompt, context.as_dict())
                speech_calls += 1
            else:
                generation_status = 'bypassed_after_interpretation'
                facts = [identity for c in interpretation.concerns for identity in c.fact_ids]
                answer_kind = 'answer' if 'factual' in kinds and facts else 'clarify'
                generation = GenerationResult(raw_text='', raw_json={
                    'answer_kind': answer_kind, 'fact_ids': facts[:2], 'dialogue': ''})
        except Exception as exc:
            interpretation_calls = interpretation_context.provider_calls
            span_repairs = interpretation_context.span_repairs
            interpretation_failed = not bool(context.accepted_interpretation)
            generation_status = 'interpretation_failure' if interpretation_failed else 'speech_provider_or_decode_failure'
            logger.error("Local interpretation or speech failed for NPC %s (%s: %s); using zero-effect degradation", npc_id, type(exc).__name__, str(exc))
            generation = GenerationResult(raw_text="{}", raw_json={})

        generation_seconds = monotonic() - generation_started

        # Atomic compare-and-swap also acquires SQLite's write lock (FOR UPDATE
        # alone does not). Reset and clear rotate this persisted token. Advance
        # it for accepted processing so concurrent old proposals cannot overwrite.
        player = self._require_player()
        if player.game_scope != requested_scope:
            self._db.rollback()
            raise StaleConversationError("This game has been replaced. Reload the current game.")
        decision_id = str(uuid4())
        acquired = self._db.execute(update(NPC).where(NPC.id == npc_id, NPC.memory_revision == revision)
                                    .values(memory_revision=decision_id).execution_options(synchronize_session=False))
        if acquired.rowcount != 1:
            self._db.rollback()
            raise StaleConversationError("The world or conversation changed. Please try again.")
        self._db.expire_all()
        player = self._require_player()
        npc = self._require_npc(npc_id)
        if chat_blocked(self._db, player, npc):
            self._db.rollback()
            raise StaleConversationError("The Gatherer encounter has started. Finish it before talking.")
        quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id))
        # Re-render selections against current facts/resources, including quest
        # changes that happened during generation. Do not retrieve/embed again.
        context.inventory = list(player.inventory or [])
        context.quest = bow_snapshot(self._db.get(BowQuest, player.id))
        context.facts = build_facts(self._db, npc, player, context.quest, datetime.now(timezone.utc).isoformat())
        quest_before = get_quest(self._db, player.id).phase
        pending_before = npc.pending_item
        self._output_rejected = False
        self._rejection_reason = None
        grounded = None
        if not interpretation_failed and not outside_world(player_message):
            if (context.accepted_interpretation.get('clarification') and
                all(c.get('kind') == 'clarification' for c in context.accepted_interpretation.get('concerns', []))):
                grounded = reply(context.accepted_interpretation['clarification'], intent='clarify')
            direct_operations = [c for c in context.accepted_interpretation.get('concerns', [])
                                 if c.get('kind') == 'operation_request' and c.get('modality') == 'direct']
            if grounded is None and len(direct_operations) > 1:
                grounded = reply('Which single action would you like me to handle first?')
            elif grounded is None:
                grounded = transfer_interpretation(context.accepted_interpretation, list(npc.inventory or []),
                                                   list(player.inventory or []), npc.pending_item)
            if grounded is not None and any(c.get('kind') == 'social' for c in context.accepted_interpretation.get('concerns', [])):
                try:
                    social_segment = self._validation_service.validate(generation.raw_json, validation_npc, context).output
                    combined = ' '.join(part.strip() for part in (social_segment.dialogue, grounded.dialogue) if part.strip())
                    if len(combined) > self._settings.max_dialogue_chars:
                        raise ValidationError('Mixed social and operation reply exceeds dialogue limit')
                    grounded.dialogue = combined
                except ValidationError as exc:
                    self._output_rejected = True
                    self._rejection_reason = str(exc)
                    grounded = None
            if grounded is not None and grounded.intent == 'cancel_transfer' and npc.pending_item:
                npc.pending_item = None
            operation = next((c for c in context.accepted_interpretation.get('concerns', [])
                              if c.get('kind') == 'operation_request' and c.get('modality') == 'direct'
                              and c.get('operation', '').startswith('craftsman.')), None)
            if operation is None and npc.role == 'craftsman' and context.encounter.get('offer_pending'):
                consent = next((c for c in context.accepted_interpretation.get('concerns', [])
                    if c.get('kind') == 'pending_answer' and c.get('modality') == 'direct'
                    and c.get('pending_question_id') == 'craftsman:ship-inspection'
                    and c.get('answer_type') == 'assent'), None)
                if consent:
                    operation = {'operation': 'craftsman.begin_inspection'}
            report = next((c for c in context.accepted_interpretation.get('concerns', [])
                           if c.get('kind') == 'player_report' and c.get('modality') == 'direct'
                           and c.get('target') in {'ship', 'quest.ship'}), None)
            if grounded is None and operation is None and report and npc.role == 'craftsman' and not context.encounter.get('wreck_reported'):
                from app.services.craftsman import record, apply_command
                row = record(self._db, player)
                apply_command(self._db, player, npc, 'report_wreck', decision_id, row.revision, {})
                grounded = reply("I'm sorry the ship was damaged. Would you like me to inspect it with you?")
            if grounded is None and operation and operation.get('operation') == 'craftsman.request_bow':
                from app.services.quests.bow import request_from_interpretation
                grounded = request_from_interpretation(self._db, npc, player)
            if grounded is None and operation and npc.role == 'craftsman':
                from app.services.craftsman import record, apply_command, encounter_snapshot
                row = record(self._db, player)
                command = operation['operation'].split('.', 1)[1]
                command_map = {'report_wreck': 'report_wreck', 'begin_inspection': 'begin_ship_inspection',
                               'wait': 'wait', 'resume': 'resume', 'return': 'return', 'postpone': 'postpone'}
                encounter = encounter_snapshot(self._db, player)
                allowed = ((command == 'report_wreck' and not encounter['inspection_complete']) or
                           (command == 'begin_inspection' and encounter['offer_pending'] and not encounter['outing_active']) or
                           (command in {'wait', 'resume', 'return', 'postpone'} and encounter['outing_active']))
                if command == 'postpone' and not encounter['outing_active']:
                    grounded = reply('Of course. We can talk here until you feel ready.')
                elif allowed:
                    apply_command(self._db, player, npc, command_map[command], decision_id, row.revision, {})
                    text = {'report_wreck': "I'm glad you made it ashore. I can take a look at the damage with you, if you'd like.",
                            'begin_inspection': "All right. Let's go and look at the ship together.",
                            'wait': "Of course. I'll wait here; tell me when you're ready to go.",
                            'resume': "All right. Lead the way; we'll take it at your pace.",
                            'return': "I'll head back to my workshop.", 'postpone': 'Of course. There is no hurry.'}[command]
                    grounded = reply(text)
        if interpretation_failed:
            self._output_rejected = True
            self._rejection_reason = 'Local interpretation unavailable; no action was considered.'
            validated_output = LLMResponse(intent='clarify', emotion='calm',
                dialogue='I could not understand that just now. Please try again in a moment.', action='speak',
                reasoning='Explicit local interpretation failure degradation.', state_update=StateUpdate())
        elif self._output_rejected:
            validated_output = self._fallback_output(npc=npc, context=context, player_message=player_message)
        else:
            validated_output = grounded or self._validate_or_repair(generation.raw_json, npc, context, player_message)
        conditioned_output = self._role_conditioning.apply(npc, validated_output)
        if (not self._output_rejected and grounded is None and validated_output.answer_kind == 'chat'
                and set(generation.raw_json) == {'answer_kind', 'fact_ids', 'dialogue'}):
            from app.services.npc.emotional_feedback import emotional_feedback
            # Action restrictions remain role-conditioned. The trusted reaction
            # policy owns these bounded deltas, rather than legacy model caps.
            conditioned_output.state_update = emotional_feedback(context.accepted_interpretation)
        try:
            self._validation_service.validate_control(conditioned_output, npc, player, authoritative=grounded is not None)
        except ValidationError as exc:
            self._output_rejected = True
            self._rejection_reason = str(exc)
            conditioned_output = self._fallback_output(npc, context, player_message)
        conditioned_output, behavior_trace = select_behavior(
            npc, player, conditioned_output, rejected=self._output_rejected,
            decision_id=decision_id, scope=revision,
        )
        before_inventory = {'player': list(player.inventory or []), 'npc': list(npc.inventory or [])}

        state_service = StateService(self._db)
        if self._output_rejected:
            snapshot = WorldStateSnapshot(list(player.inventory or []), quest.status if quest else 'unknown', quest.progress if quest else 0)
        else:
            snapshot = state_service.apply(npc=npc, player=player, quest=quest, output=conditioned_output)

        transfer_evidence = None
        if not self._output_rejected and conditioned_output.action in {'give_item', 'receive_item'}:
            source, destination = ('npc', 'player') if conditioned_output.action == 'give_item' else ('player', 'npc')
            after = {'npc': list(npc.inventory or []), 'player': list(player.inventory or [])}
            item = conditioned_output.item
            transfer_evidence = {'action': conditioned_output.action, 'item': item,
                'source_before': before_inventory[source].count(item), 'source_after': after[source].count(item),
                'destination_before': before_inventory[destination].count(item), 'destination_after': after[destination].count(item)}
        if not self._output_rejected:
            maybe_start(self._db, player, npc, conditioned_output)

        behavior_trace['verified_outcome'] = {
            'transfer': transfer_evidence,
            'action': conditioned_output.action if not self._output_rejected else None,
            'inventory_before': before_inventory,
            'inventory_after': {'player': list(player.inventory or []), 'npc': list(npc.inventory or [])},
            'quest_before': quest_before, 'quest_after': get_quest(self._db, player.id).phase,
            'pending_before': pending_before, 'pending_after': npc.pending_item,
            'dialogue': conditioned_output.dialogue,
        }
        decision = classify(
            player_message, conditioned_output, grounded=grounded is not None,
            quest_before=quest_before, quest_after=get_quest(self._db, player.id).phase,
            pending_before=pending_before, pending_after=npc.pending_item,
            rejected=self._output_rejected,
        )
        memory_classification = decision.payload() | {'stored': False}

        trace = {
            'context_fact_ids': [fact['id'] for fact in context.facts],
            'fact_sources': [{k: fact[k] for k in ('id', 'source', 'status', 'as_of')} for fact in context.facts],
            'memory_retrieval': context.memory_retrieval,
            'retrieved_memory_ids': [memory['id'] for memory in context.memories],
            'retrieved_memory_provenance': [{k: memory.get(k) for k in ('id', 'game_scope', 'epistemic_status', 'authority', 'lifecycle', 'source_event_id')} for memory in context.memories],
            'selected_fact_ids': conditioned_output.fact_ids,
            'answer_kind': conditioned_output.answer_kind,
            'rejected': self._output_rejected,
            'rejection_reason': self._rejection_reason,
            'provider': type(self._llm_service._provider).__name__,
            'routing_version': ROUTING_VERSION,
            'interpretation_origin': 'structured_ui' if structured_interpretation is not None else 'local_model',
            'accepted_interpretation': context.accepted_interpretation,
            'interpretation_seconds': round(interpretation_seconds, 6),
            'model_calls': {'interpretation': interpretation_calls,
                            'speech_and_repair': speech_calls},
            'interpretation_span_repairs': span_repairs,
        }
        conversation = Conversation(
            npc_id=npc.id,
            game_scope=player.game_scope,
            source_event_id=decision_id,
            player_input=player_message,
            llm_output=generation.raw_json,
            validated_output=conditioned_output.model_dump() | {"memory_classification": memory_classification, "grounding_trace": trace, "behavior_trace": behavior_trace},
            final_dialogue=conditioned_output.dialogue,
        )
        self._db.add(conversation)
        self._db.flush()
        # This existing durable row is the outcome identity; no new event bus.
        behavior_trace = behavior_trace | {'verified_outcome': behavior_trace['verified_outcome'] | {'conversation_id': conversation.id, 'event_id': decision_id}}
        conversation.validated_output = conversation.validated_output | {'behavior_trace': behavior_trace}
        self._db.flush()
        write = self._memory_service.store_conversation(npc, conversation)
        memory_classification = memory_classification | write.payload()
        decision_trace = build_decision_trace(
            context=context, raw_proposal=generation.raw_json, grounding=trace, behavior=behavior_trace,
            generation={'status': generation_status, 'authoritative_override': grounded is not None},
            conversation=conversation, memory_classification=memory_classification, settings=self._settings,
            timings={'context': context_seconds,
                     'generation': max(0.0, generation_seconds - interpretation_seconds),
                     'interpretation': interpretation_seconds,
                     'through_memory_write': monotonic() - started},
        )
        conversation.validated_output = conversation.validated_output | {
            'memory_classification': memory_classification, 'decision_trace': decision_trace}
        self._db.commit()

        # The attributed memory row committed with its conversation. Semantic
        # embedding is optional work and must happen after the game writer ends.
        self._memory_service.embed_deferred_conversation_memories()

        refreshed_npc = self._db.scalar(select(NPC).where(NPC.id == npc.id)) or npc
        memories = self._memory_service.retrieve_relevant_memories(refreshed_npc, player_message, self._settings.memory_top_k)
        current_quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id))
        current_player = self._db.scalar(select(Player).where(Player.id == player.id)) or player

        from app.services.craftsman import encounter_snapshot
        from app.services.quests.ship_repair import ship_snapshot
        return ChatResponse(
            game_scope=current_player.game_scope,
            craftsman_encounter=encounter_snapshot(self._db,current_player),
            ship_repair=ship_snapshot(self._db,current_player),
            decision_trace=decision_trace,
            grounding_trace=trace,
            behavior_trace=behavior_trace,
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
            self._rejection_reason = str(exc)
            logger.warning("NPC %s knowledge boundary: %s", npc.id, exc)
            return unfamiliar_topic_response(npc.role)
        except ValidationError as exc:
            self._output_rejected = True
            self._rejection_reason = str(exc)
            logger.warning("NPC %s output rejected: %s", npc.id, exc)
            return self._fallback_output(npc=npc, context=context, player_message=player_message)

    def _fallback_output(self, npc: NPC, context, player_message: str) -> LLMResponse:
        if not context.accepted_interpretation:
            return LLMResponse(intent='clarify', emotion='calm',
                dialogue='I could not understand that just now. Please try again in a moment.', action='speak',
                reasoning='Explicit local interpretation failure degradation.', state_update=StateUpdate())
        if npc.role == "gatherer":
            refused = (context.encounter.get('status') == 'resolved_declined' and npc.trust < .3)
            return LLMResponse(
                intent="assist",
                emotion="wary" if refused else "friendly",
                dialogue=("You left when I needed help. I haven't forgotten. What do you want?" if refused
                          else "I can tell you about the forest. Ask me about the supplies I have."),
                action="speak",
                reasoning="Fallback response after validation rejected the raw output.",
                state_update=StateUpdate(),
            )

        return LLMResponse(
            intent="assist",
            emotion="calm",
            dialogue="I can't form a grounded reply right now. Please try again shortly.",
            action="speak",
            reasoning="Explicit zero-effect degradation after speech validation failed.",
            state_update=StateUpdate(),
        )

    def _require_npc(self, npc_id: int) -> NPC:
        npc = self._db.scalar(select(NPC).where(NPC.id == npc_id).with_for_update())
        if npc is None:
            raise ValueError(f"NPC {npc_id} does not exist")
        return npc

    def _require_player(self) -> Player:
        from app.services.state.locking import lock_player
        player = lock_player(self._db)
        if player is None:
            raise ValueError("Seed player does not exist")
        return player
