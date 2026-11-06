"""Isolated T02 origin/latency measurement. Never import app.main/session/init_db."""
from __future__ import annotations
import hashlib
import json
import logging
import math
from pathlib import Path
import sys
import time
from collections import Counter
from urllib.parse import urlsplit, urlunsplit
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'backend'))


def safe_url(url):
    parts = urlsplit(url)
    host = parts.hostname or ''
    if ':' in host:
        host = '[' + host + ']'
    return urlunsplit((parts.scheme, host + (f':{parts.port}' if parts.port else ''), parts.path, '', ''))


def percentiles(values):
    values = sorted(values)
    return {'n': len(values), 'p50_seconds': values[math.ceil(.5 * len(values)) - 1] if values else None,
            'p95_seconds': values[math.ceil(.95 * len(values)) - 1] if values else None}


def classify_origin(trace, mode, error_type=None):
    generation = trace['generation']
    if generation['authoritative_override']:
        return 'scripted'
    if generation['status'] == 'provider_or_decode_failure':
        if error_type in {'ConnectError', 'ConnectTimeout', 'ReadTimeout', 'WriteTimeout', 'PoolTimeout', 'ConnectionError', 'ReadError', 'WriteError'}:
            return 'outage_fallback'
        return 'provider_error_fallback' if error_type else 'decode_or_unknown_error_fallback'
    if trace['validation']['rejected']:
        return 'explicit_mock_fallback' if mode == 'explicit_mock' else 'healthy_provider_fallback'
    if trace['validation']['selected_fact_ids']:
        return 'scripted_fact_render'
    return 'explicit_mock' if mode == 'explicit_mock' else 'generated'


def prepare_fixture_player(db):
    """Persist synthetic run identity before versioned writers refresh the row."""
    from app.models import Player

    player = db.get(Player, 1)
    if player is None:
        raise RuntimeError('Measurement fixture did not seed its player')
    player.game_scope = 'baseline-measurement'
    player.opening_state = 'complete'
    db.flush()
    return player


def run():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool
    from app.config.settings import get_settings
    from app.database.base import Base
    from app.database.seed import seed_world
    from app.services.gatherer import record
    from app.services.pipeline import ConversationPipeline
    from app.services.llm.mock import MockLLMProvider
    from app.services.llm.openai_compatible import OpenAICompatibleProvider
    from app.services.llm.service import LLMService

    settings = get_settings()
    fixtures_bytes = (HERE / 'fixtures.json').read_bytes()
    fixtures = json.loads(fixtures_bytes)
    secrets = [value for value in (settings.llm_api_key,) if value]
    secrets += [value for value in (urlsplit(settings.llm_base_url).password,
                                  urlsplit(settings.llm_base_url).query) if value]
    sentinel = 'BASELINE_DIAGNOSTIC_SECRET_SENTINEL'
    secrets.append(sentinel)
    config = {'provider': 'OpenAICompatibleProvider' if settings.llm_base_url else 'MockLLMProvider',
              'model': settings.llm_model, 'base_url': safe_url(settings.llm_base_url),
              'structured_output': settings.llm_structured_output, 'temperature': .2,
              'timeout_seconds': settings.llm_timeout_seconds, 'connect_timeout_seconds': 5,
              'max_tokens': None, 'max_dialogue_chars': settings.max_dialogue_chars,
              'memory_top_k': settings.memory_top_k, 'memory_candidate_count': settings.memory_candidate_count,
              'embedding': 'fake one-hot in memory; configured embedding never called',
              'embedding_dimensions': settings.embedding_dimensions,
              'model_version': 'configured tag only; immutable weight digest unavailable'}
    rows = []
    diagnostic_checks = 0
    calls = []

    class ControlledProvider:
        def __init__(self, mode):
            self.mode = mode
            self.upstream = OpenAICompatibleProvider() if mode == 'configured' else MockLLMProvider()
        def generate(self, prompt, context):
            started = time.perf_counter()
            error = None
            try:
                if self.mode == 'outage':
                    raise ConnectionError(sentinel)
                if self.mode == 'healthy_valid':
                    return json.dumps({'answer_kind': 'chat', 'fact_ids': [],
                                       'dialogue': 'I feel calmer with familiar work around me.'})
                if self.mode == 'healthy_rejected':
                    return json.dumps({'intent': 'attack', 'emotion': 'hostile', 'action': 'attack',
                                       'dialogue': 'I will strike you now.', 'reasoning': sentinel, 'state_update': {}})
                return self.upstream.generate(prompt, context)
            except Exception as exc:
                # Never export exception text/HTTP headers/body/URL.
                error = type(exc).__name__
                raise
            finally:
                calls.append({'mode': self.mode, 'elapsed_seconds': time.perf_counter() - started,
                              'error_type': error})

    def session(mode, fixture, replay, stop_on_outage=False):
        nonlocal diagnostic_checks
        engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
        try:
            Base.metadata.create_all(engine)
            with Session(engine) as db:
                seed_world(db)
                player = prepare_fixture_player(db)
                encounter = record(db, player)
                encounter.state = encounter.state | {'status': 'resolved_helped'}
                db.commit()
                pipeline = ConversationPipeline(db)
                pipeline._llm_service = LLMService(provider=ControlledProvider(mode))
                for index, turn in enumerate(fixture['turns']):
                    started = time.perf_counter()
                    before = len(calls)
                    response = pipeline.chat(fixture['npc_id'], turn['message'])
                    elapsed = time.perf_counter() - started
                    payload = response.model_dump(mode='json')
                    diagnostic = json.dumps({key: payload[key] for key in ('decision_trace', 'grounding_trace')})
                    assert all(secret not in diagnostic for secret in secrets), 'Credential diagnostic check failed'
                    diagnostic_checks += 1
                    trace = payload['decision_trace']
                    rows.append({'mode': mode, 'session': fixture['id'], 'replay': replay, 'turn': index + 1,
                                 'route': turn['route'], 'message': turn['message'],
                                 'elapsed_seconds': elapsed, 'origin': classify_origin(trace, mode, calls[-1]['error_type'] if len(calls) > before else None),
                                 'provider_error_type': calls[-1]['error_type'] if len(calls) > before else None,
                                 'generation_status': trace['generation']['status'],
                                 'authoritative_override': trace['generation']['authoritative_override'],
                                 'rejected': trace['validation']['rejected'],
                                 'provider_calls': len(calls) - before,
                                 'final_dialogue': payload['final_dialogue'],
                                 'action': payload['validated_output']['action'],
                                 'player_inventory': payload['player_inventory'], 'npc_inventory': payload['npc']['inventory'],
                                 'trace_provider': trace['configuration']['provider']})
                    if stop_on_outage and trace['generation']['status'] == 'provider_or_decode_failure':
                        return False
        finally:
            engine.dispose()
        return True

    logging.disable(logging.CRITICAL)  # Pipeline logs contain known text, but do not collect free-form errors.
    with patch('app.services.memory.embedding.EmbeddingService.embed_many',
               side_effect=lambda texts, **kw: [[1.] + [0.] * (settings.embedding_dimensions - 1) for _ in texts]):
        for mode in ('explicit_mock', 'healthy_valid', 'healthy_rejected', 'outage'):
            for replay in (1, 2):
                for fixture in fixtures['sessions']:
                    session(mode, fixture, replay)
        live_available = False
        if settings.llm_base_url:
            live_available = True
            for replay in (1, 2):
                for fixture in fixtures['sessions']:
                    if not session('configured', fixture, replay, stop_on_outage=True):
                        live_available = False
                        break
                if not live_available:
                    break
    # Equivalent deterministic replays exclude timing and generated UUIDs (never exported).
    deterministic_replay = {}
    for mode in ('explicit_mock', 'healthy_valid', 'healthy_rejected', 'outage'):
        values = [[{k: v for k, v in row.items() if k not in {'elapsed_seconds', 'replay'}}
                   for row in rows if row['mode'] == mode and row['replay'] == replay] for replay in (1, 2)]
        deterministic_replay[mode] = values[0] == values[1]
    assert all(deterministic_replay.values())
    assert 'app.main' not in sys.modules and 'app.database.session' not in sys.modules, 'Unsafe application startup import'
    summary = {}
    for mode in sorted({row['mode'] for row in rows}):
        selected = [row for row in rows if row['mode'] == mode]
        origins = Counter(row['origin'] for row in selected)
        summary[mode] = {'turn_count': len(selected), 'origins': dict(origins),
            'generated_count': origins['generated'], 'scripted_count': origins['scripted'] + origins['scripted_fact_render'],
            'fallback_count': origins['healthy_provider_fallback'] + origins['outage_fallback'] + origins['explicit_mock_fallback'] + origins['provider_error_fallback'] + origins['decode_or_unknown_error_fallback'],
            'error_count': sum(row['generation_status'] == 'provider_or_decode_failure' for row in selected),
            'explicit_mock_count': origins['explicit_mock'] + origins['explicit_mock_fallback'],
            'routes': {route: percentiles([row['elapsed_seconds'] for row in selected if row['route'] == route])
                       for route in ('ordinary', 'action', 'repair')}}
    result = {'task': 'baseline/T02', 'cwd': str(ROOT), 'command': '.venv/bin/python docs/evidence/conversation-redesign-baseline/measurement/measure.py',
              'fixture_schema_version': fixtures['schema_version'],
              'source_revision': __import__('subprocess').check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'fixture_sha256': hashlib.sha256(fixtures_bytes).hexdigest(), 'configuration': config,
              'live_available': live_available, 'live_gate_complete': live_available,
              'configured_error_types': sorted({c['error_type'] for c in calls if c['mode'] == 'configured' and c['error_type']}),
              'deterministic_replay_equal': deterministic_replay, 'diagnostics_checked': diagnostic_checks,
              'credential_check': 'actual configured API key/URL password/query plus injected sentinel absent in decision_trace and grounding_trace; full export also checked',
              'summary': summary, 'provider_calls': calls, 'turns': rows}
    exported = json.dumps(result, indent=2)
    assert all(secret not in exported for secret in secrets), 'Credential export check failed'
    (HERE / 'results.json').write_text(exported + '\n')
    print(json.dumps({'live_available': live_available, 'diagnostics_checked': diagnostic_checks,
                      'replay_equal': deterministic_replay, 'summary': summary}, indent=2))

if __name__ == '__main__':
    run()
