"""D1 real-provider evidence on a disposable file-backed world; no mocks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.config.settings import get_settings
from app.database.base import Base
from app.database.seed import seed_world, reset_world
from app.database.session import get_db
from app.models import NPC, Player, Memory, Conversation
from app.schemas.memory import MemoryRead
from app.services.context.builder import ContextBuilder
from app.services.memory.service import MemoryService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error('Evidence exists; use a new output file.')
    settings = get_settings()
    if not settings.llm_base_url:
        parser.error('Configured real generation is required.')
    result = dict(started_at=datetime.now(timezone.utc).isoformat(), model=settings.llm_model,
                  embedding_model=settings.embedding_model, temperature=.2,
                  structured_output=settings.llm_structured_output, world='disposable file-backed SQLite',
                  chats=[], checks=[])
    files = sorted((Path(__file__).parents[1] / 'app').rglob('*.py'))
    result['implementation_sha256'] = {str(p.relative_to(Path(__file__).parents[1])): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        result['passed'] = sum(c['passed'] for c in result['checks'])
        result['total'] = len(result['checks'])
        output.write_text(json.dumps(result, indent=2) + '\n')
    def check(label, passed, details=None):
        result['checks'].append(dict(label=label, passed=bool(passed), details=details))
        save()
        print(('PASS ' if passed else 'FAIL ') + label, flush=True)
    with TemporaryDirectory(prefix='npc-memory-provenance-') as temporary:
        engine = create_engine('sqlite:///' + str(Path(temporary) / 'world.db'), connect_args={'check_same_thread': False})
        Base.metadata.create_all(engine)
        app = FastAPI()
        app.include_router(api_router)  # never execute production saved-world startup
        def session():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[get_db] = session
        with Session(engine) as db:
            seed_world(db)
        with TestClient(app) as client:
            for attempt in (1, 2):
                for npc_id, item in ((1, 'rope'), (2, 'fruits')):
                    with Session(engine) as db:
                        reset_world(db)
                        db.commit()
                    prefix = f'attempt {attempt}, NPC {npc_id}: '
                    def chat(message):
                        started = time.monotonic()
                        response = client.post('/chat', json=dict(npc_id=npc_id, player_message=message))
                        data = response.json()
                        with Session(engine) as db:
                            source = db.scalar(select(Conversation).order_by(Conversation.id.desc()))
                            proposal = source.llm_output if source else None
                        result['chats'].append(dict(attempt=attempt, npc_id=npc_id, message=message,
                            seconds=round(time.monotonic()-started, 3), response=data, proposal=proposal))
                        check(prefix + 'accepted ' + message, response.status_code == 200 and not data.get('grounding_trace', {}).get('rejected', True))
                        return data
                    hello = chat('Hello' if attempt == 1 else 'Good morning')
                    check(prefix + 'routine greeting excluded', not hello.get('memory_classification', {}).get('important'))
                    claim = chat('I gave you wood')
                    check(prefix + 'claim cannot establish delivery',
                          all(claim.get(k) == hello.get(k) for k in ('player_inventory', 'bow_quest'))
                          and claim.get('npc', {}).get('inventory') == hello.get('npc', {}).get('inventory'))
                    first = chat('I prefer quiet forests')
                    second = chat('I prefer quiet forests')
                    correction = chat('I no longer prefer quiet forests')
                    request = chat(f'Can I have {item}?')
                    transfer = chat('For my work in the village')
                    check(prefix + 'authoritative transfer executed once', transfer.get('player_inventory', []).count(item) == 1)
                    ids = [d.get('memory_classification', {}).get('memory_id') for d in (claim, first, second, correction, transfer)]
                    with Session(engine) as db:
                        rows = [db.get(Memory, identity) if identity else None for identity in ids]
                        claimed, original, repeated, retraction, verified = rows
                        check(prefix + 'delivery statement is reported claim', claimed and claimed.epistemic_status == 'claim' and claimed.authority == 'reported')
                        check(prefix + 'repeated preference consolidates', original and repeated and original.id == repeated.id and not second.get('memory_classification', {}).get('stored'))
                        check(prefix + 'correction preserves and links original history', original and retraction and original.lifecycle == 'retracted'
                              and original.superseded_by_id == retraction.id and retraction.correction_of_id == original.id and retraction.epistemic_status == 'retraction')
                        check(prefix + 'transfer fact excludes unverified explanation', verified and verified.epistemic_status == 'fact' and verified.authority == 'authoritative' and 'Player explanation' not in verified.event)
                        scope = db.get(Player, 1).game_scope
                        check(prefix + 'all memories have matching source, recipient and run', all(row and row.npc_id == npc_id and row.game_scope == scope
                              and row.source_event_id == db.get(Conversation, row.source_conversation_id).source_event_id for row in rows))
                        context = ContextBuilder(db).build(db.get(NPC, npc_id), db.get(Player, 1), 'quiet forest preferences and supplies')
                        active_ids = {m['id'] for m in context.memories}
                        check(prefix + 'retracted claim excluded from live context', original and original.id not in active_ids)
                        check(prefix + 'real scoped vectors stored', all(row and len(row.semantic_embedding or []) == settings.embedding_dimensions for row in rows))
                        result.setdefault('snapshots', []).append(dict(attempt=attempt, npc_id=npc_id,
                            memories=[MemoryRead.model_validate(m).model_dump(mode='json') for m in db.scalars(select(Memory).order_by(Memory.id))],
                            context_memories=context.memories))
                        if verified:
                            source = db.get(Conversation, verified.source_conversation_id)
                            source_ref = SimpleNamespace(id=source.id, source_event_id=source.source_event_id)
                            count = len(list(db.scalars(select(Memory))))
                        else:
                            source_ref, count = None, 0
                    # Reopened session uses persisted identities, not in-process receipts.
                    with Session(engine) as db:
                        seed_world(db)
                        service = MemoryService(db)
                        if source_ref:
                            write = service.store_conversation(db.get(NPC, npc_id), source_ref)
                            check(prefix + 'reprocessing after reopen creates no duplicate', not write.created and len(list(db.scalars(select(Memory)))) == count)
                            try:
                                service.store_conversation(db.get(NPC, 3-npc_id), source_ref)
                                refused = False
                            except ValueError:
                                refused = True
                            check(prefix + 'other recipient cannot consume source', refused)
                        reset_world(db)
                        db.commit()
                        if source_ref:
                            try:
                                service.store_conversation(db.get(NPC, npc_id), source_ref)
                                refused = False
                            except ValueError:
                                refused = True
                            check(prefix + 'old source rejected after reset', refused and db.get(Player, 1).game_scope != scope)
                        check(prefix + 'reset leaves no active old memory', list(db.scalars(select(Memory))) == [])
                    save()
        engine.dispose()
    print(f"Passed {result['passed']}/{result['total']}; evidence: {output}")
    return 0 if result['passed'] == result['total'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
