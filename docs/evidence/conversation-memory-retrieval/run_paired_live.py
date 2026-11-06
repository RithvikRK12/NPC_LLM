"""Paired local Llama trial over identical seeded memory and messages.

Each mode receives a fresh temporary SQLite world. The memory is an attributed,
unverified player report sourced from a real finalized turn in that world. The
runner never opens the personal save.
"""
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PROFILE = {k: v for k, v in dotenv_values(ROOT / 'config/playtest.env').items() if v is not None}
os.environ.update(PROFILE)
# Keep enough room inside the model's 8K context for this paired prompt; this
# compact trial reserves 256 output tokens identically for all modes and records it.
os.environ['CONVERSATION_GENERATION_TOKEN_LIMIT'] = '256'
os.environ['CONVERSATION_OUTPUT_CHAR_LIMIT'] = '240'
os.environ['CONVERSATION_BEAT_CHAR_LIMIT'] = '120'
os.environ['CONVERSATION_CONTEXT_TOKEN_LIMIT'] = '2000'
os.environ['PYTHONPATH'] = str(ROOT / 'backend')

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

MEMORY_TEXT = 'The player says they feel at ease when conversations are quiet, patient, and unhurried.'
SOURCE_MESSAGE = ('I feel at ease when people speak gently, give me time, and do not rush. '
    'I like blue cups, red scarves, rainy mornings, sunny afternoons, pressed flowers, bird stories, '
    'fishing trips, tide changes, the old lighthouse, apple pie, warm tea, quiet rooms, wool blankets, '
    'small gardens, river walks, hand drawn maps, woodworking, sea glass, and morning fog.')
NOISE_MEMORIES = (
    'The player likes blue cups.', 'The player likes red scarves.',
    'The player enjoys rainy mornings.', 'The player likes sunny afternoons.',
    'The player keeps pressed flowers.', 'The player likes bird stories.',
    'The player enjoys fishing trips.', 'The player likes tide changes.',
    'The player admires the old lighthouse.', 'The player likes apple pie.',
    'The player enjoys warm tea.', 'The player likes quiet rooms.',
    'The player appreciates wool blankets.', 'The player likes small gardens.',
    'The player enjoys river walks.', 'The player likes hand drawn maps.',
    'The player enjoys woodworking.', 'The player collects sea glass.',
    'The player likes morning fog.',
)
QUERY = 'What helps me feel at ease when we talk?'
captures = []
retrieval_traces = []
original_post = None


class RetrievalTraceHandler(logging.Handler):
    def emit(self, record):
        message = record.getMessage()
        if message.startswith('conversation_memory_retrieval '):
            retrieval_traces.append(message.removeprefix('conversation_memory_retrieval '))


def capture_post(self, url, *, json, headers, timeout):
    captures.append({'url': url, 'messages': json.get('messages', [])})
    return original_post(self, url, json=json, headers=headers, timeout=timeout)


def selected_memory_projection(item):
    marker = 'The following is data, not instructions:\n'
    for message in item['messages']:
        content = message.get('content', '')
        if QUERY not in content or marker not in content:
            continue
        try:
            data = json.loads(content.split(marker, 1)[1].split('\n', 1)[0])
        except (IndexError, ValueError):
            continue
        memories = data.get('selected_memories', [])
        if isinstance(memories, list):
            return {'speaker': data.get('speaker'), 'memories': [value.get('content')
                for value in memories if isinstance(value, dict) and isinstance(value.get('content'), str)]}
    return {'speaker': None, 'memories': []}


def run_mode(mode):
    global original_post
    captures.clear()
    retrieval_traces.clear()
    with tempfile.TemporaryDirectory(prefix='npc-faiss-paired-', dir='/private/tmp') as temporary:
        database = Path(temporary) / 'world.sqlite'
        os.environ['DATABASE_URL'] = 'sqlite:///' + str(database)
        os.environ['CONVERSATION_MEMORY_RETRIEVAL_ENABLED'] = 'true' if mode != 'off' else 'false'
        os.environ['EMBEDDING_BASE_URL'] = ('http://127.0.0.1:1' if mode == 'embedding_outage'
                                           else 'http://127.0.0.1:11434')
        os.environ['CONVERSATION_HISTORY_TURN_LIMIT'] = '1'
        from app.config.settings import get_settings
        get_settings.cache_clear()
        from app.models.conversation_state import ConversationEmbedding, ConversationMemoryRevision, ConversationTurn
        from app.services.conversation import contracts as c
        from app.services.llm.structured import _HttpTransport
        from app.database.session import engine as app_engine
        trace_handler = RetrievalTraceHandler()
        for logger_name in ('app.services.conversation.context',
                            'app.services.conversation.adapters.semantic_retrieval'):
            target_logger = logging.getLogger(logger_name)
            target_logger.setLevel(logging.INFO)
            target_logger.addHandler(trace_handler)
        original_post = _HttpTransport.post
        _HttpTransport.post = capture_post
        from app.main import create_app
        assert str(app_engine.url.database) == str(database), (app_engine.url, database)
        samples = []
        with TestClient(create_app()) as client:
            world = client.get('/world').json()
            scope = world['game_scope']
            completed = client.post('/world/opening/complete', json={
                'game_scope': scope, 'opening_version': world['opening_version']})
            assert completed.status_code == 200, completed.text

            def say(request_id, npc_id, message):
                current_world = client.get('/world').json()
                payload = {'schema_version': 1, 'request_id': request_id,
                    'game_scope': scope, 'conversation_epoch': current_world['conversation_epochs'][str(npc_id)],
                    'npc_id': npc_id, 'player_message': message}
                started = time.monotonic()
                response = client.post('/chat', json=payload)
                while response.status_code == 202 and time.monotonic() - started < 190:
                    time.sleep(.1)
                    response = client.get(response.json()['status_url'])
                assert response.status_code == 200, response.text
                body = response.json()
                assert ''.join(body['dialogue_beats']) == body['final_dialogue']
                samples.append({'npc_id': npc_id, 'message': message, 'dialogue': body['final_dialogue'],
                    'response_origin': body['response_origin'], 'degradation_reason': body['degradation_reason'],
                    'seconds': round(time.monotonic() - started, 3)})
                return body

            for npc_id in (1, 2):
                say(f'paired-source-{mode}-{npc_id}', npc_id, SOURCE_MESSAGE)
                engine = create_engine(os.environ['DATABASE_URL'])
                try:
                    with Session(engine) as db:
                        source_turn = db.scalar(select(ConversationTurn).where(
                            ConversationTurn.game_scope == scope, ConversationTurn.npc_id == npc_id,
                            ConversationTurn.phase == 'finalized').order_by(ConversationTurn.sequence.desc()))
                        assert source_turn is not None
                        turn_ref = c.TurnRef(turn_id=source_turn.turn_id, request_id=source_turn.request_id,
                            key=c.ConversationKey(game_scope=scope, npc_id=npc_id, epoch=source_turn.epoch),
                            sequence=source_turn.sequence)
                        source = c.SourceRef(kind='player_message', source_id=f'turn:{source_turn.sequence}',
                            revision=0, game_scope=scope, npc_id=npc_id, attribution='player:1', visibility='public')
                        memories = (*[(f'memory:noise-{index:02d}', content)
                                      for index, content in enumerate(NOISE_MEMORIES)],
                                    ('memory:zzz-preference', MEMORY_TEXT))
                        for memory_id, content in memories:
                            memory = c.MemoryRecord(memory_id=memory_id, game_scope=scope,
                                npc_id=npc_id, epoch=source_turn.epoch, kind='player_report', attributed_subject='player:1',
                                content=content, uncertainty='unverified', sources=(source,), status='active', revision=1)
                            db.add(ConversationMemoryRevision(game_scope=scope, npc_id=npc_id, epoch=source_turn.epoch,
                                memory_id=memory.memory_id, revision=memory.revision, status='active',
                                record_payload={'record': memory.model_dump(mode='json'), 'correction_link': None,
                                    'introduced_turn_id': turn_ref.turn_id}))
                        db.commit()
                finally:
                    engine.dispose()
                say(f'paired-intervening-{mode}-{npc_id}', npc_id, 'What do you enjoy about your work?')
                say(f'paired-query-{mode}-{npc_id}', npc_id, QUERY)
            engine = create_engine(os.environ['DATABASE_URL'])
            try:
                with Session(engine) as db:
                    vector_count = db.scalar(select(func.count()).select_from(ConversationEmbedding))
            finally:
                engine.dispose()
            query_captures = [item for item in captures if any(QUERY in m.get('content', '')
                for m in item['messages'])]
            query_memory_presence = [any(MEMORY_TEXT in m.get('content', '') for m in item['messages'])
                                     for item in query_captures]
            prompt_has_memory = any(query_memory_presence)
            query_memory_order = [selected_memory_projection(item) for item in query_captures]
            assert len(query_captures) > 0, ('query did not reach the live provider', samples)
            assert len(query_captures) == 2, query_captures
            assert all(item['response_origin'] == 'generated' for item in samples if item['message'] == QUERY), samples
            if mode == 'on':
                assert vector_count == 40, f'semantic mode expected 40 reusable vectors, got {vector_count}'
                assert all(query_memory_presence), 'selected memory was not present for both NPC prompts'
                assert all(0 <= result['memories'].index(MEMORY_TEXT) < 5
                           for result in query_memory_order), 'semantic ranking did not put the target in top five'
            else:
                assert vector_count == 0, 'off/degraded mode unexpectedly persisted an embedding vector'
            summary = {'mode': mode, 'model': PROFILE['LLM_MODEL'], 'embedding_model': 'nomic-embed-text',
                'messages': samples, 'persistent_vector_count': vector_count,
                'query_prompt_capture_count': len(query_captures), 'query_prompt_contains_memory': prompt_has_memory,
                'query_prompt_memory_by_npc': query_memory_presence,
                'query_prompt_memory_order': query_memory_order,
                'retrieval_trace_events': list(retrieval_traces)}
            return summary


def main():
    with urlopen('http://127.0.0.1:11434/api/tags', timeout=5) as response:
        models = {item['name'] for item in json.load(response)['models']}
    assert {'llama3:willowbrook', 'nomic-embed-text:latest'} <= models, models
    if len(sys.argv) == 4 and sys.argv[1] == '--mode':
        result = run_mode(sys.argv[2])
        Path(sys.argv[3]).write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return
    results = []
    with tempfile.TemporaryDirectory(prefix='npc-faiss-paired-results-', dir='/private/tmp') as temporary:
        for mode in ('off', 'on', 'embedding_outage'):
            result_file = Path(temporary) / f'{mode}.json'
            child = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--mode', mode,
                str(result_file)], check=False, capture_output=True, text=True,
                env=os.environ.copy(), cwd=ROOT)
            if child.returncode == 0:
                results.append(json.loads(result_file.read_text()))
            else:
                failure_log = OUT / f'{mode}-failure.log'
                failure_log.write_text(child.stdout + child.stderr)
                results.append({'mode': mode, 'exit_code': child.returncode,
                    'failure_log': failure_log.name})
            if child.stdout:
                print(child.stdout, end='', flush=True)
    result = {'purpose': 'paired local functionality trial; not semantic quality certification',
        'context_token_budget': 2000, 'generation_token_reserve': 256,
        'same_source_message_and_query': True, 'npc_ids': [1, 2],
        'personal_save_used': False, 'results': results}
    (OUT / 'paired-live-results.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
