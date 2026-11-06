"""Game-owned revisions and coherent detached snapshots for the active run.

All existing mechanics keep their own rules. Short deterministic writer scopes
serialize on Player before reading resources. Nested owners share that scope;
labels and effects flush in the caller's transaction, never commit here.
"""
from contextlib import contextmanager
from copy import deepcopy
from functools import wraps
import inspect

from fastapi import HTTPException
from sqlalchemy import select

from app.models import Player, NPC, Quest, BowQuest, ShipRepairQuest, CraftsmanEncounter, GathererEncounter
from app.services.state.locking import lock_player

WORLD = 'world'
PLAYER_INVENTORY = 'inventory:player'
LEGACY_QUEST = 'quest:legacy'
BOW_QUEST = 'quest:bow'
SHIP_QUEST = 'quest:ship_repair'
CRAFTSMAN_ACTIVITY = 'activity:ship_inspection'
GATHERER_ENCOUNTER = 'encounter:gatherer'
_BASE = (WORLD, PLAYER_INVENTORY, LEGACY_QUEST, BOW_QUEST, SHIP_QUEST,
         CRAFTSMAN_ACTIVITY, GATHERER_ENCOUNTER)
_ACTIVE = 'game_resource_writer'


def _values(db, player):
    """Copy stored state, excluding clocks, memory/CAS tokens and retry logs."""
    values = {
        WORLD: {key: deepcopy(getattr(player, key)) for key in (
            'position', 'current_location', 'opening_state', 'opening_version',
            'map_version', 'map_recovery_notice', 'salvage_ids')},
        PLAYER_INVENTORY: list(player.inventory or []),
    }
    for npc in db.scalars(select(NPC).order_by(NPC.id)):
        values[f'inventory:npc:{npc.id}'] = list(npc.inventory or [])
        values[f'npc:{npc.id}'] = {key: deepcopy(getattr(npc, key)) for key in (
            'id', 'name', 'role', 'trust', 'fear', 'aggression', 'curiosity',
            'location', 'current_state', 'pending_item', 'inventory')}
    quest = db.scalar(select(Quest).where(Quest.player_id == player.id))
    values[LEGACY_QUEST] = None if quest is None else dict(status=quest.status, progress=quest.progress)
    bow = db.get(BowQuest, player.id)
    values[BOW_QUEST] = None if bow is None else dict(phase=bow.phase, string_collected=bow.string_collected, ready_at=bow.ready_at)
    ship = db.get(ShipRepairQuest, player.id)
    values[SHIP_QUEST] = None if ship is None or ship.game_scope != player.game_scope else dict(
        phase=ship.phase, contributions=deepcopy(ship.contributions), outcome_id=ship.outcome_id)
    for key, model in ((CRAFTSMAN_ACTIVITY, CraftsmanEncounter), (GATHERER_ENCOUNTER, GathererEncounter)):
        row = db.get(model, player.id)
        values[key] = None if row is None or row.game_scope != player.game_scope else dict(
            state=deepcopy(row.state), revision=row.revision)
    return values


def revision_labels(db, player):
    """Detached complete labels; an untouched resource has baseline revision 0."""
    keys = set(_BASE)
    with db.no_autoflush:
        for npc_id in db.scalars(select(NPC.id).order_by(NPC.id)):
            keys.update((f'npc:{npc_id}', f'inventory:npc:{npc_id}'))
    return {key: (player.resource_revisions or {}).get(key, 0) for key in sorted(keys)}


def checkpoint_revisions(db):
    """Version effects before an owner freezes its historical replay result."""
    active = db.info.get(_ACTIVE)
    if active is None:
        return
    player, scope, before = active
    db.flush()
    if player.game_scope != scope:
        # A run switch invalidates every old label; counters never cross scopes.
        player.resource_revisions = {}
        active[1], active[2] = player.game_scope, _values(db, player)
        db.flush()
        return
    after = _values(db, player)
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    if changed:
        counters = dict(player.resource_revisions or {})
        for key in changed:
            current = counters.get(key, 0)
            if type(current) is not int or current < 0 or current >= 9007199254740991:
                raise ValueError('Invalid game resource revision')
            counters[key] = current + 1
        player.resource_revisions = counters
        db.flush()
    active[2] = after


@contextmanager
def game_writer(db):
    """Acquire common ordering, then version only changed resources on success.

    Does not own commit/rollback. Exceptions leave rollback to the existing
    caller (or the operation participant's savepoint).
    """
    if _ACTIVE in db.info:
        yield db.info[_ACTIVE][0]
        return
    player = lock_player(db)
    if player is None:
        raise ValueError('Player not found')
    # Callers may retain clean entities from an unlocked proposal transaction.
    # Reload them after acquiring the writer lock; preserve intentional dirty
    # values from an already locked outer caller with autoflush disabled.
    for row in list(db.identity_map.values()):
        if (isinstance(row, (NPC, Quest, BowQuest, ShipRepairQuest, CraftsmanEncounter, GathererEncounter))
                and row not in db.dirty and row not in db.deleted):
            db.expire(row)
    with db.no_autoflush:
        before = _values(db, player)
    db.info[_ACTIVE] = [player, player.game_scope, before]
    try:
        yield player
        checkpoint_revisions(db)
    finally:
        db.info.pop(_ACTIVE, None)


def versioned(function):
    """Wrap a flush-only existing owner; accept db-first functions and services."""
    signature = inspect.signature(function)
    @wraps(function)
    def call(*args, **kwargs):
        bound = signature.bind(*args, **kwargs).arguments
        db = bound.get('db')
        if db is None:
            db = bound['self']._db
        supplied_player = bound.get('player')
        scope = supplied_player.game_scope if supplied_player is not None else None
        with game_writer(db) as player:
            if scope is not None and scope != player.game_scope:
                raise HTTPException(409, 'This game has been replaced')
            return function(*args, **kwargs)
    return call


def resource_snapshot(db, game_scope):
    """Coherent detached server projection; caller releases the short lock.

    This interface is server-private (NPC projections contain existing social
    state). Public readers filter it. Godot/API can select the existing public
    fields and their labels; publication compares its exact dependency subset.
    Reads create no game records and never finish quests or migrate staging.
    """
    player = lock_player(db)
    if player is None or player.game_scope != game_scope:
        raise HTTPException(409, 'This game has been replaced')
    checkpoint_revisions(db)
    db.flush()
    # Acquiring the first lock refreshes Player; refresh clean game rows as well
    # if this Session retained an earlier unlocked proposal read.
    for model in (NPC, Quest, BowQuest, ShipRepairQuest, CraftsmanEncounter, GathererEncounter):
        list(db.scalars(select(model).execution_options(populate_existing=True)))
    return dict(game_scope=player.game_scope, state_revisions=revision_labels(db, player),
                resources=deepcopy(_values(db, player)))


def revisions_match(db, game_scope, expected):
    """Publication dependency check under the same writer ordering boundary."""
    player = lock_player(db)
    if player is None or player.game_scope != game_scope:
        return False
    checkpoint_revisions(db)
    current = revision_labels(db, player)
    return all(key in current and type(value) is int and value == current[key]
               for key, value in expected.items())
