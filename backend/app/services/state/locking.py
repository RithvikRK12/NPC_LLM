"""Serialize this single-player world's writers on PostgreSQL and SQLite."""
from sqlalchemy import select, update
from app.models.player import Player


def lock_player(db, player_id=1):
    # SQLite ignores FOR UPDATE. A no-op UPDATE acquires its writer lock before
    # reading state; PostgreSQL locks the same row. Always lock player before NPC.
    db.execute(update(Player).where(Player.id == player_id).values(id=Player.id)
               .execution_options(synchronize_session=False))
    return db.scalar(select(Player).where(Player.id == player_id).with_for_update()
                     .execution_options(populate_existing=True))
