import json
import unittest
from sqlalchemy import create_engine, text
from app.database.inventory_migration import upgrade_inventory_schema


class InventoryMigrationTests(unittest.TestCase):
    def test_upgrade_preserves_progress_and_only_grants_once(self):
        engine = create_engine('sqlite://')
        with engine.begin() as conn:
            conn.execute(text('CREATE TABLE npcs (id INTEGER, role TEXT)'))
            conn.execute(text("INSERT INTO npcs VALUES (1, 'craftsman'), (2, 'gatherer')"))
            conn.execute(text('CREATE TABLE players (id INTEGER, inventory JSON)'))
            conn.execute(text('INSERT INTO players VALUES (1, :items)'), {'items': json.dumps(['axe'])})
        upgrade_inventory_schema(engine)
        with engine.begin() as conn:
            self.assertEqual(json.loads(conn.scalar(text('SELECT inventory FROM players'))), ['axe', 'water', 'food'])
            self.assertEqual(json.loads(conn.scalar(text('SELECT inventory FROM npcs WHERE id=2'))), ['axe', 'wood', 'fruits'])
            conn.execute(text("UPDATE npcs SET inventory='[]' WHERE id=2"))
            conn.execute(text("UPDATE players SET inventory='[]'"))
        upgrade_inventory_schema(engine)
        with engine.connect() as conn:
            self.assertEqual(json.loads(conn.scalar(text('SELECT inventory FROM npcs WHERE id=2'))), [])
            self.assertEqual(json.loads(conn.scalar(text('SELECT inventory FROM players'))), [])
        engine.dispose()
