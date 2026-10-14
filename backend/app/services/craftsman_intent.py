"""A bounded intent adapter, separate from generated speech and inventory permissions."""
import re
from app.services.craftsman import record, apply_command
from app.services.quests.ship_repair import ship_snapshot, material_list
from app.services.quests.bow import reply
from uuid import uuid4

def resolve_craftsman_intent(message, recent_context, encounter, focus=None):
    text=message.lower().replace('’',"'").strip(' .!?')
    # Quotes, hypotheticals and general questions never authorize an outing.
    if re.search(r'''["“”]|^\s*'|\b(?:imagine|hypothetic\w*|suppose|someone|somebody|he said|she said|do ships often|if my)\b''',text): return {}
    if re.search(r"\b(?:don't need help|do not need help|isn't damaged|is not damaged|isn't wrecked|is not wrecked|not asking for help)\b",text): return {}
    if re.search(r"\b(?:not now|don't want|do not want|not yet|rather not|don't go|do not go)\b",text):
        return {'command':'postpone'} if encounter['outing_active'] else {'kind':'postponed'}
    if text in {'wait','wait here','please wait','stay here','can you wait here'}:
        return {'command':'wait'} if encounter['outing_active'] else {}
    if re.search(r"^(?:let's go|lets go|follow me|come along|resume|keep following|we can go now)$",text):
        return {'command':'resume' if encounter['outing_active'] else 'begin_ship_inspection'} if encounter['outing_active'] or encounter.get('offer_pending') else {}
    if re.search(r'\b(?:go|head|return|back)\b.*\b(?:workshop|home)\b',text) and encounter['outing_active']:
        return {'command':'return'}
    # An explicit new subject wins over durable wreck-report context.
    if re.search(r'\b(?:bow|axe|string|wood|food|water|rope)\b',text) and not re.search(r'\b(?:ship|boat|wreck)\b',text): return {}
    ship = bool(re.search(r'\b(?:ship|boat|wreck|washed (?:up|ashore))\b',text))
    owned = bool(re.search(r'\b(?:my|our) (?:ship|boat)|\bi washed\b',text))
    damage = bool(re.search(r'\b(?:wreck\w*|broke\w*|damag\w*|storm|sank|washed)\b',text))
    help_request = bool(re.search(r'\b(?:help|repair|fix|inspect|look at|see the ship)\b',text)) and bool(re.search(r'\b(?:can|could|would|please|need|come|help me)\b',text))
    agreement = text in {'yes','yes please','yes, please','please do','thank you, yes','okay','ok','sure','show you','lead the way'}
    if encounter['inspection_complete'] and help_request and (ship or encounter['wreck_reported']):
        return {'kind':'inspected'}
    if help_request and (ship or encounter['wreck_reported']):
        if not owned and not encounter['wreck_reported'] and not re.search(r'inspect the wreck with me',text):
            return {'kind':'clarify'}
        return {'command':'begin_ship_inspection'}
    if agreement and encounter.get('offer_pending'): return {'command':'begin_ship_inspection'}
    if ship and owned and damage: return {'command':'report_wreck'}
    return {}

def dialogue(db,npc,message,player,context):
    if npc.role!='craftsman': return None
    row=record(db,player)
    intent=resolve_craftsman_intent(message,context.recent_dialogue,row.state,context.conversation_focus)
    command=intent.get('command')
    if command:
        if command=='begin_ship_inspection' and row.state['outing_active']:
            return reply("I'm ready to inspect it with you. Lead the way when you're ready.")
        apply_command(db,player,npc,command,str(uuid4()),row.revision,{})
        texts={
            'report_wreck':"I'm glad you made it ashore. I can take a look at the damage with you, if you'd like.",
            'begin_ship_inspection':"Oh no, that's very unfortunate. I'm glad you made it ashore. Can I see the ship so I can work out what I can do? Lead the way.",
            'wait':"Of course. I'll wait here; tell me when you're ready to go.",
            'resume':"All right. Lead the way; we'll take it at your pace.",
            'postpone':"Of course. There's no hurry to go back before you're ready.",
            'return':"I'll head back to my workshop. Come and find me when you're ready to try again.",
        }
        from app.models import BowQuest
        if command=='begin_ship_inspection' and (bow:=db.get(BowQuest,player.id)) and bow.phase=='crafting':
            return reply("I'm glad you made it ashore. I'll finish this bow first, then come and inspect your ship. It will only take a moment.")
        return reply(texts[command])
    if intent.get('kind')=='clarify': return reply('Is this your damaged ship, and would you like me to come and inspect it with you?')
    if intent.get('kind')=='postponed': return reply("Of course. We can talk here until you feel ready.")
    if intent.get('kind')=='inspected': return reply("We've inspected her together. A Way Home has the material list; gathering and repair are not available in this version yet.")
    text=message.lower()
    ship_named=bool(re.search(r'\b(?:ship|wreck|boat)\b',text))
    bow_named=bool(re.search(r'\bbow\b',text))
    if ship_named or bow_named:
        row.state=row.state | {'topic':'ship' if ship_named else 'bow'}
    requirements=bool(re.search(r'\b(?:materials|requirements|need|bring|delivered|brought)\b',text))
    if requirements and (ship_named or bow_named or re.fullmatch(r'\s*(?:what (?:do you|should i) (?:need|bring)|what materials do you need)[ ?!.]*',text)):
        from app.models import BowQuest
        ship=ship_snapshot(db,player)
        bow=db.get(BowQuest,player.id)
        topic='ship' if ship_named else ('bow' if bow_named else row.state.get('topic'))
        if not topic and ship['phase']!='not_started' and bow and bow.phase not in {'available','completed'}:
            return reply('For the bow, or for your ship?')
        if topic=='ship' or (not topic and ship['phase']!='not_started'):
            if ship['phase']=='not_started': return reply("I'll need to inspect the damage before I can tell you what the ship needs.")
            counts=material_list(ship['materials'],remaining=True)
            return reply('For your ship, still needed: '+counts+'. No contributions are recorded yet.')
    return None
