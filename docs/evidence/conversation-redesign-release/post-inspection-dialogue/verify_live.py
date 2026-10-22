"""Live dialogue and repair on an isolated SQLite backup of the reported save."""
import json,os,sqlite3,tempfile,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='npc-inspected-dialogue-') as directory:
    target=Path(directory)/'world.db'
    with sqlite3.connect('file:'+str(ROOT/'backend/mvp.db')+'?mode=ro',uri=True) as source, sqlite3.connect(target) as destination:
        source.backup(destination)
    os.environ['DATABASE_URL']='sqlite:///'+str(target)
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.services.conversation import contracts as c
    samples=[]
    with TestClient(create_app()) as client:
        world=client.get('/world').json()
        assert world['craftsman_encounter']['inspection_complete'], 'Reported save must have completed inspection'
        scope=world['game_scope'];epoch=world['conversation_epochs']['1']
        for message in ('Thanks for looking at my ship!', 'Thanks for looking at my ship.',
                        'Thank you for your help.', 'Thanks for inspecting the damage.',
                        'Thank you so much.', 'Thanks for taking the time to help me.'):
            payload={'schema_version':1,'request_id':'verify:'+uuid.uuid4().hex,'game_scope':scope,
                'conversation_epoch':epoch,'npc_id':1,'player_message':message}
            start=time.monotonic(); response=client.post('/chat',json=payload)
            while response.status_code==202 and time.monotonic()-start<185:
                time.sleep(.1); response=client.get(response.json()['status_url'])
            assert response.status_code==200,response.text
            result=response.json();text=result['final_dialogue']
            row={'message':message,'dialogue':text,'origin':result['response_origin'],
                'degradation_reason':result['degradation_reason'],'seconds':round(time.monotonic()-start,3)}
            samples.append(row);print(json.dumps(row),flush=True)
            (OUT/'live-results.json').write_text(json.dumps(samples,indent=2)+'\n')
            assert result['response_origin']!='fallback',row
            assert not result['receipt_refs'],row
            assert not any(term in text.lower() for term in ('my ship','if you\'d like','i agreed to inspect','take a look at the damage','everything is in order','project come together','ship is seaworthy')),row
            state=result['craftsman_encounter']
            assert state['inspection_complete'] and not state['outing_active'],row
        # Force one observed class of invalid first draft; correction uses real Llama.
        ports=client.app.state.conversation_runtime.coordinator._ports
        delegate=ports._proposal._generation
        class BadFirstDraft:
            def generate(self,purpose,context,deadline,dialogue_codepoint_limit):
                return c.TurnProposal(concerns=(),references=(),reports=(),correction_candidates=(),
                    operation_candidates=(),interaction_links=(),canon_candidates=(),reply=(
                        c.ExpressiveSegment(kind='expressive',segment_id='bad:perspective',
                            text="Thanks for looking at my ship! I can take a look at the damage with you.",
                            addressed_concern_ids=()),))
        ports._proposal._generation=BadFirstDraft()
        payload={**payload,'request_id':'repair:'+uuid.uuid4().hex,'player_message':'Thanks for looking at my ship!'}
        start=time.monotonic();response=client.post('/chat',json=payload)
        while response.status_code==202 and time.monotonic()-start<185:
            time.sleep(.1);response=client.get(response.json()['status_url'])
        assert response.status_code==200,response.text
        result=response.json(); row={'forced_invalid_draft':True,'dialogue':result['final_dialogue'],
            'origin':result['response_origin'],'degradation_reason':result['degradation_reason'],
            'seconds':round(time.monotonic()-start,3)}
        samples.append(row);print(json.dumps(row),flush=True)
        (OUT/'live-results.json').write_text(json.dumps(samples,indent=2)+'\n')
        assert result['response_origin']=='repaired',row
        assert 'my ship' not in result['final_dialogue'].lower(),row
        assert not result['receipt_refs'],row
    print('PASS six generated gratitude variants and real Llama repair on disposable save',flush=True)
