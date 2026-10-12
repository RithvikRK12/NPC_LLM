from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import Player, NPC
from app.schemas.npc import NPCRead
from app.services.quests.bow import get_quest, snapshot, finish_if_ready, STRING_POSITION

router = APIRouter(prefix='/quests/bow', tags=['quests'])


def lock_player(db):
    player = db.scalar(select(Player).where(Player.id == 1).with_for_update())
    if player is None: raise HTTPException(404, 'Player not found')
    return player


def payload(db, player, reward=None):
    db.flush()
    data = {'bow_quest': snapshot(get_quest(db)), 'player_inventory': list(player.inventory or []),
            'npcs': [NPCRead.model_validate(npc).model_dump() for npc in db.scalars(select(NPC).order_by(NPC.id))],
            'reward_dialogue': reward}
    db.commit()
    return data


@router.post('/start')
def start(db: Session = Depends(get_db)):
    player = lock_player(db)
    quest = get_quest(db)
    if quest.phase == 'available':
        quest.phase = 'meet'
        # Existing saved worlds may have used the initial wood. Ensure this new quest is playable once.
        npcs = list(db.scalars(select(NPC).order_by(NPC.id).with_for_update()))
        if 'wood' not in (player.inventory or []) and not any('wood' in (n.inventory or []) for n in npcs):
            gatherer = next(n for n in npcs if n.role == 'gatherer')
            gatherer.inventory = list(gatherer.inventory or []) + ['wood']
    return payload(db, player)


class PickupRequest(BaseModel):
    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)


@router.post('/pickup-string')
def pickup(request: PickupRequest, db: Session = Depends(get_db)):
    player = lock_player(db)
    quest = get_quest(db)
    if quest.phase != 'gather' or quest.string_collected:
        raise HTTPException(409, 'String is not available to pick up')
    if (request.x - STRING_POSITION['x']) ** 2 + (request.y - STRING_POSITION['y']) ** 2 > 64 ** 2:
        raise HTTPException(409, 'Move closer to the string')
    quest.string_collected = True
    player.inventory = list(player.inventory or []) + ['string']
    return payload(db, player)


@router.post('/advance')
def advance(db: Session = Depends(get_db)):
    player = lock_player(db)
    reward = finish_if_ready(db, player)
    return payload(db, player, reward)
