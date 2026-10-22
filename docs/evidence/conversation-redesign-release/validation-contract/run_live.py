"""Real provider, fresh isolated worlds; never changes the personal save."""
import json,os,tempfile,time,re
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
for key,value in dotenv_values(ROOT/'config/playtest.env').items():
    if value is not None:os.environ[key]=value
with tempfile.TemporaryDirectory(prefix='npc-validation-contract-') as temporary:
    os.environ['DATABASE_URL']='sqlite:///'+str(Path(temporary)/'world.db')
    from fastapi.testclient import TestClient
    from app.main import create_app
    samples=[];calls=[]
    with TestClient(create_app()) as client:
        # Capture timings/token usage at the actual production transport boundary.
        adapter=client.app.state.conversation_runtime.coordinator._ports._generation
        delegate=adapter._transport
        class RecordingTransport:
            def post(self,url,**kwargs):
                started=time.monotonic();response=delegate.post(url,**kwargs)
                calls.append({'seconds':round(time.monotonic()-started,4),
                    'prompt_characters':len(kwargs['json']['messages'][0]['content']),
                    'usage':response.json().get('usage',{}), 'output': response.json()['choices'][0]['message']['content']})
                return response
        adapter._transport=RecordingTransport()
        for npc,text in [(1,"my ship just wrecked and i'm stranded!")]:
            scope=client.get('/world').json()['game_scope']
            reset=client.post('/world/new-game',json={'expected_scope':scope})
            assert reset.status_code==200,reset.text
            world=client.get('/world').json()
            arrived=client.post('/world/opening/complete',json={'game_scope':world['game_scope'],'opening_version':world['opening_version']})
            assert arrived.status_code==200,arrived.text
            payload={'schema_version':1,'request_id':'greeting:'+str(len(samples)),
                'game_scope':world['game_scope'],'conversation_epoch':world['conversation_epochs'][str(npc)],
                'npc_id':npc,'player_message':text}
            start=time.monotonic();before=len(calls);r=client.post('/chat',json=payload)
            while r.status_code==202 and time.monotonic()-start<185:
                time.sleep(.05);r=client.get(r.json()['status_url'])
            assert r.status_code==200,r.text
            result=r.json()
            row={'npc':npc,'message':text,'seconds':round(time.monotonic()-start,4),
                'dialogue':result['final_dialogue'],'origin':result['response_origin'],
                'degradation_reason':result['degradation_reason'],'provider_calls':calls[before:]}
            samples.append(row);print(row,flush=True)
            (OUT/'live-samples.json').write_text(json.dumps(samples,indent=2))
            assert 'recorded' not in result['final_dialogue'].lower(),row
            assert "glad you made it ashore" in result['final_dialogue'],row
            assert "if you'd like" in result['final_dialogue'],row
            assert result['response_origin']=='generated',row
            assert result['degradation_reason'] is None,row
            assert len(result['receipt_refs'])==1
            encounter=client.get('/world').json()['craftsman_encounter']
            assert encounter['wreck_reported'] and encounter['offer_pending']
            assert not encounter['outing_active'] and not encounter['inspection_complete']
            retry=client.post('/chat',json=payload)
            assert retry.status_code==200 and retry.json()==result
            assert client.get('/world').json()['player_inventory']==world['player_inventory']
    print('PASS exact stranded report is GENERATED, one receipt, no automatic inspection, exact retry.',flush=True)
