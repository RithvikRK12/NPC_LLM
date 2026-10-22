import os, sys, socket, subprocess, tempfile, time, json, shutil
from pathlib import Path
from urllib.request import urlopen, Request
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parents[4]; OUT=Path(__file__).resolve().parent
GODOT=os.environ.get('GODOT_BIN') or '/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot'
env=os.environ.copy(); env.update({k:v for k,v in dotenv_values(ROOT/'config/playtest.env').items() if v is not None}); env['PYTHONPATH']=str(ROOT/'backend')
with tempfile.TemporaryDirectory(prefix='npc-release-') as temp:
    work=Path(temp); env['DATABASE_URL']='sqlite:///'+str(work/'world.db')
    project=work/'frontend/godot'; shutil.copytree(ROOT/'frontend/godot',project)
    shutil.copytree(ROOT/'backend/tests/fixtures', work/'backend/tests/fixtures')
    shutil.copytree(ROOT/'contracts',work/'contracts')
    p=project/'project.godot'; p.write_text(p.read_text().replace('config/name="Closed Loop NPC MVP"','config/name="NPC Release Verification '+work.name+'"'))
    with socket.socket() as listener, (OUT/'backend-live.log').open('w') as log:
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        listener.bind(('127.0.0.1',8001)); listener.listen(128)
        server=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--fd',str(listener.fileno())],env=env,pass_fds=(listener.fileno(),),stdout=log,stderr=subprocess.STDOUT)
        results=json.loads((OUT/'godot-summary.json').read_text()) if sys.argv[1:] and (OUT/'godot-summary.json').exists() else []
        results=[result for result in results if result['test'] not in sys.argv[1:]]
        try:
            for _ in range(100):
                try:
                    if urlopen('http://127.0.0.1:8001/health',timeout=.5).status==200: break
                except OSError: time.sleep(.1)
            else: raise RuntimeError('backend startup failed')
            for name in (sys.argv[1:] or ['conversation_signal_smoke','gatherer_navigation_smoke','conversation_gateway_smoke','conversation_presenter_smoke','revisioned_state_smoke','gateway_contract_codec_smoke','contract_fixture_smoke','ui_rework_smoke','bow_quest_smoke','building_interiors_smoke','persistence_smoke','craftsman_integration_smoke','gatherer_integration_smoke']):
                # Each test gets a clean disposable world and a distinct gateway cache.
                with urlopen('http://127.0.0.1:8001/world') as response:
                    scope=json.load(response)['game_scope']
                reset=Request('http://127.0.0.1:8001/world/new-game',data=json.dumps({'expected_scope':scope}).encode(),headers={'Content-Type':'application/json'})
                with urlopen(reset) as response: response.read()
                p.write_text((ROOT/'frontend/godot/project.godot').read_text().replace('config/name="Closed Loop NPC MVP"', 'config/name='+json.dumps('NPC Release Verification '+name+' '+work.name)))
                started=time.monotonic()
                with (OUT/(name+'.log')).open('w') as gdlog:
                    try:
                        run=subprocess.run([GODOT,'--headless','--path',str(project),'--script','res://tests/'+name+'.gd'],stdout=gdlog,stderr=subprocess.STDOUT,timeout=300)
                        code=run.returncode
                    except subprocess.TimeoutExpired: code=124
                import sqlite3
                with sqlite3.connect(work/'world.db') as database:
                    turns=[json.loads(row[0]) for row in database.execute('SELECT payload FROM conversation_turns WHERE phase="finalized" ORDER BY npc_id,sequence')]
                (OUT/(name+'-turns.json')).write_text(json.dumps(turns,indent=2))
                content=(OUT/(name+'.log')).read_text()
                shutdown_warning='resources still in use at exit' in content
                errors=('SCRIPT ERROR:' in content or '\nFAIL ' in content or any(line.startswith('ERROR:') and 'resources still in use at exit' not in line for line in content.splitlines()))
                result=dict(test=name,exit_code=code,seconds=round(time.monotonic()-started,3),passed=code==0 and not errors,shutdown_resource_warning=shutdown_warning)
                results.append(result); print(result,flush=True)
                (OUT/'godot-summary.json').write_text(json.dumps(results,indent=2))
        finally:
            server.terminate()
            try: server.wait(timeout=10)
            except subprocess.TimeoutExpired: server.kill(); server.wait()

if not all(result['passed'] for result in results): sys.exit(1)
