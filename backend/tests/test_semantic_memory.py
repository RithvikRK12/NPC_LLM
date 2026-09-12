import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx
import numpy as np
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.memory_migration import upgrade_memory_schema
from app.database.seed import seed_world, reset_world
from app.models import Memory, NPC
from app.services.memory.embedding import EmbeddingService, EmbeddingUnavailable
from app.services.memory.index import CandidateIndex
from app.services.memory.reindex import reindex_memories
from app.services.memory.service import MemoryService


class FixedEmbedder:
    dimensions = 3
    model_key = 'test:semantic:v1:3'

    def embed(self, text, **kwargs):
        return [1.0, 0.0, 0.0]

    def embed_many(self, texts, **kwargs):
        return [self.embed(t) for t in texts]


class SemanticMemoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        seed_world(self.db)
        self.npc = self.db.get(NPC, 1)
        self.service = MemoryService(self.db)
        self.service._embedder = FixedEmbedder()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def add(self, event, *, npc_id=1, vector=None, importance=.8, kind='preference',
            quest=None, timestamp=None, model='test:semantic:v1:3'):
        row = Memory(npc_id=npc_id, event=event, importance=importance, emotion='calm',
                     semantic_embedding=vector if vector is not None else [1., 0., 0.],
                     embedding_model=model, event_type=kind, quest_id=quest,
                     timestamp=timestamp or datetime.now(timezone.utc).replace(tzinfo=None))
        self.db.add(row)
        self.db.flush()
        return row

    def test_candidates_are_bounded_and_reranked(self):
        old = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=100)
        for i in range(60):
            self.add(f'past event {i}', vector=[1, 0, 0], importance=.65, timestamp=old)
        # All vectors tie semantically; a high-importance recent event among candidates
        # should outrank the others in stage two.
        self.db.commit()
        with patch.object(CandidateIndex, 'search', return_value=[(i, .8) for i in range(1, 41)]) as search:
            self.db.get(Memory, 35).importance = 1.0
            self.db.get(Memory, 35).timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
            self.db.flush()
            result = self.service.retrieve_relevant_memories(self.npc, 'event')
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0].id, 35)
        self.assertAlmostEqual(result[0].score, .8 * .65 + .2 + .15, places=5)
        self.assertEqual(search.call_args.args[1], 40)
        self.assertTrue(all(r.id <= 40 for r in result))

    def test_hnsw_search_uses_nearest_vectors(self):
        close = self.add('closest', vector=[1., .01, 0.])
        self.add('unrelated', vector=[0., 1., 0.])
        self.add('opposite', vector=[-1., 0., 0.])
        self.db.commit()
        self.assertEqual(self.service.retrieve_relevant_memories(self.npc, 'query', top_k=1)[0].id, close.id)

    def test_metadata_filters_apply_before_search(self):
        old = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=10)
        self.add('other npc', npc_id=2, kind='quest_progress', quest='get_bow')
        self.add('old', kind='quest_progress', quest='get_bow', timestamp=old)
        self.add('other quest', kind='quest_progress', quest='get_axe')
        self.add('wrong event type', kind='preference', quest='get_bow')
        self.add('routine', importance=.1, kind='quest_progress', quest='get_bow')
        self.add('wrong model', kind='quest_progress', quest='get_bow', model='old-model')
        wanted = self.add('wanted', kind='quest_progress', quest='get_bow')
        self.db.commit()
        now = datetime.now(timezone.utc)
        with patch.object(CandidateIndex, 'build', wraps=CandidateIndex.build) as build:
            result = self.service.retrieve_relevant_memories(self.npc, 'query',
                event_types=['quest_progress'], quest_id='get_bow', since=now-timedelta(days=1), until=now)
        self.assertEqual([r.id for r in result], [wanted.id])
        self.assertEqual(len(build.call_args.args[0]), 1)
        with self.assertRaises(ValueError):
            self.service.retrieve_relevant_memories(self.npc, 'q', since=now, until=now-timedelta(days=1))

    def test_cache_reused_and_rebuilt_for_writes_and_reset(self):
        self.add('first')
        self.db.commit()
        with patch.object(CandidateIndex, 'build', wraps=CandidateIndex.build) as build:
            self.service.retrieve_relevant_memories(self.npc, 'query')
            self.service.retrieve_relevant_memories(self.npc, 'another query')
            self.assertEqual(build.call_count, 1)
            self.add('second')
            self.db.commit()
            self.assertEqual(len(self.service.retrieve_relevant_memories(self.npc, 'q')), 2)
            self.assertEqual(build.call_count, 2)
            reset_world(self.db)
            self.db.commit()
            self.assertEqual(self.service.retrieve_relevant_memories(self.npc, 'q'), [])

    def test_rollback_cannot_leak_indexed_uncommitted_memory(self):
        self.add('kept')
        self.db.commit()
        self.service.retrieve_relevant_memories(self.npc, 'q')
        self.add('rolled back')
        self.assertEqual(len(self.service.retrieve_relevant_memories(self.npc, 'q')), 2)
        self.db.rollback()
        self.assertEqual([r.event for r in self.service.retrieve_relevant_memories(self.npc, 'q')], ['kept'])
        self.add('new row reusing rolled back id')
        self.db.commit()
        result = self.service.retrieve_relevant_memories(self.npc, 'q')
        self.assertNotIn('rolled back', [r.event for r in result])
        self.assertEqual(len(result), 2)

    def test_duplicate_normalization_preserves_opposites_and_actual_transfers(self):
        store = self.service.store_memory
        store(self.npc, 'I prefer quiet forests.', .75, 'calm', event_type='preference')
        duplicate = store(self.npc, '  I PREFER  quiet forests! ', .8, 'calm', event_type='preference')
        self.assertIsNone(duplicate)
        store(self.npc, 'I do not prefer quiet forests.', .75, 'calm', event_type='preference')
        for _ in range(2):
            store(self.npc, 'NPC gave player wood.', .9, 'calm', event_type='item_transfer')
        self.db.commit()
        self.assertEqual(len(list(self.db.scalars(select(Memory)))), 4)
        # Historical repeated transfers remain stored but occupy one context slot.
        self.assertEqual(len(self.service.retrieve_relevant_memories(self.npc, 'q')), 3)

    def test_embedding_outage_preserves_event_without_fake_vector(self):
        with patch.object(FixedEmbedder, 'embed', side_effect=EmbeddingUnavailable('offline')):
            with self.assertLogs('app.services.memory.service', level='ERROR'):
                row = self.service.store_memory(self.npc, 'NPC gave player wood', .9, 'calm', event_type='item_transfer')
        self.db.commit()
        self.assertIsNone(row.semantic_embedding)
        self.assertIsNone(row.embedding_model)
        self.assertEqual(self.service.retrieve_relevant_memories(self.npc, 'q'), [])
        self.assertEqual(reindex_memories(self.db, embedder=FixedEmbedder()), 1)
        self.assertEqual(len(self.service.retrieve_relevant_memories(self.npc, 'q')), 1)
        self.assertEqual(reindex_memories(self.db, embedder=FixedEmbedder()), 0)

    def test_legacy_hashes_are_not_searchable_until_reembedded(self):
        row = Memory(npc_id=1, event='old important event', importance=.9, embedding=[.1]*1536)
        self.db.add(row)
        self.db.commit()
        self.assertEqual(self.service.retrieve_relevant_memories(self.npc, 'q'), [])
        reindex_memories(self.db, batch_size=1, embedder=FixedEmbedder())
        self.assertEqual(len(row.embedding), 1536)
        self.assertEqual(row.semantic_embedding, [1., 0., 0.])
        self.assertEqual(len(self.service.retrieve_relevant_memories(self.npc, 'q')), 1)

    def test_reindex_failure_rolls_back_batch(self):
        row = self.add('legacy', model='old')
        self.db.commit()
        with patch.object(FixedEmbedder, 'embed_many', side_effect=EmbeddingUnavailable('offline')):
            with self.assertRaises(EmbeddingUnavailable):
                reindex_memories(self.db, embedder=FixedEmbedder())
        self.assertEqual(self.db.get(Memory, row.id).embedding_model, 'old')

    def test_malformed_vectors_are_not_indexed(self):
        self.add('wrong dimension', vector=[1., 0.])
        self.add('zero vector', vector=[0., 0., 0.])
        self.add('malformed vector', vector=['not a number'])
        self.db.commit()
        self.assertEqual(self.service.retrieve_relevant_memories(self.npc, 'q'), [])


class EmbeddingContractTests(unittest.TestCase):
    def test_task_prefixes_normalization_and_shape_validation(self):
        embedder = EmbeddingService()
        embedder.dimensions = 3
        with patch('app.services.memory.embedding.httpx.post') as post:
            post.return_value.json.return_value = {'embeddings': [[3., 4., 0.]]}
            result = embedder.embed('forest', query=True)
            np.testing.assert_allclose(result, [.6, .8, 0.])
            self.assertEqual(post.call_args.kwargs['json']['input'], ['search_query: forest'])
            embedder.embed('forest')
            self.assertEqual(post.call_args.kwargs['json']['input'], ['search_document: forest'])
            for vectors in ([[0., 0., 0.]], [[1., 2.]], [[float('nan'), 1., 2.]], []):
                post.return_value.json.return_value = {'embeddings': vectors}
                with self.assertRaises(EmbeddingUnavailable):
                    embedder.embed('forest')

    def test_schema_upgrade_is_additive_and_repeatable(self):
        engine = create_engine('sqlite://')
        with engine.begin() as connection:
            connection.execute(text('CREATE TABLE npcs (id INTEGER PRIMARY KEY)'))
            connection.execute(text('CREATE TABLE memories (id INTEGER PRIMARY KEY, npc_id INTEGER, timestamp DATETIME, event TEXT, embedding JSON)'))
            connection.execute(text("INSERT INTO memories VALUES (1, 1, NULL, 'historic', '[1,2]')"))
        upgrade_memory_schema(engine)
        upgrade_memory_schema(engine)
        with engine.connect() as connection:
            row = connection.execute(text('SELECT event, embedding, semantic_embedding, event_type FROM memories')).one()
            self.assertEqual(tuple(row), ('historic', '[1,2]', None, 'legacy'))
            self.assertIn('memory_revision', {c['name'] for c in inspect(connection).get_columns('npcs')})
        engine.dispose()


if __name__ == '__main__':
    unittest.main()
