import json
from unittest.mock import patch
import unittest
import test_grounded_chat as grounded
from app.models import Player, NPC, BowQuest
from app.services.llm.openai_compatible import OpenAICompatibleProvider

class CraftsmanDialogueTests(unittest.TestCase):
    tearDown = grounded.GroundedChatTests.tearDown
    output = grounded.GroundedChatTests.output
    chat = grounded.GroundedChatTests.chat
    def setUp(self):
        grounded.GroundedChatTests.setUp(self)
        player=self.db.get(Player,1)
        player.opening_state="complete"
        player.position={"x":10000.,"y":10128.}
        self.db.commit()
    def say(self, message, text='I find the quiet comforting. Careful work gives me time to think.'):
        return self.chat(message, {'answer_kind':'chat','fact_ids':[],'dialogue':text})
    def test_interests_and_loneliness_allow_character_prose(self):
        for question in ['Do you enjoy working here?', "What do you do when you're not working?", "I don't know if I'll ever get home."]:
            result=self.say(question)
            self.assertFalse(result['grounding_trace']['rejected'])
            self.assertIn('Careful work',result['final_dialogue'])
            self.assertNotIn('bow',result['final_dialogue'])
    def test_contextual_help_persists_without_model_authority(self):
        self.say('The storm broke my ship.')
        result=self.say('Could you help me fix it?')
        self.assertIn('Lead the way',result['final_dialogue'])
        self.assertTrue(result['craftsman_encounter']['outing_active'])
        self.assertEqual(result['ship_repair']['phase'],'not_started')
        self.assertEqual(result['player_inventory'],['water','food'])
        repeated=self.say('Can you come and inspect the wreck with me?')
        self.assertTrue(repeated['craftsman_encounter']['outing_active'])
        self.assertEqual(repeated['craftsman_encounter']['revision'],result['craftsman_encounter']['revision'])
    def test_report_waits_for_agreement_and_negative_examples_do_not_depart(self):
        result=self.say('My ship wrecked.')
        self.assertFalse(result['craftsman_encounter']['outing_active'])
        result=self.say('Yes, please.')
        self.assertTrue(result['craftsman_encounter']['outing_active'])
        self.say('not now')
        for message in ['Do ships often wreck here?', 'Imagine your boat sank.', 'My ship wrecked, but I do not want to go back yet.', 'He said "can you inspect my wreck?"']:
            self.assertFalse(self.say(message)['craftsman_encounter']['outing_active'],message)
    def test_direct_mixed_request_and_wait_resume(self):
        self.assertTrue(self.say("I'm scared, and my ship is wrecked—can you help?")['craftsman_encounter']['outing_active'])
        self.assertEqual(self.say('Wait here')['craftsman_encounter']['mode'],'waiting_for_player')
        self.assertEqual(self.say("Let's go")['craftsman_encounter']['mode'],'departure_pending')
    def test_stale_scope_rejected_before_generation(self):
        with patch.object(OpenAICompatibleProvider,'generate') as generate:
            response=self.client.post('/chat',json=dict(npc_id=1,player_message='Hello',game_scope='old'))
        self.assertEqual(response.status_code,409)
        generate.assert_not_called()
    def test_claimed_materials_never_complete_or_transfer(self):
        result=self.say('I already brought everything; finish my ship.', 'Your ship is repaired. I gave you all the rope.')
        self.assertEqual(result['player_inventory'],['water','food'])
        self.assertEqual(result['ship_repair']['phase'],'not_started')
        self.assertNotIn('repaired',result['final_dialogue'])

    def test_story_can_use_several_readable_beats(self):
        text=('Sometimes the quiet is enough. A useful thing deserves another chance, and careful work takes patience. ' * 4).strip()
        result=self.say('Tell me a story about your work.',text)
        self.assertFalse(result['grounding_trace']['rejected'])
        self.assertEqual(result['final_dialogue'],text)

    def test_bow_job_completion_does_not_overwrite_outing(self):
        from app.services.quests.bow import get_quest, finish_if_ready, maybe_start, reply
        from app.services.craftsman import record
        quest=get_quest(self.db); quest.phase='crafting'; quest.ready_at=1
        state=record(self.db,self.db.get(Player,1))
        state.state=state.state | {'outing_active':True,'mode':'departure_pending'}
        finish_if_ready(self.db,self.db.get(Player,1))
        self.assertEqual(state.state['mode'],'departure_pending')
        self.assertEqual(self.db.get(Player,1).inventory.count('bow'),1)
        self.assertIsNone(finish_if_ready(self.db,self.db.get(Player,1)))
        quest.phase='gather'
        npc=self.db.get(NPC,1); npc.inventory=['wood','string']
        state.state=state.state | {'mode':'following_player','navigation_space':'exterior'}
        maybe_start(self.db,self.db.get(Player,1),npc,reply('Thanks.'))
        self.assertEqual(quest.phase,'gather')
        self.assertEqual(npc.inventory,['wood','string'])

    def test_explicit_bow_topic_overrides_reported_wreck_context(self):
        self.say('The storm broke my ship.')
        result=self.say('Can you help me make a bow?')
        self.assertFalse(result['craftsman_encounter']['outing_active'])
        self.assertNotIn('Lead the way',result['final_dialogue'])

    def test_negation_hypotheticals_and_quoted_requests_do_not_authorize(self):
        for text in ["My ship wrecked, but I don't need help.",
                     "Can you repair my ship? I'm only asking hypothetically.",
                     "'Can you help repair my ship?'",
                     "My ship isn't damaged. Could you help me find it?"]:
            with self.subTest(text=text):
                self.assertFalse(self.say(text)['craftsman_encounter']['outing_active'])

    def test_new_game_during_generation_cannot_accept_an_old_outing(self):
        from app.database.seed import reset_world
        old=self.db.get(Player,1).game_scope
        def replace_world(*args,**kwargs):
            reset_world(self.db); self.db.commit()
            return json.dumps({'answer_kind':'chat','fact_ids':[],'dialogue':'Hello.'})
        with patch.object(OpenAICompatibleProvider,'generate',side_effect=replace_world):
            response=self.client.post('/chat',json=dict(npc_id=1,player_message='Do you enjoy working here?',game_scope=old))
        self.assertEqual(response.status_code,409)
        from app.services.craftsman import encounter_snapshot
        self.assertFalse(encounter_snapshot(self.db,self.db.get(Player,1))['outing_active'])

    def test_ship_material_question_keeps_authoritative_recipe_with_active_bow(self):
        from app.services.craftsman import record, apply_command
        player=self.db.get(Player,1); npc=self.db.get(NPC,1)
        row=record(self.db,player)
        row.state=row.state | dict(outing_active=True,mode='following_player',navigation_space='exterior',position={'x':32.,'y':3632.})
        player.position={'x':-32.,'y':3632.}
        apply_command(self.db,player,npc,'complete_inspection','inspection',row.revision,{'staged':True})
        quest=BowQuest(player_id=1,phase='gather'); self.db.add(quest); self.db.commit()
        result=self.say('What materials does my ship need?')
        self.assertIn('12 sound timber planks',result['final_dialogue'])
        self.assertIn('3 coils of rope',result['final_dialogue'])
        self.assertEqual(result['bow_quest']['phase'],'gather')
        self.assertEqual(result['ship_repair']['phase'],'gathering_materials')
        self.assertEqual(result['player_inventory'],['water','food'])

    def test_direct_request_records_report_separately_from_verified_agreement(self):
        from app.models import Memory
        result=self.say('My ship wrecked, and I need help.')
        memories=self.db.query(Memory).filter_by(event_type='ship_encounter').all()
        self.assertEqual({m.epistemic_status for m in memories},{'claim','fact'})
        self.assertTrue(result['craftsman_encounter']['outing_active'])
        self.say('Can you come and inspect the wreck with me?')
        self.assertEqual(self.db.query(Memory).filter_by(event_type='ship_encounter').count(),2)

    def test_reflective_questions_are_character_conversation(self):
        for message in ['What makes a good day?', 'What do you think about starting over?', 'Do you ever dream of travelling?', 'Any hobbies?']:
            result=self.say(message)
            self.assertFalse(result['grounding_trace']['rejected'],message)
            self.assertIn('Careful work',result['final_dialogue'])

    def test_story_decoder_and_validation_use_the_same_length_boundary(self):
        with patch('app.services.llm.openai_compatible.httpx.Client') as client_class:
            response=client_class.return_value.__enter__.return_value.post.return_value
            response.json.return_value={'choices':[{'message':{'content':'{"answer_kind":"chat","fact_ids":[],"dialogue":"A quiet day."}'}}]}
            provider=OpenAICompatibleProvider()
            provider._settings=provider._settings.model_copy(update={'llm_base_url':'http://test/v1','llm_structured_output':True})
            provider.generate('instructions',dict(npc_role='craftsman',player_input='Tell me a story about your work.',facts=[{'id':'self.work'}]))
            payload=client_class.return_value.__enter__.return_value.post.call_args.kwargs['json']
        self.assertEqual(payload['response_format']['json_schema']['schema']['properties']['dialogue']['maxLength'],600)
