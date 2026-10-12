"""Decision evidence through production HTTP routes; providers are deterministic here."""
import json
import unittest
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.orm import Session

import test_behavior_pipeline as behavior_tests
from app.config.settings import get_settings
from app.models import BowQuest, Conversation, NPC, Player
from app.services.decision_trace import proposal_summary
from app.services.llm.service import GenerationResult
from app.services.quests.bow import get_quest


class DecisionTraceTests(unittest.TestCase):
    setUp = behavior_tests.BehaviorPipelineTests.setUp
    chat = behavior_tests.BehaviorPipelineTests.chat

    def answer(self, message, raw):
        with patch('app.services.llm.service.LLMService.generate', return_value=GenerationResult('', raw)):
            return self.chat(message)

    def test_accepted_trace_links_context_proposal_selection_and_persisted_outcome(self):
        data = self.answer('Where is the Gatherer?', dict(answer_kind='answer', fact_ids=['person.gatherer.location']))
        trace = data['decision_trace']
        self.assertEqual(trace['schema_version'], 1)
        self.assertEqual(trace['proposal']['fact_ids'], ['person.gatherer.location'])
        self.assertFalse(trace['validation']['rejected'])
        self.assertEqual(trace['behavior']['ordering'], ['role_conditioning', 'final_control_validation', 'fsec'])
        self.assertEqual(trace['behavior']['selection'], data['behavior_trace']['selection'])
        self.assertTrue(all(v >= 0 for v in trace['timings_seconds'].values()))
        with Session(self.engine) as db:
            saved = db.get(Conversation, trace['outcome']['conversation_id'])
            self.assertEqual(saved.source_event_id, trace['decision_id'])
            self.assertEqual(trace['outcome']['event_id'], saved.source_event_id)
            self.assertEqual(trace['game_scope'], db.get(Player, 1).game_scope)
            self.assertEqual(saved.validated_output['decision_trace'], trace)
            self.assertEqual(data['behavior_trace']['verified_outcome']['event_id'], trace['decision_id'])

    def test_malformed_secrets_and_unrelated_private_state_do_not_enter_trace(self):
        marker = 'PRIVATE_SECRET_TRACE_CANARY'
        with Session(self.engine) as db:
            other = db.get(NPC, 2)
            other.inventory = [marker]
            other.current_state = marker
            db.commit()
        raw = dict(answer_kind='answer', fact_ids=[marker], dialogue=marker,
                   reasoning=marker, api_key=marker, state_update={'trust': marker})
        with patch.object(get_settings(), 'llm_api_key', marker):
            data = self.answer('Where is the Gatherer?', raw)
        self.assertTrue(data['decision_trace']['validation']['rejected'])
        self.assertEqual(data['decision_trace']['validation']['reason'], 'Malformed structured JSON')
        self.assertNotIn(marker, json.dumps(data['decision_trace']))
        self.assertNotIn(marker, json.dumps(data['grounding_trace']))
        self.assertEqual(data['decision_trace']['proposal']['unrecognized_fact_count'], 1)
        with Session(self.engine) as db:
            source = db.scalar(select(Conversation).order_by(Conversation.id.desc()))
            self.assertEqual(source.llm_output, raw)  # original audit retains separate raw proposal

    def test_provider_failure_is_explicit_without_exception_text_or_effects(self):
        with patch('app.services.llm.service.LLMService.generate', side_effect=RuntimeError('secret-transport-token')):
            data = self.chat('Hello')
        trace = data['decision_trace']
        self.assertEqual(trace['generation']['status'], 'provider_or_decode_failure')
        self.assertTrue(trace['validation']['rejected'])
        self.assertIsNone(trace['outcome']['action'])
        self.assertFalse(trace['memory_write']['stored'])
        self.assertNotIn('secret-transport-token', json.dumps(trace))

    def test_authoritative_transfer_bypasses_generation_and_links_real_memory(self):
        with patch('app.services.llm.service.LLMService.generate', side_effect=AssertionError('should bypass')) as provider:
            self.chat('Give me rope')
            data = self.chat('For my work in the village')
        provider.assert_not_called()
        trace = data['decision_trace']
        self.assertEqual(trace['generation'], {'status': 'bypassed', 'authoritative_override': True})
        self.assertEqual(trace['outcome']['transfer']['destination_after'], 1)
        self.assertEqual(trace['memory_write']['source_event_id'], trace['outcome']['event_id'])
        self.assertTrue(trace['memory_write']['stored'])
        self.assertNotIn('inventory_before', trace['outcome'])

    def test_retrieved_claim_keeps_source_status_and_empty_search_is_traced(self):
        first = self.answer('I gave you wood', dict(answer_kind='answer', fact_ids=['quest.bow.delivered']))
        second = self.answer('What have I delivered?', dict(answer_kind='answer', fact_ids=['quest.bow.delivered']))
        context = second['decision_trace']['context']
        self.assertIn(first['memory_classification']['memory_id'], context['memory_retrieval']['selected_ids'])
        self.assertEqual(context['retrieved_memory_provenance'][0]['epistemic_status'], 'claim')
        self.assertEqual(context['retrieved_memory_provenance'][0]['source_event_id'], first['decision_trace']['decision_id'])
        self.assertIn('no materials recorded', second['final_dialogue'])
        self.assertEqual(first['decision_trace']['context']['memory_retrieval']['selected_ids'], [])

    def test_accepted_legacy_prose_and_emotion_are_omitted_from_export(self):
        marker = 'PRIVATE_MODEL_LABEL_CANARY'
        raw = dict(intent=marker, emotion=marker, dialogue='Good to see you.', action='speak',
                   reasoning=marker, state_update={})
        data = self.answer('Hello', raw)
        self.assertFalse(data['grounding_trace']['rejected'])
        self.assertIsNone(data['decision_trace']['behavior']['mapping']['emotion'])
        self.assertNotIn(marker, json.dumps(data['decision_trace']))

    def test_timed_reward_receipt_has_durable_identity_and_is_unique(self):
        with Session(self.engine) as db:
            quest = get_quest(db, 1)
            quest.phase, quest.ready_at = 'crafting', 1
            db.commit()
        first = self.client.post('/quests/bow/advance').json()
        second = self.client.post('/quests/bow/advance').json()
        self.assertEqual(first['player_inventory'].count('bow'), 1)
        self.assertEqual(second['player_inventory'].count('bow'), 1)
        with Session(self.engine) as db:
            sources = list(db.scalars(select(Conversation)))
            self.assertEqual(len(sources), 1)
            receipt = sources[0].validated_output['behavior_trace']['verified_outcome']
            self.assertEqual(receipt['event_id'], sources[0].source_event_id)
            self.assertEqual(receipt['conversation_id'], sources[0].id)

    def test_projection_handles_invalid_numbers_and_bounds_selected_references(self):
        raw = dict(answer_kind='private', action='secret', item='private',
                   fact_ids=['a', 'b', 'c', 'secret', {}],
                   state_update={'trust': 10**400, 'fear': float('nan'), 'aggression': True, 'curiosity': .2})
        trace = proposal_summary(raw, ['a', 'b', 'c'])
        self.assertEqual(trace['fact_ids'], ['a', 'b'])
        self.assertEqual(trace['state_update'], {'curiosity': .2})
        self.assertEqual(trace['unrecognized_fact_count'], 2)
        self.assertTrue(trace['state_update_invalid'])
        self.assertNotIn('secret', json.dumps(trace))


if __name__ == '__main__':
    unittest.main()
