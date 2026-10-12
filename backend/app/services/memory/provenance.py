"""Persist only accepted, scoped conversation evidence; never authorize gameplay."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm.exc import ObjectDeletedError, DetachedInstanceError

from app.contracts import PolicyVersion
from app.memory.reconcile import (MemoryRecord, RelatedRecords, ReconciliationPolicy,
                                  ReconciliationPlan, ReconciliationAction, reconcile)
from app.models import Conversation, Memory
from app.services.memory.importance import classify, MemoryDecision
from app.services.memory.service import normalized_event
from app.services.state.locking import lock_player
from app.services.validation.models import LLMResponse


@dataclass
class MemoryWrite:
    memory: Memory | None
    created: bool = False

    def payload(self):
        return {'memory_id': self.memory.id if self.memory else None, 'stored': self.created,
                'source_event_id': self.memory.source_event_id if self.memory else None}


def store_conversation(service, npc, conversation):
    db = service._db
    player = lock_player(db)
    try:
        source_id, event_id = conversation.id, conversation.source_event_id
    except (ObjectDeletedError, DetachedInstanceError) as exc:
        raise ValueError('Memory source no longer exists or must be reloaded') from exc
    source = db.scalar(select(Conversation).where(Conversation.id == source_id,
                       Conversation.source_event_id == event_id).execution_options(populate_existing=True))
    if (player is None or source is None or source.npc_id != npc.id or
            not source.source_event_id or source.game_scope != player.game_scope):
        raise ValueError('Memory source is missing, belongs to another recipient, or is from an old game')
    accepted = source.validated_output or {}
    if accepted.get('grounding_trace', {}).get('rejected'):
        return MemoryWrite(None)
    prior = db.scalar(select(Memory).where(Memory.game_scope == player.game_scope,
                      Memory.npc_id == npc.id, Memory.source_event_id == source.source_event_id))
    if prior:
        return MemoryWrite(prior)
    # Repeated consolidated claims still point to their first source; each
    # subsequent accepted conversation records the same memory identity.
    prior_id = accepted.get('memory_classification', {}).get('memory_id')
    prior = db.get(Memory, prior_id) if prior_id else None
    if prior and prior.npc_id == npc.id and prior.game_scope == player.game_scope:
        return MemoryWrite(prior)
    output = LLMResponse.model_validate({k: v for k, v in accepted.items() if k in LLMResponse.model_fields})
    outcome = accepted.get('behavior_trace', {}).get('verified_outcome', {})
    transfer = outcome.get('transfer')
    verified_transfer = bool(transfer and transfer.get('item') == output.item
                             and transfer.get('action') == output.action
                             and transfer.get('source_before', 0) - transfer.get('source_after', 0) == 1
                             and transfer.get('destination_after', 0) - transfer.get('destination_before', 0) == 1)
    if output.action in {'give_item', 'receive_item'} and not verified_transfer:
        raise ValueError('Transfer memory requires executed ownership/count evidence')
    decision = classify(source.player_input, output, grounded=verified_transfer,
                        quest_before=outcome.get('quest_before'), quest_after=outcome.get('quest_after'),
                        pending_before=outcome.get('pending_before'), pending_after=outcome.get('pending_after'))
    if outcome.get('reward') == 'bow':
        before = outcome.get('inventory_before', {}).get('player', [])
        after = outcome.get('inventory_after', {}).get('player', [])
        if outcome.get('quest_before') != 'crafting' or outcome.get('quest_after') != 'completed' or after.count('bow') - before.count('bow') != 1:
            raise ValueError('Completion memory requires verified reward evidence')
        decision = MemoryDecision(1., 'quest_completion', 'Authoritative timed reward executed.',
                                  'Bow quest completed. Craftsman gave the player one bow.')
    if not decision.important:
        return MemoryWrite(None)
    metadata = decision.payload()
    row = service.store_memory(npc, decision.event, decision.importance, output.emotion,
        event_type=decision.category, quest_id='get_bow' if decision.category.startswith('quest_') else None,
        game_scope=source.game_scope, source_event_id=source.source_event_id,
        source_conversation_id=source.id, epistemic_status=metadata['epistemic_status'],
        authority=metadata['authority'], claim_text=decision.claim_text)
    if row is None:
        # Consolidation preserves the first provenance and original text.
        from app.services.memory.service import duplicate_key
        row = db.scalar(select(Memory).where(Memory.npc_id == npc.id, Memory.game_scope == source.game_scope,
                        Memory.lifecycle == 'active', Memory.duplicate_key == duplicate_key(decision.event, decision.category, None)))
        return MemoryWrite(row)
    if decision.retracts_claim:
        targets = list(db.scalars(select(Memory).where(Memory.npc_id == npc.id,
                       Memory.game_scope == source.game_scope, Memory.lifecycle == 'active',
                       Memory.epistemic_status == 'claim', Memory.event_type == 'preference')))
        for target in targets:
            if normalized_event(target.claim_text or '') == normalized_event(decision.retracts_claim):
                _retract(db, row, target)
    return MemoryWrite(row, True)


def _retract(db, new, old):
    """Reuse pure reconciliation for an explicitly identified exact preference."""
    version = PolicyVersion(policy_id='memory-reconciliation', version='1')
    envelope = dict(schema_version=1, trace_id=new.source_event_id, game_id='single-player',
                    timeline_id=new.game_scope, npc_id=str(new.npc_id), actor_id='player:1',
                    created_at=datetime.now(timezone.utc), policy_versions=(version,))
    def record(row):
        source = 'conversation:' + str(row.source_conversation_id)
        return MemoryRecord(**envelope, record_id='memory:' + str(row.id), causation_id=source,
                            source_ids=(source,), memory_id=str(row.id), subject_id='player:1',
                            predicate='explicit_preference', object_text=row.claim_text or row.event,
                            status=row.epistemic_status, authority=row.authority, confidence=.5,
                            occurred_at=row.timestamp.replace(tzinfo=timezone.utc))
    new_record = record(new)
    related = RelatedRecords(**envelope, record_id='related:' + str(old.id), causation_id=new_record.record_id,
                             source_ids=(new_record.record_id,), records=(record(old),))
    policy = ReconciliationPolicy(**envelope, record_id='policy:memory-reconciliation:1',
                causation_id=new_record.record_id, source_ids=(new_record.record_id,), policy=version,
                authoritative_statuses=('fact',), allow_claim_consolidation=True)
    plan = reconcile(new_record, related, policy, record_id='reconciliation:' + str(new.id))
    if not isinstance(plan, ReconciliationPlan):
        raise ValueError(plan.public_message)
    if any(link.action == ReconciliationAction.MARK_RETRACTED for link in plan.links):
        from app.memory.lifecycle import MemoryLifecycleState
        old.lifecycle = MemoryLifecycleState.RETRACTED.value
        old.superseded_by_id = new.id
        new.correction_of_id = old.id
        db.flush()
