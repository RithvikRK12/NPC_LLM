"""Run-scoped, idempotent world writes. No cinematic coordinates are accepted."""
from fastapi import HTTPException
from app.services.state.resources import game_writer
from app.services.state.locking import lock_player
from app.services.island import BEACH, MAP_VERSION, exterior_walkable

_at = BEACH['markers']['ControlHandoff']
HANDOFF = {'x': float(_at[0]), 'y': float(_at[1])}
assert exterior_walkable(**HANDOFF)


def current_run(db, scope):
    player = lock_player(db)
    if player is None:
        raise HTTPException(404, 'Player not found')
    if player.game_scope != scope:
        raise HTTPException(409, 'This game has been replaced. Return and reload the current game.')
    return player


def complete_opening(db, scope, version):
    with game_writer(db):
        player = current_run(db, scope)
        if version != 1 or player.opening_version != version:
            raise HTTPException(409, 'Unsupported opening version')
        if player.opening_state != 'complete':
            player.opening_state = 'complete'
            player.position = dict(HANDOFF)
            player.current_location = 'shipwreck_beach'
            player.map_version = MAP_VERSION
    db.commit()
    return {'saved': True, 'game_scope': scope, 'opening_state': player.opening_state}


def collect_salvage(db, scope, x, y):
    with game_writer(db):
        player = current_run(db, scope)
        if player.opening_state != 'complete':
            raise HTTPException(409, 'Finish arriving before collecting salvage')
        ax, ay = BEACH['salvage_at']
        if (x-ax)**2 + (y-ay)**2 > 64**2 or not exterior_walkable(x, y):
            raise HTTPException(400, 'Move closer to the washed-up rope')
        if BEACH['salvage_id'] not in (player.salvage_ids or []):
            player.salvage_ids = list(player.salvage_ids or []) + [BEACH['salvage_id']]
            player.inventory = list(player.inventory or []) + ['rope']
    db.commit()
    return {'player_inventory': player.inventory, 'salvage_ids': player.salvage_ids}
