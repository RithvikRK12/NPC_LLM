"""Bounded speech repair with recorded allowances and real assembly/validation."""
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unittest

from app.services.conversation import contracts as c
from app.services.conversation.composition import AssemblyEvidence
from app.services.conversation.validation import ResponseValidator
from conversation_store_fakes import FakeConversationRepository


class RepairServiceTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.find_spec('app.services.conversation.repair')
        self.assertIsNotNone(spec, 'T03 speech-only RepairService is absent')
        self.module = importlib.import_module('app.services.conversation.repair')
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/contracts-t02-valid.json').read_text())
        self.repository = FakeConversationRepository()
        key = c.ConversationKey(game_scope='run:1', npc_id=1, epoch=0)
        self.repository.submit(c.TurnSubmission(schema_version=1, request_id='request:1',
            key=key, player_message='Give me wood.'))
        self.lease = self.repository.claim_next(key, 'worker:repair', c.LeasePolicy(
            schema_version=1, policy_version='lease:1', lease_duration_seconds=20)).value
        self.turn = self.lease.turn
        self.receipt = c.OperationReceipt.model_validate(raw['receipt'])
        self.operation = c.ReadyToRecheck(kind='ready_to_recheck', consent=None,
            checked_preconditions=(), operation=c.OperationCandidate.model_validate(raw['operation']))
        self.policy = c.ConversationPolicy(schema_version=1, policy_version='test:1', input_char_limit=500,
            total_deadline_seconds=10, provider_stage_budget_seconds=4, context_token_limit=1000,
            output_char_limit=600, beat_char_limit=80, queue_capacity=5, lease_duration_seconds=20,
            summary_trigger_turns=10, diagnostic_retention_seconds=100)
        self.context = c.ContextPacket(turn=self.turn, current_message=c.TextValue(
            text_id='message:1', text='Give me wood.'), character_profile=(), active_canon=(),
            visible_recent_turns=(), summaries=(), reports=(), interpretations=(), visible_facts=(),
            capabilities=(), pending_interactions=(), revisions=c.RevisionSet(resources={}),
            policy_versions={'bounds':'test:1'})
        self.assembly = AssemblyEvidence(turn=self.turn, text_id='final:repair', facts=(),
            receipts=(self.receipt,), revisions=self.context.revisions, resource_sources=(),
            receipt_sources=(c.SourceRef(kind='operation_receipt', source_id=self.receipt.receipt_id,
                revision=self.receipt.argument_digest, game_scope='run:1', npc_id=1,
                attribution='server', visibility='public'),))
        self.evidence = self.module.RepairEvidence(context=self.context, assembly=self.assembly,
            operation=self.operation)
        self.candidate = self.candidate_for('I kept the wood.')
        self.findings = ResponseValidator().check_text('I kept the wood.',
            evidence={self.receipt.receipt_id:self.receipt})
        self.output = self.candidate_for('A🙂éZ')
        self.clock = [100.0]
        self.deadline = c.Deadline.after(10, clock=lambda:self.clock[0])
        self.calls = []
        self.reservations = []
        self.delay = 0
        self.service = self.module.RepairService(self.hook, self.validate, self.policy)
        self.allowance = self.allow()

    def candidate_for(self, text, *, canon=False, receipt=True):
        segments = [c.ExpressiveSegment(kind='expressive', segment_id='prose', text=text,
            addressed_concern_ids=())]
        if receipt:
            segments.append(c.ReceiptSlot(kind='receipt_slot', segment_id='outcome',
                receipt_id='receipt:1', speech_act='completed', renderer_id='receipt.completed'))
        candidates = (c.CanonCandidate(kind='add', candidate_id='canon:repair', subject='npc:1',
            predicate='story', content='🙂é', supporting_span=c.TextSpan(text_id='prose', start=1, end=4),
            expected_revision=None, correction_candidate_id=None),) if canon else ()
        return c.CandidateReply(segments=tuple(segments), canon_candidates=candidates,
            source=c.ReplySource(origin='generated', source_id='proposal:1', schema_version=1,
                policy_versions={'bounds':'test:1'}))

    def attempt(self, kind='final_response', **updates):
        return c.ProviderAttempt.model_validate(dict(turn=self.turn, attempt_id='attempt:repair',
            fence=self.lease.fence, purpose='repair', repair_kind=kind,
            dispatched_at=datetime(2026,10,14,tzinfo=timezone.utc), status='dispatched', output=None,
            **updates))

    def allow(self, recovery=None, reserve=None):
        return self.module.RepairAllowance(recovery or self.repository.recover(self.turn), reserve or self.reserve)

    def reserve(self, turn, deadline):
        self.reservations.append(turn)
        return self.repository.record_attempt(turn, self.lease.fence, self.attempt())

    def hook(self, candidate, findings, evidence, deadline, dialogue_codepoint_limit):
        self.assertTrue(self.repository.recover(self.turn).repair_consumed,
            'repair was dispatched before durable token consumption')
        self.calls.append((candidate, findings, evidence, deadline, dialogue_codepoint_limit))
        self.clock[0] += self.delay
        if isinstance(self.output, Exception):
            raise self.output
        return self.output

    def validate(self, reply, evidence):
        return ResponseValidator().check(reply, evidence.context, evidence.assembly)

    def repair(self, allowance='default', **updates):
        return self.service.repair(updates.get('candidate', self.candidate), self.findings,
            updates.get('evidence', self.evidence), self.deadline,
            allowance=self.allowance if allowance == 'default' else allowance)

    def assert_error(self, result, code):
        self.assertIsNone(result.value)
        self.assertEqual(result.error.code, code)
        self.assertEqual(result.error.turn, self.turn)

    def test_approved_repair_rebuilds_unicode_spans_and_preserves_receipt_operation_turn(self):
        self.output = self.candidate_for('A🙂éZ', canon=True)
        original_receipt = self.receipt.model_dump_json()
        original_operation = self.operation.model_dump_json()
        result = self.repair()
        self.assertIsNone(result.error)
        accepted = result.value
        self.assertEqual(accepted.turn, self.turn)
        self.assertEqual(accepted.reply.final_text, 'A🙂éZ I gave you 1 wood.')
        self.assertEqual(accepted.reply.segment_spans['outcome'],
            c.TextSpan(text_id='final:repair', start=6, end=24))
        self.assertEqual(accepted.reply.candidate_continuity_changes[0].supporting_span,
            c.TextSpan(text_id='final:repair', start=1, end=4))
        accepted.reply.validate_segment_texts({'prose':'A🙂éZ','outcome':'I gave you 1 wood.'})
        self.assertEqual(accepted.candidate.source.origin, 'repaired')
        self.assertEqual(accepted.operation.model_dump_json(), original_operation)
        self.assertEqual(accepted.receipts[0].model_dump_json(), original_receipt)
        self.assertEqual(self.receipt.model_dump_json(), original_receipt)
        self.assertEqual(self.operation.model_dump_json(), original_operation)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][1], self.findings)
        self.assertEqual(self.calls[0][3].expires_at, 104.0)
        self.assertEqual(self.calls[0][4], 600)

    def test_ungranted_allowance_and_second_use_do_not_dispatch(self):
        self.assert_error(self.repair(allowance=None), 'INVALID_BOUNDS')
        self.assertEqual(self.calls, [])
        self.assertIsNone(self.repair().error)
        self.assert_error(self.repair(), 'INVALID_BOUNDS')
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(len(self.reservations), 1)

    def test_format_recovery_spends_the_same_repair_token_across_restart(self):
        format_attempt = self.attempt('proposal_format')
        self.repository.record_attempt(self.turn, self.lease.fence, format_attempt)
        restarted = self.repository.scenario_restart()
        self.assert_error(self.repair(allowance=self.allow(restarted.recover(self.turn))), 'INVALID_BOUNDS')
        self.assertEqual(self.calls, [])
        self.assertEqual(self.reservations, [])

    def test_stale_allowance_snapshot_cannot_bypass_durable_shared_budget(self):
        other = self.attempt('proposal_format').model_copy(update={'attempt_id':'earlier:format'})
        self.repository.record_attempt(self.turn, self.lease.fence, other)
        self.assert_error(self.repair(), 'INVALID_BOUNDS')
        self.assertEqual(self.calls, [])

    def test_provider_failure_consumes_allowance_and_returns_safe_typed_failure(self):
        for failure, code in ((TimeoutError('secret'), 'PROVIDER_TIMEOUT'),
                              (c.ConversationError(code='PROVIDER_UNAVAILABLE', stage='repair.hook',
                                  retryable=True, turn=self.turn, safe_detail='Provider unavailable.'), 'PROVIDER_UNAVAILABLE'),
                              (ValueError('secret'), 'PROVIDER_INVALID_OUTPUT')):
            with self.subTest(code=code):
                self.setUp()
                self.output = failure
                result = self.repair()
                self.assert_error(result, code)
                self.assertNotIn('secret', result.error.safe_detail)
                self.assert_error(self.repair(), 'INVALID_BOUNDS')
                self.assertEqual(len(self.calls), 1)

    def test_blocking_whole_reply_findings_release_no_reply_or_canon(self):
        self.output = self.candidate_for('A🙂éZ I kept the wood.', canon=True)
        self.assert_error(self.repair(), 'PROVIDER_INVALID_OUTPUT')
        self.assertTrue(self.repository.recover(self.turn).repair_consumed)

    def test_unrepairable_findings_fail_before_token_reservation(self):
        self.findings = (self.findings[0].model_copy(update={'repairable':False}),)
        self.assert_error(self.repair(), 'INVALID_INPUT')
        self.assertEqual(self.calls, [])
        self.assertEqual(self.reservations, [])

    def test_operation_bearing_output_and_forged_candidate_fail_strictly(self):
        self.output = self.output.model_dump() | {'operation_candidates':(self.operation.operation,)}
        self.assert_error(self.repair(), 'PROVIDER_INVALID_OUTPUT')
        self.assertEqual(self.operation.operation.command_id, 'give_item')

    def test_action_repair_cannot_omit_or_replace_exact_committed_receipt(self):
        for output in (self.candidate_for('Done.', receipt=False), self.candidate_for('Done.').model_copy(
                update={'segments':(c.ReceiptSlot(kind='receipt_slot', segment_id='outcome',
                    receipt_id='receipt:forged', speech_act='completed', renderer_id='receipt.completed'),)})):
            with self.subTest(output=output):
                self.setUp()
                self.output = output
                self.assert_error(self.repair(), 'PROVIDER_INVALID_OUTPUT')

    def test_deadline_checked_before_dispatch_and_after_late_output(self):
        self.clock[0] = 110
        self.assert_error(self.repair(), 'DEADLINE_EXCEEDED')
        self.assertEqual(self.reservations, [])
        self.clock[0] = 100
        self.delay = 4
        self.assert_error(self.repair(), 'PROVIDER_TIMEOUT')
        self.assert_error(self.repair(), 'INVALID_BOUNDS')
        self.assertEqual(len(self.calls), 1)

    def test_mismatched_turn_or_receipt_fails_before_dispatch(self):
        for assembly in (self.assembly.model_copy(update={'turn':self.turn.model_copy(update={'turn_id':'other'})}),
                self.assembly.model_copy(update={'receipts':(self.receipt.model_copy(update={'turn_id':'other'}),)})):
            with self.subTest(assembly=assembly):
                evidence = self.module.RepairEvidence(context=self.context, assembly=assembly, operation=self.operation)
                self.assert_error(self.repair(evidence=evidence), 'EVIDENCE_CHANGED')
        self.assertEqual(self.reservations, [])

    def test_invalid_grant_fence_and_wrong_turn_never_reach_repair_hook(self):
        for updates in ({'fence':2}, {'turn':self.turn.model_copy(update={'turn_id':'other'})}):
            with self.subTest(updates=updates):
                grant = self.attempt().model_copy(update=updates)
                allowance = self.allow(reserve=lambda *args:grant)
                self.assert_error(self.repair(allowance=allowance), 'INVALID_INPUT')
        self.assertEqual(self.calls, [])

    def test_validator_failure_and_stale_report_fail_closed(self):
        self.service = self.module.RepairService(self.hook,
            lambda *args:c.ValidationReport(report_id='stale', findings=(),
                checked_evidence_revisions=c.RevisionSet(resources={'world':99})), self.policy)
        self.assert_error(self.repair(), 'EVIDENCE_CHANGED')

    def test_ordinary_repair_and_advisory_findings_can_pass_without_receipts(self):
        assembly = self.assembly.model_copy(update={'receipts':(), 'receipt_sources':()})
        self.evidence = self.module.RepairEvidence(context=self.context, assembly=assembly)
        self.candidate = self.candidate_for('Bad wording.', receipt=False)
        self.output = self.candidate_for('I hear you.', receipt=False)
        advisory = self.findings[0].model_copy(update={'severity':'advisory'})
        self.service = self.module.RepairService(self.hook,
            lambda *args:c.ValidationReport(report_id='validation:advisory', findings=(advisory,),
                checked_evidence_revisions=self.context.revisions), self.policy)
        result = self.repair()
        self.assertIsNone(result.error)
        self.assertEqual(result.value.reply.final_text, 'I hear you.')
        self.assertEqual(result.value.receipts, ())
        self.assertIsNone(result.value.operation)

    def test_reservation_failure_never_dispatches_and_cannot_reuse_allowance(self):
        failure = c.ConversationError(code='COMMIT_UNCERTAIN', stage='attempt', retryable=True,
            turn=self.turn, safe_detail='Recover the recorded attempt.')
        self.allowance = self.allow(reserve=lambda *args:failure)
        self.assertEqual(self.repair().error, failure)
        self.assert_error(self.repair(), 'INVALID_BOUNDS')
        self.assertEqual(self.calls, [])

    def test_validator_exception_exposes_no_replacement_or_private_details(self):
        def broken(*args):
            raise RuntimeError('private validation details')
        self.service = self.module.RepairService(self.hook, broken, self.policy)
        result = self.repair()
        self.assert_error(result, 'INTERNAL_FAILURE')
        self.assertNotIn('private', result.error.safe_detail)

    def test_repair_import_has_no_database_or_game_execution_dependencies(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, '-c',
            "import sys; import app.services.conversation.repair; "
            "assert not any(name.split('.')[0] in {'sqlalchemy','fastapi','httpx','openai'} "
            "for name in sys.modules)"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
