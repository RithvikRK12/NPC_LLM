import json
import time
import unittest
from unittest.mock import patch

import test_npc_pipeline as helpers
from app.models import NPC, Player, BowQuest
from app.services.llm.service import LLMService
from app.services.llm.openai_compatible import OpenAICompatibleProvider
from app.services.semantic_routing import AcceptedInterpretation, Concern


class GathererWoodRecoveryTests(unittest.TestCase):
    setUp = helpers.NPCPipelineTests.setUp
    tearDown = helpers.NPCPipelineTests.tearDown
    _test_interpretation = helpers.NPCPipelineTests._test_interpretation

    def prepare(self):
        from app.services.quests.bow import get_quest
        player = self.db.get(Player, 1)
        player.opening_state = 'complete'
        self.db.flush()
        get_quest(self.db).phase = 'gather'
        gatherer = self.db.get(NPC, 2)
        gatherer.aggression, gatherer.trust = 1., 0.
        self.scope = player.game_scope
        self.db.commit()

    def say(self, npc_id, message, kind='operation_request', target='wood', operation='give_item', purpose=None,
            answer_type=None, pending_question_id=None):
        concern = Concern(id='c1', kind=kind, evidence=message, start=0, end=len(message),
            modality='direct', target=target, operation=operation, purpose=purpose,
            answer_type=answer_type, pending_question_id=pending_question_id)
        interpretation = AcceptedInterpretation(version=1, concerns=[concern], clarification=None)
        with patch.object(LLMService, 'interpret', return_value=(interpretation, .001)), patch.object(
                OpenAICompatibleProvider, 'generate', return_value=json.dumps({
                    'answer_kind': 'chat', 'fact_ids': [], 'dialogue': 'I hear you.'})):
            response = self.client.post('/chat', json={'npc_id': npc_id, 'player_message': message,
                                                      'game_scope': self.scope})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def give(self, npc, item):
        response = self.client.post('/inventory/transfer', json={'npc_id': npc, 'item': item,
            'direction': 'to_npc', 'game_scope': self.scope})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_refusal_advice_forest_gifts_restore_wood_and_finish_bow(self):
        self.prepare()
        refused = self.say(2, 'Please give me wood to make a bow.', purpose='to make a bow')
        self.assertNotIn('wood', refused['player_inventory'])
        self.assertIn('angry', refused['final_dialogue'].lower())
        self.assertIsNone(refused['npc']['pending_item'])
        advice = self.say(1, "The Gatherer is furious and won't share lumber.",
                          kind='player_report', target='gatherer', operation=None)
        self.assertIn('honeycomb', advice['final_dialogue'].lower())
        recovery = advice['bow_quest']['gatherer_recovery']
        self.assertTrue(recovery['hint_unlocked'])
        self.assertEqual(len(recovery['pickups']), 3)
        # Save/reload projection must preserve the new objective and pickup state.
        world = self.client.get('/world').json()
        self.assertTrue(world['bow_quest']['gatherer_recovery']['hint_unlocked'])
        for index, pickup in enumerate(recovery['pickups'][:2]):
            payload = {'game_scope': self.scope, 'pickup_id': pickup['id'], **pickup['position']}
            taken = self.client.post('/quests/bow/pickup-honeycomb', json=payload)
            self.assertEqual(taken.status_code, 200, taken.text)
            repeated = self.client.post('/quests/bow/pickup-honeycomb', json=payload)
            self.assertEqual(repeated.status_code, 200, repeated.text)
            self.assertEqual(repeated.json()['player_inventory'].count('honeycomb'), 1)
            gifted = self.give(2, 'honeycomb')
            self.assertNotIn('honeycomb', gifted['player_inventory'])
            self.assertAlmostEqual(gifted['npc']['aggression'], 1. - .4 * (index + 1))
            self.assertAlmostEqual(gifted['npc']['trust'], .3 * (index + 1))
        wood = self.say(2, 'Please give me wood to make a bow.', purpose='to make a bow')
        self.assertEqual(wood['player_inventory'].count('wood'), 1)
        self.give(1, 'wood')
        picked = self.client.post('/quests/bow/pickup-string', json={'x': -70., 'y': 240.})
        self.assertEqual(picked.status_code, 200, picked.text)
        crafting = self.give(1, 'string')
        self.assertEqual(crafting['bow_quest']['phase'], 'crafting')
        self.db.get(BowQuest, 1).ready_at = time.time() - 1
        self.db.commit()
        completed = self.client.post('/quests/bow/advance').json()
        self.assertEqual(completed['bow_quest']['phase'], 'completed')
        self.assertEqual(completed['player_inventory'].count('bow'), 1)

    def test_unowned_gifts_do_not_change_emotions_and_pickups_require_advice(self):
        self.prepare()
        unowned = self.client.post('/inventory/transfer', json={'npc_id': 2, 'item': 'honeycomb',
            'direction': 'to_npc', 'game_scope': self.scope})
        self.assertEqual(unowned.status_code, 404, unowned.text)
        self.db.expire_all()
        self.assertEqual(self.db.get(NPC, 2).aggression, 1.)
        self.assertEqual(self.db.get(NPC, 2).trust, 0.)
        response = self.client.post('/quests/bow/pickup-honeycomb', json={
            'game_scope': self.scope, 'pickup_id': 'honeycomb-1', 'x': -880., 'y': 224.})
        self.assertEqual(response.status_code, 409, response.text)

    def unlock(self):
        self.prepare()
        self.say(2, 'Can I have wood?')
        return self.say(1, 'The Gatherer refused the wood.', kind='player_report',
                        target='gatherer', operation=None)['bow_quest']['gatherer_recovery']

    def test_pending_wood_request_is_rechecked_after_gatherer_becomes_angry(self):
        self.prepare()
        npc = self.db.get(NPC, 2)
        npc.aggression, npc.trust = .1, .7
        self.db.commit()
        pending = self.say(2, 'Can I have wood?')
        self.assertEqual(pending['npc']['pending_item'], 'wood')
        self.db.get(NPC, 2).aggression = .9
        self.db.commit()
        refused = self.say(2, 'For making a bow.', kind='pending_answer', operation=None,
            answer_type='purpose', pending_question_id='purpose:wood')
        self.assertNotIn('wood', refused['player_inventory'])
        self.assertIsNone(refused['npc']['pending_item'])
        self.assertTrue(refused['bow_quest']['gatherer_recovery']['refused'])

    def test_pickup_rejects_far_or_stale_requests_and_reset_clears_recovery(self):
        recovery = self.unlock()
        pickup = recovery['pickups'][0]
        base = {'game_scope': self.scope, 'pickup_id': pickup['id'], **pickup['position']}
        for changed, code in (({'game_scope': 'old-save'}, 409), ({'x': 0, 'y': 0}, 409),
                               ({'pickup_id': 'invented'}, 400)):
            with self.subTest(changed=changed):
                result = self.client.post('/quests/bow/pickup-honeycomb', json=base | changed)
                self.assertEqual(result.status_code, code, result.text)
        reset = self.client.post('/world/new-game').json()
        self.assertNotEqual(reset['game_scope'], self.scope)
        self.assertFalse(reset['bow_quest']['gatherer_recovery']['hint_unlocked'])
        self.assertFalse(reset['bow_quest']['gatherer_recovery']['refused'])
        self.assertNotIn('honeycomb', reset['player_inventory'])

    def test_giving_honeycomb_to_craftsman_does_not_calm_gatherer(self):
        recovery = self.unlock()
        pickup = recovery['pickups'][0]
        result = self.client.post('/quests/bow/pickup-honeycomb', json={
            'game_scope': self.scope, 'pickup_id': pickup['id'], **pickup['position']})
        self.assertEqual(result.status_code, 200, result.text)
        given = self.give(1, 'honeycomb')
        self.assertNotIn('honeycomb', given['player_inventory'])
        self.db.expire_all()
        self.assertEqual(self.db.get(NPC, 2).aggression, 1.)
        self.assertEqual(self.db.get(NPC, 2).trust, 0.)
        self.assertEqual(given['bow_quest']['gatherer_recovery']['gifts_given'], 0)
