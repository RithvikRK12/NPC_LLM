"""Integrated behavior and cross-reset race checks, isolated file-backed SQLite."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.database.base import Base
from app.database.seed import seed_world
from app.database.session import get_db
from app.models import NPC, Player, Conversation, Memory, BowQuest
from app.services.llm.service import GenerationResult
from app.services.pipeline import ConversationPipeline, StaleConversationError
from app.services.rule_engine.behavior import tendencies, select_behavior
from app.services.validation.models import LLMResponse, StateUpdate
from app.services.validation.service import ValidationService, ValidationError


class BehaviorPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.engine = create_engine('sqlite:///' + str(Path(self.temp.name) / 'world.db'),
                                    connect_args={'check_same_thread': False, 'timeout': 3})
        self.addCleanup(self.engine.dispose)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            seed_world(db)
        self.app = FastAPI()
        self.app.include_router(api_router)
        def session():
            with Session(self.engine) as db:
                yield db
        self.app.dependency_overrides[get_db] = session
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)
        embedding = patch('app.services.memory.embedding.EmbeddingService.embed_many',
                          side_effect=lambda texts, **kw: [[1.] + [0.] * 767 for _ in texts])
        embedding.start()
        self.addCleanup(embedding.stop)

    def state(self, trust, fear, aggression=0.05, curiosity=0.3, role='craftsman'):
        with Session(self.engine) as db:
            npc = db.get(NPC, 1)
            npc.trust, npc.fear, npc.aggression, npc.curiosity, npc.role = trust, fear, aggression, curiosity, role
            db.commit()

    def chat(self, message, status=200):
        response = self.client.post('/chat', json={'npc_id': 1, 'player_message': message})
        self.assertEqual(response.status_code, status, response.text)
        return response.json()

    def test_same_optional_request_has_visible_helpful_cautious_distrustful_behavior(self):
        cases = [(0.95, 0.05, 'cooperate', 'Glad to help.'),
                 (0.65, 0.6, 'clarify', "Let's be careful."),
                 (0.05, 0.8, 'refuse', "I'd rather keep my rope")]
        for trust, fear, expected, text in cases:
            self.client.delete('/chat/1')
            self.state(trust, fear)
            data = self.chat('Can I have rope?')
            trace = data['behavior_trace']
            self.assertEqual(trace['selection'], expected)
            self.assertIn(text, data['final_dialogue'])
            self.assertEqual(data['player_inventory'], ['water', 'food'])
            self.assertIn('rope', data['npc']['inventory'])
            self.assertFalse(trace['eligibility']['offer_recovery']['eligible'])
            self.assertEqual(trace['ordering'], ['role_conditioning', 'final_control_validation', 'fsec'])
            with Session(self.engine) as db:
                saved = db.scalar(select(Conversation).order_by(Conversation.id.desc()))
                self.assertEqual(saved.validated_output['behavior_trace'], trace)
                self.assertEqual(trace['verified_outcome']['conversation_id'], saved.id)

    def test_optional_refusal_cancels_pending_request_without_effects(self):
        self.state(.95, .05)
        self.chat('Give me rope')
        self.state(.05, .8)
        data = self.chat('For my work in the village')
        self.assertEqual(data['behavior_trace']['selection'], 'refuse')
        self.assertIsNone(data['npc']['pending_item'])
        self.assertEqual(data['player_inventory'], ['water', 'food'])
        self.assertFalse(any(data['validated_output']['state_update'].values()))

    def test_required_cooperation_cannot_be_refused_and_duplicate_transfer_is_safe(self):
        with Session(self.engine) as db:
            npc = db.get(NPC, 1)
            npc.inventory = list(npc.inventory) + ['wood']
            db.commit()
        self.state(.01, .99)
        first = self.chat('Give me wood')
        self.assertFalse(first['behavior_trace']['eligibility']['refuse']['eligible'])
        transferred = self.chat('For my bow')
        self.assertEqual(transferred['player_inventory'].count('wood'), 1)
        repeated = self.chat('Give me wood')
        self.assertEqual(repeated['player_inventory'].count('wood'), 1)
        self.assertEqual(repeated['behavior_trace']['selection'], 'answer')
        self.client.post('/quests/bow/start')
        data = self.chat('Can you make me a bow?')
        self.assertEqual(data['bow_quest']['phase'], 'gather')

    def test_high_cooperation_never_creates_missing_resources_or_role_capabilities(self):
        self.state(.99, .01)
        data = self.chat('Give me wood')
        self.assertNotIn('wood', data['player_inventory'])
        self.assertFalse(data['behavior_trace']['eligibility']['cooperate']['eligible'])
        self.state(.99, .01, role='unsupported')
        self.chat('Give me rope')
        data = self.chat('For my work in the village')
        self.assertTrue(data['grounding_trace']['rejected'])
        self.assertFalse(data['behavior_trace']['eligibility']['cooperate']['eligible'])
        self.assertIn('rope', data['npc']['inventory'])

    def test_factual_answer_is_preserved_and_rejection_has_no_fuzzy_effect(self):
        for proposal, rejected in [({'answer_kind': 'answer', 'fact_ids': ['person.gatherer.location']}, False),
                                   ({'action': 'attack'}, True)]:
            with patch('app.services.llm.service.LLMService.generate', return_value=GenerationResult('', proposal)):
                data = self.chat('Where is the Gatherer?')
            self.assertEqual(data['grounding_trace']['rejected'], rejected)
            self.assertEqual(data['behavior_trace']['selection'], 'answer')
            self.assertEqual(data['npc']['trust'], .65)
            if not rejected:
                self.assertIn('forest', data['final_dialogue'].lower())
            else:
                self.assertIsNone(data['behavior_trace']['verified_outcome']['action'])
                self.assertFalse(data['memory_classification']['important'])

    def test_candidate_uses_accepted_conditioned_deltas_and_stays_bounded(self):
        proposal = dict(intent='assist', emotion='calm', dialogue='Good to see you.', action='speak',
                        reasoning='Social response.', state_update=dict(trust=1., fear=-1., aggression=1., curiosity=1.))
        with patch('app.services.llm.service.LLMService.generate', return_value=GenerationResult('', proposal)):
            data = self.chat('Hello')
        candidate = data['behavior_trace']['candidate_state']
        self.assertEqual(candidate, dict(trust=1., fear=0., aggression=.25, curiosity=1.))
        for key, value in candidate.items():
            self.assertEqual(data['npc'][key], value)

    def test_memberships_and_outputs_are_reproducible_bounded_and_gradual(self):
        previous = None
        for i in range(101):
            state = dict(trust=i / 100, fear=.1, aggression=.05, curiosity=.3)
            one = tendencies(state, 'decision', 'scope')
            self.assertEqual(one, tendencies(state, 'decision', 'scope'))
            for value in one[2].values():
                self.assertTrue(0 <= value <= 1)
            if previous is not None:
                self.assertLess(abs(one[2]['cooperation'] - previous), .03)
            previous = one[2]['cooperation']

    def test_ties_use_behavior_id_and_only_eligible_candidates_are_scored(self):
        from app.services.rule_engine.behavior import POLICY
        self.state(.95, .05)
        with patch.dict(POLICY, scores={name: {'bias': .5} for name in ('answer', 'clarify', 'cooperate', 'refuse')}):
            data = self.chat('Give me rope')
        self.assertEqual(data['behavior_trace']['scores'], {'clarify': .5, 'cooperate': .5})
        self.assertEqual(data['behavior_trace']['selection'], 'clarify')

    def test_social_expression_keeps_accepted_generation_visible(self):
        proposal = dict(answer_kind='chat', fact_ids=[], dialogue='Good to see you.')
        for trust, fear, prefix in [(.95, .05, 'Glad to help.'), (.05, .8, "Let's be careful.")]:
            self.state(trust, fear)
            with patch('app.services.llm.service.LLMService.generate', return_value=GenerationResult('', proposal)):
                data = self.chat('Hello')
            self.assertIn(prefix, data['final_dialogue'])
            self.assertIn('Good to see you.', data['final_dialogue'])

    def delayed(self, concurrent):
        entered, release = Event(), Event()
        def generation(pipeline, prompt, context):
            self.assertFalse(pipeline._db.in_transaction(), 'generation holds a DB transaction')
            entered.set()
            self.assertTrue(release.wait(5), 'test did not release generation')
            return GenerationResult('', dict(answer_kind='chat', fact_ids=[], dialogue='Good to see you.'))
        with patch('app.services.pipeline.LLMService.generate', autospec=True,
                   side_effect=lambda service, prompt, context: generation(active[0], prompt, context)):
            # Capture the actual pipeline without sharing its session across threads.
            def captured_work():
                with Session(self.engine) as db:
                    pipeline = ConversationPipeline(db)
                    active.append(pipeline)
                    return pipeline.chat(1, 'I prefer quiet forests')
            active = []
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(captured_work)
                try:
                    self.assertTrue(entered.wait(3))
                    concurrent()
                finally:
                    release.set()
                with self.assertRaises(StaleConversationError):
                    future.result(timeout=5)

    def test_delayed_generation_after_reset_cannot_restore_state_history_or_memory(self):
        def reset():
            self.assertEqual(self.client.post('/world/new-game').status_code, 200)
        self.delayed(reset)
        with Session(self.engine) as reopened:
            self.assertEqual(list(reopened.scalars(select(Conversation))), [])
            self.assertEqual(list(reopened.scalars(select(Memory))), [])
            self.assertEqual(reopened.get(Player, 1).inventory, ['water', 'food'])
            self.assertEqual(reopened.get(NPC, 1).trust, .65)
            self.assertEqual(reopened.get(BowQuest, 1).phase, 'available')

    def test_delayed_generation_after_clear_cannot_reenter_memory(self):
        self.delayed(lambda: self.client.delete('/chat/1'))
        with Session(self.engine) as db:
            self.assertEqual(list(db.scalars(select(Conversation))), [])
            self.assertEqual(list(db.scalars(select(Memory))), [])

    def test_newer_conversation_invalidates_old_generation(self):
        self.delayed(lambda: self.chat('Give me rope'))
        with Session(self.engine) as db:
            self.assertEqual(len(list(db.scalars(select(Conversation)))), 1)
            self.assertEqual(db.get(NPC, 1).pending_item, 'rope')

    def test_stale_errors_are_409_on_both_routes(self):
        with patch('app.services.pipeline.ConversationPipeline.chat', side_effect=StaleConversationError('retry')):
            self.chat('Hello', status=409)
            response = self.client.post('/inventory/transfer', json={'npc_id': 1, 'item': 'rope', 'direction': 'to_player'})
            self.assertEqual(response.status_code, 409)


if __name__ == '__main__':
    unittest.main()
