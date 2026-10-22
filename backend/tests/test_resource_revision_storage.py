"""Isolated SQLite/PostgreSQL acceptance checks for persistence-adapters/T05."""
import os
import unittest
from unittest.mock import patch

from sqlalchemy import JSON, MetaData, Table, create_engine, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.models import Player


class ResourceRevisionStorageTests(unittest.TestCase):
    def setUp(self):
        database_url = os.environ.get('CONVERSATION_TEST_DATABASE_URL')
        if database_url:
            if not (make_url(database_url).database or '').startswith('npc_test_'):
                raise RuntimeError('Tests require a disposable npc_test_* database')
            self.engine = create_engine(database_url, future=True)
            metadata = MetaData()
            metadata.reflect(self.engine)
            metadata.drop_all(self.engine)
        else:
            self.engine = create_engine('sqlite:///:memory:', future=True)
        self.addCleanup(self.engine.dispose)

    def _legacy_players(self):
        # A populated pre-ledger schema, including opaque data this migration must retain.
        with self.engine.begin() as connection:
            connection.execute(text('''CREATE TABLE players (
                id INTEGER PRIMARY KEY, game_scope VARCHAR(36) NOT NULL,
                inventory JSON NOT NULL, position JSON NOT NULL,
                current_location VARCHAR(128) NOT NULL,
                opening_version INTEGER NOT NULL DEFAULT 1,
                opening_state VARCHAR(16) NOT NULL DEFAULT 'complete',
                map_version INTEGER NOT NULL DEFAULT 2,
                salvage_ids JSON NOT NULL, map_recovery_notice VARCHAR(255) NOT NULL,
                legacy_payload TEXT
            )'''))
            connection.execute(text('''INSERT INTO players VALUES (
                1, 'unchanged-scope', :inventory, :position,
                'forest_edge', 4, 'pending', 2, :salvage_ids, 'keep this notice',
                'opaque legacy data'
            )'''), {'inventory': '["rope","food"]', 'position': '{"x":3.25,"y":-2.5}',
                    'salvage_ids': '["wreck-7"]'})

    def _ledger(self, player_id=1):
        players = Table('players', MetaData(), autoload_with=self.engine)
        with self.engine.connect() as connection:
            return connection.scalar(select(players.c.resource_revisions).where(players.c.id == player_id))

    def test_fresh_schema_and_migration_default_to_an_empty_nonnullable_json_ledger(self):
        from app.database.resource_revision_migration import upgrade_resource_revision_schema

        upgrade_resource_revision_schema(self.engine)
        Player.__table__.create(self.engine)
        upgrade_resource_revision_schema(self.engine)
        columns = {column['name']: column for column in inspect(self.engine).get_columns('players')}
        self.assertIn('resource_revisions', columns)
        self.assertIsInstance(columns['resource_revisions']['type'], JSON)
        self.assertFalse(columns['resource_revisions']['nullable'])
        with Session(self.engine) as db:
            db.add(Player(id=1, game_scope='new-scope'))
            db.commit()
            self.assertEqual(db.get(Player, 1).resource_revisions, {})
        # Raw inserts also receive the default, independently of ORM client defaults.
        with self.engine.begin() as connection:
            connection.execute(text('''INSERT INTO players
                (id, inventory, position, current_location, salvage_ids)
                VALUES (2, '[]', :position, 'village_square', '[]')'''),
                {'position': '{"x":0,"y":0}'})
        self.assertEqual(self._ledger(2), {})

    def test_populated_migration_preserves_every_existing_field_and_defaults_legacy_rows(self):
        from app.database.resource_revision_migration import upgrade_resource_revision_schema

        self._legacy_players()
        with self.engine.connect() as connection:
            before = connection.execute(text('SELECT * FROM players ORDER BY id')).all()
        upgrade_resource_revision_schema(self.engine)
        columns = {column['name']: column for column in inspect(self.engine).get_columns('players')}
        self.assertFalse(columns['resource_revisions']['nullable'])
        self.assertIsInstance(columns['resource_revisions']['type'], JSON)
        with self.engine.connect() as connection:
            after = connection.execute(text('''SELECT id, game_scope, inventory, position,
                current_location, opening_version, opening_state, map_version,
                salvage_ids, map_recovery_notice, legacy_payload FROM players ORDER BY id''')).all()
        self.assertEqual(after, before)
        self.assertEqual(self._ledger(), {})
        with self.engine.begin() as connection:
            connection.execute(text('''INSERT INTO players
                (id, game_scope, inventory, position, current_location, salvage_ids, map_recovery_notice)
                VALUES (2, 'later-scope', '[]', '{}', 'workshop', '[]', '')'''))
        self.assertEqual(self._ledger(2), {})

    def test_repeated_migration_preserves_existing_revisions_and_scope(self):
        from app.database.resource_revision_migration import upgrade_resource_revision_schema

        self._legacy_players()
        upgrade_resource_revision_schema(self.engine)
        players = Table('players', MetaData(), autoload_with=self.engine)
        with self.engine.begin() as connection:
            connection.execute(players.update().values(resource_revisions={'inventory:player': 9, 'quest:bow': 3}))
        upgrade_resource_revision_schema(self.engine)
        upgrade_resource_revision_schema(self.engine)
        self.assertEqual(self._ledger(), {'inventory:player': 9, 'quest:bow': 3})
        with self.engine.connect() as connection:
            self.assertEqual(connection.scalar(text('SELECT game_scope FROM players WHERE id=1')), 'unchanged-scope')

    def test_revision_writes_rollback_with_the_callers_player_transaction(self):
        Player.__table__.create(self.engine)
        with Session(self.engine) as db:
            db.add(Player(id=1, game_scope='same-scope'))
            db.commit()
            player = db.get(Player, 1)
            player.resource_revisions = {'inventory:player': 8}
            player.inventory = ['hammer']
            db.flush()
            db.rollback()
        with Session(self.engine) as db:
            player = db.get(Player, 1)
            self.assertEqual(player.resource_revisions, {})
            self.assertEqual(player.inventory, [])
            self.assertEqual(player.game_scope, 'same-scope')

    def test_database_initialization_upgrades_populated_players_idempotently(self):
        from app.database import init_db

        self._legacy_players()
        with patch.object(init_db, 'engine', self.engine):
            init_db.initialize_database()
            self.assertEqual(self._ledger(), {})
            players = Table('players', MetaData(), autoload_with=self.engine)
            with self.engine.begin() as connection:
                connection.execute(players.update().values(resource_revisions={'inventory:player': 4}))
            init_db.initialize_database()
        self.assertEqual(self._ledger(), {'inventory:player': 4})
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(text('''SELECT game_scope, current_location,
                opening_state, map_recovery_notice, legacy_payload FROM players WHERE id=1''')).one(),
                ('unchanged-scope', 'forest_edge', 'pending', 'keep this notice', 'opaque legacy data'))


if __name__ == '__main__':
    unittest.main()
