"""Serialize this single-player world's writers on PostgreSQL and SQLite."""
from sqlalchemy import select, update
from app.models.player import Player


def lock_player(db, player_id=1):
    transaction = db.get_transaction()
    held = db.info.get('game_player_lock')
    if held is not None and held == (transaction, player_id):
        # Nested owners must not refresh away unflushed caller state.
        return db.get(Player, player_id)
    # SQLite ignores FOR UPDATE. A no-op UPDATE acquires its writer lock before
    # reading state; PostgreSQL locks the same row. Always lock player before NPC.
    with db.no_autoflush:
        db.execute(update(Player).where(Player.id == player_id).values(id=Player.id)
               .execution_options(synchronize_session=False))
        player = db.scalar(select(Player).where(Player.id == player_id).with_for_update()
                           .execution_options(populate_existing=True))
    db.info['game_player_lock'] = (db.get_transaction(), player_id)
    return player
