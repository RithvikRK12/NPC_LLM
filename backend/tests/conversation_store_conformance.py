"""Reusable T02 write/recovery conformance, independent of concrete adapters.

Mix these cases into unittest.TestCase and provide the harness demonstrated by
test_conversation_store_ports.FakeWriteRepositoryTests: a repository implementing
all five ports, scoped fixtures, injected-clock/fault controls and detached audit
observations. Cases call the public protocol methods; scenario_* controls only
seed outcomes, advance time or inject infrastructure faults. Pure fake runs do
not prove SQL atomicity, crash durability or SQLite/PostgreSQL locking.
"""
from app.services.conversation.contracts import ConversationError


class AdmissionCases:
    def test_same_id_replays_and_different_payload_conflicts(self):
        first = self.repository.submit(self.submission('request:1', 'hello'))
        again = self.repository.submit(self.submission('request:1', 'hello'))
        conflict = self.repository.submit(self.submission('request:1', 'changed'))
        self.assertEqual(first, again)
        self.assertEqual(first.turn.sequence, 1)
        self.assertEqual(conflict.code, 'IDEMPOTENCY_CONFLICT')
        second = self.repository.submit(self.submission('request:2', 'next'))
        self.assertEqual(second.turn.sequence, 2)
        self.assertEqual(self.repository.lookup(self.key, 'request:1'), first)

    def test_lookup_is_scoped_and_does_not_admit_or_execute(self):
        first = self.repository.submit(self.submission('request:1', 'hello'))
        other_key = self.key.model_copy(update={'npc_id': 2})
        missing = self.repository.lookup(other_key, 'request:1')
        self.assertIsInstance(missing, ConversationError)
        self.assertEqual(self.effect_count(), 0)
        self.assertEqual(self.repository.lookup(self.key, 'request:1'), first)
        next_turn = self.repository.submit(self.submission('request:2', 'next'))
        self.assertEqual(next_turn.turn.sequence, 2)

    def test_clear_tombstone_replays_identity_without_erased_payload(self):
        first = self.repository.submit(self.submission('request:1', 'secret message'))
        self.simulate_clear(self.key)
        status = self.repository.lookup(self.key, 'request:1')
        replay = self.repository.submit(self.submission('request:1', 'secret message'))
        self.assertEqual(status, replay)
        self.assertEqual(status.turn, first.turn)
        self.assertEqual(status.phase, 'invalidated')
        self.assertIsNone(status.response)
        self.assertFalse(self.has_recoverable_payload(first.turn))
        stale = self.repository.submit(self.submission('request:new', 'new text'))
        self.assertEqual(stale.code, 'STALE_EPOCH')


class OperationCases:
    def test_existing_receipt_is_recovered_without_a_second_effect(self):
        turn = self.repository.submit(self.submission('request:1', 'give wood')).turn
        fence = self.claim(turn, 'worker:1')
        expected = self.receipt_for(turn)
        first = self.repository.execute_once(turn, fence, self.decision)
        restarted = self.restart()
        second = restarted.execute_once(turn, fence, self.decision)
        self.assertEqual(first, expected)
        self.assertEqual(second, expected)
        self.assertEqual(self.effect_count(), 1)
        self.assertEqual(self.repository.lookup(self.key, 'request:1').phase, 'operation_resolved')

    def test_replaced_fence_cannot_execute(self):
        turn = self.repository.submit(self.submission('request:1', 'give wood')).turn
        old_fence = self.claim(turn, 'worker:old')
        self.expire_lease(turn)
        current_fence = self.claim(turn, 'worker:new')
        self.receipt_for(turn)
        stale = self.repository.execute_once(turn, old_fence, self.decision)
        self.assertEqual(stale.code, 'LEASE_LOST')
        self.assertEqual(self.effect_count(), 0)
        self.assertNotEqual(current_fence, old_fence)
        self.assertNotIsInstance(self.repository.execute_once(turn, current_fence, self.decision), ConversationError)
        self.assertEqual(self.effect_count(), 1)

    def test_receipt_failure_rolls_back_effect_and_phase(self):
        turn = self.repository.submit(self.submission('request:1', 'give wood')).turn
        fence = self.claim(turn, 'worker:1')
        expected = self.receipt_for(turn)
        before = self.repository.lookup(self.key, 'request:1')
        self.fail_next_receipt()
        failed = self.repository.execute_once(turn, fence, self.decision)
        self.assertEqual(failed.code, 'STORAGE_UNAVAILABLE')
        self.assertEqual(self.effect_count(), 0)
        self.assertEqual(self.repository.lookup(self.key, 'request:1'), before)
        self.assertEqual(self.repository.execute_once(turn, fence, self.decision), expected)
        self.assertEqual(self.effect_count(), 1)

    def test_cleared_turn_cannot_execute_or_recover_in_new_epoch(self):
        turn = self.repository.submit(self.submission('request:1', 'give wood')).turn
        fence = self.claim(turn, 'worker:1')
        self.receipt_for(turn)
        self.simulate_clear(self.key)
        result = self.repository.execute_once(turn, fence, self.decision)
        self.assertEqual(result.code, 'TURN_INVALIDATED')
        self.assertEqual(self.effect_count(), 0)
        fresh_key = self.key.model_copy(update={'epoch': 1})
        self.assertIsInstance(self.repository.lookup(fresh_key, 'request:1'), ConversationError)

    def test_committed_receipt_survives_clear_but_old_execution_is_invalidated(self):
        turn = self.repository.submit(self.submission('request:1', 'give wood')).turn
        fence = self.claim(turn, 'worker:1')
        expected = self.receipt_for(turn)
        self.assertEqual(self.repository.execute_once(turn, fence, self.decision), expected)
        self.simulate_clear(self.key)
        self.assertEqual(self.saved_receipt(turn), expected)
        self.assertEqual(self.repository.execute_once(turn, fence, self.decision).code, 'TURN_INVALIDATED')
        self.assertEqual(self.effect_count(), 1)


class ClaimCases:
    def test_claim_next_only_oldest_and_independent_npc_streams(self):
        first = self.repository.submit(self.submission('request:1', 'first')).turn
        self.repository.submit(self.submission('request:2', 'second'))
        lease = self.repository.claim_next(self.key, 'worker:1', self.lease_policy).value
        self.assertEqual(lease.turn, first)
        self.assertEqual(lease.fence, 1)
        busy = self.repository.claim_next(self.key, 'worker:other', self.lease_policy)
        self.assertEqual((busy.status, busy.value), ('success', None))
        other_key = self.key.model_copy(update={'npc_id': 2})
        other = self.repository.submit(self.submission('request:other', 'other', key=other_key)).turn
        self.assertEqual(self.repository.claim_next(other_key, 'worker:2', self.lease_policy).value.turn, other)

    def test_expired_claim_increments_fence_without_skipping_pending_turn(self):
        first = self.repository.submit(self.submission('request:1', 'first')).turn
        self.repository.submit(self.submission('request:2', 'second'))
        old = self.repository.claim_next(self.key, 'worker:old', self.lease_policy).value
        self.advance_seconds(21)
        replacement = self.repository.claim_next(self.key, 'worker:new', self.lease_policy).value
        self.assertEqual((replacement.turn, replacement.fence), (first, 2))
        self.assertEqual(old.fence, 1)
        recovered = self.repository.recover(first)
        self.assertEqual(recovered.status.phase, 'preparing')
        self.assertEqual(recovered.fence, 2)
        self.assertEqual(recovered.submission.player_message, 'first')

    def test_pending_scan_is_scoped_durable_and_read_only(self):
        first = self.repository.submit(self.submission('request:1', 'first')).turn
        second = self.repository.submit(self.submission('request:2', 'second')).turn
        restarted = self.restart()
        self.assertEqual(tuple(status.turn for status in restarted.pending(self.key)), (first, second))
        self.assertEqual(tuple(status.phase for status in restarted.pending(self.key)), ('queued', 'queued'))
        other_key = self.key.model_copy(update={'npc_id': 2})
        self.assertEqual(restarted.pending(other_key), ())
        self.assertEqual(self.effect_count(), 0)

    def test_receipt_lookup_is_exact_scoped_and_does_not_execute(self):
        turn = self.repository.submit(self.submission('request:1', 'give wood')).turn
        fence = self.claim(turn, 'worker:1')
        expected = self.receipt_for(turn)
        missing = self.repository.lookup_receipt(turn)
        self.assertEqual((missing.status, missing.value), ('success', None))
        self.assertEqual(self.effect_count(), 0)
        self.repository.execute_once(turn, fence, self.decision)
        self.assertEqual(self.restart().lookup_receipt(turn).value, expected)
        forged = turn.model_copy(update={'key': turn.key.model_copy(update={'npc_id': 2})})
        self.assertEqual(self.repository.lookup_receipt(forged).error.code, 'INVALID_INPUT')
        self.assertEqual(self.effect_count(), 1)


class PublicationCases:
    def test_final_retry_is_exact_and_releases_next_turn(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        next_turn = self.repository.submit(self.submission('request:2', 'next')).turn
        reply, plan, expected = self.publication_for(turn, 'A🙂éB')
        result = self.repository.commit(turn, fence, reply, plan)
        self.assertEqual(result, expected)
        self.assertEqual(self.repository.commit(turn, fence, reply, plan), expected)
        self.assertEqual(self.repository.lookup(self.key, 'request:1').response, expected)
        self.assertEqual(self.repository.claim_next(self.key, 'worker:2', self.lease_policy).value.turn, next_turn)
        self.assertEqual(self.transcript(turn), 'A🙂éB')

    def test_finalization_failure_rolls_back_transcript_continuity_and_status(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        reply, plan, expected = self.publication_for(turn, 'Old harbor story.', add_canon=True, add_memory=True)
        before = self.repository.lookup(self.key, 'request:1')
        self.fail_next_publication()
        self.assertEqual(self.repository.commit(turn, fence, reply, plan).code, 'STORAGE_UNAVAILABLE')
        self.assertIsNone(self.transcript(turn))
        self.assertEqual(self.canon_count(), 0)
        self.assertEqual(self.memory_count(), 0)
        self.assertEqual(self.repository.lookup(self.key, 'request:1'), before)
        self.assertEqual(self.repository.commit(turn, fence, reply, plan), expected)
        self.assertEqual((self.canon_count(), self.memory_count()), (1, 1))

    def test_publication_rejects_replaced_fence_and_relevant_revision_change(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        old_fence = self.claim(turn, 'worker:old')
        reply, plan, _ = self.publication_for(turn, 'The harbor.', expected={'event:1': 1})
        self.set_revisions(self.key, {'event:1': 1, 'unrelated:inventory': 99})
        self.expire_lease(turn)
        fence = self.claim(turn, 'worker:new')
        self.assertEqual(self.repository.commit(turn, old_fence, reply, plan).code, 'LEASE_LOST')
        self.set_revisions(self.key, {'event:1': 2})
        self.assertEqual(self.repository.commit(turn, fence, reply, plan).code, 'EVIDENCE_CHANGED')
        self.assertIsNone(self.transcript(turn))
        self.set_revisions(self.key, {'event:1': 1, 'unrelated:inventory': 100})
        self.assertNotIsInstance(self.repository.commit(turn, fence, reply, plan), ConversationError)

    def test_canon_creation_collision_rolls_back_all_publication(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        reply, plan, _ = self.publication_for(turn, 'Harbor story.', add_canon=True)
        self.seed_canon_collision(turn, plan.canon_changes[0])
        self.assertEqual(self.repository.commit(turn, fence, reply, plan).code, 'EVIDENCE_CHANGED')
        self.assertIsNone(self.transcript(turn))
        self.assertEqual(self.repository.lookup(self.key, 'request:1').phase, 'preparing')

    def test_operation_committed_interaction_cannot_be_overwritten(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        reply, plan, _ = self.publication_for(turn, 'All done.', stale_interaction=True)
        self.assertEqual(self.repository.commit(turn, fence, reply, plan).code, 'EVIDENCE_CHANGED')
        self.assertIsNone(self.transcript(turn))
        self.assertEqual(self.interaction_status(), 'fulfilled')


class LifecycleSummaryCases:
    def test_clear_deletes_publication_and_preserves_canon_and_receipt(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        receipt = self.receipt_for(turn)
        self.repository.execute_once(turn, fence, self.decision)
        reply, plan, _ = self.publication_for(turn, 'Harbor story.', add_canon=True, add_memory=True)
        self.repository.commit(turn, fence, reply, plan)
        cleared = self.repository.clear(self.key)
        self.assertEqual(cleared.current_key.epoch, 1)
        self.assertEqual((self.canon_count(), self.memory_count(), self.effect_count()), (1, 0, 1))
        self.assertIsNone(self.transcript(turn))
        status = self.repository.lookup(self.key, 'request:1')
        self.assertEqual((status.phase, status.response), ('invalidated', None))
        recovered = self.repository.recover(turn)
        self.assertEqual((recovered.submission, recovered.attempts, recovered.assembled_reply), (None, (), None))
        self.assertEqual(recovered.receipt, receipt)
        self.assertEqual(self.repository.clear(self.key).code, 'STALE_EPOCH')
        self.assertEqual(self.repository.commit(turn, fence, reply, plan).code, 'TURN_INVALIDATED')

    def test_new_game_replaces_scope_and_prevents_old_recovery_and_writes(self):
        turn = self.repository.submit(self.submission('request:1', 'give wood')).turn
        fence = self.claim(turn, 'worker:1')
        self.receipt_for(turn)
        self.repository.execute_once(turn, fence, self.decision)
        reply, plan, _ = self.publication_for(turn, 'Harbor story.', add_canon=True)
        self.repository.commit(turn, fence, reply, plan)
        reset = self.repository.new_game('run:1')
        self.assertNotEqual(reset.game_scope, 'run:1')
        self.assertEqual((self.canon_count(), self.memory_count(), self.effect_count()), (0, 0, 0))
        self.assertEqual(self.repository.recover(turn).code, 'STALE_SCOPE')
        self.assertEqual(self.repository.lookup_receipt(turn).error.code, 'STALE_SCOPE')
        self.assertEqual(self.repository.new_game('run:1').code, 'STALE_SCOPE')
        self.assertEqual(self.repository.execute_once(turn, fence, self.decision).code, 'TURN_INVALIDATED')

    def test_summary_cas_and_source_revisions_survive_restart(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        reply, plan, _ = self.publication_for(turn, 'Harbor story.', add_memory=True)
        self.repository.commit(turn, fence, reply, plan)
        summary = self.summary_for(turn)
        self.set_revisions(self.key, dict(summary.source_revisions.resources))
        self.assertIn(self.key, self.restart().dirty_keys('run:1'))
        sources = self.repository.read_sources(self.key, summary.source_range)
        self.assertEqual(tuple(source.turn for source in sources), (turn,))
        self.assertEqual(self.repository.publish(summary, None), summary)
        self.assertEqual(self.repository.lookup_summary(self.key).value, summary)
        self.assertNotIn(self.key, self.restart().dirty_keys('run:1'))
        self.assertEqual(self.repository.publish(summary, None).code, 'EVIDENCE_CHANGED')
        stale = summary.model_copy(update={'revision': 1})
        self.set_revisions(self.key, {**summary.source_revisions.resources, 'memory:1': 2})
        self.assertEqual(self.repository.publish(stale, 0).code, 'EVIDENCE_CHANGED')
        self.assertEqual(self.repository.lookup_summary(self.key).value, summary)

    def test_summary_publication_after_clear_is_rejected_and_old_summary_removed(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        reply, plan, _ = self.publication_for(turn, 'Harbor story.', add_memory=True)
        self.repository.commit(turn, fence, reply, plan)
        summary = self.summary_for(turn)
        self.set_revisions(self.key, dict(summary.source_revisions.resources))
        self.repository.publish(summary, None)
        self.repository.clear(self.key)
        self.assertEqual(self.repository.publish(summary, 0).code, 'STALE_EPOCH')
        self.assertEqual(self.repository.lookup_summary(self.key).error.code, 'STALE_EPOCH')
        fresh = self.key.model_copy(update={'epoch': 1})
        self.assertIsNone(self.repository.lookup_summary(fresh).value)


class AttemptCases:
    def test_dispatch_consumption_survives_restart_and_replacement_without_output(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        attempt = self.attempt_for(turn, fence, 'proposal')
        self.assertEqual(self.repository.record_attempt(turn, fence, attempt), attempt)
        self.assertEqual(self.repository.record_attempt(turn, fence, attempt), attempt)
        self.expire_lease(turn)
        new_fence = self.claim(turn, 'worker:2')
        recovered = self.restart().recover(turn)
        self.assertEqual((recovered.fence, recovered.consumed_purposes), (new_fence, ('proposal',)))
        self.assertIsNone(recovered.attempts[0].output)
        duplicate = self.attempt_for(turn, new_fence, 'proposal', attempt_id='attempt:second')
        self.assertEqual(self.repository.record_attempt(turn, new_fence, duplicate).code, 'INVALID_BOUNDS')

    def test_one_repair_token_is_shared_by_proposal_and_final_response(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        repair = self.attempt_for(turn, fence, 'repair', repair_kind='proposal_format')
        self.repository.record_attempt(turn, fence, repair)
        self.assertTrue(self.restart().recover(turn).repair_consumed)
        later = self.attempt_for(turn, fence, 'repair', attempt_id='attempt:later', repair_kind='final_response')
        self.assertEqual(self.repository.record_attempt(turn, fence, later).code, 'INVALID_BOUNDS')
        self.assertEqual(len(self.repository.recover(turn).attempts), 1)

    def test_recorded_output_and_assembly_recover_with_original_fence(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        attempt = self.attempt_for(turn, fence, 'composition')
        self.repository.record_attempt(turn, fence, attempt)
        output = self.persisted_attempt(attempt)
        self.assertEqual(self.repository.save_attempt_output(turn, fence, output), output)
        reply, _, _ = self.publication_for(turn, 'Harbor story.')
        assembly = self.repository.save_reply(turn, fence, reply)
        self.expire_lease(turn)
        new_fence = self.claim(turn, 'worker:2')
        recovered = self.restart().recover(turn)
        self.assertEqual((recovered.fence,recovered.attempts[0].fence,recovered.assembled_reply.fence),
                         (new_fence,fence,fence))
        self.assertEqual(recovered.attempts[0], output)
        self.assertEqual(recovered.assembled_reply, assembly)
        self.assertEqual(self.repository.save_attempt_output(turn, fence, output).code, 'LEASE_LOST')
        self.assertEqual(self.repository.save_reply(turn, fence, reply).code, 'LEASE_LOST')

    def test_output_cannot_be_persisted_without_dispatch_or_changed_after_persistence(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        attempt = self.attempt_for(turn, fence, 'composition')
        output = self.persisted_attempt(attempt)
        self.assertEqual(self.repository.save_attempt_output(turn, fence, output).code, 'INVALID_INPUT')
        self.repository.record_attempt(turn, fence, attempt)
        self.assertEqual(self.repository.save_attempt_output(turn, fence, output), output)
        changed = self.persisted_attempt(attempt, changed=True)
        self.assertEqual(self.repository.save_attempt_output(turn, fence, changed).code, 'IDEMPOTENCY_CONFLICT')
        self.assertEqual(self.repository.recover(turn).attempts[0], output)

    def test_clear_erases_attempt_outputs_and_assembly_but_keeps_tombstone(self):
        turn = self.repository.submit(self.submission('request:1', 'story')).turn
        fence = self.claim(turn, 'worker:1')
        attempt = self.attempt_for(turn, fence, 'composition')
        self.repository.record_attempt(turn, fence, attempt)
        self.repository.save_attempt_output(turn, fence, self.persisted_attempt(attempt))
        reply, _, _ = self.publication_for(turn, 'Secret story.')
        self.repository.save_reply(turn, fence, reply)
        self.repository.clear(self.key)
        recovered = self.repository.recover(turn)
        self.assertEqual((recovered.status.phase,recovered.submission,recovered.attempts,recovered.assembled_reply),
                         ('invalidated',None,(),None))
        self.assertEqual(self.repository.record_attempt(turn, fence, attempt).code, 'TURN_INVALIDATED')
