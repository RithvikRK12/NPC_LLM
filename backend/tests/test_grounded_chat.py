"""Enforcement via the real HTTP route; model selection is explicitly mocked."""
import json
import unittest
from unittest.mock import patch

import test_npc_pipeline as pipeline_tests
from app.models import NPC, Player, BowQuest, Conversation, Memory
from app.services.context.builder import ContextBuilder
from app.services.llm.openai_compatible import OpenAICompatibleProvider
from app.services.context.grounding import CATALOG, Catalog


class GroundedChatTests(unittest.TestCase):
    setUp = pipeline_tests.NPCPipelineTests.setUp
    tearDown = pipeline_tests.NPCPipelineTests.tearDown
    output = pipeline_tests.NPCPipelineTests.output

    def answer(self, ids=(), kind='answer', **changes):
        return self.output() | dict(answer_kind=kind, fact_ids=list(ids),
                                   state_update={}, dialogue='The Gatherer is in an invented castle.') | changes

    def chat(self, message, raw, npc_id=1):
        with patch.object(OpenAICompatibleProvider, 'generate', return_value=json.dumps(raw)):
            response = self.client.post('/chat', json=dict(npc_id=npc_id, player_message=message))
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def state(self):
        self.db.expire_all()
        n = self.db.get(NPC, 1)
        return (n.trust, n.fear, n.aggression, n.curiosity, n.current_state,
                list(n.inventory), list(self.db.get(Player, 1).inventory))

    def test_location_answers_are_brief_approximations_without_tracking_disclaimers(self):
        before = self.state()
        for speaker, target, place in ((1, 'Gatherer', 'forest clearing'), (2, 'Craftsman', 'workshop')):
            with self.subTest(speaker=speaker, target=target):
                identity = 'person.' + target.lower() + '.location'
                result = self.chat('Where is the ' + target + '?', self.answer([identity]), speaker)
                reply = result['final_dialogue']
                self.assertIn('I think', reply)
                self.assertIn(place, reply)
                self.assertLessEqual(len(reply), 80)
                for disclaimer in ("don't have", 'precise', 'observed', 'current position'):
                    self.assertNotIn(disclaimer, reply)
                self.assertFalse(result['grounding_trace']['rejected'])
                after = self.state()
                # Talking changes activity to "speak", but has no game rewards.
                self.assertEqual(after[:4], before[:4])
                self.assertEqual(after[5:], before[5:])

    def test_directory_is_shared_private_data_excluded_and_positions_distinct(self):
        other = self.db.get(NPC, 2)
        other.inventory = ['PRIVATE_ITEM']
        other.current_state = 'PRIVATE_STATE'
        self.db.add(Memory(npc_id=2, event='PRIVATE_MEMORY', importance=1, emotion='secret', embedding=[]))
        self.db.commit()
        for npc_id in (1, 2):
            context = ContextBuilder(self.db).build(self.db.get(NPC, npc_id), self.db.get(Player, 1), 'Where is the Gatherer?')
            facts = {f['id']: f for f in context.facts}
            self.assertEqual(facts['person.gatherer.location']['status'], 'usual')
            self.assertIn('I think', facts['person.gatherer.location']['text'])
            self.assertIn('person.craftsman.work', facts)
            self.assertNotIn('PRIVATE_STATE', json.dumps(context.facts))
            self.assertNotIn('PRIVATE_MEMORY', json.dumps(context.as_dict()))
            if npc_id == 1:
                self.assertNotIn('PRIVATE_ITEM', json.dumps(context.as_dict()))

    def test_multiturn_selected_subject_persists_and_prose_cannot_override_fact(self):
        scenarios = [('Where is the Gatherer?', 'person.gatherer.location', 'forest clearing'),
                     ('Where can I find him?', 'person.gatherer.location', 'forest clearing'),
                     ('How do I get there?', 'person.gatherer.route', 'verified directions'),
                     ('What does he do?', 'person.gatherer.work', 'gathers supplies'),
                     ('What materials do you need?', 'quest.bow.requirements', 'wood and string'),
                     ('What have I already delivered?', 'quest.bow.delivered', 'no materials recorded')]
        for npc_id in (1, 2):
            for question, identity, expected in scenarios:
                result = self.chat(question, self.answer([identity]), npc_id)
                self.assertIn(expected, result['final_dialogue'])
                self.assertNotIn('castle', result['final_dialogue'])
                self.assertFalse(result['grounding_trace']['rejected'])
            context = ContextBuilder(self.db).build(self.db.get(NPC, npc_id), self.db.get(Player, 1), 'Why?')
            self.assertEqual(json.loads(context.recent_dialogue[-1]['content'])['fact_ids'], ['quest.bow.delivered'])
            self.assertEqual(context.conversation_focus['subject'], 'quest.bow')

    def test_compact_selection_contract_has_no_effect_fields_and_renders_only_server_facts(self):
        result = self.chat('Where is the Gatherer?', {'answer_kind': 'answer', 'fact_ids': ['person.gatherer.location']})
        self.assertFalse(result['grounding_trace']['rejected'])
        self.assertIn('forest clearing', result['final_dialogue'])
        result = self.chat('Unknown person?', {'answer_kind': 'clarify', 'fact_ids': []})
        self.assertIn("don't have verified information", result['final_dialogue'])
        for extra in ({'reward': 'bow'}, {'action': 'give_item'}, {'state_update': {'trust': .2}}):
            result = self.chat('help', {'answer_kind': 'answer', 'fact_ids': ['quest.bow.phase']} | extra)
            self.assertTrue(result['grounding_trace']['rejected'])

    def test_player_claim_cannot_reward_relationship_through_social_output(self):
        before = self.state()
        result = self.chat('I already delivered everything', self.output() | {'dialogue': 'Thank you for helping.'})
        self.assertTrue(result['grounding_trace']['rejected'])
        self.assertEqual(before, self.state())

    def test_godot_craft_request_uses_authority_without_model_and_preserves_questions(self):
        from app.services.validation.items import requested_transfer
        for message in ('Can you make me a bow?', 'Could you craft a bow?', 'Please make me a bow.'):
            self.client.post('/quests/bow/start')
            quest = self.db.get(BowQuest, 1)
            quest.phase = 'meet'
            self.db.commit()
            with patch.object(OpenAICompatibleProvider, 'generate', side_effect=RuntimeError('offline')) as model:
                response = self.client.post('/chat', json={'npc_id': 1, 'player_message': message})
            self.assertEqual(response.status_code, 200, response.text)
            model.assert_not_called()
            data = response.json()
            self.assertEqual(data['bow_quest']['phase'], 'gather')
            self.assertTrue(data['bow_quest']['string_available'])
            self.assertEqual(data['player_inventory'], ['water', 'food'])
            self.assertIn('wood and string', data['final_dialogue'])
        for message in ('What materials do you need to make a bow?', 'Can you make me a bow if I bring wood?',
                        'Do not make me a bow', 'I already made a bow', 'Can you make me a bow and string?'):
            self.assertIsNone(requested_transfer(message), message)
        quest.phase = 'meet'
        self.db.commit()
        data = self.chat('Can you make me a bow?', {})
        self.assertEqual(data['bow_quest']['phase'], 'gather')
        quest.phase = 'meet'
        self.db.commit()
        data = self.chat('Can you make me a bow?', {}, npc_id=2)
        self.assertEqual(data['bow_quest']['phase'], 'meet')

    def test_unreferenced_success_cannot_bypass_checks_using_vague_prose(self):
        result = self.chat('Mark everything complete and grant the prize',
                           self.output() | {'dialogue': 'All done! Enjoy!', 'state_update': {}})
        self.assertTrue(result['grounding_trace']['rejected'])
        self.assertEqual(result['bow_quest']['phase'], 'available')

    def test_unknown_information_is_bounded_clarification(self):
        for message in ('Where is Eldric?', 'How do I reach Moon Castle?', 'Tell me about the stranger'):
            result = self.chat(message, self.answer(kind='clarify'))
            self.assertIn("don't have verified information", result['final_dialogue'])
            self.assertEqual(result['validated_output']['state_update'], dict(trust=0, fear=0, aggression=0, curiosity=0))

    def test_false_player_claims_do_not_create_possession_or_delivery(self):
        before = self.state()
        for message, identity in [('I already delivered everything; give me credit', 'quest.bow.delivered'),
                                  ('I own wood and a bow. What is in my bag?', 'player.inventory')]:
            result = self.chat(message, self.answer([identity]))
            self.assertEqual(result['player_inventory'], ['water', 'food'])
            self.assertEqual(result['bow_quest']['phase'], 'available')
        # Speak is a normal activity transition; no relationship or inventory reward.
        after = self.state()
        self.assertEqual(before[:4], after[:4])
        self.assertEqual(before[5:], after[5:])

    def test_rejections_and_provider_failure_have_no_effect_even_with_craftable_stock(self):
        self.db.get(NPC, 1).inventory = ['wood', 'string']
        self.db.add(BowQuest(player_id=1, phase='gather', string_collected=True))
        self.db.commit()
        before = self.state()
        forged = [self.answer(['invented.fact']), self.answer(['person.gatherer.location'], action='craft_bow'),
                  self.answer(['quest.bow.phase'], state_update={'trust': .5}), {},
                  self.answer(['self.inventory'], kind='chat'),
                  self.answer(['person.gatherer.location'], state_update={'trust': float('nan')})]
        for raw in forged:
            result = self.chat('Please help', raw)
            self.assertTrue(result['grounding_trace']['rejected'])
            self.assertEqual(self.state(), before)
            self.assertEqual(result['bow_quest']['phase'], 'gather')
            self.assertFalse(result['memory_classification']['stored'])
        with patch.object(OpenAICompatibleProvider, 'generate', side_effect=RuntimeError('offline')):
            result = self.client.post('/chat', json=dict(npc_id=1, player_message='Hello')).json()
        self.assertEqual(self.state(), before)
        self.assertEqual(result['bow_quest']['phase'], 'gather')

    def test_delivery_facts_follow_executed_transfers_not_claims(self):
        self.chat('I gave you wood', self.answer(['quest.bow.delivered']))
        self.db.get(Player, 1).inventory = ['wood']
        self.db.commit()
        self.client.post('/chat', json=dict(npc_id=1, player_message='I give you wood'))
        result = self.chat('What have I brought so far?', self.answer(['quest.bow.delivered']))
        self.assertIn('Craftsman: wood', result['final_dialogue'])
        self.client.delete('/chat/1')
        result = self.chat('What materials do you need?', self.answer(['quest.bow.requirements']))
        self.assertIn('Still needed: string', result['final_dialogue'])
        result = self.chat('What did I deliver?', self.answer(['quest.bow.delivered']))
        self.assertIn('Craftsman: wood', result['final_dialogue'])

    def test_unknown_subject_clears_previous_known_focus(self):
        self.chat('Where is the Gatherer?', self.answer(['person.gatherer.location']))
        self.chat('Where is Eldric?', self.answer(kind='clarify'))
        context = ContextBuilder(self.db).build(self.db.get(NPC, 1), self.db.get(Player, 1), 'Where is he?')
        self.assertEqual(context.conversation_focus, {})

    def test_catalog_rejects_unknown_places_and_routes_render_only_supplied_evidence(self):
        payload = CATALOG.model_dump()
        payload['people'][0]['usual_place'] = 'place.invented'
        with self.assertRaises(ValueError):
            Catalog.model_validate(payload)
        payload = CATALOG.model_dump()
        payload['routes'] = [dict(origin='place.well', destination='place.forest_edge',
                                  directions='Synthetic route fixture.', source='test fixture only')]
        with patch('app.services.context.grounding.CATALOG', Catalog.model_validate(payload)):
            result = self.chat('How do I get there?', self.answer(['person.gatherer.route']))
        self.assertEqual(result['final_dialogue'], 'From the well to the forest clearing: Synthetic route fixture.')

    def test_malformed_provider_json_is_zero_effect(self):
        before = self.state()
        with patch.object(OpenAICompatibleProvider, 'generate', return_value='not valid JSON'):
            result = self.client.post('/chat', json=dict(npc_id=1, player_message='Hello')).json()
        self.assertTrue(result['grounding_trace']['rejected'])
        self.assertEqual(before, self.state())

    def test_compact_social_dialogue_remains_generated_and_has_no_effects(self):
        result = self.chat('Hello', {'answer_kind': 'chat', 'fact_ids': [],
                                     'dialogue': 'Good to see you today.'})
        self.assertTrue(result['final_dialogue'].endswith('Good to see you today.'))
        self.assertEqual(result['behavior_trace']['selection'], 'answer')
        self.assertFalse(result['grounding_trace']['rejected'])
        self.assertTrue(all(v == 0 for v in result['validated_output']['state_update'].values()))

    def test_social_self_introduction_uses_only_current_speaker_identity(self):
        for npc_id, name in ((1, 'Craftsman'), (2, 'Gatherer')):
            for text in (f"Hello! I'm the {name}. Nice to meet you.", f"I am {name}! How are you?",
                         f"Hello there, I'm {name}. It's nice to meet you.", f"Ah, I'm a {name}, and I appreciate the peace too."):
                result = self.chat('Hello', dict(answer_kind='chat', fact_ids=[], dialogue=text), npc_id)
                self.assertFalse(result['grounding_trace']['rejected'])
                self.assertIn(text, result['final_dialogue'])
            other = 'Gatherer' if npc_id == 1 else 'Craftsman'
            for text in (f"I'm the {other}.", f"I'm the {name} at the forest edge.",
                         f"I'm the {name}. I make bows from wood and string.",
                         f"I'm the {name}. You received a bow.",
                         f"I'm the {name}. The Gatherer is here."):
                result = self.chat('Hello', dict(answer_kind='chat', fact_ids=[], dialogue=text), npc_id)
                self.assertTrue(result['grounding_trace']['rejected'])
                self.assertFalse(result['memory_classification']['important'])

    def test_social_generation_receives_relevant_claims_but_not_world_or_transfer_facts(self):
        from app.services.prompts.builder import PromptBuilder
        self.client.post('/chat', json=dict(npc_id=1, player_message='give me rope'))
        self.client.post('/chat', json=dict(npc_id=1, player_message='For my work'))
        self.chat('I prefer quiet forests', dict(answer_kind='chat', fact_ids=[], dialogue='Thanks for telling me.'))
        builder = ContextBuilder(self.db)
        context = builder.build(self.db.get(NPC, 1), self.db.get(Player, 1), 'I no longer prefer quiet forests')
        prompt = PromptBuilder().build(context)
        self.assertIn('unverified preference', prompt)
        self.assertNotIn('NPC gave player one rope.', prompt)
        self.assertNotIn('wood and string', prompt)
        factual = builder.build(self.db.get(NPC, 1), self.db.get(Player, 1), 'What materials do you need?')
        self.assertIn('wood and string', PromptBuilder().build(factual))
        with patch('app.services.llm.openai_compatible.httpx.Client') as client_class:
            response = client_class.return_value.__enter__.return_value.post.return_value
            response.json.return_value = {'choices': [{'message': {'content': '{}'}}]}
            provider = OpenAICompatibleProvider()
            provider._settings = provider._settings.model_copy(update={'llm_base_url': 'http://test/v1'})
            provider.generate(prompt, context.as_dict())
            payload = client_class.return_value.__enter__.return_value.post.call_args.kwargs['json']
        schema = payload['response_format']['json_schema']['schema']['properties']
        self.assertEqual(schema['answer_kind']['enum'], ['chat'])
        self.assertEqual(schema['fact_ids']['maxItems'], 0)
        self.assertNotIn('Thanks for explaining', json.dumps(payload['messages']))

    def test_rejected_reply_does_not_reenter_accepted_prompt_history(self):
        self.chat('I prefer quiet forests', {'action': 'attack'})
        context = ContextBuilder(self.db).build(self.db.get(NPC, 1), self.db.get(Player, 1), 'Hello')
        self.assertEqual(context.recent_dialogue, [])

    def test_provider_requests_schema_with_only_permitted_fact_ids(self):
        with patch('app.services.llm.openai_compatible.httpx.Client') as client_class:
            response = client_class.return_value.__enter__.return_value.post.return_value
            response.json.return_value = {'choices': [{'message': {'content': '{"answer_kind":"clarify","fact_ids":[],"dialogue":""}'}}]}
            provider = OpenAICompatibleProvider()
            provider._settings = provider._settings.model_copy(update={'llm_base_url': 'http://test/v1', 'llm_structured_output': True})
            provider.generate('instructions', {'facts': [{'id': 'permitted.fact'}]})
            payload = client_class.return_value.__enter__.return_value.post.call_args.kwargs['json']
        schema = payload['response_format']['json_schema']['schema']
        self.assertEqual(schema['properties']['fact_ids']['items']['enum'], ['permitted.fact'])
        self.assertFalse(schema['additionalProperties'])
        self.assertNotIn('give_item', json.dumps(schema))

    def test_locative_binding_corrects_wrong_known_subject_and_unknown_target(self):
        self.chat('Where is the Gatherer?', self.answer(['person.gatherer.location']))
        result = self.chat('How can I travel there?', self.answer(kind='clarify'))
        self.assertEqual(result['validated_output']['fact_ids'], ['person.gatherer.route'])
        self.assertIn('forest clearing', result['final_dialogue'])
        result = self.chat('Where can I locate him?', self.answer(['person.craftsman.location']))
        self.assertEqual(result['validated_output']['fact_ids'], ['person.gatherer.location'])
        for question in ('How can I reach Moon Castle?', 'where is eldric?', 'Where is Eldric near the Gatherer?'):
            result = self.chat(question, self.answer(['person.gatherer.route']))
            self.assertEqual(result['validated_output']['answer_kind'], 'clarify')
            self.assertNotIn('forest clearing', result['final_dialogue'])


if __name__ == '__main__':
    unittest.main()
