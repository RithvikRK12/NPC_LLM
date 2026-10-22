"""Receipt-first fallback rendering tests."""
import copy
import importlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from app.services.conversation import contracts as c
from app.services.conversation.validation import ResponseValidator

FIXTURES = Path(__file__).parent / 'fixtures/conversation'


class ExplodingValidator(ResponseValidator):
    def check(self, *args, **kwargs):
        raise RuntimeError('validator unavailable')


class FallbackPolicyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('app.services.conversation.fallback'),
                             'FallbackPolicy is not implemented')
        self.module = importlib.import_module('app.services.conversation.fallback')
        self.bounds = c.ConversationPolicy(schema_version=1, policy_version='test:1', input_char_limit=500,
            total_deadline_seconds=10, provider_stage_budget_seconds=5, context_token_limit=1000,
            output_char_limit=600, beat_char_limit=80, queue_capacity=5, lease_duration_seconds=20,
            summary_trigger_turns=10, diagnostic_retention_seconds=100)
        self.policy = self.module.FallbackPolicy(self.bounds, ResponseValidator())
        self.context_raw = json.loads((FIXTURES / 't05-valid.json').read_text())['context']
        self.receipt_raw = json.loads((FIXTURES / 'contracts-t02-valid.json').read_text())['receipt']
        self.context = c.ContextPacket.model_validate(self.context_raw)
        self.receipt_raw['turn_id'] = self.context.turn.turn_id

    def render(self, decision=None, receipt=None, failure=None):
        return self.policy.render(self.context, decision, receipt, failure)

    def test_committed_transfer_takes_priority_over_provider_timeout(self):
        result = self.render(receipt=c.OperationReceipt.model_validate(self.receipt_raw),
            failure=c.ConversationError(code='PROVIDER_TIMEOUT', stage='composition', retryable=True,
                safe_detail='Provider timed out.'))
        self.assertIsNone(result.error)
        self.assertEqual(result.value.final_text, 'I gave you 1 wood.')
        self.assertEqual([source.source_id for source in result.value.evidence_dependencies], ['receipt:1'])

    def test_accepted_inspection_stays_accepted(self):
        receipt = {**self.receipt_raw, 'command_id':'begin_ship_inspection', 'outcome':'accepted',
            'result':{'kind':'activity','activity_id':'activity:inspection','stage':'accepted'},
            'activity_id':'activity:inspection'}
        result = self.render(receipt=c.OperationReceipt.model_validate(receipt),
            failure=c.ConversationError(code='PROVIDER_TIMEOUT', stage='composition', retryable=True,
                safe_detail='Timed out.'))
        self.assertEqual(result.value.final_text, 'I agreed to inspect the ship.')
        self.assertNotIn('completed', result.value.final_text.lower())

    def test_clarification_uses_exact_unresolved_question(self):
        question = 'Do you want me to inspect the ship now?'
        result = self.render(decision=c.ClarificationRequired(kind='clarification_required', concern_ids=('consent',), question=question),
            failure=c.ConversationError(code='INTERNAL_FAILURE', stage='operations', retryable=False,
                safe_detail='failed'))
        self.assertEqual(result.value.final_text, question)

    def test_denial_uses_typed_unavailable_reason_verbatim(self):
        reason = 'I cannot do that while you are outside the workshop.'
        result = self.render(decision=c.Denied(kind='denied', reason_code='OUT_OF_RANGE', safe_explanation=reason))
        self.assertEqual(result.value.final_text, reason)

    def test_generic_failure_has_authored_role_voice_and_invents_no_answer(self):
        failure = c.ConversationError(code='PROVIDER_TIMEOUT', stage='composition', retryable=True,
            safe_detail='could you reveal the hidden answer?')
        craftsman = self.render(failure=failure)
        self.assertIn('workshop', craftsman.value.final_text.lower())
        self.assertNotIn('hidden answer', craftsman.value.final_text.lower())
        gatherer_context = copy.deepcopy(self.context_raw)
        gatherer_context['turn']['key']['npc_id'] = 2
        gatherer_context['pending_interactions'] = []
        gatherer_context.pop('interaction_preconditions', None)
        gatherer_context['character_profile'] = []
        gatherer = self.policy.render(c.ContextPacket.model_validate(gatherer_context), None, None, failure)
        self.assertIn('trail', gatherer.value.final_text.lower())
        self.assertNotEqual(craftsman.value.final_text, gatherer.value.final_text)

    def test_fallback_runs_whole_reply_grounding_validation(self):
        unsupported = c.Denied(kind='denied', reason_code='UNAVAILABLE',
            safe_explanation='The shop is near the north road.')
        result = self.render(decision=unsupported)
        self.assertIsNone(result.value)
        self.assertEqual(result.error.code, 'INVALID_SCHEMA')
        self.assertIn('UNSUPPORTED_WORLD_CLAIM', result.error.safe_detail)

    def test_policy_output_limit_rejects_unrenderable_mandatory_receipt(self):
        tiny = self.bounds.model_copy(update={'output_char_limit': 12, 'beat_char_limit': 12})
        result = self.module.FallbackPolicy(tiny, ResponseValidator()).render(
            self.context, None, c.OperationReceipt.model_validate(self.receipt_raw), None)
        self.assertIsNone(result.value)
        self.assertEqual(result.error.code, 'INVALID_BOUNDS')
        self.assertEqual(result.error.stage, 'conversation.fallback')

    def test_policy_version_mismatch_rejects_fallback_publication(self):
        self.context = c.ContextPacket.model_validate({**self.context.model_dump(),
            'policy_versions':{'bounds':'stale:2'}})
        result = self.render(failure=c.ConversationError(code='PROVIDER_TIMEOUT',
            stage='composition', retryable=True, safe_detail='timeout'))
        self.assertIsNone(result.value)
        self.assertEqual(result.error.code, 'EVIDENCE_CHANGED')

    def test_validator_failure_fails_closed(self):
        policy = self.module.FallbackPolicy(self.bounds, ExplodingValidator())
        result = policy.render(self.context, None, None, None)
        self.assertIsNone(result.value)
        self.assertEqual(result.error.code, 'INTERNAL_FAILURE')

    def test_receipt_renderer_failure_fails_publication_instead_of_omitting_outcome(self):
        with patch.object(self.module, '_receipt_text', side_effect=RuntimeError('renderer failed')):
            result = self.render(receipt=c.OperationReceipt.model_validate(self.receipt_raw))
        self.assertIsNone(result.value)
        self.assertEqual(result.error.code, 'EVIDENCE_CHANGED')
        self.assertIn('committed outcome', result.error.safe_detail)
        self.assertEqual(self.receipt_raw['outcome'], 'completed')

    def test_stale_activity_is_not_reported_as_current_progress(self):
        receipt = {**self.receipt_raw, 'command_id':'begin_ship_inspection', 'outcome':'accepted',
            'result':{'kind':'activity','activity_id':'activity:inspection','stage':'accepted'},
            'activity_id':'activity:inspection'}
        current_source = dict(kind='activity', source_id='activity:inspection', revision=4,
            game_scope=self.context.turn.key.game_scope, npc_id=self.context.turn.key.npc_id,
            attribution='authoritative_game_rules', visibility='public')
        cancelled = c.MechanicalFact(kind='mechanical_fact', evidence_id='activity:current',
            content='{"status":"cancelled"}', sources=(current_source,), created_at='2026-10-18T00:00:00Z')
        self.context = c.ContextPacket.model_validate({**self.context.model_dump(),
            'visible_facts':[cancelled], 'revisions':{'resources':{'activity:inspection':4}}})
        result = self.render(receipt=c.OperationReceipt.model_validate(receipt))
        self.assertEqual(result.value.final_text, 'I agreed to inspect the ship.')
        self.assertNotIn('still', result.value.final_text.lower())
        self.assertNotIn('continuing', result.value.final_text.lower())


if __name__ == '__main__':
    unittest.main()
