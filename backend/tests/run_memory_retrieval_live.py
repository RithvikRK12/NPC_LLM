"""D2 real embedding transport outage/recovery; disposable SQLite, no generation.

Run with PYTHONPATH=backend .venv/bin/python backend/tests/run_memory_retrieval_live.py
--output docs/evidence/NEW.json. Never connects to the gameplay server.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.routes.memory import router
from app.config.settings import get_settings
from app.database.base import Base
from app.database.seed import seed_world
from app.database.session import get_db
from app.models import Conversation, Memory, NPC, Player
from app.services.context.builder import ContextBuilder
from app.services.memory.embedding import EmbeddingService, EmbeddingUnavailable
from app.services.memory.reindex import reindex_memories
from app.services.memory.service import MemoryService
from app.services.validation.models import LLMResponse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error('Use a new evidence filename; existing evidence is preserved.')
    settings = get_settings()
    result = {'started_at': datetime.now(timezone.utc).isoformat(),
              'embedding_model': settings.embedding_model, 'dimensions': settings.embedding_dimensions,
              'embedding_revision': settings.embedding_revision,
              'world': 'temporary file-backed SQLite; deleted after run',
              'generation': 'not exercised; accepted conversation fixtures are explicitly synthetic',
              'checks': [], 'retrievals': []}
    root = Path(__file__).parents[1]
    result['implementation_sha256'] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sorted((root / 'app').rglob('*.py'))}
    def save():
        result.update(passed=sum(c['passed'] for c in result['checks']), total=len(result['checks']))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + '\n')
    def check(label, passed):
        result['checks'].append({'label': label, 'passed': bool(passed)})
        print(('PASS ' if passed else 'FAIL ') + label, flush=True)
        save()
    try:
        # Reserve a loopback port without listening: real TCP connections are refused.
        # Keep it bound throughout the outage so no unrelated service can occupy it.
        with socket.socket() as unavailable, TemporaryDirectory(prefix='npc-d2-') as temporary:
            unavailable.bind(('127.0.0.1', 0))
            outage_url = f'http://127.0.0.1:{unavailable.getsockname()[1]}'
            result['outage_endpoint'] = outage_url
            engine = create_engine('sqlite:///' + str(Path(temporary) / 'world.db'),
                                   connect_args={'check_same_thread': False})
            Base.metadata.create_all(engine)
            def outage_embedder():
                embedder = EmbeddingService()
                embedder.settings = settings.model_copy(update={'embedding_base_url': outage_url,
                                                                 'embedding_timeout_seconds': 1.})
                return embedder
            with Session(engine) as db:
                seed_world(db)
                npc, player = db.get(NPC, 1), db.get(Player, 1)
                service = MemoryService(db)
                inventory_before = (list(npc.inventory), list(player.inventory))
                output_fixture = LLMResponse(intent='chat', emotion='neutral', dialogue='Thanks for telling me.',
                    action='speak', reasoning='Accepted fixture for retrieval only.', state_update={}).model_dump()
                def source(message, npc_id=1):
                    row = Conversation(npc_id=npc_id, game_scope=player.game_scope, source_event_id=str(uuid4()),
                        player_input=message, final_dialogue='Thanks for telling me.',
                        llm_output=output_fixture, validated_output=output_fixture | {'grounding_trace': {'rejected': False}})
                    db.add(row)
                    db.flush()
                    return row
                indexed = service.store_conversation(npc, source('I prefer quiet forests')).memory
                db.commit()
                check('real indexed memory has configured vector', indexed is not None and
                      len(indexed.semantic_embedding or []) == settings.embedding_dimensions)
                def retrieve(label, query, **kwargs):
                    started = time.monotonic()
                    rows = service.retrieve_relevant_memories(npc, query, **kwargs)
                    result['retrievals'].append({'label': label, 'seconds': round(time.monotonic()-started, 4),
                        'trace': dict(service.last_retrieval_trace), 'memories': [m.to_payload() for m in rows]})
                    save()
                    return rows
                normal = retrieve('normal paraphrase', 'I enjoy peaceful woodland')
                check('normal semantic retrieval uses real provider', any(m.id == indexed.id and m.retrieval_mode == 'semantic' for m in normal))
                service._embedder = outage_embedder()
                try:
                    service._embedder.embed('transport outage probe', query=True)
                    transport_failed = False
                except EmbeddingUnavailable as exc:
                    transport_failed = True
                    result['actual_transport_error'] = str(exc)
                check('isolated endpoint produces actual embedding transport failure', transport_failed)
                outage = retrieve('query outage with existing vector', 'quiet forests')
                check('query outage retrieves existing memory lexically', outage and outage[0].id == indexed.id
                      and outage[0].retrieval_mode == 'lexical' and service.last_retrieval_trace['reason'] == 'query_embedding_unavailable')
                vectorless = service.store_conversation(npc, source('I prefer calm rivers')).memory
                other = service.store_conversation(db.get(NPC, 2), source('I prefer calm rivers', 2)).memory
                db.commit()
                check('outage write has no fake vector or model', vectorless is not None and
                      vectorless.semantic_embedding is None and vectorless.embedding_model is None)
                rows = retrieve('query outage including vectorless write', 'calm rivers')
                check('vectorless write retrievable during outage', rows and rows[0].id == vectorless.id)
                check('recipient isolation during outage', other.id not in {m.id for m in rows})
                check('provenance and reported claim preserved', rows[0].source_conversation_id == vectorless.source_conversation_id
                      and rows[0].source_event_id == vectorless.source_event_id and rows[0].epistemic_status == 'claim')
                ids = [m.id for m in rows]
                again = retrieve('repeat outage', 'calm rivers')
                check('repeat outage deterministic', ids == [m.id for m in again])
                empty = retrieve('empty filtered outage', 'calm rivers', quest_id='not-authored')
                check('empty result has selected-ID trace', not empty and service.last_retrieval_trace['selected_ids'] == [])
                context = ContextBuilder(db, memory_service=service).build(npc, player, 'What have I delivered?')
                check('current authoritative delivery state remains supplied', any(f['id'] == 'quest.bow.delivered'
                      and 'no materials recorded' in f['text'] for f in context.facts))
                check('context captures outage diagnostics', context.memory_retrieval['mode'] == 'lexical')
                service._embedder = EmbeddingService()  # restore endpoint, no settings mutation
                mixed = retrieve('endpoint restored before explicit reindex', 'calm rivers')
                check('healthy path includes vectorless memory with honest lexical score', any(
                    m.id == vectorless.id and m.to_payload()['score_kind'] == 'lexical_importance_recency' for m in mixed)
                    and service.last_retrieval_trace['mode'] == 'mixed')
                repaired = reindex_memories(db, embedder=service._embedder)
                check('explicit real reindex repairs only disposable vectorless data', repaired == 2)
                recovered = retrieve('semantic recovery after explicit reindex', 'calm rivers')
                check('semantic recovery with real configured vectors', service.last_retrieval_trace['mode'] == 'semantic'
                      and any(m.id == vectorless.id and m.retrieval_mode == 'semantic' for m in recovered)
                      and len(db.get(Memory, vectorless.id).semantic_embedding or []) == settings.embedding_dimensions)
                check('retrieval creates no inventory effects', inventory_before == (list(npc.inventory), list(player.inventory)))
                vectorless.lifecycle = 'retracted'
                indexed.game_scope = 'historical-run'
                db.commit()
                service._embedder = outage_embedder()
                isolated = retrieve('outage lifecycle and run exclusion', 'quiet forests calm rivers')
                check('old-run retracted and other recipient excluded', not isolated)
            app = FastAPI()
            app.include_router(router)
            def session():
                with Session(engine) as db:
                    yield db
            app.dependency_overrides[get_db] = session
            with TestClient(app) as client:
                payload = client.get('/memory/2/search', params={'query': 'calm rivers'}).json()
                check('production search response remains a list', isinstance(payload, list) and len(payload) == 1
                      and payload[0]['retrieval_mode'] == 'semantic')
            engine.dispose()
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
        check('live run completed without error', False)
        raise
    finally:
        result['finished_at'] = datetime.now(timezone.utc).isoformat()
        save()
    print(f"{result['passed']}/{result['total']} checks passed", flush=True)
    return 0 if result['passed'] == result['total'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
