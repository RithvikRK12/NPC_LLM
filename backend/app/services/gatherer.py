"""Run-scoped Gatherer story; combat stays local, outcomes commit atomically."""
from uuid import uuid4, uuid5, NAMESPACE_URL
import json
from app.services.island import RESOURCES
from fastapi import HTTPException
from sqlalchemy import select
from app.models import GathererEncounter, Memory, NPC
from app.schemas.npc import NPCRead

STAGING = json.loads((RESOURCES / 'gatherer_encounter.json').read_text())
MARKS = STAGING['marks']
def position_at(name):
    x, y = MARKS[name]
    return {'x': float(x), 'y': float(y)}
CHECKPOINT = {'position': position_at('IntroCheckpoint'), 'facing': {'x': -1., 'y': 0.}, 'staging_version': STAGING['version']}
HELPED = 'The player accepted my request, took my borrowed knife, and helped defeat the two boars threatening me.'
DECLINED = 'I asked the player for help against two boars. They refused and returned toward the village; I dealt with the boars myself.'
RESOLVED = {'resolved_helped', 'resolved_declined'}


def defaults():
    return dict(status='unseen', checkpoint={}, attempt_id='', accepted_attempt_id='', outcome_fact='')


def record(db, player):
    row = db.get(GathererEncounter, player.id)
    if row is None:
        row = GathererEncounter(player_id=player.id, game_scope=player.game_scope,
                                revision=0, state=defaults(), commands={})
        db.add(row)
        db.flush()
    if row.game_scope != player.game_scope:
        row.game_scope, row.revision, row.state, row.commands = player.game_scope, 0, defaults(), {}
    checkpoint = row.state.get('checkpoint', {})
    if checkpoint and checkpoint.get('staging_version', 1) < STAGING['version']:
        # This migrates authored staging only: no branch, attempt, revision,
        # inventory or social outcome is replayed. Pending scenes load on the
        # new clear marks instead of routing from the obsolete clearing.
        row.state = row.state | {'checkpoint': CHECKPOINT}
        status = row.state['status']
        if status == 'intro_pending': player.position = position_at('IntroCheckpoint')
        elif status in {'saved_thanks_pending', 'declined_retreat_pending', 'declined_confrontation_pending'}:
            player.position = position_at('PlayerTalkMark')
    return row


def encounter_snapshot(db, player):
    row = record(db, player)
    return row.state | dict(game_scope=player.game_scope, revision=row.revision)


def snapshot(db, player):
    return dict(game_scope=player.game_scope, gatherer_encounter=encounter_snapshot(db, player))


def apply_command(db, player, command, request_id, expected_revision, payload):
    # API caller holds the player lock, serializing new-game, chat and outcomes.
    if player.opening_state != 'complete':
        raise HTTPException(409, 'Finish arriving first')
    row = record(db, player)
    if request_id in row.commands:
        saved = row.commands[request_id]
        if saved['command'] != command or saved['payload'] != payload:
            raise HTTPException(409, 'Command ID already used for a different request')
        return saved['result']
    if row.revision != expected_revision:
        raise HTTPException(409, 'Encounter changed; reload current state')
    state = dict(row.state)
    status = state['status']
    allowed = {
        'begin_intro': {'unseen'}, 'accept': {'intro_pending'},
        'restart_attempt': {'intro_pending'}, 'victory': {'intro_pending'},
        'decline': {'intro_pending'}, 'complete_retreat': {'declined_retreat_pending'},
        'begin_confrontation': {'declined_return_pending'},
        'finish_presentation': {'saved_thanks_pending', 'declined_confrontation_pending'},
    }
    if command not in allowed:
        raise HTTPException(400, 'Unsupported encounter command')
    if status not in allowed[command]:
        raise HTTPException(409, 'Command is not allowed in this encounter state')
    if command in {'accept', 'restart_attempt', 'victory'}:
        if not state['attempt_id'] or payload.get('attempt_id') != state['attempt_id']:
            raise HTTPException(409, 'Encounter attempt has changed')
    if command == 'begin_intro':
        state.update(status='intro_pending', checkpoint=CHECKPOINT, attempt_id=str(uuid4()))
        player.position = dict(CHECKPOINT['position'])
    elif command == 'accept':
        if state['accepted_attempt_id']:
            raise HTTPException(409, 'Attempt already accepted')
        state['accepted_attempt_id'] = state['attempt_id']
    elif command == 'restart_attempt':
        state.update(attempt_id=str(uuid4()), accepted_attempt_id='')
        player.position = dict(CHECKPOINT['position'])
    elif command == 'victory':
        if state['accepted_attempt_id'] != state['attempt_id']:
            raise HTTPException(409, 'Accept help before committing victory')
        state.update(status='saved_thanks_pending', outcome_fact=HELPED)
    elif command == 'decline':
        if state['accepted_attempt_id']:
            raise HTTPException(409, 'Restart the accepted attempt before choosing again')
        state.update(status='declined_retreat_pending', outcome_fact=DECLINED)
    elif command == 'complete_retreat':
        state['status'] = 'declined_return_pending'
        player.position = position_at('VillageReturnMark')
    elif command == 'begin_confrontation':
        state['status'] = 'declined_confrontation_pending'
    elif command == 'finish_presentation':
        state['status'] = 'resolved_helped' if status == 'saved_thanks_pending' else 'resolved_declined'
    if command in {'victory', 'decline'}:
        npc = db.scalar(select(NPC).where(NPC.role == 'gatherer').with_for_update())
        if npc is None:
            raise HTTPException(404, 'Gatherer not found')
        if command == 'victory':
            for field, change in {'trust': .35, 'fear': -.15, 'aggression': -.05, 'curiosity': .10}.items():
                setattr(npc, field, min(1., max(0., getattr(npc, field) + change)))
        else:
            npc.trust, npc.aggression = min(npc.trust, .15), max(npc.aggression, .75)
        # Direct authoritative event insertion follows craftsman; the Memory model
        # listener invalidates its retrieval revision in this same transaction.
        db.add(Memory(npc_id=npc.id, game_scope=player.game_scope,
                      source_event_id=str(uuid5(NAMESPACE_URL, f'gatherer:{player.game_scope}:{player.id}')),
                      event=state['outcome_fact'], event_type='gatherer_encounter', importance=1.,
                      emotion='gratitude and relief' if command == 'victory' else 'anger and distrust',
                      epistemic_status='fact', authority='authoritative'))
    row.state, row.revision = state, row.revision + 1
    db.flush()
    result = snapshot(db, player)
    gatherer = db.scalar(select(NPC).where(NPC.role == 'gatherer'))
    if gatherer is not None:
        result['npc'] = NPCRead.model_validate(gatherer).model_dump()
    row.commands = row.commands | {request_id: dict(command=command, payload=dict(payload), result=result)}
    db.flush()
    return result


def chat_blocked(db, player, npc):
    row = db.get(GathererEncounter, player.id)
    if row is None or row.game_scope != player.game_scope:
        return False
    status = row.state.get('status', 'unseen')
    if status in RESOLVED or status == 'unseen':
        return False
    return status != 'declined_return_pending' or npc.role == 'gatherer'
