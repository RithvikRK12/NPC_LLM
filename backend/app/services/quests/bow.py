from app.services.state.resources import versioned
"""Authoritative, restart-safe bow quest. Only these rules can craft/reward a bow."""
import re
import time
from sqlalchemy import select
from app.models.bow_quest import BowQuest
from app.models import NPC, Conversation
from app.services.validation.models import LLMResponse, StateUpdate

CRAFT_SECONDS = 5.0
STRING_POSITION = {'x': -70.0, 'y': 240.0}


@versioned
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
        'available': 'Explore the village. Start Get a bow when you are ready.',
        'meet': 'Talk to the Craftsman and ask for a bow.',
        'gather': 'Get wood from the Gatherer. Pick up string near the well. Give both to the Craftsman.',
        'crafting': 'The Craftsman is making your bow.',
        'completed': 'Quest complete! Your bow is in your satchel.',
    }
    return {'title': 'Get a bow', 'phase': phase, 'objective': objectives[phase],
            'string_available': bool(quest and phase == 'gather' and not quest.string_collected),
            'string_position': STRING_POSITION, 'remaining_seconds': remaining,
            'craft_seconds': CRAFT_SECONDS, 'craft_progress': (1 - remaining / CRAFT_SECONDS) * 100 if phase == 'crafting' else (100 if phase == 'completed' else 0)}


def reply(text, intent='inform'):
    return LLMResponse(intent=intent, emotion='calm', dialogue=text, action='speak',
                       reasoning='Authoritative village and bow quest state.', state_update=StateUpdate())


@versioned
def dialogue(db, npc, message, player):
    quest = get_quest(db, player.id)
    words = set(re.findall(r'[a-z]+', message.lower()))
    relevant = bool(words & {'bow', 'quest', 'craft', 'crafting', 'materials', 'string'}) or message.lower().strip(' ?!.') in {'what do you want', 'what do you need', 'what next', 'what should i do'}
    if not relevant:
        return None
    if quest.phase == 'available':
        return reply('If you want a bow, Open Quests and begin Get a bow. For now, feel free to explore the village.')
    if quest.phase == 'completed':
        return reply('Your bow quest is complete. The bow is in your satchel.' if 'bow' in (player.inventory or []) else 'Your bow quest is complete. You have since given the bow away; check the villagers supplies.')
    if quest.phase == 'crafting':
        return reply('The bow is still being crafted. Watch the progress bar; it will be placed in your satchel when it is ready.')
    if npc.role != 'craftsman':
        return reply('Ask the Craftsman about the bow. I can share wood if I have some; the fallen string is near the well.')
    if quest.phase == 'meet':
        quest.phase = 'gather'
    missing = [item for item in ('wood', 'string') if item not in (npc.inventory or [])]
    if missing:
        return reply('I need ' + ' and '.join(missing) + ' to make your bow. Get wood from the Gatherer and pick up string near the well, then give me the materials.')
    return reply('I have the wood and string. I will begin crafting your bow now.')


@versioned
def maybe_start(db, player, npc, output):
    quest = get_quest(db, player.id)
    if npc.role != 'craftsman' or quest.phase != 'gather':
        return
    from app.models import CraftsmanEncounter
    encounter = db.get(CraftsmanEncounter, player.id)
    if encounter and (encounter.state.get('mode') != 'workshop_routine' or encounter.state.get('navigation_space') != 'workshop'):
        return
    stock = list(npc.inventory or [])
    if not all(item in stock for item in ('wood', 'string')):
        return
    stock.remove('wood')
    stock.remove('string')
    npc.inventory = stock
    npc.pending_item = None
    npc.current_state = 'crafting_bow'
    quest.phase = 'crafting'
    quest.ready_at = time.time() + CRAFT_SECONDS
    output.dialogue = 'Thank you! I have the wood and string. Give me a few seconds to craft your bow.'
    db.flush()


@versioned
def finish_if_ready(db, player):
    quest = get_quest(db, player.id)
    if quest.phase != 'crafting' or time.time() < (quest.ready_at or float('inf')):
        return None
    craftsman = db.scalar(select(NPC).where(NPC.role == 'craftsman').with_for_update())
    inventory_before = list(player.inventory or [])
    player.inventory = inventory_before + ['bow']
    quest.phase = 'completed'
    craftsman.current_state = 'available'
    output = reply('Your bow is ready. Here you are! Get a bow is complete.')
    from app.services.memory.service import MemoryService
    from app.services.memory.importance import MemoryDecision
    classification = MemoryDecision(1., 'quest_completion', 'Authoritative timed reward executed.',
                                    'Bow quest completed. Craftsman gave the player one bow.').payload()
    outcome = {'quest_before': 'crafting', 'quest_after': 'completed', 'reward': 'bow',
               'inventory_before': {'player': inventory_before}, 'inventory_after': {'player': list(player.inventory)}}
    conversation = Conversation(npc_id=craftsman.id, game_scope=player.game_scope,
        player_input='[Bow crafting finished]', llm_output={},
        validated_output=output.model_dump() | {'memory_classification': classification,
                          'behavior_trace': {'verified_outcome': outcome}}, final_dialogue=output.dialogue)
    db.add(conversation)
    db.flush()
    conversation.validated_output = conversation.validated_output | {'behavior_trace': {
        'verified_outcome': outcome | {'event_id': conversation.source_event_id, 'conversation_id': conversation.id}}}
    write = MemoryService(db).store_conversation(craftsman, conversation)
    conversation.validated_output = conversation.validated_output | {'memory_classification': classification | write.payload()}
    return output.dialogue
