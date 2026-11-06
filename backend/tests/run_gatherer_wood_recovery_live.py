"""Live local-Llama wood refusal/recovery scenario using a disposable in-memory save.

Export config/playtest.env and run with PYTHONPATH=backend. This never connects
Godot or modifies the player's saved database. Unit tests cover full bow completion.
"""
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.api.router import api_router
from app.database.base import Base
from app.database.seed import seed_world
from app.database.session import get_db
from app.models import Player,NPC
from app.services.quests.bow import get_quest
from app.services.gatherer import record
from app.config.settings import get_settings
settings=get_settings()
if settings.llm_model!='llama3:willowbrook' or settings.llm_base_url.rstrip('/')!='http://127.0.0.1:11434/v1':
    raise SystemExit('Run with config/playtest.env and local llama3:willowbrook; no hosted/mock inference allowed')
engine=create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread':False})
Base.metadata.create_all(engine)
app=FastAPI();app.include_router(api_router)
with Session(engine) as db,TestClient(app) as client:
    seed_world(db);p=db.get(Player,1);p.opening_state='complete';db.flush()
    get_quest(db).phase='gather';g=db.get(NPC,2);g.trust=0.;g.aggression=1.
    record(db,p).state=record(db,p).state|{'status':'resolved_helped'};db.commit()
    scope=p.game_scope
    app.dependency_overrides[get_db]=lambda:db
    def say(npc,message):
        response=client.post('/chat',json={'npc_id':npc,'player_message':message,'game_scope':scope})
        assert response.status_code==200,response.text
        data=response.json()
        print(json.dumps({'npc':npc,'message':message,'dialogue':data['final_dialogue'],
            'interpretation':data['grounding_trace']['accepted_interpretation'],
            'rejected':data['grounding_trace']['rejected'],'state':data['npc'],
            'inventory':data['player_inventory'],'quest':data['bow_quest']}),flush=True)
        assert not data['grounding_trace']['rejected']
        return data
    denied=say(2,'Could you spare some wood so the Craftsman can make my bow?')
    assert 'wood' not in denied['player_inventory']
    assert denied['bow_quest']['gatherer_recovery']['refused']
    hint=say(1,"The Gatherer is furious with me and won't share lumber. What can I do?")
    assert hint['bow_quest']['gatherer_recovery']['hint_unlocked']
    pickups=hint['bow_quest']['gatherer_recovery']['pickups']
    for index,pickup in enumerate(pickups[:2]):
        response=client.post('/quests/bow/pickup-honeycomb',json={'game_scope':scope,'pickup_id':pickup['id'],**pickup['position']})
        assert response.status_code==200,response.text
        result=say(2,'Here, take this honeycomb.' if index==0 else "I brought another honeycomb for you. Please take it.")
        assert result['npc']['aggression'] <= 1-.4*(index+1)+1e-9
        assert result['npc']['trust'] >= .3*(index+1)-1e-9
        assert 'honeycomb' not in result['player_inventory']
    result=say(2,'Could you give me wood to make a bow?')
    if 'wood' not in result['player_inventory']:
        result=say(2,'To make a bow.')
    assert 'wood' in result['player_inventory']
print('LIVE WOOD RECOVERY PASS',flush=True)
engine.dispose()
