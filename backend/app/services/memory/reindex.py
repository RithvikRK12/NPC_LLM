"""Run: python -m app.services.memory.reindex [--npc-id N] [--batch-size 32]."""
import argparse

from sqlalchemy import or_, select

from app.models import Memory, NPC, Player
from app.services.memory.embedding import EmbeddingService
from app.services.memory.importance import MIN_IMPORTANCE
from app.services.memory.service import duplicate_key


def reindex_memories(db, *, npc_id=None, batch_size=32, embedder=None):
    if not 1 <= batch_size <= 256:
        raise ValueError('batch_size must be between 1 and 256')
    embedder = embedder or EmbeddingService()
    # Same lock order as dialogue and reset. Failure rolls back the current batch.
    last_id, total = 0, 0
    while True:
        db.scalar(select(Player).where(Player.id == 1).with_for_update())
        conditions = [Memory.id > last_id, Memory.importance >= MIN_IMPORTANCE,
                      Memory.event_type.notin_(['excluded', 'routine']),
                      or_(Memory.embedding_model.is_(None), Memory.embedding_model != embedder.model_key,
                          Memory.semantic_embedding.is_(None))]
        if npc_id is not None:
            conditions.append(Memory.npc_id == npc_id)
        rows = list(db.scalars(select(Memory).where(*conditions).order_by(Memory.id).limit(batch_size)))
        if not rows:
            db.commit()
            return total
        for owner in sorted({row.npc_id for row in rows}):
            db.scalar(select(NPC).where(NPC.id == owner).with_for_update())
        try:
            vectors = embedder.embed_many([row.event for row in rows])
            if len(vectors) != len(rows):
                raise ValueError('Embedding batch count mismatch')
            for row, vector in zip(rows, vectors):
                row.semantic_embedding = vector
                row.embedding_model = embedder.model_key
                row.duplicate_key = duplicate_key(row.event, row.event_type, row.quest_id)
            last_id = rows[-1].id
            db.commit()
        except Exception:
            db.rollback()
            raise
        total += len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--npc-id', type=int)
    parser.add_argument('--batch-size', type=int, default=32)
    args = parser.parse_args()
    from app.database.init_db import initialize_database
    from app.database.session import SessionLocal
    initialize_database()
    with SessionLocal() as db:
        print(f'Re-embedded {reindex_memories(db, npc_id=args.npc_id, batch_size=args.batch_size)} important memories.')


if __name__ == '__main__':
    main()
