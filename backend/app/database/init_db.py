from sqlalchemy import text, inspect

from app.database.base import Base
from app.database.memory_migration import upgrade_memory_schema
from app.database.inventory_migration import upgrade_inventory_schema
from app.database.session import engine
from app.models import conversation, memory, npc, player, quest  # noqa: F401


def initialize_database() -> None:
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    upgrade_inventory_schema(engine)
    upgrade_memory_schema(engine)
    if 'pending_item' not in {c['name'] for c in inspect(engine).get_columns('npcs')}:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE npcs ADD COLUMN pending_item VARCHAR(64)'))

    if 'position' not in {c['name'] for c in inspect(engine).get_columns('players')}:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE players ADD COLUMN position JSON'))
