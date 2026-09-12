"""Additive migration: never mix old hashed vectors into semantic search."""
from sqlalchemy import inspect, text


def upgrade_memory_schema(engine):
    columns = {
        'memories': {
            'semantic_embedding': 'JSON', 'embedding_model': 'VARCHAR(255)',
            'event_type': "VARCHAR(64) NOT NULL DEFAULT 'legacy'", 'quest_id': 'VARCHAR(64)',
            'duplicate_key': 'VARCHAR(64)',
        },
        'npcs': {'memory_revision': "VARCHAR(36) NOT NULL DEFAULT 'initial'"},
    }
    with engine.begin() as connection:
        for table, additions in columns.items():
            existing = {c['name'] for c in inspect(connection).get_columns(table)}
            for name, definition in additions.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {definition}'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS ix_memory_scope ON memories (npc_id, embedding_model, event_type, quest_id, timestamp)'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS ix_memories_duplicate_key ON memories (duplicate_key)'))
