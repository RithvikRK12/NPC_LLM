"""Accepted semantic consent must reach the authoritative follow activity."""
import unittest
from unittest.mock import patch

import test_npc_pipeline as helpers
from app.models import NPC, Player
from app.services.craftsman import apply_command, record
from app.services.llm.service import LLMService
from app.services.semantic_routing import AcceptedInterpretation, Concern


class ShipwreckRoutingTests(unittest.TestCase):
    setUp = helpers.NPCPipelineTests.setUp
    tearDown = helpers.NPCPipelineTests.tearDown
    _test_interpretation = helpers.NPCPipelineTests._test_interpretation

    def test_inspection_consent_starts_following_without_completing_quest(self):
        player = self.db.get(Player, 1)
        player.opening_state = 'complete'
        row = record(self.db, player)
        apply_command(self.db, player, self.db.get(NPC, 1), 'report_wreck',
                      'test:report', row.revision, {})
        self.db.commit()
        message = 'Yes please'
        interpretation = AcceptedInterpretation(version=1, concerns=[Concern(
            id='c1', kind='pending_answer', evidence=message, start=0, end=10,
            modality='direct', target='ship', pending_question_id='craftsman:ship-inspection',
            answer_type='assent')], clarification=None)
        with patch.object(LLMService, 'interpret', return_value=(interpretation, .001)):
            response = self.client.post('/chat', json={'npc_id': 1, 'player_message': message})
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data['craftsman_encounter']['outing_active'])
        self.assertFalse(data['craftsman_encounter']['offer_pending'])
        self.assertEqual(data['craftsman_encounter']['mode'], 'departure_pending')
        self.assertFalse(data['craftsman_encounter']['inspection_complete'])
        self.assertEqual(data['ship_repair']['phase'], 'not_started')
        self.assertEqual(data['player_inventory'], ['water', 'food'])
