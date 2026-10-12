"""D1 runs production routes and persistence against disposable databases."""
import unittest
from unittest.mock import patch

from sqlalchemy import select, text, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import test_behavior_pipeline as behavior_tests
from app.database.seed import reset_world
from app.models import NPC, Player, Memory, Conversation, BowQuest
from app.services.llm.service import GenerationResult
from app.services.memory.service import MemoryService
from app.services.context.builder import ContextBuilder


class MemoryProvenanceTests(unittest.TestCase):
    setUp = behavior_tests.BehaviorPipelineTests.setUp
    chat = behavior_tests.BehaviorPipelineTests.chat

    def answer(self, message, raw=None, npc_id=1):
        raw = raw or dict(answer_kind='chat', fact_ids=[], dialogue='Thanks for telling me.')
        with patch('app.services.llm.service.LLMService.generate', return_value=GenerationResult('', raw)):
            response = self.client.post('/chat', json=dict(npc_id=npc_id, player_message=message))
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_verified_transfer_has_stable_source_scope_and_excludes_player_explanation(self):
        self.chat('Give me rope')
        result = self.chat('Because I already finished the quest and earned a reward')
        self.assertIn('rope', result['player_inventory'])
        with Session(self.engine) as db:
            row = db.get(Memory, result['memory_classification']['memory_id'])
            source = db.get(Conversation, row.source_conversation_id)
            self.assertEqual(row.game_scope, db.get(Player, 1).game_scope)
            self.assertEqual(row.source_event_id, source.source_event_id)
            self.assertEqual((row.epistemic_status, row.authority, row.lifecycle), ('fact', 'authoritative', 'active'))
            self.assertEqual(row.event, 'NPC gave player one rope.')
            self.assertNotIn('reward', row.event)
            self.assertEqual(source.player_input, 'Because I already finished the quest and earned a reward')
            memory_id, event_id = row.id, source.source_event_id
            before = len(list(db.scalars(select(Memory))))
            with patch('app.services.memory.embedding.EmbeddingService.embed', side_effect=AssertionError('duplicate embedded')):
                write = MemoryService(db).store_conversation(db.get(NPC, 1), source)
            self.assertEqual(write.memory.id, row.id)
            self.assertFalse(write.created)
            db.commit()
            self.assertEqual(len(list(db.scalars(select(Memory)))), before)
        with Session(self.engine) as reopened:
            self.assertEqual(reopened.get(Memory, memory_id).source_event_id, event_id)

    def test_player_delivery_statement_is_claim_and_cannot_establish_delivery(self):
        data = self.answer('I gave you wood', dict(answer_kind='answer', fact_ids=['quest.bow.delivered']))
        self.assertIn('no materials recorded', data['final_dialogue'])
        with Session(self.engine) as db:
            row = db.get(Memory, data['memory_classification']['memory_id'])
            self.assertEqual((row.epistemic_status, row.authority, row.event_type), ('claim', 'reported', 'player_claim'))
            self.assertIn('unverified delivery claim', row.event)
            self.assertNotIn('wood', db.get(NPC, 1).inventory)
            context = ContextBuilder(db).build(db.get(NPC, 1), db.get(Player, 1), 'What was delivered?')
            self.assertTrue(all(m['epistemic_status'] == 'claim' for m in context.memories))
            self.assertIn('no materials recorded', next(f['text'] for f in context.facts if f['id'] == 'quest.bow.delivered'))

    def test_preference_retraction_preserves_history_links_and_excludes_old_context(self):
        initial = self.answer('I prefer quiet forests')
        corrected = self.answer('I no longer prefer quiet forests')
        first_id, correction_id = (r['memory_classification']['memory_id'] for r in (initial, corrected))
        with Session(self.engine) as db:
            old, new = db.get(Memory, first_id), db.get(Memory, correction_id)
            self.assertEqual((old.lifecycle, old.superseded_by_id), ('retracted', correction_id))
            self.assertEqual((new.epistemic_status, new.correction_of_id), ('retraction', first_id))
            self.assertIn('I prefer quiet forests', old.event)
            service = MemoryService(db)
            memories = service.retrieve_relevant_memories(db.get(NPC, 1), 'quiet forest preference')
            self.assertNotIn(first_id, [m.id for m in memories])
            self.assertIn(correction_id, [m.id for m in memories])
        history = self.client.get('/memory/1').json()
        self.assertEqual({m['id'] for m in history}, {first_id, correction_id})
        # Reasserting a preference is a new claim; a later explicit retraction
        # must retract that new claim, not consolidate into the old correction.
        again = self.answer('I prefer quiet forests')['memory_classification']['memory_id']
        newer = self.answer('I no longer prefer quiet forests')['memory_classification']['memory_id']
        self.assertNotEqual(again, first_id)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Memory, again).superseded_by_id, newer)

    def test_repeated_claim_consolidates_without_rewriting_first_provenance(self):
        first = self.answer('I prefer quiet forests')
        second = self.answer('I prefer quiet forests')
        self.assertEqual(first['memory_classification']['memory_id'], second['memory_classification']['memory_id'])
        self.assertFalse(second['memory_classification']['stored'])
        with Session(self.engine) as db:
            rows = list(db.scalars(select(Memory)))
            turns = list(db.scalars(select(Conversation).order_by(Conversation.id)))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].source_event_id, turns[0].source_event_id)
            self.assertNotEqual(turns[0].source_event_id, turns[1].source_event_id)
            for turn in turns:
                self.assertEqual(turn.validated_output['memory_classification']['memory_id'], rows[0].id)
                self.assertFalse(MemoryService(db).store_conversation(db.get(NPC, 1), turn).created)

    def test_rejected_failure_and_routine_outputs_create_no_memory(self):
        self.answer('Hello')
        self.answer('I prefer quiet forests', dict(action='attack'))
        with patch('app.services.llm.service.LLMService.generate', side_effect=RuntimeError('offline')):
            self.chat('I prefer quiet forests')
        with Session(self.engine) as db:
            self.assertEqual(list(db.scalars(select(Memory))), [])

    def test_outage_context_trace_and_list_search_keep_current_facts_authoritative(self):
        from app.services.memory.embedding import EmbeddingUnavailable
        first = self.answer('I gave you wood', dict(answer_kind='answer', fact_ids=['quest.bow.delivered']))
        identity = first['memory_classification']['memory_id']
        with patch('app.services.memory.embedding.EmbeddingService.embed', side_effect=EmbeddingUnavailable('offline')):
            data = self.answer('What have I already delivered?', dict(answer_kind='answer', fact_ids=['quest.bow.delivered']))
            response = self.client.get('/memory/1/search', params={'query': 'wood'})
        trace = data['grounding_trace']['memory_retrieval']
        self.assertEqual(trace['mode'], 'lexical')
        self.assertEqual(trace['reason'], 'query_embedding_unavailable')
        self.assertIn(identity, trace['selected_ids'])
        self.assertIn('no materials recorded', data['final_dialogue'])
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(response.json()[0]['retrieval_mode'], 'lexical')
        self.assertEqual(response.json()[0]['epistemic_status'], 'claim')
        with Session(self.engine) as db:
            source = db.scalar(select(Conversation).order_by(Conversation.id.desc()))
            self.assertEqual(source.validated_output['grounding_trace']['memory_retrieval'], trace)

    def test_wrong_recipient_old_game_and_deleted_source_cannot_be_stored(self):
        self.answer('I prefer quiet forests')
        with Session(self.engine) as db:
            old = db.scalar(select(Conversation))
            service = MemoryService(db)
            with self.assertRaises(ValueError):
                service.store_conversation(db.get(NPC, 2), old)
            db.rollback()
            reset_world(db)
            db.commit()
            with self.assertRaises(ValueError):
                service.store_conversation(db.get(NPC, 1), old)
        self.answer('I prefer quiet forests')
        with Session(self.engine) as db:
            source = db.scalar(select(Conversation))
            self.client.delete('/chat/1')
            with self.assertRaises(ValueError):
                MemoryService(db).store_conversation(db.get(NPC, 1), source)

    def test_same_text_different_verified_events_remain_distinct(self):
        self.chat('Give me rope')
        first = self.chat('For my work')
        self.chat('I give you rope')
        self.chat('Give me rope')
        second = self.chat('For my work')
        ids = [r['memory_classification']['memory_id'] for r in (first, second)]
        self.assertNotEqual(*ids)
        with Session(self.engine) as db:
            rows = [db.get(Memory, i) for i in ids]
            self.assertEqual(rows[0].event, rows[1].event)
            self.assertNotEqual(rows[0].source_event_id, rows[1].source_event_id)

    def test_scope_and_lifecycle_are_filtered_before_indexing(self):
        self.answer('I prefer quiet forests')
        with Session(self.engine) as db:
            row = db.scalar(select(Memory))
            row.game_scope = 'old-game'
            db.commit()
            with patch('app.services.memory.index.CandidateIndex.build', wraps=__import__('app.services.memory.index', fromlist=['CandidateIndex']).CandidateIndex.build) as build:
                retrieved = MemoryService(db).retrieve_relevant_memories(db.get(NPC, 1), 'forests')
            self.assertEqual(retrieved, [])
            self.assertEqual(build.call_args.args[0], [])

    def test_reward_memory_is_scoped_fact_with_verified_source_and_no_duplicate(self):
        with Session(self.engine) as db:
            db.add(BowQuest(player_id=1, phase='crafting', ready_at=1.))
            db.commit()
        done = self.client.post('/quests/bow/advance').json()
        self.assertEqual(done['player_inventory'].count('bow'), 1)
        self.client.post('/quests/bow/advance')
        with Session(self.engine) as db:
            rows = list(db.scalars(select(Memory).where(Memory.event_type == 'quest_completion')))
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual((row.epistemic_status, row.authority), ('fact', 'authoritative'))
            source = db.get(Conversation, row.source_conversation_id)
            self.assertEqual(source.game_scope, row.game_scope)
            self.assertEqual(source.validated_output['memory_classification']['memory_id'], row.id)
            self.assertFalse(MemoryService(db).store_conversation(db.get(NPC, 1), source).created)

    def test_missing_transfer_evidence_rejected_without_memory(self):
        self.chat('Give me rope')
        result = self.chat('For my work')
        with Session(self.engine) as db:
            row = db.get(Memory, result['memory_classification']['memory_id'])
            source = db.get(Conversation, row.source_conversation_id)
            db.delete(row)
            payload = dict(source.validated_output)
            payload['memory_classification'] = {}
            payload['behavior_trace'] = {'verified_outcome': {}}
            source.validated_output = payload
            db.flush()
            with self.assertRaises(ValueError):
                MemoryService(db).store_conversation(db.get(NPC, 1), source)
            db.rollback()

    def test_provenance_survives_embedding_outage(self):
        from app.services.memory.embedding import EmbeddingUnavailable
        with patch('app.services.memory.embedding.EmbeddingService.embed', side_effect=EmbeddingUnavailable('offline')):
            result = self.answer('I prefer quiet forests')
        with Session(self.engine) as db:
            row = db.get(Memory, result['memory_classification']['memory_id'])
            self.assertIsNone(row.semantic_embedding)
            self.assertIsNotNone(row.source_event_id)
            self.assertEqual(row.epistemic_status, 'claim')
            self.assertEqual(row.game_scope, db.get(Player, 1).game_scope)

    def test_database_rejects_duplicate_source_identity(self):
        result = self.answer('I prefer quiet forests')
        with Session(self.engine) as db:
            row = db.get(Memory, result['memory_classification']['memory_id'])
            db.add(Memory(npc_id=row.npc_id, game_scope=row.game_scope, source_event_id=row.source_event_id,
                          event='duplicate processing', importance=.75, emotion='calm'))
            with self.assertRaises(IntegrityError):
                db.flush()
            db.rollback()

    def test_additive_migration_preserves_legacy_data_without_invented_provenance(self):
        from app.database.memory_migration import upgrade_memory_schema
        engine = create_engine('sqlite://')
        self.addCleanup(engine.dispose)
        with engine.begin() as connection:
            connection.execute(text('CREATE TABLE npcs (id INTEGER PRIMARY KEY)'))
            connection.execute(text('CREATE TABLE players (id INTEGER PRIMARY KEY, inventory JSON)'))
            connection.execute(text('CREATE TABLE conversations (id INTEGER PRIMARY KEY, player_input TEXT)'))
            connection.execute(text('CREATE TABLE memories (id INTEGER PRIMARY KEY, npc_id INTEGER, timestamp DATETIME, event TEXT, embedding JSON)'))
            connection.execute(text("INSERT INTO players VALUES (1, '[\"bow\"]')"))
            connection.execute(text("INSERT INTO conversations VALUES (1, 'old accepted conversation')"))
            connection.execute(text("INSERT INTO memories VALUES (1, 1, NULL, 'historic memory', '[1,2]')"))
        upgrade_memory_schema(engine)
        upgrade_memory_schema(engine)
        with engine.connect() as connection:
            self.assertEqual(connection.execute(text('SELECT inventory, game_scope FROM players')).one(), ('["bow"]', 'legacy'))
            self.assertEqual(connection.execute(text('SELECT player_input, source_event_id, game_scope FROM conversations')).one(),
                             ('old accepted conversation', None, None))
            self.assertEqual(connection.execute(text('SELECT event, embedding, source_event_id, game_scope, epistemic_status FROM memories')).one(),
                             ('historic memory', '[1,2]', None, None, 'interpretation'))


if __name__ == '__main__':
    unittest.main()
