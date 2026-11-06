"""Additive upgrade: legacy games never replay the opening; map migration is separate."""
import json
from sqlalchemy import inspect, text
from app.services.island import recover, MAP_VERSION


def upgrade_opening_schema(engine):
    columns = {
        'opening_version': 'INTEGER NOT NULL DEFAULT 1',
        'opening_state': "VARCHAR(16) NOT NULL DEFAULT 'complete'",
        'map_version': 'INTEGER NOT NULL DEFAULT 0',
        'salvage_ids': "JSON NOT NULL DEFAULT '[]'",
        'map_recovery_notice': "VARCHAR(255) NOT NULL DEFAULT ''",
    }
    with engine.begin() as c:
        existing = {col['name'] for col in inspect(c).get_columns('players')}
        for name, definition in columns.items():
            if name not in existing:
                c.execute(text(f'ALTER TABLE players ADD COLUMN {name} {definition}'))
        for row in list(c.execute(text('SELECT id,position FROM players WHERE map_version < :version'), {'version': MAP_VERSION})):
            position = json.loads(row.position) if isinstance(row.position, str) else row.position
            position = position or {'x': 0.0, 'y': 0.0}
            restored = recover(position)
            value = 'CAST(:position AS JSON)' if engine.dialect.name == 'postgresql' else ':position'
            c.execute(text(f'UPDATE players SET position={value}, map_version=:version, map_recovery_notice=:notice WHERE id=:id'),
                      {'position': json.dumps(restored), 'version': MAP_VERSION, 'id': row.id,
                       'notice': 'Your old position was offshore. Returned to reachable island ground.' if restored != position else ''})
