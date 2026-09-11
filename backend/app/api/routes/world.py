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
    return {'bow_quest': snapshot(db.get(BowQuest, 1)), 'npcs': [NPCRead.model_validate(npc).model_dump() for npc in npcs],
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
