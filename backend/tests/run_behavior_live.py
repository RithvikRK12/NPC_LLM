"""Real configured providers, production routes, disposable SQLite only.

Controlled NPC states demonstrate policy behavior, not playable recovery content.
"""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.config.settings import get_settings
from app.database.base import Base
from app.database.seed import seed_world, reset_world
from app.database.session import get_db
from app.models import NPC, Conversation, Memory
from app.services.memory.service import MemoryService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--attempts', type=int, default=2)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error('Evidence already exists; choose a new output file.')
    if args.attempts < 1:
        parser.error('attempts must be positive')
    settings = get_settings()
    if not settings.llm_base_url:
        parser.error('No live provider configured; mocks are forbidden.')
    result = dict(started_at=datetime.now(timezone.utc).isoformat(), model=settings.llm_model,
                  temperature=.2, structured_output=settings.llm_structured_output,
                  embedding_model=settings.embedding_model, attempts=args.attempts,
                  world='disposable file-backed SQLite; controlled NPC state fixtures', cases=[], memory_checks=[])
    names = ['services/pipeline.py', 'services/rule_engine/behavior.py',
             'services/rule_engine/behavior_policy.json', 'services/validation/service.py',
             'services/state/locking.py', 'database/seed.py', 'domain/fuzzy/membership.py',
             'services/prompts/builder.py', 'services/memory/embedding.py', 'services/memory/service.py',
             'services/llm/openai_compatible.py']
    result['implementation_sha256'] = {name: hashlib.sha256(
        (Path(__file__).parents[1] / 'app' / name).read_bytes()).hexdigest() for name in names}
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='npc-behavior-') as temporary:
        engine = create_engine('sqlite:///' + str(Path(temporary) / 'world.db'),
                               connect_args={'check_same_thread': False})
        Base.metadata.create_all(engine)
        app = FastAPI()
        app.include_router(api_router)  # omit production startup, preserve saved world
        def session():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[get_db] = session
        with Session(engine) as db:
            seed_world(db)
        with TestClient(app) as client:
            for attempt in range(args.attempts):
                for npc_id, item in ((1, 'rope'), (2, 'fruits')):
                    for label, trust, fear, expected in (
                        ('helpful', .95, .05, 'cooperate'),
                        ('cautious', .65, .6, 'clarify'),
                        ('distrustful', .05, .8, 'refuse'),
                    ):
                        with Session(engine) as db:
                            reset_world(db)
                            npc = db.get(NPC, npc_id)
                            npc.trust, npc.fear, npc.aggression, npc.curiosity = trust, fear, .05, .3
                            db.commit()
                        cases = [('Hello' if attempt == 0 else 'Good morning', 'answer'),
                                 ('Where is the Gatherer?' if attempt == 0 else 'Where can I find the Gatherer?', 'answer'),
                                 (f'Can I have {item}?' if attempt == 0 else f'Please give me {item}', expected)]
                        if label != 'distrustful':
                            cases.append(('For my work in the village', 'cooperate'))
                        for message, selection in cases:
                            started = time.monotonic()
                            response = client.post('/chat', json=dict(npc_id=npc_id, player_message=message))
                            data = response.json()
                            trace = data.get('behavior_trace', {})
                            transferred = message == 'For my work in the village'
                            safe = (response.status_code == 200 and data['bow_quest']['phase'] == 'available'
                                    and data['player_inventory'].count(item) == int(transferred)
                                    and data['npc']['inventory'].count(item) == int(not transferred)
                                    and all(data['npc'][k] == v for k, v in
                                            dict(trust=trust, fear=fear, aggression=.05, curiosity=.3).items()))
                            passed = (safe and trace.get('selection') == selection
                                      and not data.get('grounding_trace', {}).get('rejected'))
                            if 'Gatherer' in message:
                                passed = passed and data.get('validated_output', {}).get('fact_ids') == ['person.gatherer.location']
                            with Session(engine) as db:
                                saved = db.scalar(select(Conversation).order_by(Conversation.id.desc()))
                                raw = saved.llm_output if saved else None
                            record = dict(attempt=attempt + 1, npc_id=npc_id, state=label, message=message,
                                          seconds=round(time.monotonic() - started, 3), passed=bool(passed),
                                          safe=bool(safe), dialogue=data.get('final_dialogue'), proposal=raw,
                                          grounding_trace=data.get('grounding_trace'), behavior_trace=trace)
                            result['cases'].append(record)
                            result['passed'] = sum(c['passed'] for c in result['cases'])
                            result['total'] = len(result['cases'])
                            output.write_text(json.dumps(result, indent=2) + '\n')
                            print(json.dumps({k: record[k] for k in ('npc_id', 'state', 'message', 'passed', 'dialogue')}), flush=True)
                        if label != 'distrustful':
                            with Session(engine) as db:
                                rows = list(db.scalars(select(Memory).where(Memory.npc_id == npc_id)))
                                stored = [dict(id=m.id, npc_id=m.npc_id, event_type=m.event_type,
                                               embedding_model=m.embedding_model,
                                               dimensions=len(m.semantic_embedding or []),
                                               norm=math.sqrt(sum(v * v for v in (m.semantic_embedding or [])))) for m in rows]
                                retrieved = MemoryService(db).retrieve_relevant_memories(
                                    db.get(NPC, npc_id), 'The villager handed over supplies after I explained my purpose.')
                                transfer_ids = {m.id for m in rows if m.event_type == 'item_transfer'}
                                vectors_ok = bool(stored) and all(m['dimensions'] == settings.embedding_dimensions
                                                                 and abs(m['norm'] - 1.) < .0001 for m in stored)
                                retrieval_ok = bool(transfer_ids & {m.id for m in retrieved}) and all(m.npc_id == npc_id for m in retrieved)
                                result['memory_checks'].append(dict(attempt=attempt + 1, npc_id=npc_id, state=label,
                                    stored=stored, retrieved_ids=[m.id for m in retrieved],
                                    vectors_ok=vectors_ok, retrieval_ok=retrieval_ok, passed=vectors_ok and retrieval_ok))
                                result['memory_passed'] = sum(m['passed'] for m in result['memory_checks'])
                                result['memory_total'] = len(result['memory_checks'])
                                output.write_text(json.dumps(result, indent=2) + '\n')
        engine.dispose()
    print(f"Passed {result['passed']}/{result['total']}; evidence: {output}")
    return 0 if result['passed'] == result['total'] and result.get('memory_passed') == result.get('memory_total') else 1


if __name__ == '__main__':
    raise SystemExit(main())
