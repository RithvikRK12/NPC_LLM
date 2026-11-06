"""Add storage for shared-resource counters without changing existing player state."""
from sqlalchemy import inspect, text


def upgrade_resource_revision_schema(engine):
    """Add the active-game-scope ledger; repeated upgrades retain all counters."""
    with engine.begin() as connection:
        if not inspect(connection).has_table('players'):
            return
        existing = {column['name'] for column in inspect(connection).get_columns('players')}
        if 'resource_revisions' not in existing:
            connection.execute(text(
                "ALTER TABLE players ADD COLUMN resource_revisions JSON NOT NULL DEFAULT '{}'"
            ))
