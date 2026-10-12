"""Additive migration: never mix old hashed vectors into semantic search."""
from sqlalchemy import inspect, text


def upgrade_memory_schema(engine):
    columns = {
        'memories': {
            'semantic_embedding': 'JSON', 'embedding_model': 'VARCHAR(255)',
            'event_type': "VARCHAR(64) NOT NULL DEFAULT 'legacy'", 'quest_id': 'VARCHAR(64)',
            'duplicate_key': 'VARCHAR(64)',
            'game_scope': 'VARCHAR(36)', 'source_event_id': 'VARCHAR(36)',
            'source_conversation_id': 'INTEGER',
            'epistemic_status': "VARCHAR(24) NOT NULL DEFAULT 'interpretation'",
            'authority': "VARCHAR(24) NOT NULL DEFAULT 'inferred'",
            'lifecycle': "VARCHAR(24) NOT NULL DEFAULT 'active'",
            'claim_text': 'VARCHAR(500)', 'correction_of_id': 'INTEGER', 'superseded_by_id': 'INTEGER',
        },
        'players': {'game_scope': "VARCHAR(36) NOT NULL DEFAULT 'legacy'"},
        'conversations': {'game_scope': 'VARCHAR(36)', 'source_event_id': 'VARCHAR(36)'},
        'npcs': {'memory_revision': "VARCHAR(36) NOT NULL DEFAULT 'initial'"},
    }
    with engine.begin() as connection:
        for table, additions in columns.items():
            if not inspect(connection).has_table(table):
                continue
            existing = {c['name'] for c in inspect(connection).get_columns(table)}
            for name, definition in additions.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {definition}'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS ix_memory_scope ON memories (npc_id, embedding_model, event_type, quest_id, timestamp)'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS ix_memories_duplicate_key ON memories (duplicate_key)'))

        connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS uq_memory_source ON memories (game_scope, npc_id, source_event_id)'))
