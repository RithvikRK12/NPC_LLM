"""Small enabled-route playtest, not the frozen release-quality benchmark.

Uses a temporary SQLite database and real local Llama transport. Does not open,
reset, migrate or inspect the personal game save.
"""
import json
import math
import re
import os
from pathlib import Path
import tempfile
import time
from urllib.request import urlopen
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
for key,value in dotenv_values(ROOT/'config/playtest.env').items():
    if value is not None: os.environ[key]=value
samples=[]
with tempfile.TemporaryDirectory(prefix='npc-live-adoption-') as temp:
    os.environ['DATABASE_URL']='sqlite:///'+str(Path(temp)/'world.db')
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.config.settings import get_settings
    with TestClient(create_app()) as client:
        world=client.get('/world').json()
        scope=world['game_scope']
        completed=client.post('/world/opening/complete',json={'game_scope':scope,'opening_version':world['opening_version']})
        assert completed.status_code==200,completed.text
        def say(npc,message,route):
            world=client.get('/world').json()
            payload={'schema_version':1,'request_id':'live:'+str(len(samples)+1),'game_scope':scope,
                'conversation_epoch':world['conversation_epochs'][str(npc)],'npc_id':npc,'player_message':message}
            before=world['player_inventory'];started=time.monotonic()
            response=client.post('/chat',json=payload)
            while response.status_code==202 and time.monotonic()-started<190:
                time.sleep(.1);response=client.get(response.json()['status_url'])
            assert response.status_code==200,response.text
            body=response.json()
            assert ''.join(body['dialogue_beats'])==body['final_dialogue']
            replay=client.post('/chat',json=payload)
            assert replay.status_code==200 and replay.json()==body
            if route in {'ordinary','action'}:
                assert body['response_origin']=='generated' and body['degradation_reason'] is None,body
            if message == 'I give you water':
                assert not re.search(r'\b(?:ship|wreck|bow|stranded)\b',body['final_dialogue'],re.I),body
            if route in {'ordinary','provider_outage'}:
                assert client.get('/world').json()['player_inventory']==before
            sample={'npc_id':npc,'message':message,'route':route,'seconds':round(time.monotonic()-started,4),
                'response_origin':body['response_origin'],'degradation_reason':body['degradation_reason'],
                'dialogue':body['final_dialogue'],'receipt_count':len(body['receipt_refs']),
                'exact_retry':True}
            samples.append(sample)
            (OUT/'live-route-samples.json').write_text(json.dumps(samples,indent=2))
            print(sample,flush=True)
            return body
        for npc in (1,2):
            say(npc,'What do you enjoy about your work?','ordinary')
            say(npc,'What helps you feel at ease?','ordinary')
        wreck=say(1, "my ship just wrecked and i'm stranded!", 'action')
        assert len(wreck['receipt_refs'])==1
        assert client.post('/quests/bow/start').status_code==200
        say(1,'Can you make me a bow?','action')
        request=say(2,'May I have wood?','purpose_question')
        assert not request['receipt_refs']
        transfer=say(2,'To help the Craftsman make a bow','action')
        assert len(transfer['receipt_refs'])==1
        gift=say(1,'I give you water','action')
        assert len(gift['receipt_refs'])==1
        # Real connection refusal, never mock speech or an alternate model.
        settings=get_settings();endpoint=settings.llm_base_url
        try:
            settings.llm_base_url='http://127.0.0.1:1/v1'
            for npc in (1,2):
                w=client.get('/world').json()
                cleared=client.delete('/chat/'+str(npc),params={'game_scope':scope,'conversation_epoch':w['conversation_epochs'][str(npc)]})
                assert cleared.status_code==200,cleared.text
                outage=say(npc,'How are you feeling today?','provider_outage')
                assert outage['response_origin']=='fallback' and outage['degradation_reason']=='PROVIDER_UNAVAILABLE' and not outage['receipt_refs']
        finally:settings.llm_base_url=endpoint
        with urlopen('http://127.0.0.1:11434/api/ps',timeout=5) as response:
            active=json.load(response)
        with urlopen('http://127.0.0.1:11434/api/tags',timeout=5) as response:
            tags=json.load(response)
        model=[row for row in active['models'] if row['name']=='llama3:willowbrook']
        assert model and model[0]['context_length']==8192,active
        routes={}
        for route in sorted({row['route'] for row in samples}):
            values=sorted(row['seconds'] for row in samples if row['route']==route)
            routes[route]={'n':len(values),'p50':values[max(0,math.ceil(len(values)*.5)-1)],
                'p95':values[max(0,math.ceil(len(values)*.95)-1)]}
        summary={'purpose':'local pilot functionality, not semantic release certification',
            'model':'llama3:willowbrook','temperature':.2,'context':8192,
            'generation_tokens':2048,'contract_json_characters':16384,'dialogue_characters':600,
            'models':[row for row in tags['models'] if row['name'] in {'llama3:latest','llama3:willowbrook'}],
            'routes':routes,'exact_retries':len(samples),'passed':True,
            'semantic_quality_percentages':'unmeasured; human scoring waived',
            'repair_latency':{'n':0,'p50':None,'p95':None}}
        (OUT/'live-route-summary.json').write_text(json.dumps(summary,indent=2))
        print('PASS enabled route, exact retries, isolated effects and real provider outage.',flush=True)
