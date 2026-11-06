"""T02 frozen-value write/recovery protocols and bounded fake conformance."""
import importlib
import inspect
import json
import hashlib
from pathlib import Path
import unittest
from typing import get_type_hints

from app.services.conversation import contracts as c, ports as p
from conversation_store_conformance import (
    AdmissionCases, AttemptCases, ClaimCases, LifecycleSummaryCases, OperationCases, PublicationCases,
)

try:
    fakes = importlib.import_module('conversation_store_fakes')
except ModuleNotFoundError as exc:
    if exc.name != 'conversation_store_fakes':
        raise
    fakes = None


class FrozenWriteProtocolTests(unittest.TestCase):
    def test_remaining_protocols_expose_frozen_envelopes(self):
        signatures = [
            ('TurnStore', 'claim_next', {'key': c.ConversationKey, 'worker_id': str,
                'lease_policy': c.LeasePolicy, 'return': c.OptionalResult[c.TurnLease]}),
            ('TurnStore', 'recover', {'turn': c.TurnRef, 'return': c.TurnRecovery | c.ConversationError}),
            ('OperationGateway', 'lookup_receipt', {'turn': c.TurnRef,
                'return': c.OptionalResult[c.OperationReceipt]}),
            ('FinalizationStore', 'commit', {'turn': c.TurnRef, 'fence': int,
                'reply': c.AssembledReply, 'continuity_plan': c.ContinuityPlan,
                'return': c.FinalTurnResult | c.ConversationError}),
            ('LifecycleStore', 'clear', {'key': c.ConversationKey,
                'return': c.ClearResult | c.ConversationError}),
            ('LifecycleStore', 'new_game', {'expected_scope': str,
                'return': c.WorldResult | c.ConversationError}),
            ('SummaryStore', 'publish', {'summary': c.SummaryRecord, 'expected_revision': int | None,
                'return': c.SummaryRecord | c.ConversationError}),
        ]
        for interface, method, expected in signatures:
            with self.subTest(interface=interface, method=method):
                self.assertTrue(hasattr(p, interface), f'T02 {interface} is absent')
                self.assertTrue(hasattr(getattr(p, interface), method), f'T02 {method} is absent')
                self.assertEqual(get_type_hints(getattr(getattr(p, interface), method)), expected)

    def test_attempt_protocols_use_t04_shared_repair_and_recovery_values(self):
        for method in ('record_attempt','save_attempt_output'):
            self.assertTrue(hasattr(p.TurnStore, method), f'T02 {method} is absent')
            self.assertEqual(get_type_hints(getattr(p.TurnStore,method)), {
                'turn':c.TurnRef,'fence':int,'attempt':c.ProviderAttempt,
                'return':c.ProviderAttempt | c.ConversationError})
        self.assertTrue(hasattr(p.TurnStore,'save_reply'), 'T02 save_reply is absent')
        self.assertEqual(get_type_hints(p.TurnStore.save_reply), {
            'turn':c.TurnRef,'fence':int,'reply':c.AssembledReply,
            'return':c.RecoveredReply | c.ConversationError})

    def test_turn_store_declares_exact_submission_and_lookup_values(self):
        self.assertTrue(hasattr(p, 'TurnStore'), 'T02 TurnStore is absent')
        self.assertEqual(tuple(inspect.signature(p.TurnStore.submit).parameters), ('self', 'submission'))
        self.assertEqual(get_type_hints(p.TurnStore.submit), {
            'submission': c.TurnSubmission, 'return': c.TurnStatus | c.ConversationError})
        self.assertEqual(get_type_hints(p.TurnStore.lookup), {
            'key': c.ConversationKey, 'request_id': str,
            'return': c.TurnStatus | c.ConversationError})

    def test_operation_gateway_declares_fenced_typed_operation(self):
        self.assertTrue(hasattr(p, 'OperationGateway'), 'T02 OperationGateway is absent')
        self.assertEqual(tuple(inspect.signature(p.OperationGateway.execute_once).parameters),
                         ('self', 'turn', 'fence', 'decision'))
        self.assertEqual(get_type_hints(p.OperationGateway.execute_once), {
            'turn': c.TurnRef, 'fence': int, 'decision': c.ReadyToRecheck,
            'return': c.OperationReceipt | c.ConversationError})


class FakeWriteRepositoryTests(AdmissionCases, AttemptCases, ClaimCases, OperationCases,
                              PublicationCases, LifecycleSummaryCases, unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(fakes, 'T02 bounded fake repository is absent')
        self.repository = fakes.FakeConversationRepository()
        for method in ('claim_next', 'recover', 'pending', 'lookup_receipt', 'commit',
                       'clear', 'new_game', 'publish', 'lookup_summary', 'read_sources', 'dirty_keys',
                       'record_attempt','save_attempt_output','save_reply'):
            self.assertTrue(hasattr(self.repository, method), f'T02 fake {method} is absent')
        self.key = c.ConversationKey(game_scope='run:1', npc_id=1, epoch=0)
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/contracts-t02-valid.json').read_text())
        self.decision = c.ReadyToRecheck(kind='ready_to_recheck',
            operation=c.OperationCandidate.model_validate(raw['operation']), consent=None, checked_preconditions=())
        self.raw_receipt = raw['receipt']
        self.lease_policy = c.LeasePolicy(schema_version=1, policy_version='test:lease', lease_duration_seconds=20.0)

    def submission(self, request_id, message, key=None):
        return c.TurnSubmission(schema_version=1, request_id=request_id, key=key or self.key, player_message=message)

    def attempt_for(self, turn, fence, purpose, attempt_id='attempt:1', repair_kind=None):
        from datetime import datetime, timezone
        return c.ProviderAttempt(turn=turn,attempt_id=attempt_id,fence=fence,purpose=purpose,
            repair_kind=repair_kind,dispatched_at=datetime(2026,10,14,tzinfo=timezone.utc),
            status='dispatched',output=None)

    def persisted_attempt(self, attempt, changed=False):
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/contracts-t02-valid.json').read_text())['candidate']
        if changed:
            raw['source']['source_id'] = 'different:output'
        return c.ProviderAttempt.model_validate({**attempt.model_dump(mode='json'),
            'status':'output_persisted','output':raw})

    def advance_seconds(self, seconds):
        self.repository.scenario_advance_seconds(seconds)

    def set_revisions(self, key, revisions):
        self.repository.scenario_set_revisions(key, c.RevisionSet(resources=revisions))

    def publication_for(self, turn, text, add_canon=False, add_memory=False,
                        expected=None, stale_interaction=False):
        reply = c.AssembledReply(text_id=f'final:{turn.turn_id}', final_text=text,
            beats=(text,), segment_spans={}, evidence_dependencies=(), candidate_continuity_changes=())
        canon = ()
        if add_canon:
            canon = (c.AddCanonChange(kind='add', canon_id='canon:1', expected_revision=0,
                subject='npc:1', predicate='story', content=text, category='history',
                origin='generated', authority='narrative_only',
                supporting_span=c.TextSpan(text_id=reply.text_id,start=0,end=len(text))),)
        writes = ()
        if add_memory:
            record = c.MemoryRecord(memory_id='memory:1',game_scope=turn.key.game_scope,
                npc_id=turn.key.npc_id,epoch=turn.key.epoch,kind='player_report',
                attributed_subject='player',content='The player reports a harbor story.',uncertainty='unverified',
                sources=(c.SourceRef(kind='player_message',source_id=turn.turn_id,revision=0,
                    game_scope=turn.key.game_scope,npc_id=turn.key.npc_id,attribution='player',visibility='public'),),
                status='active',revision=0)
            writes = (c.MemoryWrite(expected_revision=None,record=record,correction_link=None),)
        transitions = ()
        if stale_interaction:
            raw = json.loads((Path(__file__).parent / 'fixtures/conversation/contracts-t02-valid.json').read_text())['pending']
            old = c.PendingInteraction.model_validate({**raw,'originating_turn':turn.model_dump(mode='json'),
                'key':turn.key.model_dump(mode='json'),'question_turn_id':turn.turn_id,
                'revision':2,'status':'fulfilled','status_reason':'operation_committed'})
            self.repository.scenario_seed_interaction(old)
            replacement = c.PendingInteraction.model_validate({**old.model_dump(mode='json'),
                'status':'cancelled','status_reason':'old_plan'})
            transitions = (c.InteractionTransition(expected_revision=1,replacement=replacement),)
        plan = c.ContinuityPlan(turn=turn,canon_changes=canon,
            memory_plan=c.MemoryPlan(turn=turn,writes=writes),
            interaction_plan=c.InteractionPlan(turn=turn,transitions=transitions,consent_bindings=(),clarification=None),
            expected_revisions=c.RevisionSet(resources=expected or {}))
        receipt = self.saved_receipt(turn)
        result = c.FinalTurnResult(schema_version=1,turn=turn,final_dialogue=text,dialogue_beats=(text,),
            response_origin='fallback',degradation_reason='test_fixture',
            receipt_refs=(receipt.receipt_id,) if receipt is not None else (),
            state_projection={},state_revisions=c.RevisionSet(resources={}),diagnostic_ref=None)
        self.repository.scenario_seed_publication(turn,result)
        return reply, plan, result

    def summary_for(self, turn):
        memory = self.repository.scenario_memory('memory:1')
        revisions = c.RevisionSet(resources={f'turn:{turn.turn_id}':0,'memory:1':0})
        canonical = json.dumps(dict(revisions.resources),sort_keys=True,separators=(',',':'),ensure_ascii=False)
        return c.SummaryRecord(summary_id='summary:1',key=turn.key,
            source_range=c.SourceRange(first_sequence=turn.sequence,last_sequence=turn.sequence),
            source_revisions=revisions,source_revision_digest=hashlib.sha256(canonical.encode()).hexdigest(),
            entries=(c.SummaryEntry(memory=memory,source_turns=(turn,),correction_link=None),),revision=0)

    def fail_next_publication(self):
        self.repository.scenario_fail_next_publication()

    def transcript(self, turn):
        return self.repository.scenario_transcript(turn)

    def canon_count(self):
        return self.repository.scenario_canon_count()

    def memory_count(self):
        return self.repository.scenario_memory_count()

    def seed_canon_collision(self, turn, change):
        self.repository.scenario_seed_canon(turn, change)

    def interaction_status(self):
        return self.repository.scenario_interaction_status('interaction:1')

    def claim(self, turn, worker):
        return self.repository.scenario_claim(turn, worker)

    def expire_lease(self, turn):
        self.repository.scenario_expire_lease(turn)

    def receipt_for(self, turn):
        receipt = c.OperationReceipt.model_validate({**self.raw_receipt,
            'turn_id': turn.turn_id, 'game_scope': turn.key.game_scope, 'npc_id': turn.key.npc_id})
        self.repository.scenario_seed_outcome(turn, receipt)
        return receipt

    def fail_next_receipt(self):
        self.repository.scenario_fail_next_receipt()

    def simulate_clear(self, key):
        self.repository.scenario_clear(key)

    def restart(self):
        return self.repository.scenario_restart()

    def effect_count(self):
        return self.repository.scenario_effect_count()

    def has_recoverable_payload(self, turn):
        return self.repository.scenario_has_payload(turn)

    def saved_receipt(self, turn):
        return self.repository.scenario_receipt(turn)

    def test_fake_structurally_conforms_to_available_protocols(self):
        self.assertIsInstance(self.repository, p.TurnStore)
        self.assertIsInstance(self.repository, p.OperationGateway)
        self.assertIsInstance(self.repository, p.FinalizationStore)
        self.assertIsInstance(self.repository, p.LifecycleStore)
        self.assertIsInstance(self.repository, p.SummaryStore)

    def test_fake_claim_control_models_oldest_turn_and_independent_npcs(self):
        first = self.repository.submit(self.submission('request:1', 'first')).turn
        second = self.repository.submit(self.submission('request:2', 'second')).turn
        blocked = self.claim(second, 'worker:2')
        self.assertEqual(blocked.code, 'LEASE_LOST')
        self.assertEqual(self.claim(first, 'worker:1'), 1)
        other_key = self.key.model_copy(update={'npc_id': 2})
        other = self.repository.submit(c.TurnSubmission(schema_version=1,
            request_id='request:1', key=other_key, player_message='other NPC')).turn
        self.assertEqual(other.sequence, 1)
        self.assertEqual(self.claim(other, 'worker:other'), 1)
        self.assertEqual(self.claim(first, 'worker:competing').code, 'LEASE_LOST')


if __name__ == '__main__':
    unittest.main()
