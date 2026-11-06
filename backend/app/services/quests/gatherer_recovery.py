"""Save-scoped wood refusal and verified forest-gift recovery for the bow quest."""
import json

from fastapi import HTTPException
from sqlalchemy import select
from app.models import BowQuest, GathererEncounter, NPC
from app.services.island import RESOURCES
from app.services.state.resources import versioned
from app.services.validation.models import StateUpdate
from app.utils.math_utils import clamp

RULES = json.loads((RESOURCES / 'gatherer_recovery.json').read_text())
ITEM = RULES['item']
FACT_ID = 'quest.bow.gatherer_recovery'


def state(db, player):
    row = db.get(GathererEncounter, player.id)
    saved = row.state.get('wood_recovery', {}) if row and row.game_scope == player.game_scope else {}
    return {'refused': False, 'hint_unlocked': False, 'collected': [], 'gifts_given': 0} | saved


def store(db, player, value):
    from app.services.gatherer import record
    row = record(db, player)
    row.state = row.state | {'wood_recovery': value}


def active(db, player):
    quest = db.get(BowQuest, player.id)
    return bool(quest and quest.phase in {'meet', 'gather'})


def blocked(db, player, npc):
    return active(db, player) and (npc.aggression >= RULES['anger_threshold'] or (
        state(db, player)['refused'] and npc.trust < RULES['trust_threshold']))


def snapshot(db, player):
    saved = state(db, player)
    npc = db.scalar(select(NPC).where(NPC.role == 'gatherer'))
    refusing = bool(npc and blocked(db, player, npc))
    pickups = [p for p in RULES['pickups'] if p['id'] not in saved['collected']]
    return saved | {'blocked': refusing, 'item': ITEM,
        'pickups': pickups if active(db, player) and saved['hint_unlocked'] and refusing else []}


@versioned
def refuse_wood(db, player, npc, output):
    if (npc.role != 'gatherer' or output.item != 'wood'
            or not (output.action == 'give_item' or output.intent == 'confirm_transfer')
            or not blocked(db, player, npc)):
        return output
    saved = state(db, player)
    store(db, player, saved | {'refused': True})
    from app.services.quests.bow import reply
    text = ("I'm too angry to help with your bow. I'm keeping the wood. Talk to the Craftsman."
            if npc.aggression >= RULES['anger_threshold'] else
            "I'm calmer, but I don't trust you enough to share the wood yet. Talk to the Craftsman.")
    return reply(text, intent='wood_refused')


@versioned
def advise(db, player, npc, interpretation):
    if npc.role != 'craftsman' or not active(db, player):
        return None
    direct = [c for c in interpretation.get('concerns', []) if c.get('modality') == 'direct']
    requested = any((c.get('kind') == 'player_report' and c.get('target') == 'gatherer') or
                    c.get('operation') == 'craftsman.advise_gatherer' or
                    FACT_ID in c.get('fact_ids', []) for c in direct)
    if not requested:
        return None
    from app.services.quests.bow import reply
    saved = state(db, player)
    if not saved['refused']:
        return reply("Ask the Gatherer for the wood first. If he refuses, come back and tell me.")
    saved['hint_unlocked'] = True
    store(db, player, saved)
    db.get(BowQuest, player.id).phase = 'gather'
    return reply("He likes honeycomb. Look for golden pieces along the forest path west of the well. Give him one as a gift; bring another if he's still angry. Then ask for wood again.",
                 intent='gatherer_recovery_advice')


@versioned
def pickup(db, player, pickup_id, x, y):
    saved = state(db, player)
    if player.opening_state != 'complete' or not active(db, player) or not saved['hint_unlocked']:
        raise HTTPException(409, 'Ask the Craftsman about the refused wood first')
    at = next((p['position'] for p in RULES['pickups'] if p['id'] == pickup_id), None)
    if at is None:
        raise HTTPException(400, 'Unknown honeycomb pickup')
    if pickup_id in saved['collected']:
        return
    if (x - at['x']) ** 2 + (y - at['y']) ** 2 > 64 ** 2:
        raise HTTPException(409, 'Move closer to the honeycomb')
    saved['collected'] = [*saved['collected'], pickup_id]
    store(db, player, saved)
    player.inventory = list(player.inventory or []) + [ITEM]
    player.position = {'x': x, 'y': y}
    player.current_location = 'forest_edge'


def prepare_gift(db, player, npc, output):
    if (npc.role != 'gatherer' or output.action != 'receive_item' or output.item != ITEM
            or not active(db, player) or not state(db, player)['hint_unlocked']):
        return output
    output.state_update = StateUpdate(trust=RULES['gift_trust_change'], aggression=RULES['gift_aggression_change'])
    output.intent = 'recovery_gift'
    ready = (clamp(npc.aggression + output.state_update.aggression) < RULES['anger_threshold']
             and clamp(npc.trust + output.state_update.trust) >= RULES['trust_threshold'])
    output.dialogue = ("Thank you for the honeycomb. I'm calmer now. Ask me for the wood; I'll help with your bow." if ready
                       else "Thank you for the honeycomb. That helps, but I'm still on edge. Another gift would help me settle down.")
    return output


def record_gift(db, player, npc, output):
    if (npc.role == 'gatherer' and output.action == 'receive_item' and output.item == ITEM
            and active(db, player) and state(db, player)['hint_unlocked']):
        saved = state(db, player)
        store(db, player, saved | {'gifts_given': saved['gifts_given'] + 1})
