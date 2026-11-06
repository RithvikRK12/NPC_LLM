import json, os, subprocess, sys
from pathlib import Path
root=Path.cwd(); dest=root/'docs/evidence/conversation-redesign-context/t04';dest.mkdir(exist_ok=True)
label=sys.argv[1];args=sys.argv[2:]
env=os.environ.copy();env['PYTHONPATH']='backend:backend/tests'
result=subprocess.run(args,env=env,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(dest/f'{label}.log').write_text(result.stdout)
manifest=dest/'checks.json'; entries=json.loads(manifest.read_text()) if manifest.exists() else []
entries.append({'label':label,'cwd':str(root),'command':args,'env':{'PYTHONPATH':env['PYTHONPATH'],'CONVERSATION_TEST_DATABASE_URL':'isolated npc_test_* database' if env.get('CONVERSATION_TEST_DATABASE_URL') else 'unset; isolated SQLite fixtures'},'exit_code':result.returncode,'log':f'{label}.log'})
manifest.write_text(json.dumps(entries,indent=2)+'\n');print(result.stdout[-7000:]);print('EXIT',result.returncode)
sys.exit(result.returncode)
