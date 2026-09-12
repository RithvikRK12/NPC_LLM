"""Optional live local-model check: PYTHONPATH=backend .venv/bin/python backend/tests/semantic_smoke.py"""
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.seed import seed_world
from app.models import NPC
from app.services.memory.embedding import EmbeddingService
from app.services.memory.service import MemoryService


def main():
    embedder = EmbeddingService()
    query = 'I am frightened of the woods'
    events = ['Player stated: I am afraid of forests.',
              'Craftsman gave the player one hammer.',
              'The bow quest is complete.']
    vectors = embedder.embed_many(events)
    scores = np.asarray(vectors) @ np.asarray(embedder.embed(query, query=True))
    assert scores[0] > max(scores[1:]), scores
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_world(db)
        npc = db.get(NPC, 1)
        service = MemoryService(db)
        for event in events:
            row = service.store_memory(npc, event, .75, 'calm', event_type='preference')
            assert row.semantic_embedding is not None
        # The other NPC's equally relevant fact cannot enter the result.
        service.store_memory(db.get(NPC, 2), query, 1., 'calm', event_type='preference')
        db.commit()
        found = service.retrieve_relevant_memories(npc, query, top_k=1)
        assert found and found[0].event == events[0], found
        assert found[0].npc_id == 1
    engine.dispose()
    print('PASS real Nomic embeddings + FAISS + reranking + NPC isolation')
    print('Cosine scores (paraphrase, hammer, quest):', [round(float(v), 4) for v in scores])


if __name__ == '__main__':
    main()
