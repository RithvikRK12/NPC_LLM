from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NPC, Memory, Conversation, Player, Quest


NPC_SEEDS = [
    {
        "name": "Craftsman",
        "role": "craftsman",
        "inventory": ["saw", "hammer", "rope"],
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
        "inventory": ["axe", "wood", "fruits"],
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
        player = Player(id=1, inventory=["water", "food"], current_location="village_square")
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

def reset_world(db: Session) -> None:
    """Start a new single-player run without deleting schema or changing NPC IDs."""
    from sqlalchemy import delete
    from app.models import BowQuest

    player = db.scalar(select(Player).where(Player.id == 1).with_for_update())
    if player is None:
        raise ValueError('The world must be initialized before starting a game')
    npcs = list(db.scalars(select(NPC).order_by(NPC.id).with_for_update()))
    db.execute(delete(Conversation))
    db.execute(delete(Memory))
    player.inventory = ['water', 'food']
    player.current_location = 'village_square'
    for npc in npcs:
        initial = next((values for values in NPC_SEEDS if values['name'] == npc.name), None)
        if initial is not None:
            for name, value in initial.items():
                setattr(npc, name, list(value) if isinstance(value, list) else value)
        from uuid import uuid4
        npc.memory_revision = str(uuid4())
        npc.pending_item = None
    quest = db.scalar(select(Quest).where(Quest.player_id == player.id))
    if quest is not None:
        quest.status = 'not_started'
        quest.progress = 0
    bow = db.get(BowQuest, player.id)
    if bow is None:
        bow = BowQuest(player_id=player.id)
        db.add(bow)
    bow.phase = 'available'
    bow.string_collected = False
    bow.ready_at = None
    db.flush()
