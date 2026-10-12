"""Live configured provider through /chat, disposable in-memory world only.

PYTHONPATH=backend .venv/bin/python backend/tests/run_grounding_live.py --output docs/evidence/grounding-live.json
Never mocks generation or embeddings. Scoring checks selected facts and effects;
inspect saved actual answers as well as machine scores.
"""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config.settings import get_settings
from app.database.base import Base
from app.database.seed import seed_world
from app.database.session import get_db
from fastapi import FastAPI
from app.api.router import api_router

# Exclude production startup hooks: even schema/seed maintenance must never
# touch the saved world from this runner. Routes and dependencies are unchanged.
app = FastAPI()
app.include_router(api_router)
from app.models import Conversation, NPC


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--attempts', type=int, default=2)
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()
    settings = get_settings()
    if not settings.llm_base_url:
        raise SystemExit('No live model configured; refusing to report mock results as live.')
    cases = json.loads(Path(__file__).with_name('grounding_scenarios.json').read_text())
    if args.limit:
        cases = cases[:args.limit]
    result = dict(started_at=datetime.now(timezone.utc).isoformat(), model=settings.llm_model,
                  temperature=.2, structured_output=settings.llm_structured_output, provider='OpenAICompatibleProvider', attempts=args.attempts,
                  world='disposable in-memory SQLite', cases=[])
    implementation_files = [
        'app/services/prompts/builder.py', 'app/services/context/builder.py',
        'app/services/context/grounding.py', 'app/services/context/village.json',
        'app/services/validation/models.py', 'app/services/validation/service.py',
        'app/services/pipeline.py', 'app/services/llm/openai_compatible.py',
        'app/config/settings.py',
    ]
    result['implementation_sha256'] = {
        name: hashlib.sha256((Path(__file__).parents[1] / name).read_bytes()).hexdigest()
        for name in implementation_files
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(args.attempts):
        for npc_id in (1, 2):
            engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
            Base.metadata.create_all(engine)
            with Session(engine) as db, TestClient(app) as client:
                seed_world(db)
                app.dependency_overrides[get_db] = lambda: db
                for case in cases:
                    npc = db.get(NPC, npc_id)
                    before = [npc.trust, npc.fear, npc.aggression, npc.curiosity]
                    start = time.monotonic()
                    response = client.post('/chat', json={'npc_id': npc_id, 'player_message': case['message']})
                    data = response.json()
                    safe = (response.status_code == 200 and data['player_inventory'] == ['water', 'food']
                            and data['bow_quest']['phase'] == 'available'
                            and before == [data['npc'][f] for f in ('trust', 'fear', 'aggression', 'curiosity')])
                    selected = data.get('validated_output', {})
                    correct = (set(case.get('facts', [])) <= set(selected.get('fact_ids', []))
                               and (case.get('kind') is None or selected.get('answer_kind') == case['kind'])
                               and not data.get('grounding_trace', {}).get('rejected'))
                    if case.get('safe_only'):
                        correct = True
                    saved = db.scalar(select(Conversation).order_by(Conversation.id.desc()).limit(1))
                    record = dict(attempt=attempt + 1, npc_id=npc_id, message=case['message'],
                                  seconds=round(time.monotonic() - start, 3), passed=safe and correct,
                                  safe=safe, actual_answer=data.get('final_dialogue'),
                                  proposal=saved.llm_output if saved else None,
                                  trace=data.get('grounding_trace'))
                    result['cases'].append(record)
                    result['passed'] = sum(c['passed'] for c in result['cases'])
                    result['total'] = len(result['cases'])
                    output.write_text(json.dumps(result, indent=2) + '\n')
                    print(json.dumps({k: record[k] for k in ('attempt', 'npc_id', 'message', 'seconds', 'passed', 'actual_answer')}), flush=True)
                app.dependency_overrides.clear()
            engine.dispose()
    print(f"Passed {result['passed']}/{result['total']}; inspect {output}")


if __name__ == '__main__':
    main()
