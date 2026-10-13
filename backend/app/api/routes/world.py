from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import NPC, Player, Quest, Conversation
from app.schemas.npc import NPCRead
from app.models.bow_quest import BowQuest
from app.services.quests.bow import snapshot

router = APIRouter(tags=['world'])


@router.get('/world')
def world(db: Session = Depends(get_db)) -> dict:
    player = db.get(Player, 1)
    quest = db.scalar(select(Quest).where(Quest.player_id == 1))
    npcs = list(db.scalars(select(NPC).order_by(NPC.id)))
    histories = {}
    for npc in npcs:
        turns = list(db.scalars(select(Conversation).where(Conversation.npc_id == npc.id)
                               .order_by(Conversation.id.desc()).limit(50)))
        histories[str(npc.id)] = [{'player': turn.player_input, 'npc': turn.final_dialogue}
                                  for turn in reversed(turns)]
    return {'opening_capability': 1, 'game_scope': player.game_scope if player else '',
            'opening_state': player.opening_state if player else 'complete',
            'opening_version': player.opening_version if player else 1,
            'map_version': player.map_version if player else 1,
            'map_recovery_notice': player.map_recovery_notice if player else '',
            'salvage_ids': player.salvage_ids if player else [], 'player_position': player.position or {'x': 0.0, 'y': 0.0} if player else {'x': 0.0, 'y': 0.0}, 'bow_quest': snapshot(db.get(BowQuest, 1)), 'npcs': [NPCRead.model_validate(npc).model_dump() for npc in npcs],
            'player_inventory': list(player.inventory or []) if player else [],
            'quest_status': quest.status if quest else 'unknown',
            'quest_progress': quest.progress if quest else 0, 'histories': histories}


@router.post('/world/new-game')
def new_game(db: Session = Depends(get_db)) -> dict:
    from app.database.seed import reset_world
    reset_world(db)
    data = world(db)
    db.commit()
    return data


from pydantic import BaseModel, Field


class PlayerPosition(BaseModel):
    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)
    game_scope: str | None = None


@router.put('/world/player-position')
def save_position(position: PlayerPosition, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from app.services.state.locking import lock_player
    player = lock_player(db)
    if player is None:
        raise HTTPException(status_code=404, detail='Player not found')
    if position.game_scope is not None and position.game_scope != player.game_scope:
        raise HTTPException(status_code=409, detail='Game has been replaced')
    if player.opening_state == 'pending':
        raise HTTPException(status_code=409, detail='Opening is still pending')
    from app.services.island import recover, location_at
    player.position = recover({'x': position.x, 'y': position.y})
    player.current_location = location_at(player.position)
    player.map_recovery_notice = ''
    db.commit()
    return {'saved': True}


class OpeningCompletion(BaseModel):
    game_scope: str
    opening_version: int


@router.post('/world/opening/complete')
def opening_complete(payload: OpeningCompletion, db: Session = Depends(get_db)):
    from app.services.opening import complete_opening
    return complete_opening(db, payload.game_scope, payload.opening_version)


class SalvagePickup(PlayerPosition):
    game_scope: str


@router.post('/world/beach/salvage')
def beach_salvage(payload: SalvagePickup, db: Session = Depends(get_db)):
    from app.services.opening import collect_salvage
    return collect_salvage(db, payload.game_scope, payload.x, payload.y)
