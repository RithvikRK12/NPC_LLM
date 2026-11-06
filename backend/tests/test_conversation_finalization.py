"""Publication prechecks plus durable Finalizer/SQL publication acceptance."""
import importlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from sqlalchemy import event, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.conversation_state import (
    CharacterCanon, ConversationMemoryRevision, ConversationOperation,
    ConversationStream, ConversationTurn, PendingInteraction,
)
from app.models.player import Player
from app.services.conversation.adapters.persistence import SQLTurnStore

from app.services.conversation import contracts as c

try:
    finalization = importlib.import_module('app.services.conversation.finalization')
except ModuleNotFoundError as exc:
    if exc.name != 'app.services.conversation.finalization':
        raise
    finalization = None


def error(turn, code='EVIDENCE_CHANGED', retryable=True):
    return c.ConversationError(code=code, stage='publication', retryable=retryable,
        turn=turn, safe_detail='Publication cannot use this snapshot.')


def source(kind, identity, revision=0):
    return c.SourceRef(kind=kind, source_id=identity, revision=revision,
        game_scope='run:1', npc_id=1, attribution='server', visibility='public')


def reply(text='A harbor story.', dependencies=()):
    return c.AssembledReply(text_id='final:1', final_text=text, beats=(text,),
        segment_spans={}, evidence_dependencies=dependencies, candidate_continuity_changes=())


def plan(turn, *, canon=(), transitions=(), writes=(), revisions=None):
    return c.ContinuityPlan(turn=turn, canon_changes=canon,
        memory_plan=c.MemoryPlan(turn=turn, writes=writes),
        interaction_plan=c.InteractionPlan(turn=turn, transitions=transitions,
            consent_bindings=(), clarification=None),
        expected_revisions=c.RevisionSet(resources=revisions or {}))


class PublicationStore:
    """Only models the frozen commit contract; no SQL or continuity writes.

    Rechecks use authoritative fixture state under a simulated writer boundary.
    A successful call supplies a scripted final projection, not durable proof.
    """

    def __init__(self, turn):
        self.turn = turn
        self.key = turn.key
        self.fence = 1
        self.sequence = turn.sequence
        self.sources = {}
        self.revisions = c.RevisionSet(resources={})
        self.canon = {}
        self.interactions = {}
        self.memories = {}
        self.receipts = ()
        self.locked = False
        self.attempts = []
        self.forced_error = None

    def commit(self, turn, fence, assembled, continuity):
        self.locked = True
        self.attempts.append((turn, fence, assembled, continuity))
        try:
            if self.key.game_scope != turn.key.game_scope:
                return error(turn, 'STALE_SCOPE', False)
            if self.key != turn.key:
                return error(turn, 'STALE_EPOCH', False)
            if turn != self.turn or fence != self.fence or turn.sequence != self.sequence:
                return error(turn, 'LEASE_LOST')
            if self.forced_error is not None:
                return self.forced_error
            if any(self.sources.get((dep.kind, dep.source_id)) != dep
                   for dep in assembled.evidence_dependencies):
                return error(turn)
            try:
                continuity.validate_revisions(self.revisions)
                continuity.interaction_plan.validate_current(self.interactions)
                continuity.memory_plan.validate_current(self.memories)
                for change in continuity.canon_changes:
                    head = self.canon.get(change.canon_id)
                    if change.kind == 'add':
                        if change.expected_revision != 0 or head is not None or any(
                                (record.subject, record.predicate) == (change.subject, change.predicate)
                                for record in self.canon.values()):
                            raise ValueError('canon addition collided')
                    elif head is None or head.revision != change.expected_revision:
                        raise ValueError('canon head changed')
            except ValueError:
                return error(turn)
            return c.FinalTurnResult(schema_version=1, turn=turn,
                final_dialogue=assembled.final_text, dialogue_beats=assembled.beats,
                response_origin='fallback', degradation_reason='test_fixture',
                receipt_refs=self.receipts, state_projection={},
                state_revisions=self.revisions, diagnostic_ref=None)
        finally:
            self.locked = False


class FinalizationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(finalization, 'T01 finalization facade is absent')
        self.turn = c.TurnRef(turn_id='turn:2', request_id='request:2', sequence=2,
            key=c.ConversationKey(game_scope='run:1', npc_id=1, epoch=0))
        self.store = PublicationStore(self.turn)

    def commit(self, assembled=None, continuity=None, **options):
        return finalization.Finalizer(self.store, **options).commit(
            self.turn, 1, assembled or reply(), continuity or plan(self.turn))

    def test_exact_final_text_beats_and_prevalidated_plan_reach_store(self):
        assembled = reply('A🙂éZ')
        continuity = plan(self.turn)
        result = self.commit(assembled, continuity)
        self.assertIsInstance(result, c.FinalTurnResult)
        self.assertEqual(result.final_dialogue, 'A🙂éZ')
        self.assertEqual(result.dialogue_beats, ('A🙂éZ',))
        self.assertEqual(self.store.attempts, [(self.turn, 1, assembled, continuity)])

    def test_active_scope_epoch_fence_and_stream_position_fail_without_refresh(self):
        for changed, value, code in (
                ('key', self.turn.key.model_copy(update={'game_scope': 'run:2'}), 'STALE_SCOPE'),
                ('key', self.turn.key.model_copy(update={'epoch': 1}), 'STALE_EPOCH'),
                ('fence', 2, 'LEASE_LOST'), ('sequence', 1, 'LEASE_LOST')):
            with self.subTest(changed=changed, value=value):
                self.store = PublicationStore(self.turn)
                setattr(self.store, changed, value)
                def forbidden(*args):
                    self.fail('identity/ownership failures cannot request regeneration')
                self.assertEqual(self.commit(refresh=forbidden).code, code)

    def test_invalid_turn_plan_fence_and_final_span_never_reach_store(self):
        other = self.turn.model_copy(update={'turn_id': 'other:turn'})
        change = c.AddCanonChange(kind='add', canon_id='canon:1', expected_revision=0,
            subject='npc:1', predicate='story', content='story', category='history',
            origin='generated', authority='narrative_only',
            supporting_span=c.TextSpan(text_id='another:final', start=0, end=5))
        for fence, continuity in ((0, plan(self.turn)), (True, plan(self.turn)),
                                  (1, plan(other)), (1, plan(self.turn, canon=(change,)))):
            with self.subTest(fence=fence, continuity=continuity):
                result = finalization.Finalizer(self.store).commit(self.turn, fence, reply(), continuity)
                self.assertEqual(result.code, 'INVALID_INPUT')
        self.assertEqual(self.store.attempts, [])

    def test_out_of_scope_or_private_speech_sources_never_reach_store(self):
        dependency = source('activity', 'activity:1')
        for updates in ({'game_scope': 'run:2'}, {'npc_id': 2}, {'visibility': 'server_private'}):
            with self.subTest(updates=updates):
                result = self.commit(reply(dependencies=(dependency.model_copy(update=updates),)))
                self.assertEqual(result.code, 'INVALID_INPUT')
        self.assertEqual(self.store.attempts, [])

    def test_exact_evidence_is_checked_even_when_revision_plan_is_empty(self):
        original = source('inventory', 'inventory:wood', 1)
        for current in (None, original.model_copy(update={'revision': 2}),
                        original.model_copy(update={'attribution': 'another:source'})):
            with self.subTest(current=current):
                self.store.sources = {} if current is None else {('inventory', 'inventory:wood'): current}
                self.assertEqual(self.commit(reply(dependencies=(original,))).code, 'EVIDENCE_CHANGED')

    def test_unrelated_revision_and_evidence_churn_does_not_request_refresh(self):
        dependency = source('inventory', 'inventory:wood', 1)
        self.store.sources = {('inventory', 'inventory:wood'): dependency,
                              ('activity', 'unrelated:activity'): source('activity', 'unrelated:activity', 99)}
        self.store.revisions = c.RevisionSet(resources={'inventory:wood': 1, 'unrelated:quest': 99})
        def forbidden(*args):
            self.fail('unrelated churn must not trigger refresh')
        result = self.commit(reply(dependencies=(dependency,)),
            plan(self.turn, revisions={'inventory:wood': 1}), refresh=forbidden)
        self.assertIsInstance(result, c.FinalTurnResult)
        self.assertEqual(len(self.store.attempts), 1)

    def test_named_revision_change_requests_revalidation(self):
        self.store.revisions = c.RevisionSet(resources={'inventory:wood': 2})
        self.assertEqual(self.commit(continuity=plan(self.turn,
            revisions={'inventory:wood': 1})).code, 'EVIDENCE_CHANGED')

    def canon_change(self):
        return c.ReviseCanonChange(kind='revise', canon_id='canon:1', expected_revision=1,
            subject='npc:1', predicate='story', content='A harbor story.', category='history',
            origin='generated', authority='narrative_only', correction_link='correction:1',
            supporting_span=c.TextSpan(text_id='final:1', start=0, end=14))

    def test_changed_canon_head_rejects_an_earlier_revision_plan(self):
        self.store.canon['canon:1'] = c.CanonRecord(canon_id='canon:1', revision=2,
            game_scope='run:1', npc_id=1, subject='npc:1', predicate='story', content='old story',
            category='history', origin='generated', authority='narrative_only', status='active',
            supersedes_revision=1, introduced_turn_id='turn:1',
            accepted_claim_evidence=c.TextSpan(text_id='final:old', start=0, end=9))
        self.assertEqual(self.commit(continuity=plan(self.turn,
            canon=(self.canon_change(),))).code, 'EVIDENCE_CHANGED')

    def test_fulfilled_interaction_invalidates_stale_reactivation(self):
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/contracts-t02-valid.json').read_text())['pending']
        active = c.PendingInteraction.model_validate(raw)
        fulfilled = active.model_copy(update={'revision': 2, 'status': 'fulfilled',
            'status_reason': 'operation_committed'})
        self.store.interactions = {active.interaction_id: fulfilled}
        transition = c.InteractionTransition(expected_revision=1,
            replacement=active.model_copy(update={'revision': 2}))
        result = self.commit(continuity=plan(self.turn, transitions=(transition,)))
        self.assertEqual(result.code, 'EVIDENCE_CHANGED')
        self.assertEqual(self.store.interactions[active.interaction_id].status, 'fulfilled')

    def test_progress_refresh_runs_outside_lock_and_keeps_historical_receipt(self):
        historical = source('operation_receipt', 'receipt:1')
        old_activity = source('activity', 'activity:inspection', 1)
        self.store.sources = {('operation_receipt', 'receipt:1'): historical,
            ('activity', 'activity:inspection'): old_activity.model_copy(update={'revision': 2})}
        self.store.receipts = ('receipt:1',)
        original = reply('I am inspecting the ship.', (historical, old_activity))
        refreshes = []
        def refresh(turn, assembled, continuity, conflict):
            self.assertFalse(self.store.locked, 'provider/semantic refresh ran under writer lock')
            refreshes.append(conflict.code)
            self.assertEqual(assembled, original)
            self.assertEqual(turn, self.turn)
            return reply('I accepted the inspection.', (historical,)), plan(turn)
        result = self.commit(original, refresh=refresh, max_refreshes=1)
        self.assertEqual(result.final_dialogue, 'I accepted the inspection.')
        self.assertEqual(result.receipt_refs, ('receipt:1',))
        self.assertEqual(refreshes, ['EVIDENCE_CHANGED'])
        self.assertEqual(len(self.store.attempts), 2)

    def test_persistent_evidence_churn_returns_recoverable_conflict_at_budget(self):
        stale = source('activity', 'activity:inspection', 1)
        def refresh(turn, assembled, continuity, conflict):
            self.assertFalse(self.store.locked)
            return assembled, continuity
        result = self.commit(reply(dependencies=(stale,)), refresh=refresh, max_refreshes=2)
        self.assertEqual(result.code, 'EVIDENCE_CHANGED')
        self.assertTrue(result.retryable)
        self.assertEqual(len(self.store.attempts), 3)

    def test_refresh_failure_preserves_typed_deadline_result(self):
        deadline = error(self.turn, 'DEADLINE_EXCEEDED')
        def refresh(*args):
            return deadline
        result = self.commit(reply(dependencies=(source('activity', 'activity:1'),)), refresh=refresh)
        self.assertIs(result, deadline)
        self.assertEqual(len(self.store.attempts), 1)

    def test_refreshed_reply_and_plan_are_prevalidated_before_another_attempt(self):
        other = self.turn.model_copy(update={'turn_id': 'other:turn'})
        def refresh(*args):
            return reply(), plan(other)
        result = self.commit(reply(dependencies=(source('activity', 'activity:1'),)), refresh=refresh)
        self.assertEqual(result.code, 'INVALID_INPUT')
        self.assertEqual(len(self.store.attempts), 1)

    def test_nonretryable_evidence_and_uncertain_storage_errors_do_not_refresh(self):
        for code, retryable in (('EVIDENCE_CHANGED', False), ('COMMIT_UNCERTAIN', True),
                                ('STORAGE_UNAVAILABLE', True), ('TURN_INVALIDATED', False)):
            with self.subTest(code=code, retryable=retryable):
                failure = error(self.turn, code, retryable)
                self.store.forced_error = failure
                def forbidden(*args):
                    self.fail('this failure must be recovered without regeneration')
                self.assertIs(self.commit(refresh=forbidden), failure)

    def test_zero_refresh_budget_returns_original_conflict(self):
        def forbidden(*args):
            self.fail('refresh budget exhausted')
        result = self.commit(reply(dependencies=(source('activity', 'activity:1'),)),
            refresh=forbidden, max_refreshes=0)
        self.assertEqual(result.code, 'EVIDENCE_CHANGED')
        self.assertEqual(len(self.store.attempts), 1)

    def test_refresh_budget_requires_nonnegative_strict_integer(self):
        for budget in (-1, True, 1.0):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                finalization.Finalizer(self.store, max_refreshes=budget)


class DurableFinalizationTests(unittest.TestCase):
    """Use the real store, writer transactions and isolated database fixture."""

    def setUp(self):
        from test_conversation_persistence_lifecycle import SQLPublicationLifecycleTests
        self.fixture = SQLPublicationLifecycleTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.engine = self.fixture.fixture.engine
        self.store = self.fixture.store
        self.lease = self.fixture.submit_and_claim()

    def publication(self):
        turn = self.lease.turn
        assembled = c.AssembledReply(text_id='final:durable',
            final_text='Harbor🙂 é.\nThe tide returns. ',
            beats=('Harbor🙂 é.\n', 'The tide returns. '), segment_spans={},
            evidence_dependencies=(), candidate_continuity_changes=())
        canon = c.AddCanonChange(kind='add', canon_id='canon:harbor', expected_revision=0,
            subject='npc:1', predicate='story', content='Harbor🙂 é.', category='history',
            origin='generated', authority='narrative_only',
            supporting_span=c.TextSpan(text_id=assembled.text_id, start=0, end=10))
        memory = c.MemoryRecord(memory_id='memory:harbor', game_scope='run:1', npc_id=1,
            epoch=0, kind='recollection', attributed_subject='npc:1', content='Harbor🙂 é.',
            uncertainty='tentative', sources=(c.SourceRef(kind='final_speech',
                source_id=assembled.text_id, revision=0, game_scope='run:1', npc_id=1,
                attribution='npc:1', visibility='npc_private'),), status='active', revision=0)
        interaction = c.PendingInteraction(interaction_id='interaction:harbor', key=turn.key,
            kind='clarification', originating_turn=turn,
            target=c.TargetReference(reference_id='npc:1', entity_kind='npc', entity_id='1'),
            item=None, quantity=None, question_text=assembled.final_text,
            question_id='question:harbor', question_turn_id=turn.turn_id,
            required_response_kind='clarification', precondition_fingerprint='terms:harbor',
            revision=0, status='active', status_reason=None)
        continuity = plan(turn, canon=(canon,),
            writes=(c.MemoryWrite(expected_revision=None, record=memory, correction_link=None),),
            transitions=(c.InteractionTransition(expected_revision=None, replacement=interaction),))
        self.assertIsInstance(self.store.save_reply(turn, self.lease.fence, assembled), c.RecoveredReply)
        return assembled, continuity

    def commit(self, assembled, continuity, **options):
        return finalization.Finalizer(self.store, **options).commit(
            self.lease.turn, self.lease.fence, assembled, continuity)

    def assert_unpublished(self):
        with Session(self.engine) as db:
            self.assertEqual(list(db.scalars(select(Conversation))), [])
            self.assertEqual(list(db.scalars(select(CharacterCanon))), [])
            self.assertEqual(list(db.scalars(select(ConversationMemoryRevision))), [])
            self.assertEqual(list(db.scalars(select(PendingInteraction))), [])
            row = db.get(ConversationTurn, self.lease.turn.turn_id)
            self.assertEqual(row.phase, 'finalizing')
            self.assertNotIn('final_result', row.payload)
            self.assertIsNone(row.final_result_id)
            self.assertFalse(db.get(ConversationStream, ('run:1', 1)).summary_dirty)

    def test_atomic_publication_and_restart_replay_keep_exact_utf8_speech_and_beats(self):
        assembled, continuity = self.publication()
        result = self.commit(assembled, continuity)
        self.assertIsInstance(result, c.FinalTurnResult)
        expected = 'Harbor🙂 é.\nThe tide returns. '
        self.assertEqual(result.final_dialogue.encode('utf-8'), expected.encode('utf-8'))
        self.assertEqual(result.dialogue_beats, ('Harbor🙂 é.\n', 'The tide returns. '))
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Conversation.final_dialogue)), expected)
            self.assertEqual(db.scalar(select(CharacterCanon.content)), 'Harbor🙂 é.')
            memory = db.scalar(select(ConversationMemoryRevision))
            self.assertEqual(memory.record_payload['record']['content'], 'Harbor🙂 é.')
            self.assertEqual(memory.record_payload['introduced_turn_id'], self.lease.turn.turn_id)
            self.assertEqual(db.scalar(select(PendingInteraction.status)), 'active')
            row = db.get(ConversationTurn, self.lease.turn.turn_id)
            self.assertEqual((row.phase, row.final_result_id), ('finalized', 'final:durable'))
            self.assertEqual(row.payload['final_result']['dialogue_beats'],
                ['Harbor🙂 é.\n', 'The tide returns. '])
        restarted = SQLTurnStore(self.engine, clock=self.fixture.fixture.clock)
        # A delivery retry must not derive speech from a new valid caller plan,
        # current resource revisions, or an expired worker lease.
        from datetime import timedelta
        self.fixture.fixture.clock.now += timedelta(seconds=30)
        with Session(self.engine) as db:
            db.get(Player, 1).resource_revisions = {'world': 99}
            db.commit()
        replay = finalization.Finalizer(restarted).commit(self.lease.turn,
            self.lease.fence, reply('Changed caller prose.'), plan(self.lease.turn))
        self.assertEqual(replay.model_dump_json().encode('utf-8'), result.model_dump_json().encode('utf-8'))
        self.assertEqual(restarted.lookup(self.lease.turn.key,
            self.lease.turn.request_id).response, result)
        with Session(self.engine) as db:
            self.assertEqual(len(list(db.scalars(select(Conversation)))), 1)
            self.assertEqual(len(list(db.scalars(select(CharacterCanon)))), 1)
            self.assertEqual(len(list(db.scalars(select(ConversationMemoryRevision)))), 1)

    def test_failure_between_transcript_and_canon_rolls_back_entire_publication(self):
        assembled, continuity = self.publication()
        def fail_canon(mapper, connection, target):
            # The transcript has been flushed on this very transaction, proving
            # the injected error falls after a real transcript write.
            self.assertEqual(connection.scalar(select(Conversation.final_dialogue)),
                'Harbor🙂 é.\nThe tide returns. ')
            raise OperationalError('injected canon insert', {}, RuntimeError('T02 rollback'))
        event.listen(CharacterCanon, 'before_insert', fail_canon)
        try:
            result = self.commit(assembled, continuity)
        finally:
            event.remove(CharacterCanon, 'before_insert', fail_canon)
        self.assertIsInstance(result, c.ConversationError)
        self.assertIn(result.code, {'STORAGE_UNAVAILABLE', 'COMMIT_UNCERTAIN'})
        self.assertTrue(result.retryable)
        self.assert_unpublished()
        self.assertIsInstance(self.commit(assembled, continuity), c.FinalTurnResult)

    def test_refresh_replacement_publishes_after_sql_transaction_is_released(self):
        assembled = reply('The tide is rising.', (source('inventory', 'world', 1),))
        continuity = plan(self.lease.turn)
        self.store.save_reply(self.lease.turn, self.lease.fence, assembled)
        def refresh(turn, previous, previous_plan, conflict):
            self.assertEqual(self.engine.pool.checkedout(), 0)
            # Resolving new evidence and rendering replacement prose occurs
            # outside the writer transaction, including any provider work.
            return reply('The tide has turned.', (source('inventory', 'world', 0),)), plan(turn)
        result = self.commit(assembled, continuity, refresh=refresh)
        self.assertIsInstance(result, c.FinalTurnResult)
        self.assertEqual(result.final_dialogue, 'The tide has turned.')
        recovered = self.store.recover(self.lease.turn)
        self.assertEqual(recovered.assembled_reply.reply.final_text, 'The tide has turned.')
        self.assertEqual(self.store.lookup(self.lease.turn.key,
            self.lease.turn.request_id).response, result)

    def test_persistent_sql_evidence_churn_never_publishes_or_marks_terminal(self):
        assembled, continuity = self.publication()
        assembled = assembled.model_copy(update={'evidence_dependencies': (source('inventory', 'world', 1),)})
        self.store.save_reply(self.lease.turn, self.lease.fence, assembled)
        refreshes = []
        def refresh(turn, previous, previous_plan, conflict):
            self.assertEqual(self.engine.pool.checkedout(), 0)
            refreshes.append(conflict.code)
            return previous, previous_plan
        result = self.commit(assembled, continuity, refresh=refresh, max_refreshes=2)
        self.assertEqual((result.code, result.retryable), ('EVIDENCE_CHANGED', True))
        self.assertEqual(refreshes, ['EVIDENCE_CHANGED', 'EVIDENCE_CHANGED'])
        self.assert_unpublished()


class OperationFulfilledFinalizationTests(unittest.TestCase):
    def setUp(self):
        from test_conversation_persistence import SQLReceiptTransactionTests
        self.fixture = SQLReceiptTransactionTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.engine = self.fixture.engine
        self.store = self.fixture.store

    def fulfilled(self):
        lease, decision, interaction = self.fixture.consent_ready(kind='item_negotiation')
        receipt = self.store.execute_once(lease.turn, lease.fence, decision)
        self.assertIsInstance(receipt, c.OperationReceipt)
        self.assertEqual(receipt.outcome, 'completed')
        assembled = reply('You have the wood.', (c.SourceRef(kind='operation_receipt',
            source_id=receipt.receipt_id, revision=receipt.argument_digest, game_scope='run:1', npc_id=2,
            attribution='server', visibility='public'),))
        self.store.save_reply(lease.turn, lease.fence, assembled)
        return lease, receipt, interaction, assembled

    def test_stale_preoperation_plan_cannot_reactivate_committed_negotiation(self):
        lease, receipt, interaction, assembled = self.fulfilled()
        stale = plan(lease.turn, transitions=(c.InteractionTransition(expected_revision=1,
            replacement=interaction.model_copy(update={'revision': 2})),))
        conflicts = []
        def refresh(turn, previous, previous_plan, conflict):
            self.assertEqual(self.engine.pool.checkedout(), 0)
            conflicts.append(conflict.code)
            with Session(self.engine) as db:
                self.assertEqual(db.get(PendingInteraction, interaction.interaction_id).status, 'fulfilled')
            return previous, plan(turn)
        with patch.object(SQLTurnStore, 'execute_once', side_effect=AssertionError('publication reexecuted operation')):
            result = finalization.Finalizer(self.store, refresh=refresh).commit(
                lease.turn, lease.fence, assembled, stale)
        self.assertIsInstance(result, c.FinalTurnResult)
        self.assertEqual(conflicts, ['EVIDENCE_CHANGED'])
        self.assertEqual(result.receipt_refs, (receipt.receipt_id,))
        self.assertEqual(self.store.lookup_receipt(lease.turn).value, receipt)
        with Session(self.engine) as db:
            current = db.get(PendingInteraction, interaction.interaction_id)
            self.assertEqual((current.status, current.revision), ('fulfilled', 2))
            self.assertEqual(current.payload['status_reason'], 'operation_committed')
            self.assertEqual(db.get(Player, 1).inventory.count('wood'), 2)
            self.assertEqual(len(list(db.scalars(select(ConversationOperation)))), 1)

    def test_matching_revision_cannot_reactivate_a_terminal_negotiation(self):
        lease, receipt, interaction, assembled = self.fulfilled()
        reactivation = plan(lease.turn, transitions=(c.InteractionTransition(expected_revision=2,
            replacement=interaction.model_copy(update={'revision': 3})),))
        result = finalization.Finalizer(self.store).commit(
            lease.turn, lease.fence, assembled, reactivation)
        self.assertIsInstance(result, c.ConversationError)
        self.assertEqual((result.code, result.retryable), ('EVIDENCE_CHANGED', True))
        with Session(self.engine) as db:
            self.assertEqual(db.get(PendingInteraction, interaction.interaction_id).status, 'fulfilled')
            self.assertIsNone(db.scalar(select(Conversation).where(Conversation.turn_id == lease.turn.turn_id)))
            self.assertEqual(db.get(ConversationTurn, lease.turn.turn_id).phase, 'finalizing')
        self.assertEqual(self.store.lookup_receipt(lease.turn).value, receipt)


if __name__ == '__main__':
    unittest.main()
