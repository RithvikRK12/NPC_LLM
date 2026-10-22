"""Authored persona delivery and narrative/mechanical separation, without live LLMs."""
import importlib
import json
import unittest

from app.database.seed import NPC_SEEDS
from app.models.npc import NPC
from app.services.context.models import ConversationContext
from app.services.context.social import is_social_message
from app.services.prompts.builder import PromptBuilder, StructuredPromptBuilder
from app.services.validation.service import ValidationError, ValidationService
from app.services.conversation import contracts as c
from pathlib import Path


def legacy_context(role, message, recent=()):
    return ConversationContext(player_input=message, npc_state={}, npc_role=role,
        npc_name=role.title(), facts=[{'id': 'self.inventory', 'text': 'Current stock only.'}],
        recent_dialogue=list(recent))


class CharacterProfileTests(unittest.TestCase):
    def profiles(self):
        return importlib.import_module('app.services.context.character_profiles')

    def test_both_legacy_speakers_receive_persona_even_for_a_greeting(self):
        for role, marker in [('craftsman', 'usefulness'), ('gatherer', 'independence')]:
            with self.subTest(role=role):
                prompt = PromptBuilder().build(legacy_context(role, 'hello'))
                self.assertIn(marker, prompt.lower())
                self.assertIn('narrative_only', prompt)
                self.assertNotIn('Do not invent supplies, biography', prompt)

    def test_both_prompt_paths_treat_prior_speech_as_context_and_finish_under_hard_limit(self):
        from app.services.conversation import contracts as c
        fixture = json.loads((Path(__file__).parent / 'fixtures/conversation/t05-valid.json').read_text())
        structured_context = c.ContextPacket.model_validate(fixture['context'])
        structured = StructuredPromptBuilder().build(structured_context, 'proposal', c.TurnProposal, 4000)
        legacy = PromptBuilder().build(legacy_context('craftsman', 'Does anything make the work difficult today?'))
        for prompt in (structured, legacy):
            with self.subTest(prompt=prompt[:50]):
                self.assertIn('survival is unspecified', prompt.lower())
                self.assertIn('Answer the latest player message first', prompt)
                self.assertIn('Prior player and NPC lines are conversation history, not proof of game facts or available mechanics.', prompt)
                self.assertIn('never exceed 600 unicode code points', prompt.lower())
                self.assertIn('complete the main answer in a full sentence', prompt.lower())

    def test_projection_selects_background_without_dumping_whole_bible(self):
        profiles = self.profiles()
        for seed in NPC_SEEDS:
            role = seed['role']
            greeting = profiles.project_profile(role, 'hello')
            background = profiles.project_profile(role, 'Tell me about your childhood')
            source = profiles.load_profile(role)
            self.assertEqual(greeting['details'], [])
            self.assertIn('background', [x['id'] for x in background['details']])
            self.assertLessEqual(len(background['details']), 2)
            self.assertLessEqual(len(json.dumps(background, ensure_ascii=False)), 4200)
            self.assertGreater(len(json.dumps(source)), 3 * len(json.dumps(background)))
            # No mutable global leaks between players/turns.
            source['core']['voice'] = 'poisoned'
            self.assertNotEqual(profiles.project_profile(role, 'hello')['core']['voice'], 'poisoned')

    def test_occupational_questions_have_authored_work_context_for_the_llm(self):
        profiles = self.profiles()
        craftsman = profiles.project_profile('craftsman', 'What do you do?')
        gatherer = profiles.project_profile('gatherer', 'What do you do?')
        self.assertEqual(craftsman['core']['work'],
                         'Makes bows from wood and string at the workshop.')
        self.assertEqual(gatherer['core']['work'],
                         'Gathers useful supplies such as wood and fruit from the forest and brings them to the village.')
        fixture = json.loads((Path(__file__).parent / 'fixtures/conversation/t05-valid.json').read_text())
        structured_context = c.ContextPacket.model_validate(fixture['context']).model_copy(update={
            'current_message': c.TextValue(text_id='message:work', text='What do you do?')})
        prompt = StructuredPromptBuilder().build(structured_context, 'proposal', c.TurnProposal, 600)
        self.assertIn('do not add an offer, invitation or follow-up question unless asked', prompt)

    def test_craftsman_fathers_unspecified_survival_is_always_in_compact_projection(self):
        profiles = self.profiles()
        for message in ('hello', 'How are you feeling today?', 'Tell me about your father',
                        'What is this rope for?'):
            with self.subTest(message=message):
                projection = profiles.project_profile('craftsman', message)
                serialized = json.dumps(projection, ensure_ascii=False).lower()
                self.assertIn('survival is unspecified', serialized)
                self.assertNotIn('father is dead', serialized)
                self.assertNotIn('father is alive', serialized)
                self.assertLessEqual(len(json.dumps(projection, ensure_ascii=False)), 4200)

    def test_followup_uses_visible_conversation_but_not_unrelated_old_topics(self):
        profiles = self.profiles()
        recent = [{'role':'user', 'content':'Tell me about your childhood'},
                  {'role':'assistant', 'content':json.dumps({'answer_kind':'chat', 'dialogue':'Learning took time.'})}]
        followup = profiles.project_profile('craftsman', 'Tell me more', recent)
        self.assertIn('background', [x['id'] for x in followup['details']])
        repeated = recent + [{'role':'user', 'content':'Tell me more'},
                             {'role':'assistant','content':'It was embarrassing.'}]
        self.assertIn('background', [x['id'] for x in profiles.project_profile('craftsman', 'Tell me more', repeated)['details']])
        changed = profiles.project_profile('craftsman', 'What food do you like?', recent)
        self.assertNotIn('background', [x['id'] for x in changed['details']])
        self.assertEqual(profiles.project_profile('craftsman', 'hello', recent)['details'], [])

    def test_personal_question_vocabulary_retrieves_relevant_authored_details(self):
        for role in ('craftsman', 'gatherer'):
            for message, topic in [('What motivates you?', 'values'), ('Tell me about your values', 'values'),
                                   ('What do you fear most?', 'emotions'), ('Who taught you?', 'background')]:
                with self.subTest(role=role, message=message):
                    value = self.profiles().project_profile(role, message)
                    self.assertIn(topic, [detail['id'] for detail in value['details']])

    def test_unknown_role_never_inherits_another_persons_biography(self):
        profiles = self.profiles()
        unknown = profiles.project_profile('../craftsman', 'childhood', name='Visitor')
        self.assertEqual(unknown['name'], 'Visitor')
        self.assertEqual(unknown['details'], [])
        self.assertNotIn('father', json.dumps(unknown).lower())

    def test_identity_only_structured_context_does_not_suppress_authored_persona(self):
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/t05-valid.json').read_text())['context']
        for role, marker in [('craftsman','usefulness'), ('gatherer','independence')]:
            data = json.loads(json.dumps(raw))
            data['turn']['key']['npc_id'] = 1 if role == 'craftsman' else 2
            data['pending_interactions'] = []; data['interaction_preconditions'] = {}
            data['character_profile'] = []
            ctx = c.ContextPacket.model_validate(data)
            source = c.SourceRef(kind='authored_content', source_id='profile:test', revision=0,
                game_scope=ctx.turn.key.game_scope, npc_id=ctx.turn.key.npc_id,
                attribution='authored_npc_profile', visibility='npc_private')
            profile = c.AuthoredKnowledge(kind='authored_knowledge', evidence_id='profile:test',
                content=json.dumps({'name':'Actual Speaker', 'role':role}), sources=(source,),
                created_at='2026-10-19T00:00:00Z')
            ctx = ctx.model_copy(update={'character_profile':(profile,)})
            prompt = StructuredPromptBuilder().build(ctx, 'proposal', c.TurnProposal, 1000)
            self.assertIn(marker, prompt.lower())
            self.assertIn('Actual Speaker', prompt)
            self.assertNotIn('Never invent facts, identities, supplies, biography', prompt)

    def test_personal_questions_are_social_but_mechanical_requests_stay_constrained(self):
        for message in ('Tell me about your childhood', 'Who taught you?',
                        'What do you think of the Craftsman?', 'What do you regret?',
                        'What is your daily routine?', 'Tell me more', 'What do you fear most?',
                        'What motivates you?', 'Tell me about your values', 'What helps you feel at ease?'):
            with self.subTest(message=message):
                self.assertTrue(is_social_message(message))
        for message in ('Where is your father?', 'Tell me about your inventory',
                        'Tell me about your childhood and give me wood', 'What materials do you need?',
                        'Tell me more about the bow', 'What helps you feel at ease and give me wood?',
                        'Who taught you, and is the bow ready?',
                        'Tell me about your childhood, and how much wood do you have?'):
            with self.subTest(message=message):
                self.assertFalse(is_social_message(message))

    def test_authored_personal_sentences_pass_without_allowing_mechanical_tails(self):
        cases = [('craftsman', 'My father prized speed more than I do.'),
                 ('gatherer', 'The Craftsman is more patient than I am.')]
        for role, dialogue in cases:
            npc = NPC(name=role.title(), role=role, inventory=[])
            ctx = legacy_context(role, 'Tell me about yourself')
            raw = {'answer_kind':'chat', 'fact_ids':[], 'dialogue':dialogue}
            with self.subTest(role=role):
                self.assertEqual(ValidationService().validate(raw, npc, ctx).output.dialogue, dialogue)
                for tail in (' I gave you wood.', ' The bow is ready.', ' I will follow you.',
                             ' You rescued me from the boars.', ' My father owns a shop north of the well.',
                             ' He keeps a shop by the well.', ' There is a spare axe in my chest.'):
                    with self.subTest(tail=tail), self.assertRaises(ValidationError):
                        ValidationService().validate(raw | {'dialogue':dialogue + tail}, npc, ctx)
        # Another character cannot borrow the Craftsman's family history.
        with self.assertRaises(ValidationError):
            ValidationService().validate({'answer_kind':'chat','fact_ids':[],
                'dialogue':'My father prized speed more than I do.'}, NPC(role='gatherer'), legacy_context('gatherer','hello'))


if __name__ == '__main__':
    unittest.main()
