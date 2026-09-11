"""One-time additive upgrade for worlds created before NPC inventories existed."""
import json
from sqlalchemy import inspect, text


def upgrade_inventory_schema(engine) -> None:
    if 'inventory' in {c['name'] for c in inspect(engine).get_columns('npcs')}:
        return
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE npcs ADD COLUMN inventory JSON NOT NULL DEFAULT '[]'"))
        for role, items in [('craftsman', ['saw', 'hammer', 'rope']), ('gatherer', ['axe', 'wood', 'fruits'])]:
            # Use an explicit JSON cast on PostgreSQL; SQLite stores JSON as text.
            value = 'CAST(:items AS JSON)' if engine.dialect.name == 'postgresql' else ':items'
            connection.execute(text(f'UPDATE npcs SET inventory = {value} WHERE role = :role'),
                               {'items': json.dumps(items), 'role': role})
        for player_id, inventory in connection.execute(text('SELECT id, inventory FROM players')):
            items = json.loads(inventory) if isinstance(inventory, str) else list(inventory or [])
            items += [item for item in ['water', 'food'] if item not in items]
            value = 'CAST(:items AS JSON)' if engine.dialect.name == 'postgresql' else ':items'
            connection.execute(text(f'UPDATE players SET inventory = {value} WHERE id = :id'),
                               {'items': json.dumps(items), 'id': player_id})
