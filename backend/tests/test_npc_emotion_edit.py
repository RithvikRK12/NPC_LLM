import unittest

import test_npc_pipeline as helpers
from app.models import NPC, Player


class NPCEmotionEditTests(unittest.TestCase):
    setUp = helpers.NPCPipelineTests.setUp
    tearDown = helpers.NPCPipelineTests.tearDown
    _test_interpretation = helpers.NPCPipelineTests._test_interpretation

    def payload(self):
        return {'game_scope': self.db.get(Player, 1).game_scope,
                'trust': .8, 'fear': .2, 'aggression': .1, 'curiosity': .9}

    def test_edit_persists_values_and_invalidates_old_generation_without_changing_inventory(self):
        npc = self.db.get(NPC, 1)
        revision, inventory = npc.memory_revision, list(npc.inventory)
        response = self.client.patch('/npc/1/emotions', json=self.payload())
        self.assertEqual(response.status_code, 200, response.text)
        self.db.expire_all()
        npc = self.db.get(NPC, 1)
        self.assertEqual((npc.trust, npc.fear, npc.aggression, npc.curiosity), (.8, .2, .1, .9))
        self.assertNotEqual(npc.memory_revision, revision)
        self.assertEqual(npc.inventory, inventory)
        self.assertEqual(response.json()['trust'], .8)
        from app.services.context.builder import ContextBuilder
        context = ContextBuilder(self.db).build(npc, self.db.get(Player, 1), 'hello')
        self.assertEqual(context.npc_state['trust'], .8)
        self.assertEqual(context.npc_state['fear'], .2)

    def test_edit_rejects_wrong_save_out_of_range_and_extra_fields(self):
        for change, code in (({'game_scope': 'old-save'}, 409), ({'fear': -0.1}, 422),
                             ({'trust': 1.1}, 422), ({'inventory': ['bow']}, 422)):
            with self.subTest(change=change):
                response = self.client.patch('/npc/1/emotions', json=self.payload() | change)
                self.assertEqual(response.status_code, code, response.text)

