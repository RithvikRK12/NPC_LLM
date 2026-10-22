"""Verify ordinary Settings/.env startup against a disposable database."""
import os,tempfile,time,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='npc-chat-startup-') as temporary:
    os.environ['DATABASE_URL']='sqlite:///'+str(Path(temporary)/'world.db')
    from fastapi.testclient import TestClient
    from app.main import create_app
    with TestClient(create_app()) as client:
        assert client.app.state.conversation_enabled
        assert client.app.state.conversation_runtime is not None
        world=client.get('/world').json()
        arrival=client.post('/world/opening/complete',json={'game_scope':world['game_scope'],'opening_version':world['opening_version']})
        assert arrival.status_code==200,arrival.text
        payload={'schema_version':1,'request_id':'startup:hello','game_scope':world['game_scope'],
            'conversation_epoch':world['conversation_epochs']['1'],'npc_id':1,'player_message':'hello'}
        start=time.monotonic(); response=client.post('/chat',json=payload)
        while response.status_code==202 and time.monotonic()-start<185:
            time.sleep(.1); response=client.get(response.json()['status_url'])
        assert response.status_code==200,response.text
        result=response.json()
        assert result['final_dialogue'].strip()
        replay=client.post('/chat',json=payload)
        assert replay.status_code==200 and replay.json()==result
        evidence={'status':response.status_code,'seconds':round(time.monotonic()-start,3),
            'dialogue':result['final_dialogue'],'origin':result['response_origin'],
            'degradation_reason':result['degradation_reason'],'exact_replay':True,
            'configuration':'ordinary Settings reads backend/.env; no exported playtest profile'}
        (OUT/'live-result.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(evidence),flush=True)
