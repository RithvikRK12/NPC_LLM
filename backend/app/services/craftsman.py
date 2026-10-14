"""Trusted encounter commands. Dialogue proposals cannot write these outcomes."""
import json
import math
from uuid import uuid4
from fastapi import HTTPException
from app.models import CraftsmanEncounter, NPC, BowQuest
from app.models.ship_repair_quest import ShipRepairQuest
from app.services.island import RESOURCES, INTERIORS, BEACH, exterior_walkable
from app.services.quests.ship_repair import ship_snapshot

MARKS = json.loads((RESOURCES / 'craftsman_encounter.json').read_text())
PROPS = (json.loads((RESOURCES / 'village_layout.json').read_text())
         + json.loads((RESOURCES / 'forest_layout.json').read_text())['scenery'])
MODES = {'workshop_routine', 'departure_pending', 'following_player', 'waiting_for_player', 'returning_to_workshop'}

def defaults():
    return dict(intro_seen=False, wreck_reported=False, offer_pending=False, outing_active=False,
                inspection_complete=False, outcome_id='', mode='workshop_routine', navigation_space='workshop',
                position={'x': 10064., 'y': 9968.}, wait_reason='', return_index=0, presentation='', presentation_beat=0)

def record(db, player):
    row = db.get(CraftsmanEncounter, player.id)
    if row is None:
        row = CraftsmanEncounter(player_id=player.id, game_scope=player.game_scope, revision=0,
                                 state=defaults(), commands={})
        db.add(row)
        db.flush()
    if row.game_scope != player.game_scope:
        row.game_scope, row.revision, row.state, row.commands = player.game_scope, 0, defaults(), {}
    return row

def encounter_snapshot(db, player):
    row = record(db, player)
    return row.state | dict(game_scope=player.game_scope, revision=row.revision)

def snapshot(db, player):
    return dict(game_scope=player.game_scope, craftsman_encounter=encounter_snapshot(db, player),
                ship_repair=ship_snapshot(db, player))

def space_at(pos):
    x, y = pos['x'], pos['y']
    for name, room in INTERIORS.items():
        ox, oy = room['origin']
        if abs(x-ox) < 512 and abs(y-oy) < 384:
            return name
    return 'exterior'

def point_clear(pos):
    if not isinstance(pos,dict) or any(not isinstance(pos.get(key),(int,float)) or isinstance(pos.get(key),bool) for key in ("x","y")):
        return False
    try:
        x, y = float(pos['x']), float(pos['y'])
    except (KeyError, TypeError, ValueError):
        return False
    if not math.isfinite(x) or not math.isfinite(y): return False
    space = space_at(pos)
    def inside(rect):
        a, b, w, h = rect
        return a-12 <= x < a+w+12 and b-8 <= y < b+h+8
    if space != 'exterior':
        ox, oy = INTERIORS[space]['origin']
        if not (ox-308 <= x < ox+308 and oy-168 <= y < oy+200): return False
        for prop in INTERIORS[space]['furniture']:
            a,b,w,h = prop['footprint']; px,py=prop['at']
            if inside((ox+px+a,oy+py+b,w,h)): return False
        return True
    from app.services.scenery_geometry import blocked
    if not exterior_walkable(x,y) or blocked(x,y): return False
    for solid in BEACH['solids']:
        if inside(solid): return False
    for prop in PROPS:
        a,b,w,h=prop.get('footprint',[0,0,0,0]); px,py=prop['at']
        if w and h and inside((px+a,py+b,w,h)): return False
    return True

def require_revision(row, revision):
    if revision != row.revision: raise HTTPException(409, 'Encounter changed; reload its current state and retry')

def distance(pos, target):
    return math.hypot(pos['x']-target[0], pos['y']-target[1])

def checkpoint(db, player, data, revision):
    row = record(db, player)
    require_revision(row, revision)
    allowed = {'position','navigation_space','mode','wait_reason','return_index','presentation','presentation_beat'}
    if not data or set(data)-allowed: raise HTTPException(400, 'Unsupported encounter checkpoint')
    state = dict(row.state)
    pos = data.get('position', state['position'])
    if not point_clear(pos): raise HTTPException(400, 'Actor checkpoint is not clear ground')
    space = data.get('navigation_space', space_at(pos))
    if space != space_at(pos) or space not in {'workshop','exterior'}:
        raise HTTPException(400, 'Invalid actor navigation space')
    mode = data.get('mode', state['mode'])
    if mode not in MODES: raise HTTPException(400, 'Unknown activity')
    if mode in {'following_player','waiting_for_player','departure_pending'} and not state['outing_active']:
        raise HTTPException(409, 'No accepted outing')
    if mode == 'returning_to_workshop' and state['mode'] != mode:
        raise HTTPException(409, 'Return requires an authored command')
    if mode == 'workshop_routine' and (space != 'workshop' or state['mode'] not in {'workshop_routine','returning_to_workshop'}):
        raise HTTPException(409, 'Workshop arrival required')
    presentation = data.get('presentation', state['presentation'])
    if presentation not in {'','inspection_staging','inspection_dialogue','outcome_pending'}:
        raise HTTPException(400, 'Invalid presentation checkpoint')
    if presentation and (not state['outing_active'] or state['inspection_complete'] or space != 'exterior'
                         or distance(pos,MARKS['InspectionArrival'])>220):
        raise HTTPException(409, 'Inspection staging is not eligible')
    beat=data.get('presentation_beat',state.get('presentation_beat',0))
    if not isinstance(beat,int) or not 0<=beat<=4: raise HTTPException(400,'Invalid inspection beat')
    index = data.get('return_index',state['return_index'])
    if not isinstance(index,int) or not 0 <= index <= len(MARKS['return_route']):
        raise HTTPException(400, 'Invalid return landmark')
    state.update(data)
    state['position'], state['navigation_space'] = dict(pos), space
    row.state, row.revision = state, row.revision+1
    npc = db.query(NPC).filter_by(role='craftsman').first()
    if npc: npc.location = 'workshop' if space=='workshop' else ('shipwreck_beach' if pos['y']>3000 else 'island')
    db.flush()
    return snapshot(db,player)

def apply_command(db, player, npc, command, request_id, expected_revision, payload):
    if npc.role != 'craftsman': raise HTTPException(400, 'Only the Craftsman can inspect the ship')
    if player.opening_state != 'complete': raise HTTPException(409, 'Finish arriving first')
    row = record(db,player)
    if request_id in row.commands:
        saved = row.commands[request_id]
        if saved['command'] != command: raise HTTPException(409, 'Command ID already used')
        return saved['result']
    require_revision(row,expected_revision)
    state = dict(row.state)
    if command == 'intro_complete':
        reported=payload.get('player_position',player.position)
        if not point_clear(reported): raise HTTPException(400,'Invalid introduction position')
        if state['navigation_space'] != 'workshop' or space_at(reported)!='workshop':
            raise HTTPException(409,'Enter the workshop first')
        player.position=dict(reported)
        state['intro_seen'] = True
    elif command == 'report_wreck':
        state['wreck_reported'], state['offer_pending'] = True, not state['inspection_complete']
        state['topic']='ship'
    elif command == 'begin_ship_inspection':
        if not state['inspection_complete'] and not state['outing_active']:
            state.update(wreck_reported=True, offer_pending=False, outing_active=True, mode='departure_pending',wait_reason='',topic='ship')
    elif command in {'wait','resume','return','postpone'}:
        if not state['outing_active']: raise HTTPException(409,'No accepted outing')
        if command == 'wait': state.update(mode='waiting_for_player',wait_reason='requested')
        elif command == 'resume': state.update(mode='departure_pending',wait_reason='')
        elif command == 'postpone' and state['navigation_space']=='workshop':
            state.update(mode='workshop_routine',outing_active=False,wait_reason='')
        else: state.update(mode='returning_to_workshop',outing_active=False,return_index=0,wait_reason='')
    elif command == 'complete_inspection':
        if not state['inspection_complete']:
            reported = payload.get('player_position', player.position)
            if not point_clear(reported): raise HTTPException(400,'Invalid inspection position')
            if (not state['outing_active'] or state['navigation_space']!='exterior' or
                not payload.get('staged') or not point_clear(reported) or
                distance(reported,MARKS['InspectionPlayerMark'])>20 or
                distance(state['position'],MARKS['InspectionCraftsmanMark'])>20):
                raise HTTPException(409,'Both actors must reach the inspection marks')
            player.position = dict(reported)
            outcome = str(uuid4())
            state.update(inspection_complete=True,outcome_id=outcome,outing_active=False,
                         mode='returning_to_workshop',return_index=0,presentation='')
            if db.get(ShipRepairQuest,player.id) is None:
                db.add(ShipRepairQuest(player_id=player.id,game_scope=player.game_scope,
                                      phase='gathering_materials',contributions={},outcome_id=outcome))
    else: raise HTTPException(400,'Unsupported encounter command')
    if state != row.state and command in {'report_wreck','begin_ship_inspection','complete_inspection'}:
        from app.models import Memory
        if command=='begin_ship_inspection' and not row.state.get('wreck_reported'):
            db.add(Memory(npc_id=npc.id,game_scope=player.game_scope,source_event_id=str(uuid4()),
                          event='Player reported a wreck while asking for help (unverified).',event_type='ship_encounter',
                          importance=.9,emotion='calm',epistemic_status='claim',authority='reported',quest_id='ship_repair'))
        evidence = {
            'report_wreck': ('Player reported a wreck (unverified): the Craftsman has not inspected the damage.', 'claim', 'reported'),
            'begin_ship_inspection': ('Craftsman agreed to inspect the player’s wreck. Damage is not yet firsthand knowledge.', 'fact', 'authoritative'),
            'complete_inspection': ('Craftsman inspected the ship: split planking and leaking seams. A Way Home started.', 'fact', 'authoritative'),
        }[command]
        db.add(Memory(npc_id=npc.id,game_scope=player.game_scope,source_event_id=str(uuid4()),
                      event=evidence[0],event_type='ship_encounter',importance=.9,emotion='calm',
                      epistemic_status=evidence[1],authority=evidence[2],quest_id='ship_repair'))
    row.state, row.revision = state, row.revision+1
    db.flush()
    result = snapshot(db,player)
    row.commands = row.commands | {request_id:dict(command=command,result=result)}
    return result
