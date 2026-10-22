"""Proposal-stage boundary tests with scripted typed provider outputs."""
import copy
import importlib
import json
from pathlib import Path
import unittest

from pydantic import ValidationError

from app.services.conversation import contracts as c
from app.services.llm.structured import (
    GenerationCancelled,
    GenerationMalformed,
    GenerationUnavailable,
    GenerationVersionUnsupported,
)

FIXTURES = Path(__file__).parent / 'fixtures/conversation'


class ScriptedGeneration:
    def __init__(self, output, clock):
        self.output = output
        self.clock = clock
        self.calls = []

    def generate(self, purpose, context, deadline, dialogue_codepoint_limit):
        self.calls.append((purpose, context, deadline, dialogue_codepoint_limit))
        if isinstance(self.output, Exception):
            raise self.output
        return self.output


class ProposalServiceTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module('app.services.conversation.proposal')
        self.assertTrue(hasattr(self.module, 'ProposalService'), 'ProposalService is not implemented')
        self.raw = json.loads((FIXTURES / 't05-valid.json').read_text())
        self.context = c.ContextPacket.model_validate(self.raw['context'])
        self.proposal = c.TurnProposal.model_validate(self.raw['proposal'])
        self.clock = [100.0]
        self.deadline = c.Deadline.after(10, clock=lambda: self.clock[0])
        self.policy = c.ConversationPolicy(schema_version=1, policy_version='test:1', input_char_limit=500,
            total_deadline_seconds=10, provider_stage_budget_seconds=4, context_token_limit=1000,
            output_char_limit=600, beat_char_limit=80, queue_capacity=5, lease_duration_seconds=20,
            summary_trigger_turns=10, diagnostic_retention_seconds=100)
        self.provider = ScriptedGeneration(self.proposal, self.clock)
        self.service = self.module.ProposalService(self.provider, self.policy)

    def propose(self):
        return self.service.propose(self.context, self.deadline)

    def test_one_call_preserves_multiple_concerns_and_all_intent_modalities(self):
        raw = copy.deepcopy(self.raw['proposal'])
        raw['concerns'] = [
            {'concern_id':'concern:feel','kind':'emotion','message_spans':[{'text_id':'message:2','start':0,'end':2}]},
            {'concern_id':'concern:ask','kind':'request','message_spans':[{'text_id':'message:2','start':3,'end':8}]},
        ]
        # The fixture has only an expressive segment; the proposal contract keeps
        # all distinct modality labels instead of collapsing them to consent.
        operation = {
            'candidate_id':'op:1','command_id':'give_item','arguments':{'item':'wood'},
            'target':{'reference_id':'npc:1','entity_kind':'npc','entity_id':'1'},
            'source_spans':[{'text_id':'message:2','start':3,'end':8}],
            'modality':'direct','pending_question_id':None,
        }
        raw['operation_candidates'] = [
            {**operation,'candidate_id':f'op:{index}','modality':modality}
            for index, modality in enumerate(('direct','quoted','hypothetical','negated','ambiguous'), 1)
        ]
        self.context = c.ContextPacket.model_validate({**self.context.model_dump(), 'capabilities':[
            {'command_id':'give_item','parameter_schema':{'kind':'single_item','allowed_items':['wood']},
             'allowed_target_references':[operation['target']], 'available':True,
             'safe_unavailable_reason':None, 'relevant_preconditions':[],
             'supported_speech_acts':['request']}
        ]})
        self.provider.output = c.TurnProposal.model_validate(raw)
        self.service = self.module.ProposalService(self.provider, self.policy)

        result = self.propose()

        self.assertIsNone(result.error)
        self.assertEqual(result.value.concerns[0].kind, 'emotion')
        self.assertEqual(result.value.concerns[1].kind, 'request')
        self.assertEqual([op.modality for op in result.value.operation_candidates],
                         ['direct','quoted','hypothetical','negated','ambiguous'])
        self.assertEqual(len(self.provider.calls), 1)
        purpose, sent_context, stage_deadline, budget = self.provider.calls[0]
        self.assertEqual(purpose, 'proposal')
        self.assertEqual(sent_context, self.context)
        self.assertEqual(stage_deadline.expires_at, 104.0)
        self.assertEqual(budget, self.policy.output_char_limit)

    def test_lifecycle_cues_are_checked_against_current_context(self):
        result = self.propose()
        self.assertIsNone(result.error)
        self.assertEqual(len(result.value.interaction_lifecycle_cues), 2)
        self.assertEqual(result.value.interaction_lifecycle_cues[0].turn, self.context.turn)

        stale = copy.deepcopy(self.raw['proposal'])
        stale['interaction_lifecycle_cues'][0]['source_span']['start'] += 1
        self.provider.output = c.TurnProposal.model_validate(stale)
        self.service = self.module.ProposalService(self.provider, self.policy)
        rejected = self.propose()
        self.assertEqual(rejected.error.code, 'PROVIDER_INVALID_OUTPUT')

    def test_unknown_pending_interaction_is_rejected(self):
        raw = copy.deepcopy(self.raw['proposal'])
        raw['interaction_lifecycle_cues'][0]['interaction_id'] = 'interaction:unknown'
        self.provider.output = c.TurnProposal.model_validate(raw)
        result = self.propose()
        self.assertEqual(result.error.code, 'PROVIDER_INVALID_OUTPUT')

    def test_context_text_ids_cannot_resolve_to_conflicting_text(self):
        raw_context = copy.deepcopy(self.raw['context'])
        raw_context['pending_interactions'][0]['question_id'] = 'message:2'
        self.context = c.ContextPacket.model_validate(raw_context)
        self.service = self.module.ProposalService(self.provider, self.policy)
        result = self.propose()
        self.assertEqual(result.error.code, 'PROVIDER_INVALID_OUTPUT')

    def test_wrong_output_type_and_extra_fields_fail_closed(self):
        self.provider.output = {'unexpected':'field'}
        wrong = self.propose()
        self.assertEqual(wrong.error.code, 'PROVIDER_INVALID_OUTPUT')
        self.provider.output = self.proposal.model_dump(mode='json') | {'extra_field':'reject'}
        extra = self.propose()
        self.assertEqual(extra.error.code, 'PROVIDER_INVALID_OUTPUT')
        self.assertEqual(len(self.provider.calls), 2)

    def test_trusted_typed_proposal_with_empty_reply_is_revalidated_and_rejected(self):
        self.provider.output = self.proposal.model_copy(update={'reply': ()})

        result = self.propose()

        self.assertEqual(result.error.code, 'PROVIDER_INVALID_OUTPUT')

    def test_invalid_unicode_span_is_rejected(self):
        raw = copy.deepcopy(self.raw['proposal'])
        cue = raw['interaction_lifecycle_cues'][0]
        cue['source_span'] = {'text_id':'message:2','start':2,'end':100}
        cue['source_text'] = 'Cancel the wood'
        self.provider.output = c.TurnProposal.model_validate(raw)
        result = self.propose()
        self.assertEqual(result.error.code, 'PROVIDER_INVALID_OUTPUT')

    def test_command_must_be_in_context_capabilities_with_matching_bounds(self):
        operation = {
            'candidate_id':'op:1','command_id':'give_item','arguments':{'item':'wood'},
            'target':{'reference_id':'npc:1','entity_kind':'npc','entity_id':'1'},
            'source_spans':[{'text_id':'message:2','start':2,'end':17}],
            'modality':'direct','pending_question_id':None,
        }
        raw = copy.deepcopy(self.raw['proposal'])
        raw['operation_candidates'] = [operation]
        self.provider.output = c.TurnProposal.model_validate(raw)
        rejected = self.propose()
        self.assertEqual(rejected.error.code, 'PROVIDER_INVALID_OUTPUT')

        self.context = c.ContextPacket.model_validate({**self.context.model_dump(), 'capabilities':[
            {'command_id':'give_item','parameter_schema':{'kind':'single_item','allowed_items':['wood']},
             'allowed_target_references':[operation['target']], 'available':False,
             'safe_unavailable_reason':'not available', 'relevant_preconditions':[],
             'supported_speech_acts':['request']}
        ]})
        self.provider.output = c.TurnProposal.model_validate(raw)
        self.service = self.module.ProposalService(self.provider, self.policy)
        unavailable = self.propose()
        self.assertEqual(unavailable.error.code, 'PROVIDER_INVALID_OUTPUT')

    def test_unsupported_command_and_contract_extra_fields_are_rejected(self):
        raw = copy.deepcopy(self.raw['proposal'])
        raw['operation_candidates'] = [{
            'candidate_id':'op:1','command_id':'attack','arguments':{},
            'target':{'reference_id':'npc:1','entity_kind':'npc','entity_id':'1'},
            'source_spans':[{'text_id':'message:2','start':2,'end':17}],
            'modality':'direct','pending_question_id':None,
        }]
        with self.assertRaises(ValidationError):
            c.TurnProposal.model_validate(raw)
        with self.assertRaises(ValidationError):
            c.TurnProposal.model_validate(self.raw['proposal'] | {'extra_field':'reject'})

    def test_timeout_is_a_typed_failure_after_one_call(self):
        self.provider.output = TimeoutError('late')
        result = self.propose()
        self.assertEqual(result.error.code, 'PROVIDER_TIMEOUT')
        self.assertEqual(len(self.provider.calls), 1)

    def test_provider_failures_keep_distinct_typed_classification(self):
        cases = (
            (GenerationUnavailable('hidden endpoint'), 'PROVIDER_UNAVAILABLE', 'proposal.propose'),
            (GenerationCancelled('cancelled'), 'INTERNAL_FAILURE', 'proposal.cancelled'),
            (GenerationMalformed('bad json'), 'PROVIDER_INVALID_OUTPUT', 'proposal.provider_output'),
            (GenerationVersionUnsupported('future schema'), 'PROVIDER_INVALID_OUTPUT', 'proposal.provider_version'),
        )
        for exception, code, stage in cases:
            with self.subTest(code=code, stage=stage):
                self.provider.calls.clear()
                self.provider.output = exception
                result = self.propose()
                self.assertEqual(result.error.code, code)
                self.assertEqual(result.error.stage, stage)
                self.assertNotIn('hidden endpoint', result.error.safe_detail)
                self.assertNotIn('bad json', result.error.safe_detail)
                self.assertNotIn('future schema', result.error.safe_detail)
                self.assertEqual(len(self.provider.calls), 1)


if __name__ == '__main__':
    unittest.main()
