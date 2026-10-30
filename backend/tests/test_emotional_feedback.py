import json
import unittest
from unittest.mock import patch

import test_npc_pipeline as helpers
from app.models import NPC, Player
from app.services.llm.openai_compatible import OpenAICompatibleProvider


class EmotionalFeedbackTests(unittest.TestCase):
    setUp = helpers.NPCPipelineTests.setUp
    tearDown = helpers.NPCPipelineTests.tearDown
    _test_interpretation = helpers.NPCPipelineTests._test_interpretation

    def prepare(self):
        npc = self.db.get(NPC, 2)
        npc.trust, npc.fear, npc.aggression, npc.curiosity = .1, .1, .9, .8
        self.db.get(Player, 1).opening_state = 'complete'
        self.db.commit()

    def say(self, effect='conciliatory', spoofed_delta=None):
        from app.services.semantic_routing import AcceptedInterpretation, Concern
        from app.services.llm.service import LLMService
        message = 'I am sorry for being rude. I want to listen.'
        interpretation = AcceptedInterpretation(version=1, concerns=[Concern(id='c1',
            kind='social', evidence=message, start=0, end=len(message), modality='direct',
            social_effect=effect)], clarification=None)
        raw = {'answer_kind': 'chat', 'fact_ids': [], 'dialogue': "All right. I'm listening."}
        if spoofed_delta is not None: raw['state_update'] = spoofed_delta
        with patch.object(LLMService, 'interpret', return_value=(interpretation, .001)), patch.object(OpenAICompatibleProvider, 'generate', return_value=json.dumps(raw)) as generate:
            response = self.client.post('/chat', json={'npc_id': 2,
                'player_message': 'I am sorry for being rude. I want to listen.'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(generate.call_count, 1)
        return response.json()

    def test_social_reaction_is_persisted_and_returned_for_ui_refresh(self):
        self.prepare()
        inventory = list(self.db.get(Player, 1).inventory)
        result = self.say()
        self.assertFalse(result['grounding_trace']['rejected'])
        for field, expected in (('trust', .3), ('fear', 0.), ('aggression', .7), ('curiosity', .9)):
            self.assertAlmostEqual(result['npc'][field], expected)
        self.db.expire_all()
        self.assertAlmostEqual(self.db.get(NPC, 2).trust, .3)
        self.assertEqual(self.db.get(Player, 1).inventory, inventory)

    def test_speech_cannot_propose_its_own_changes(self):
        self.prepare()
        result = self.say(spoofed_delta={'trust': .5})
        self.assertTrue(result['grounding_trace']['rejected'])
        self.assertEqual(result['npc']['trust'], .1)

    def test_neutral_reaction_may_leave_values_unchanged(self):
        self.prepare()
        result = self.say(effect='neutral')
        self.assertFalse(result['grounding_trace']['rejected'])
        self.assertEqual(result['npc']['trust'], .1)
        self.assertEqual(result['npc']['aggression'], .9)

    def test_quoted_conduct_has_no_effect_and_multiple_effects_are_capped(self):
        from app.services.npc.emotional_feedback import emotional_feedback
        quoted = {'kind': 'social', 'modality': 'quoted', 'social_effect': 'antagonistic'}
        self.assertFalse(any(emotional_feedback({'concerns': [quoted]}).model_dump().values()))
        hostile = {'kind': 'social', 'modality': 'direct', 'social_effect': 'antagonistic'}
        delta = emotional_feedback({'concerns': [hostile] * 8})
        self.assertEqual(delta.trust, -.4)
        self.assertEqual(delta.aggression, .4)

    def test_hostile_social_reaction_is_not_limited_by_legacy_role_delta_cap(self):
        self.prepare()
        self.db.get(NPC, 2).aggression = .3
        self.db.commit()
        result = self.say(effect='antagonistic')
        self.assertFalse(result['grounding_trace']['rejected'])
        self.assertAlmostEqual(result['npc']['aggression'], .6)
        self.assertEqual(result['npc']['trust'], 0.)
