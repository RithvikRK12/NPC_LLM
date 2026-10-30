from __future__ import annotations

import unittest
import json
from unittest.mock import patch

from app.services.semantic_routing import AcceptedInterpretation, Concern, InterpretationContext


class SemanticRoutingContractTests(unittest.TestCase):
    def test_decoder_requires_real_operation_and_binds_pending_answers(self):
        schema = AcceptedInterpretation.json_schema(
            capabilities=[{'id': 'craftsman.begin_inspection', 'targets': ['ship']}],
            pending_question={'id': 'craftsman:ship-inspection'})
        item = schema['properties']['concerns']['items']
        variants = item.get('anyOf', [item])
        actions = [v['properties'] for v in variants
                   if 'operation_request' in v['properties']['kind']['enum']]
        self.assertTrue(actions)
        for properties in actions:
            self.assertEqual(properties['operation']['type'], 'string')
            self.assertEqual(properties['operation']['enum'], ['craftsman.begin_inspection'])
            self.assertEqual(properties['target']['enum'], ['ship'])
        answers = [v['properties'] for v in variants
                   if 'pending_answer' in v['properties']['kind']['enum']]
        self.assertTrue(answers)
        for properties in answers:
            self.assertEqual(properties['pending_question_id']['enum'], ['craftsman:ship-inspection'])
            self.assertNotIn(None, properties['answer_type']['enum'])
            self.assertEqual(properties['operation']['type'], 'null')

    def test_ship_report_with_irrelevant_purpose_preserves_intent_without_retry(self):
        from app.services.llm.provider import LLMProvider
        from app.services.llm.service import LLMService
        message = "my ship wrecked! i'm stranded"
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'player_report',
            'evidence': 'my ship wrecked!', 'start': 0, 'end': 10,
            'modality': 'direct', 'target': 'ship', 'fact_ids': [],
            'pending_question_id': None, 'answer_type': None, 'operation': None,
            'purpose': 'ship inspection'}], 'clarification': None}
        class Provider(LLMProvider):
            calls = 0
            def generate(self, prompt, context):
                self.calls += 1
                return json.dumps(raw)
        provider = Provider()
        context = InterpretationContext(message=message, history=[], facts=[], capabilities=[])
        accepted, _ = LLMService(provider=provider).interpret(context)
        concern = accepted.concerns[0]
        self.assertEqual(concern.kind, 'player_report')
        self.assertEqual(concern.target, 'ship')
        self.assertEqual(concern.end, 16)
        self.assertIsNone(concern.purpose)
        self.assertIsNone(concern.operation)
        self.assertEqual(provider.calls, 1)

    def test_operation_with_invented_purpose_is_still_rejected_without_retry(self):
        from app.services.llm.provider import LLMProvider
        from app.services.llm.service import LLMService
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'operation_request',
            'evidence': 'Give me wood.', 'start': 0, 'end': 13,
            'modality': 'direct', 'target': 'wood', 'fact_ids': [],
            'operation': 'give_item', 'purpose': 'to build a ship'}], 'clarification': None}
        class Provider(LLMProvider):
            calls = 0
            def generate(self, prompt, context):
                self.calls += 1
                return json.dumps(raw)
        provider = Provider()
        context = InterpretationContext(message='Give me wood.', history=[], facts=[],
            capabilities=[{'id': 'give_item', 'targets': ['wood']}])
        with self.assertRaisesRegex(ValueError, 'purpose must be an exact unique span'):
            LLMService(provider=provider).interpret(context)
        self.assertEqual(provider.calls, 1)

    def test_span_repair_preserves_ship_report_target_for_encounter_routing(self):
        from app.services.llm.provider import LLMProvider
        from app.services.llm.service import LLMService
        message = 'My ship wrecked.'
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'player_report',
            'evidence': message, 'start': 0, 'end': len(message) + 1,
            'modality': 'direct', 'target': 'ship', 'fact_ids': [],
            'pending_question_id': None, 'answer_type': None, 'operation': None,
            'purpose': None}], 'clarification': None}
        class Provider(LLMProvider):
            def generate(self, prompt, context):
                return json.dumps(raw)
        context = InterpretationContext(message=message, history=[], facts=[], capabilities=[])
        accepted, _ = LLMService(provider=Provider()).interpret(context)
        self.assertEqual(accepted.concerns[0].target, 'ship')
        self.assertEqual(accepted.concerns[0].end, len(message))

    def test_contract_rejects_unknown_fields_and_invalid_evidence_spans(self):
        context = InterpretationContext(message='I am well.', history=[], facts=[], capabilities=[])
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'social', 'evidence': 'well',
               'start': 100, 'end': 104, 'modality': 'direct', 'target': None,
               'fact_ids': [], 'pending_question_id': None, 'operation': None, 'purpose': None}], 'clarification': None}
        with self.assertRaises(ValueError):
            AcceptedInterpretation.validate_for_context(raw, context)

    def test_contract_accepts_contextual_social_concern_with_exact_span(self):
        message = "I'm good! Thanks for asking."
        context = InterpretationContext(message=message, history=[], facts=[], capabilities=[])
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'social', 'evidence': message,
               'start': 0, 'end': len(message), 'modality': 'direct', 'target': None,
               'fact_ids': [], 'pending_question_id': None, 'operation': None, 'purpose': None}], 'clarification': None}
        accepted = AcceptedInterpretation.validate_for_context(raw, context)
        self.assertEqual(accepted.concerns[0].kind, 'social')

    def test_contract_requires_capability_membership_for_operations(self):
        context = InterpretationContext(message='Give me rope for nets.', history=[], facts=[], capabilities=[])
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'operation_request',
               'evidence': 'Give me rope', 'start': 0, 'end': 12, 'modality': 'direct',
               'target': 'rope', 'fact_ids': [], 'pending_question_id': None,
               'operation': 'give_item', 'purpose': None}], 'clarification': None}
        with self.assertRaises(ValueError):
            AcceptedInterpretation.validate_for_context(raw, context)

    def test_contract_rejects_unsupported_operation_targets(self):
        context = InterpretationContext(message='Give me rope.', history=[], facts=[],
            capabilities=[{'id': 'give_item', 'targets': ['wood']}])
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'operation_request',
            'evidence': 'Give me rope', 'start': 0, 'end': 12, 'modality': 'direct',
            'target': 'rope', 'fact_ids': [], 'pending_question_id': None,
            'answer_type': None, 'operation': 'give_item', 'purpose': None}], 'clarification': None}
        with self.assertRaisesRegex(ValueError, 'target is not supported'):
            AcceptedInterpretation.validate_for_context(raw, context)

    def test_pending_answer_cannot_omit_or_mismatch_current_question(self):
        context = InterpretationContext(message='Yes.', history=[], facts=[], capabilities=[],
            pending_question={'id': 'purpose:wood', 'item': 'wood'})
        for question_id in (None, 'purpose:rope'):
            raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'pending_answer',
                'evidence': 'Yes.', 'start': 0, 'end': 4, 'modality': 'direct', 'target': 'wood',
                'fact_ids': [], 'pending_question_id': question_id, 'answer_type': 'assent', 'operation': None, 'purpose': None}],
                'clarification': None}
            with self.subTest(question_id=question_id), self.assertRaisesRegex(ValueError, 'current question'):
                AcceptedInterpretation.validate_for_context(raw, context)

    def test_direct_transfer_uses_only_an_exact_current_message_purpose(self):
        from app.services.validation.items import transfer_interpretation
        message = 'Would you mind bringing me a lantern? I want to light the doorway.'
        start = message.index('bringing')
        end = message.index('?', start)
        purpose = 'I want to light the doorway'
        context = InterpretationContext(message=message, history=[], facts=[], capabilities=[
            {'id': 'give_item', 'targets': ['lantern']}])
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'operation_request',
            'evidence': message[start:end], 'start': start, 'end': end, 'modality': 'direct',
            'target': 'lantern', 'fact_ids': [], 'pending_question_id': None,
            'answer_type': None, 'operation': 'give_item', 'purpose': purpose}], 'clarification': None}
        accepted = AcceptedInterpretation.validate_for_context(raw, context)
        result = transfer_interpretation(accepted.model_dump(), ['lantern'], [])
        self.assertEqual(result.action, 'give_item')
        self.assertEqual(result.item, 'lantern')

    def test_interpreter_requests_the_versioned_schema_from_local_provider(self):
        from app.services.llm.openai_compatible import OpenAICompatibleProvider
        message = 'I am doing well, thanks.'
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'social', 'evidence': message,
               'start': 0, 'end': len(message), 'modality': 'direct', 'target': None,
               'fact_ids': [], 'pending_question_id': None, 'answer_type': None, 'operation': None, 'purpose': None}],
               'clarification': None}
        context = InterpretationContext(message=message, history=[], facts=[], capabilities=[])
        with patch('app.services.llm.openai_compatible.httpx.Client') as client_class:
            response = client_class.return_value.__enter__.return_value.post.return_value
            response.json.return_value = {'choices': [{'message': {'content': json.dumps(raw)}}]}
            provider = OpenAICompatibleProvider()
            provider._settings = provider._settings.model_copy(update={'llm_base_url': 'http://test/v1'})
            from app.services.llm.service import LLMService
            accepted, _ = LLMService(provider=provider).interpret(context)
            payload = client_class.return_value.__enter__.return_value.post.call_args.kwargs['json']
        self.assertEqual(accepted.version, 1)
        self.assertEqual(context.provider_calls, 1)
        self.assertEqual(payload['messages'][-1], {'role': 'user', 'content': message})
        self.assertEqual(payload['response_format']['json_schema']['name'], 'chat_interpretation_v1')
        self.assertEqual(payload['response_format']['json_schema']['schema'], AcceptedInterpretation.json_schema())

    def test_exact_quote_span_repair_uses_only_one_provider_call(self):
        from app.services.llm.provider import LLMProvider
        from app.services.llm.service import LLMService
        message = 'That is kind of you.'
        raw = {'version': 1, 'concerns': [{'id': 'c1', 'kind': 'social', 'evidence': message,
            'start': 0, 'end': len(message) + 9, 'modality': 'direct', 'target': None, 'fact_ids': [],
            'pending_question_id': None, 'answer_type': None, 'operation': None, 'purpose': None}], 'clarification': None}
        class Provider(LLMProvider):
            def __init__(self): self.calls = []
            def generate(self, prompt, context): self.calls.append(context.copy()); return json.dumps(raw)
        provider = Provider()
        context = InterpretationContext(message=message, history=[], facts=[], capabilities=[])
        accepted, _ = LLMService(provider=provider).interpret(context)
        self.assertEqual(accepted.concerns[0].end, len(message))
        self.assertEqual(context.provider_calls, 1)
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(context.span_repairs, 1)

    def test_invalid_interpretation_is_not_retried(self):
        from app.services.llm.provider import LLMProvider
        from app.services.llm.service import LLMService
        class Provider(LLMProvider):
            calls = 0
            def generate(self, prompt, context):
                self.calls += 1
                return '{}'
        provider = Provider()
        context = InterpretationContext(message='Hello', history=[], facts=[], capabilities=[])
        with self.assertRaises(ValueError):
            LLMService(provider=provider).interpret(context)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(context.provider_calls, 1)


if __name__ == '__main__':
    unittest.main()
