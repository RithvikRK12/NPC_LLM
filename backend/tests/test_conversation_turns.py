"""Admission, ordered claim and recovery behavior against the reference store.

These deterministic cases prove delegation and scoped fake behavior, not SQL
atomicity, concurrent admission or crash durability.
"""
import importlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

from app.services.conversation import contracts as c
from conversation_store_fakes import FakeConversationRepository

try:
    TurnService = importlib.import_module('app.services.conversation.turns').TurnService
except ModuleNotFoundError as exc:
    if exc.name != 'app.services.conversation.turns':
        raise
    TurnService = None


class ObservedAdmissionStore:
    """Observe only the two T01 calls; inject typed infrastructure outcomes."""

    def __init__(self, repository):
        self.repository = repository
        self.calls = []
        self.fail_before_admission = False
        self.fail_after_admission = False

    def submit(self, submission):
        self.calls.append(('submit', submission))
        if self.fail_before_admission:
            self.fail_before_admission = False
            return c.ConversationError(code='STORAGE_UNAVAILABLE', stage='admission',
                retryable=True, turn=None, safe_detail='Admission is unavailable.')
        result = self.repository.submit(submission)
        if self.fail_after_admission and isinstance(result, c.TurnStatus):
            self.fail_after_admission = False
            return c.ConversationError(code='STORAGE_UNAVAILABLE', stage='admission',
                retryable=True, turn=result.turn, safe_detail='Resolve the admitted request.')
        return result

    def lookup(self, key, request_id):
        self.calls.append(('lookup', key, request_id))
        return self.repository.lookup(key, request_id)


class TurnServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(TurnService, 'T01 TurnService is not implemented')
        self.repository = FakeConversationRepository()
        self.store = ObservedAdmissionStore(self.repository)
        self.service = TurnService(self.store)
        self.key = c.ConversationKey(game_scope='run:1', npc_id=1, epoch=0)

    def submission(self, request_id='request:1', message='Hello.', key=None):
        return c.TurnSubmission(schema_version=1, request_id=request_id,
            key=self.key if key is None else key, player_message=message)

    def test_same_payload_replays_the_original_status_without_allocating_sequence(self):
        submission = self.submission()
        first = self.service.submit(submission)
        replay = self.service.submit(c.TurnSubmission.model_validate(submission.model_dump()))
        self.assertIsInstance(first, c.TurnStatus)
        self.assertEqual(replay, first)
        self.assertEqual(first.phase, 'queued')
        self.assertEqual(first.turn.sequence, 1)
        second = self.service.submit(self.submission('request:2', 'Next.'))
        self.assertEqual(second.turn.sequence, 2)
        self.assertEqual(self.repository.pending(self.key), (first, second))
        self.assertEqual([call[0] for call in self.store.calls], ['submit'] * 3)

    def test_changed_payload_conflicts_without_replacing_the_original(self):
        first = self.service.submit(self.submission(message='Hello.'))
        conflict = self.service.submit(self.submission(message='Hello. '))
        self.assertIsInstance(conflict, c.ConversationError)
        self.assertEqual(conflict.code, 'IDEMPOTENCY_CONFLICT')
        self.assertEqual(conflict.turn, first.turn)
        self.assertFalse(conflict.retryable)
        self.assertEqual(self.service.lookup(self.key, 'request:1'), first)
        self.assertEqual(self.repository.pending(self.key), (first,))

    def test_store_rejects_stale_scope_epoch_and_unknown_npc_before_admission(self):
        for key, code in (
            (c.ConversationKey(game_scope='old:run', npc_id=1, epoch=0), 'STALE_SCOPE'),
            (c.ConversationKey(game_scope='run:1', npc_id=1, epoch=1), 'STALE_EPOCH'),
            (c.ConversationKey(game_scope='run:1', npc_id=99, epoch=0), 'UNKNOWN_NPC'),
        ):
            with self.subTest(code=code):
                error = self.service.submit(self.submission(key=key))
                self.assertIsInstance(error, c.ConversationError)
                self.assertEqual(error.code, code)
                self.assertIsNone(error.turn)
        admitted = self.service.submit(self.submission())
        self.assertEqual(admitted.turn.sequence, 1)
        self.assertEqual([call[0] for call in self.store.calls], ['submit'] * 4)

    def test_same_request_id_is_independent_for_each_npc_stream(self):
        first = self.service.submit(self.submission())
        other_key = c.ConversationKey(game_scope='run:1', npc_id=2, epoch=0)
        other = self.service.submit(self.submission(message='Other NPC.', key=other_key))
        self.assertNotEqual(first.turn.turn_id, other.turn.turn_id)
        self.assertEqual((first.turn.sequence, other.turn.sequence), (1, 1))
        self.assertEqual(self.service.lookup(self.key, 'request:1'), first)
        self.assertEqual(self.service.lookup(other_key, 'request:1'), other)

    def test_separate_services_use_store_owned_sequence_after_restart(self):
        first = self.service.submit(self.submission())
        restarted = TurnService(self.repository.scenario_restart())
        replay = restarted.submit(self.submission())
        second = restarted.submit(self.submission('request:2', 'Next.'))
        third = self.service.submit(self.submission('request:3', 'Third.'))
        self.assertEqual(replay, first)
        self.assertEqual((first.turn.sequence, second.turn.sequence, third.turn.sequence), (1, 2, 3))

    def test_pending_lookup_calls_only_lookup_once_and_preserves_queue(self):
        pending = self.service.submit(self.submission())
        before = self.repository.pending(self.key)
        self.store.calls.clear()
        self.assertEqual(self.service.lookup(self.key, 'request:1'), pending)
        self.assertEqual(self.store.calls, [('lookup', self.key, 'request:1')])
        self.assertEqual(self.repository.pending(self.key), before)
        self.assertEqual(self.repository.scenario_effect_count(), 0)

    def test_final_lookup_and_resubmission_return_exact_durable_response(self):
        submission = self.submission()
        turn = self.service.submit(submission).turn
        fence = self.repository.scenario_claim(turn, 'worker:fixture')
        text = 'A durable reply.\nAll characters survive retry.'
        result = c.FinalTurnResult(schema_version=1, turn=turn, final_dialogue=text,
            dialogue_beats=('A durable reply.\n', 'All characters survive retry.'),
            response_origin='fallback', degradation_reason='fixture', receipt_refs=(),
            state_projection={}, state_revisions=c.RevisionSet(resources={}), diagnostic_ref=None)
        self.repository.scenario_seed_publication(turn, result)
        reply = c.AssembledReply(text_id='final:fixture', final_text=text,
            beats=result.dialogue_beats, segment_spans={}, evidence_dependencies=(),
            candidate_continuity_changes=())
        plan = c.ContinuityPlan(turn=turn, canon_changes=(),
            memory_plan=c.MemoryPlan(turn=turn, writes=()),
            interaction_plan=c.InteractionPlan(turn=turn, transitions=(), consent_bindings=(),
                clarification=None), expected_revisions=c.RevisionSet(resources={}))
        self.assertEqual(self.repository.commit(turn, fence, reply, plan), result)
        self.store.calls.clear()
        status = self.service.lookup(self.key, 'request:1')
        self.assertEqual(status.phase, 'finalized')
        self.assertEqual(status.response, result)
        self.assertEqual(self.store.calls, [('lookup', self.key, 'request:1')])
        self.assertEqual(self.service.submit(submission), status)
        self.assertEqual(self.repository.scenario_transcript(turn), text)
        self.assertEqual(self.repository.scenario_effect_count(), 0)

    def test_clear_lookup_and_same_payload_replay_return_erased_tombstone(self):
        submission = self.submission(message='Secret exchange.')
        admitted = self.service.submit(submission)
        self.repository.scenario_clear(self.key)
        self.store.calls.clear()
        status = self.service.lookup(self.key, 'request:1')
        self.assertEqual(status.turn, admitted.turn)
        self.assertEqual(status.phase, 'invalidated')
        self.assertIsNone(status.response)
        self.assertEqual(self.store.calls, [('lookup', self.key, 'request:1')])
        self.assertFalse(self.repository.scenario_has_payload(admitted.turn))
        self.assertEqual(self.service.submit(submission), status)
        self.assertEqual(self.service.submit(self.submission('request:new')).code, 'STALE_EPOCH')
        fresh_key = c.ConversationKey(game_scope='run:1', npc_id=1, epoch=1)
        fresh = self.service.submit(self.submission(key=fresh_key))
        self.assertNotEqual(fresh.turn, admitted.turn)
        self.assertEqual(fresh.turn.sequence, 1)

    def test_missing_lookup_does_not_admit_and_rejects_other_scopes(self):
        for key, code in (
            (self.key, 'INVALID_INPUT'),
            (c.ConversationKey(game_scope='old:run', npc_id=1, epoch=0), 'STALE_SCOPE'),
            (c.ConversationKey(game_scope='run:1', npc_id=1, epoch=1), 'STALE_EPOCH'),
        ):
            with self.subTest(code=code):
                self.store.calls.clear()
                result = self.service.lookup(key, 'request:missing')
                self.assertIsInstance(result, c.ConversationError)
                self.assertEqual(result.code, code)
                self.assertEqual(self.store.calls, [('lookup', key, 'request:missing')])
        self.assertEqual(self.repository.pending(self.key), ())
        self.assertEqual(self.service.submit(self.submission()).turn.sequence, 1)

    def test_failure_before_admission_stays_typed_and_same_id_can_be_retried(self):
        self.store.fail_before_admission = True
        error = self.service.submit(self.submission())
        self.assertIsInstance(error, c.ConversationError)
        self.assertEqual((error.code, error.stage, error.retryable, error.turn),
            ('STORAGE_UNAVAILABLE', 'admission', True, None))
        self.assertEqual(len(self.store.calls), 1)
        self.assertEqual(self.repository.pending(self.key), ())
        status = self.service.submit(self.submission())
        self.assertEqual((status.phase, status.turn.sequence), ('queued', 1))

    def test_failure_after_admission_is_not_retried_or_finalized_and_lookup_is_pending(self):
        self.store.fail_after_admission = True
        error = self.service.submit(self.submission())
        self.assertIsInstance(error, c.ConversationError)
        self.assertEqual((error.code, error.retryable), ('STORAGE_UNAVAILABLE', True))
        self.assertIsNotNone(error.turn)
        self.assertEqual(len(self.store.calls), 1)
        pending = self.service.lookup(self.key, 'request:1')
        self.assertEqual(pending.turn, error.turn)
        self.assertEqual(pending.phase, 'queued')
        self.assertIsNone(pending.response)
        self.assertEqual(self.service.submit(self.submission()), pending)
        self.assertEqual(self.repository.pending(self.key), (pending,))


class TurnClock:
    def __init__(self):
        self.now = datetime(2026, 10, 14, tzinfo=timezone.utc)

    def utc_now(self):
        return self.now

    def monotonic(self):
        return 0.0


class ObservedRecoveryStore:
    """Keep reference semantics; inject one typed outage at a port boundary."""

    def __init__(self, repository):
        self.repository = repository
        self.calls = []
        self.fail_next = None
        self.fail_after = None
        self.claim_override = None

    def __getattr__(self, name):
        method = getattr(self.repository, name)

        def call(*args):
            self.calls.append((name, *args))
            if name == self.fail_next or name == self.fail_after:
                if name == self.fail_after:
                    method(*args)
                self.fail_next = None
                self.fail_after = None
                turn = args[0] if isinstance(args[0], c.TurnRef) else None
                error = c.ConversationError(code='STORAGE_UNAVAILABLE', stage=name,
                    retryable=True, turn=turn, safe_detail='Retry durable work.')
                return c.OptionalResult.failure(error) if name == 'claim_next' else error
            if name == 'claim_next' and self.claim_override is not None:
                return c.OptionalResult.success(self.claim_override)
            return method(*args)

        return call


class TurnRecoveryServiceTests(unittest.TestCase):
    def setUp(self):
        for name in ('claim_next', 'pending', 'recover', 'record_attempt',
                     'save_attempt_output', 'save_reply'):
            self.assertTrue(hasattr(TurnService, name), f'T02 TurnService.{name} is absent')
        self.repository = FakeConversationRepository()
        self.store = ObservedRecoveryStore(self.repository)
        self.clock = TurnClock()
        self.service = TurnService(self.store, clock=self.clock)
        self.key = c.ConversationKey(game_scope='run:1', npc_id=1, epoch=0)
        self.policy = c.LeasePolicy(schema_version=1, policy_version='test:lease',
            lease_duration_seconds=20)
        self.fixture = json.loads((Path(__file__).parent /
            'fixtures/conversation/contracts-t02-valid.json').read_text())

    def submit(self, request_id='request:1', key=None):
        return self.service.submit(c.TurnSubmission(schema_version=1,
            request_id=request_id, key=key or self.key, player_message='Hello.')).turn

    def claim(self, worker='worker:1', key=None, service=None):
        return (service or self.service).claim_next(key or self.key, worker, self.policy)

    def advance(self, seconds):
        self.clock.now += timedelta(seconds=seconds)
        self.repository.scenario_advance_seconds(seconds)

    def restart(self):
        return TurnService(self.repository.scenario_restart(), clock=self.clock)

    def attempt(self, lease, purpose='proposal', repair_kind=None, attempt_id='attempt:1'):
        return c.ProviderAttempt(turn=lease.turn, attempt_id=attempt_id, fence=lease.fence,
            purpose=purpose, repair_kind=repair_kind, dispatched_at=self.clock.utc_now(),
            status='dispatched', output=None)

    def output(self, attempt):
        # A proposal has no operational authority; ordinary speech suffices here.
        if attempt.purpose == 'proposal' or attempt.repair_kind == 'proposal_format':
            value = c.TurnProposal(concerns=(), references=(), reports=(),
                correction_candidates=(), operation_candidates=(), interaction_links=(),
                reply=(c.ExpressiveSegment(kind='expressive', segment_id='speech:1',
                    text='Hello.', addressed_concern_ids=()),), canon_candidates=())
        else:
            value = c.CandidateReply.model_validate(self.fixture['candidate'])
        return c.ProviderAttempt.model_validate({**attempt.model_dump(),
            'status': 'output_persisted', 'output': value})

    def test_claim_oldest_once_and_busy_does_not_bypass_later_turn(self):
        first, second = self.submit(), self.submit('request:2')
        self.store.calls.clear()
        lease = self.claim().value
        self.assertEqual((lease.turn, lease.fence, lease.phase), (first, 1, 'preparing'))
        self.assertEqual(self.store.calls, [('claim_next', self.key, 'worker:1', self.policy)])
        busy = self.claim('worker:2')
        self.assertEqual((busy.status, busy.value), ('success', None))
        self.assertEqual(tuple(status.turn for status in self.service.pending(self.key)), (first, second))

    def test_empty_and_invalid_scope_claims_are_distinct(self):
        self.assertEqual((self.claim().status, self.claim().value), ('success', None))
        old_key = self.key.model_copy(update={'game_scope': 'old:run'})
        result = self.claim(key=old_key)
        self.assertEqual((result.status, result.error.code), ('failure', 'STALE_SCOPE'))
        self.assertFalse(result.error.retryable)

    def test_claim_without_injected_clock_uses_store_ownership_without_host_time(self):
        turn = self.submit()
        # Poison the former host-time source: this case must remain independent
        # of the machine's date when using an adapter's own deterministic clock.
        module = importlib.import_module('app.services.conversation.turns')
        with patch.object(module, 'datetime', create=True) as host_time:
            host_time.now.side_effect = AssertionError('Host time must not validate store ownership')
            result = self.claim(service=TurnService(self.store))
        self.assertEqual((result.status, result.value.turn), ('success', turn))

    def test_other_npc_claims_independently_while_first_stream_is_busy(self):
        first = self.submit()
        other_key = self.key.model_copy(update={'npc_id': 2})
        other = self.submit('request:other', other_key)
        self.assertEqual(self.claim().value.turn, first)
        self.assertEqual(self.claim('worker:other', other_key).value.turn, other)
        self.assertIsNone(self.claim('worker:blocked').value)

    def test_expiry_replaces_fence_at_boundary_without_skipping_turn(self):
        first = self.submit()
        self.submit('request:2')
        old = self.claim().value
        self.advance(20)
        replacement = self.claim('worker:new', service=self.restart()).value
        self.assertEqual((replacement.turn, replacement.fence, replacement.phase), (first, 2, 'preparing'))
        stale = self.service.record_attempt(first, old.fence, self.attempt(old))
        self.assertEqual((stale.code, stale.retryable), ('LEASE_LOST', True))
        self.assertEqual(self.service.recover(first).attempts, ())

    def test_claim_rejects_returned_wrong_scope_worker_or_expired_lease(self):
        self.submit()
        lease = self.claim().value
        for changed in (
            lease.model_copy(update={'turn': lease.turn.model_copy(update={
                'key': self.key.model_copy(update={'npc_id': 2})})}),
            lease.model_copy(update={'worker_id': 'worker:wrong'}),
            lease.model_copy(update={'claimed_at': self.clock.now - timedelta(seconds=40),
                'expires_at': self.clock.now}),
            lease.model_copy(update={'claimed_at': self.clock.now + timedelta(seconds=1),
                'expires_at': self.clock.now + timedelta(seconds=21)}),
        ):
            with self.subTest(lease=changed):
                self.store.claim_override = changed
                result = self.claim()
                self.assertEqual((result.status, result.error.code, result.error.retryable),
                    ('failure', 'LEASE_LOST', True))
        self.assertEqual(self.repository.pending(self.key)[0].phase, 'preparing')

    def test_restart_before_dispatch_recovers_submission_without_consumed_budget(self):
        turn = self.submit()
        self.claim()
        self.advance(21)
        restarted = self.restart()
        lease = self.claim('worker:new', service=restarted).value
        recovery = restarted.recover(turn)
        self.assertEqual((recovery.fence, recovery.status.phase), (2, 'preparing'))
        self.assertEqual(recovery.submission.player_message, 'Hello.')
        self.assertEqual(recovery.consumed_purposes, ())
        self.assertEqual(restarted.record_attempt(turn, lease.fence, self.attempt(lease)).status, 'dispatched')

    def test_restart_after_dispatch_preserves_lost_output_and_consumed_proposal(self):
        turn = self.submit()
        old = self.claim().value
        dispatched = self.attempt(old)
        self.assertEqual(self.service.record_attempt(turn, old.fence, dispatched), dispatched)
        self.advance(21)
        restarted = self.restart()
        lease = self.claim('worker:new', service=restarted).value
        recovery = restarted.recover(turn)
        self.assertEqual(recovery.attempts, (dispatched,))
        self.assertEqual(recovery.consumed_purposes, ('proposal',))
        self.assertIsNone(recovery.attempts[0].output)
        self.assertEqual(restarted.record_attempt(turn, lease.fence,
            self.attempt(lease, attempt_id='attempt:new')).code, 'INVALID_BOUNDS')

    def test_same_dispatch_replays_without_consuming_twice_and_conflicting_identity_fails(self):
        turn = self.submit()
        lease = self.claim().value
        attempt = self.attempt(lease)
        self.service.record_attempt(turn, lease.fence, attempt)
        self.assertEqual(self.service.record_attempt(turn, lease.fence, attempt), attempt)
        changed = attempt.model_copy(update={'dispatched_at': self.clock.now + timedelta(seconds=1)})
        self.assertEqual(self.service.record_attempt(turn, lease.fence, changed).code, 'IDEMPOTENCY_CONFLICT')
        self.assertEqual(self.service.recover(turn).attempts, (attempt,))

    def test_proposal_output_survives_replacement_with_original_fence_and_phase(self):
        turn = self.submit()
        old = self.claim().value
        attempt = self.attempt(old)
        self.service.record_attempt(turn, old.fence, attempt)
        output = self.output(attempt)
        self.assertEqual(self.service.save_attempt_output(turn, old.fence, output), output)
        self.advance(21)
        restarted = self.restart()
        lease = self.claim('worker:new', service=restarted).value
        recovery = restarted.recover(turn)
        self.assertEqual((lease.phase, recovery.status.phase), ('proposed', 'proposed'))
        self.assertEqual((recovery.fence, recovery.attempts[0].fence), (2, 1))
        self.assertEqual(recovery.attempts[0].output, output.output)
        self.assertEqual(self.service.save_attempt_output(turn, old.fence, output).code, 'LEASE_LOST')

    def assert_repair_budget_survives_restart(self, spent, denied):
        turn = self.submit()
        old = self.claim().value
        attempt = self.attempt(old, 'repair', spent)
        self.service.record_attempt(turn, old.fence, attempt)
        self.advance(21)
        restarted = self.restart()
        lease = self.claim('worker:new', service=restarted).value
        recovery = restarted.recover(turn)
        self.assertTrue(recovery.repair_consumed)
        self.assertEqual(recovery.attempts, (attempt,))
        self.assertEqual(restarted.record_attempt(turn, lease.fence,
            self.attempt(lease, 'repair', denied, 'attempt:other')).code, 'INVALID_BOUNDS')

    def test_proposal_repair_consumes_final_response_repair_token_across_restart(self):
        self.assert_repair_budget_survives_restart('proposal_format', 'final_response')

    def test_final_response_repair_consumes_proposal_repair_token_across_restart(self):
        self.assert_repair_budget_survives_restart('final_response', 'proposal_format')

    def test_composition_budget_is_consumed_separately_from_proposal_and_repair(self):
        turn = self.submit()
        lease = self.claim().value
        for purpose, kind in (('proposal', None), ('composition', None), ('repair', 'final_response')):
            attempt = self.attempt(lease, purpose, kind, f'attempt:{purpose}')
            self.service.record_attempt(turn, lease.fence, attempt)
        recovery = self.restart().recover(turn)
        self.assertEqual(recovery.consumed_purposes, ('proposal', 'composition', 'repair'))
        self.assertEqual(self.service.record_attempt(turn, lease.fence,
            self.attempt(lease, 'composition', attempt_id='attempt:extra')).code, 'INVALID_BOUNDS')

    def test_unrecorded_output_and_mismatched_attempt_scope_cannot_be_persisted(self):
        turn = self.submit()
        lease = self.claim().value
        output = self.output(self.attempt(lease))
        self.assertEqual(self.service.save_attempt_output(turn, lease.fence, output).code, 'INVALID_INPUT')
        wrong_turn = turn.model_copy(update={'sequence': 99})
        wrong = self.attempt(lease).model_copy(update={'turn': wrong_turn})
        self.assertEqual(self.service.record_attempt(turn, lease.fence, wrong).code, 'INVALID_INPUT')
        self.assertEqual(self.service.recover(turn).attempts, ())

    def test_receipt_and_assembly_recover_together_without_executing_again(self):
        turn = self.submit()
        old = self.claim().value
        decision = c.ReadyToRecheck(kind='ready_to_recheck',
            operation=c.OperationCandidate.model_validate(self.fixture['operation']),
            consent=None, checked_preconditions=())
        raw = {**self.fixture['receipt'], 'receipt_id': 'receipt:recovery',
            'turn_id': turn.turn_id, 'game_scope': turn.key.game_scope, 'npc_id': turn.key.npc_id}
        receipt = c.OperationReceipt.model_validate(raw)
        self.repository.scenario_seed_outcome(turn, receipt)
        self.assertEqual(self.repository.execute_once(turn, old.fence, decision), receipt)
        attempt = self.attempt(old, 'composition')
        self.service.record_attempt(turn, old.fence, attempt)
        output = self.output(attempt)
        self.service.save_attempt_output(turn, old.fence, output)
        reply = c.AssembledReply(text_id='final:recovery', final_text='It is done.',
            beats=('It is done.',), segment_spans={}, evidence_dependencies=(),
            candidate_continuity_changes=())
        saved = self.service.save_reply(turn, old.fence, reply)
        self.advance(21)
        restarted = self.restart()
        lease = self.claim('worker:new', service=restarted).value
        recovery = restarted.recover(turn)
        self.assertEqual((lease.phase, recovery.status.phase), ('operation_resolved', 'operation_resolved'))
        self.assertEqual(recovery.receipt, receipt)
        self.assertEqual(recovery.attempts, (output,))
        self.assertEqual(recovery.assembled_reply, saved)
        self.assertEqual((recovery.fence, saved.fence), (2, 1))
        self.assertEqual(self.repository.scenario_effect_count(), 1)
        self.assertIsNone(self.repository.scenario_transcript(turn))
        self.assertEqual(self.service.save_reply(turn, old.fence, reply).code, 'LEASE_LOST')

    def test_storage_failures_preserve_pending_work_and_do_not_retry_port_calls(self):
        turn = self.submit()
        self.store.fail_next = 'claim_next'
        self.store.calls.clear()
        failure = self.claim()
        self.assertEqual((failure.error.code, failure.error.retryable), ('STORAGE_UNAVAILABLE', True))
        self.assertEqual(len(self.store.calls), 1)
        self.assertEqual(self.service.lookup(self.key, 'request:1').phase, 'queued')
        lease = self.claim().value
        attempt = self.attempt(lease)
        self.store.fail_next = 'record_attempt'
        self.store.calls.clear()
        failure = self.service.record_attempt(turn, lease.fence, attempt)
        self.assertEqual((failure.code, failure.retryable, failure.turn), ('STORAGE_UNAVAILABLE', True, turn))
        self.assertEqual(len(self.store.calls), 1)
        self.assertEqual(self.service.recover(turn).attempts, ())
        self.service.record_attempt(turn, lease.fence, attempt)
        self.store.fail_next = 'save_attempt_output'
        failure = self.service.save_attempt_output(turn, lease.fence, self.output(attempt))
        self.assertEqual(failure.code, 'STORAGE_UNAVAILABLE')
        self.assertEqual(self.service.recover(turn).attempts, (attempt,))
        reply = c.AssembledReply(text_id='final:outage', final_text='Hello.', beats=('Hello.',),
            segment_spans={}, evidence_dependencies=(), candidate_continuity_changes=())
        self.store.fail_next = 'save_reply'
        failure = self.service.save_reply(turn, lease.fence, reply)
        self.assertEqual((failure.code, failure.retryable), ('STORAGE_UNAVAILABLE', True))
        self.assertIsNone(self.service.recover(turn).assembled_reply)
        self.store.fail_next = 'pending'
        failure = self.service.pending(self.key)
        self.assertEqual((failure.code, failure.retryable), ('STORAGE_UNAVAILABLE', True))
        self.store.fail_next = 'recover'
        self.store.calls.clear()
        failure = self.service.recover(turn)
        self.assertEqual((failure.code, failure.retryable), ('STORAGE_UNAVAILABLE', True))
        self.assertEqual(len(self.store.calls), 1)
        self.assertEqual(self.service.lookup(self.key, 'request:1').phase, 'preparing')
        self.assertEqual(self.repository.scenario_effect_count(), 0)

    def test_lost_attempt_acknowledgement_recovers_consumption_without_redispatch(self):
        turn = self.submit()
        lease = self.claim().value
        attempt = self.attempt(lease)
        self.store.fail_after = 'record_attempt'
        self.store.calls.clear()
        failure = self.service.record_attempt(turn, lease.fence, attempt)
        self.assertEqual((failure.code, failure.retryable), ('STORAGE_UNAVAILABLE', True))
        self.assertEqual(len(self.store.calls), 1)
        recovery = self.restart().recover(turn)
        self.assertEqual((recovery.status.phase, recovery.attempts), ('preparing', (attempt,)))
        self.assertEqual(self.service.record_attempt(turn, lease.fence,
            self.attempt(lease, attempt_id='attempt:new')).code, 'INVALID_BOUNDS')

    def test_clear_recovery_erases_drafts_and_rejects_old_fenced_writes(self):
        turn = self.submit()
        lease = self.claim().value
        attempt = self.attempt(lease, 'repair', 'proposal_format')
        self.service.record_attempt(turn, lease.fence, attempt)
        self.repository.scenario_clear(self.key)
        recovery = self.restart().recover(turn)
        self.assertEqual(recovery.status.phase, 'invalidated')
        self.assertEqual((recovery.submission, recovery.attempts, recovery.assembled_reply), (None, (), None))
        self.assertEqual(self.service.record_attempt(turn, lease.fence, attempt).code, 'TURN_INVALIDATED')


if __name__ == '__main__':
    unittest.main()
