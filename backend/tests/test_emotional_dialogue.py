import unittest
from types import SimpleNamespace

from app.services.context.models import ConversationContext
from app.services.prompts.builder import PromptBuilder
from app.services.rule_engine.behavior import select_behavior
from app.services.validation.models import LLMResponse, StateUpdate


class EmotionalDialogueTests(unittest.TestCase):
    def test_current_hostile_state_produces_explicit_style_guidance(self):
        from app.services.rule_engine.behavior import dialogue_style
        hostile = dialogue_style({'trust': .1, 'fear': .1, 'aggression': .9, 'curiosity': .8})
        friendly = dialogue_style({'trust': .9, 'fear': .1, 'aggression': .1, 'curiosity': .8})
        self.assertEqual(hostile['stance'], 'hostile')
        self.assertEqual(friendly['stance'], 'friendly')
        self.assertIn('direct', hostile['guidance'])
        self.assertIn('probing', hostile['guidance'])

    def test_social_prompt_gives_current_tone_priority_over_past_warmth(self):
        context = ConversationContext(player_input='hey', npc_role='gatherer', npc_name='Gatherer',
            npc_state={'trust': .1, 'fear': .1, 'aggression': .9, 'curiosity': .8},
            accepted_interpretation={'concerns': [{'kind': 'social'}]})
        prompt = PromptBuilder().build(context)
        self.assertIn('"stance": "hostile"', prompt)
        self.assertIn('Current emotional state overrides earlier conversational tone', prompt)

    def test_social_prose_is_not_rewritten_with_a_canned_emotion_prefix(self):
        npc = SimpleNamespace(trust=.1, fear=.1, aggression=.9, curiosity=.8,
                              role='gatherer', inventory=[])
        player = SimpleNamespace(inventory=[])
        output = LLMResponse(answer_kind='chat', intent='assist', emotion='calm',
            dialogue='What do you want?', action='speak', reasoning='Generated social reply.',
            state_update=StateUpdate())
        result, trace = select_behavior(npc, player, output, rejected=False,
                                        decision_id='test:social', scope='test:scope')
        self.assertEqual(result.dialogue, 'What do you want?')
        self.assertEqual(trace['selection'], 'answer')
        self.assertEqual(result.action, 'speak')
