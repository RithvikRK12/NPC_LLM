"""Replay the existing isolated PostgreSQL adoption runners; never uses game DB."""
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
scripts = [*ROOT.glob('docs/evidence/conversation-redesign-persistence-adapters/run_*_postgres_acceptance.py'),
    *ROOT.glob('docs/evidence/conversation-redesign-game-adapters/run_*_postgres_acceptance.py'),
    *ROOT.glob('docs/evidence/conversation-redesign-context/run_*_postgres_acceptance.py'),
    *ROOT.glob('docs/evidence/conversation-redesign-finalization/run_*_postgres_acceptance.py'),
    *ROOT.glob('docs/evidence/conversation-redesign-lifecycle/run_*_postgres_acceptance.py')]
results = []
for script in sorted(scripts):
    name = script.parent.name + '-' + script.stem
    with (OUT/(name+'.log')).open('w') as log:
        result = subprocess.run([sys.executable, str(script)], cwd=ROOT,
            stdout=log, stderr=subprocess.STDOUT, timeout=120)
    results.append(result.returncode)
    print(name, result.returncode, flush=True)
sys.exit(0 if all(code==0 for code in results) else 1)
