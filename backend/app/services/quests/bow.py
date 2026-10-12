"""Authoritative, restart-safe pulse blaster quest.

The route remains /quests/bow for API compatibility with the existing demo, but
only these rules can assemble and reward the cyberpunk quest item.
"""
import re
import time
from sqlalchemy import select
from app.models.bow_quest import BowQuest
from app.models import NPC, Conversation
from app.services.validation.models import LLMResponse, StateUpdate

CRAFT_SECONDS = 5.0
STRING_POSITION = {'x': -70.0, 'y': 240.0}
COMPONENT_FROM_BROKER = 'circuit_board'
WORLD_PICKUP = 'fiber_cable'
REWARD_ITEM = 'pulse_blaster'


def get_quest(db, player_id=1):
    quest = db.get(BowQuest, player_id)
    if quest is None:
        quest = BowQuest(player_id=player_id, phase='available', string_collected=False)
        db.add(quest)
        db.flush()
    return quest


def snapshot(quest):
    phase = quest.phase if quest else 'available'
    remaining = max(0.0, (quest.ready_at or 0) - time.time()) if quest and phase == 'crafting' else 0.0
    objectives = {
        'available': 'Explore JIT Cyber Grid. Start Assemble Pulse Blaster when you are ready.',
        'meet': 'Talk to the Neon Techsmith and ask about the Pulse Blaster.',
        'gather': 'Get a circuit board from the Data Broker. Pick up fiber cable near the power junction. Give both to the Techsmith.',
        'crafting': 'The Neon Techsmith is assembling your Pulse Blaster.',
        'completed': 'Quest complete! The Pulse Blaster is in your loadout.',
    }
    return {'title': 'Assemble Pulse Blaster', 'phase': phase, 'objective': objectives[phase],
            'string_available': bool(quest and phase == 'gather' and not quest.string_collected),
            'string_position': STRING_POSITION, 'remaining_seconds': remaining,
            'craft_seconds': CRAFT_SECONDS, 'craft_progress': (1 - remaining / CRAFT_SECONDS) * 100 if phase == 'crafting' else (100 if phase == 'completed' else 0)}


def reply(text, intent='inform'):
    return LLMResponse(intent=intent, emotion='calm', dialogue=text, action='speak',
                       reasoning='Authoritative cyberpunk quest state.', state_update=StateUpdate())


def dialogue(db, npc, message, player):
    quest = get_quest(db, player.id)
    words = set(re.findall(r'[a-z]+', message.lower()))
    relevant = bool(words & {'pulse', 'blaster', 'quest', 'assemble', 'build', 'craft', 'crafting', 'materials', 'components', 'fiber', 'cable', 'circuit', 'board'}) or message.lower().strip(' ?!.') in {'what do you want', 'what do you need', 'what next', 'what should i do'}
    if not relevant:
        return None
    if quest.phase == 'available':
        return reply('If you want a Pulse Blaster, open Quests and begin Assemble Pulse Blaster. For now, scan the neon district.')
    if quest.phase == 'completed':
        return reply('Your Pulse Blaster is complete. It is in your loadout.' if REWARD_ITEM in (player.inventory or []) else 'The Pulse Blaster quest is complete. You have since handed it off; check local supplies.')
    if quest.phase == 'crafting':
        return reply('The Pulse Blaster is still on the bench. Watch the assembly bar; it will sync to your loadout when ready.')
    if npc.role != 'craftsman':
        return reply('Ask the Neon Techsmith about the Pulse Blaster. I can share a circuit board if I have one; loose fiber cable is near the power junction.')
    if quest.phase == 'meet':
        quest.phase = 'gather'
    missing = [item for item in (COMPONENT_FROM_BROKER, WORLD_PICKUP) if item not in (npc.inventory or [])]
    if missing:
        return reply('I need ' + ' and '.join(missing) + ' to assemble your Pulse Blaster. Get a circuit board from the Data Broker and pick up fiber cable near the power junction, then bring both to my bench.')
    return reply('I have the circuit board and fiber cable. I will begin assembling your Pulse Blaster now.')


def maybe_start(db, player, npc, output):
    quest = get_quest(db, player.id)
    if npc.role != 'craftsman' or quest.phase != 'gather':
        return
    stock = list(npc.inventory or [])
    if not all(item in stock for item in (COMPONENT_FROM_BROKER, WORLD_PICKUP)):
        return
    stock.remove(COMPONENT_FROM_BROKER)
    stock.remove(WORLD_PICKUP)
    npc.inventory = stock
    npc.pending_item = None
    npc.current_state = 'assembling_pulse_blaster'
    quest.phase = 'crafting'
    quest.ready_at = time.time() + CRAFT_SECONDS
    output.dialogue = 'Good work, Runner. I have the circuit board and fiber cable. Give me a few seconds to tune the Pulse Blaster.'
    db.flush()


def finish_if_ready(db, player):
    quest = get_quest(db, player.id)
    if quest.phase != 'crafting' or time.time() < (quest.ready_at or float('inf')):
        return None
    craftsman = db.scalar(select(NPC).where(NPC.role == 'craftsman').with_for_update())
    player.inventory = list(player.inventory or []) + [REWARD_ITEM]
    quest.phase = 'completed'
    craftsman.current_state = 'available'
    output = reply('Pulse Blaster online. Sync complete; Assemble Pulse Blaster is done.')
    from app.services.memory.service import MemoryService
    classification = {'important': True, 'importance': 1.0, 'category': 'quest_completion',
                      'reason': 'Server completed assembly and granted one pulse blaster.', 'stored': True, 'version': 1}
    MemoryService(db).store_memory(craftsman, 'Pulse Blaster quest completed. Neon Techsmith gave the player one pulse blaster.', 1.0, 'calm', event_type='quest_completion', quest_id='assemble_pulse_blaster')
    db.add(Conversation(npc_id=craftsman.id, player_input='[Pulse Blaster assembly finished]', llm_output={},
                        validated_output=output.model_dump() | {"memory_classification": classification}, final_dialogue=output.dialogue))
    return output.dialogue
