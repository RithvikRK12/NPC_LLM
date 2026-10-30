import unittest

from app.services.context.models import ConversationContext
from app.services.prompts.builder import PromptBuilder


class GathererSocialContextTests(unittest.TestCase):
    def context(self, kind):
        return ConversationContext(player_input='hello', npc_name='Gatherer', npc_role='gatherer',
            npc_state={'trust': .7, 'fear': .2, 'aggression': .1, 'curiosity': .5},
            encounter={'status': 'resolved_helped', 'outcome_fact': 'ENCOUNTER_MARKER two boars defeated'},
            facts=[{'id': 'self.inventory', 'text': 'STOCK_MARKER wood', 'subject': 'self'},
                   {'id': 'person.craftsman.location', 'text': 'LOCATION_MARKER workshop'}],
            memories=[{'id': 1, 'event': 'PREFERENCE_MARKER quiet forests', 'event_type': 'preference'},
                      {'id': 2, 'event': 'TRANSFER_MARKER gave wood', 'event_type': 'transfer'}],
            accepted_interpretation={'version': 1, 'concerns': [{'kind': kind}]})

    def test_small_talk_prompt_keeps_relationship_and_preferences_without_mechanics(self):
        prompt = PromptBuilder().build(self.context('social'))
        for forbidden in ('ENCOUNTER_MARKER', 'STOCK_MARKER', 'LOCATION_MARKER', 'TRANSFER_MARKER'):
            self.assertNotIn(forbidden, prompt)
        self.assertIn('PREFERENCE_MARKER', prompt)
        self.assertIn('"trust": 0.7', prompt)
        self.assertIn('Gatherer', prompt)

    def test_factual_prompt_still_receives_current_world_and_encounter(self):
        prompt = PromptBuilder().build(self.context('factual'))
        self.assertIn('ENCOUNTER_MARKER', prompt)
        self.assertIn('STOCK_MARKER', prompt)
        self.assertIn('LOCATION_MARKER', prompt)
