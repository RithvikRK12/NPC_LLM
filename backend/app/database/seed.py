from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NPC, Memory, Conversation, Player, Quest


NPC_SEEDS = [
    {
        "name": "Craftsman",
        "role": "craftsman",
        "trust": 0.65,
        "fear": 0.10,
        "aggression": 0.05,
        "curiosity": 0.30,
        "location": "workshop",
        "current_state": "available",
    },
    {
        "name": "Gatherer",
        "role": "gatherer",
        "trust": 0.50,
        "fear": 0.25,
        "aggression": 0.05,
        "curiosity": 0.70,
        "location": "forest_edge",
        "current_state": "available",
    },
]


def seed_world(db: Session) -> None:
    player = db.scalar(select(Player).where(Player.id == 1))
    if player is None:
        player = Player(id=1, inventory=[], current_location="village_square")
        db.add(player)
        db.flush()

    quest = db.scalar(select(Quest).where(Quest.player_id == player.id))
    if quest is None:
        quest = Quest(player_id=player.id, status="active", progress=0)
        db.add(quest)

    for payload in NPC_SEEDS:
        npc = db.scalar(select(NPC).where(NPC.name == payload["name"]))
        if npc is None:
            db.add(NPC(**payload))
    db.commit()