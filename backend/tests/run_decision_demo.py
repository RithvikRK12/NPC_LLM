"""Repeatable E API demonstration with real providers and a recorded transcript.

Synthetic initial/state fixtures are disclosed; never starts the saved-world app.
The transcript is a recorded API demonstration, not a video or live replay.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
from statistics import median
from tempfile import TemporaryDirectory
import time

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.config.settings import get_settings
from app.database.base import Base
from app.database.seed import seed_world, reset_world
from app.database.session import get_db
from app.models import Conversation, NPC, Memory

STATES = {'helpful': (.95, .05), 'cautious': (.65, .6), 'distrustful': (.05, .8)}


def audit_trace(trace, saved, payload):
    """Inspect cross-stage and durable identity invariants, not natural-language quality."""
    try:
        eligibility, scores = trace['behavior']['eligibility'], trace['behavior']['scores']
        selection = trace['behavior']['selection']
        memories = trace['context']['retrieved_memory_provenance']
        retrieval = trace['context']['memory_retrieval']
        return {
            'persisted_trace_matches': saved is not None and saved.validated_output['decision_trace'] == trace,
            'durable_outcome_identity': saved is not None and saved.source_event_id == trace['decision_id']
                == trace['outcome']['event_id'] and saved.id == trace['outcome']['conversation_id'],
            'context_sources_present': bool(trace['context']['fact_sources']),
            'memory_scope_status': all(m['game_scope'] == trace['game_scope'] and m['lifecycle'] == 'active'
                and m['epistemic_status'] in {'fact', 'claim', 'interpretation', 'retraction'} for m in memories),
            'retrieval_ids_match_context': retrieval['selected_ids'] == [m['id'] for m in memories],
            'retrieval_bounded': len(retrieval['selected_ids']) <= retrieval['result_limit'] and
                retrieval['semantic_candidates'] + retrieval['lexical_candidates'] <= retrieval['materialization_limit'],
            'eligible_selection_and_scores': eligibility[selection]['eligible'] and
                selection in scores and all(eligibility[name]['eligible'] for name in scores),
            'pipeline_order': trace['behavior']['ordering'] == ['role_conditioning', 'final_control_validation', 'fsec'],
            'rejected_has_zero_authority': not trace['validation']['rejected'] or
                (trace['outcome']['action'] is None and not trace['outcome']['transfer'] and not trace['memory_write']['stored']),
            'response_trace_matches': payload['grounding_trace']['rejected'] == trace['validation']['rejected']
                and payload['behavior_trace']['selection'] == selection,
        }
    except (KeyError, TypeError, AttributeError):
        return {'complete_trace': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New evidence directory')
    parser.add_argument('--attempts', type=int, default=2)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists() or not 1 <= args.attempts <= 3:
        parser.error('Use a new directory and 1–3 attempts (2 recommended for variability).')
    settings = get_settings()
    if not settings.llm_base_url:
        parser.error('Real generation must be configured; mocks are forbidden in this runner.')
    output.mkdir(parents=True)
    fixture_path = Path(__file__).with_name('decision_demo_scenarios.json')
    cases = json.loads(fixture_path.read_text())
    root = Path(__file__).parents[1]
    paths = [*sorted((root / 'app').rglob('*.py')), *sorted((root / 'app/services').rglob('*.json')),
             Path(__file__), fixture_path]
    evidence = {'started_at': datetime.now(timezone.utc).isoformat(),
                'kind': 'recorded_api_demonstration', 'attempts': args.attempts,
                'world': 'disposable file-backed SQLite', 'python': platform.python_version(),
                'fixtures': 'seed world plus controlled helpful/cautious/distrustful initial NPC states; not memory-driven changes',
                'generation': 'real configured provider; no mocks',
                'configuration': {'model': settings.llm_model, 'temperature': .2,
                    'structured_output': settings.llm_structured_output,
                    'embedding_model': settings.embedding_model, 'embedding_dimensions': settings.embedding_dimensions,
                    'embedding_revision': settings.embedding_revision},
                'implementation_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                'cases': [], 'finished': False, 'release_ready': False,
                'limitations': ['No agreed release-quality threshold.', 'No new Godot/video recording.',
                    'D3 influence and authored mandatory recovery deferred.',
                    'Provider/decode/outage guards covered separately by deterministic tests and D2 real transport evidence.']}
    def save():
        records = evidence['cases']
        evidence['passed'] = sum(c['passed'] for c in records)
        evidence['total'] = len(records)
        evidence['trace_checks_passed'] = sum(sum(c['trace_checks'].values()) for c in records)
        evidence['trace_checks_total'] = sum(len(c['trace_checks']) for c in records)
        evidence['rejections'] = sum(c.get('decision_trace', {}).get('validation', {}).get('rejected', False) for c in records)
        evidence['inappropriate_fallbacks'] = sum(c.get('decision_trace', {}).get('validation', {}).get('rejected', False) for c in records)
        evidence['authority_failures'] = sum(not c['authority_safe'] for c in records)
        evidence['expectation_failures'] = [f"attempt {c['attempt']} {c['id']}" for c in records if not c['expected_behavior']]
        durations = sorted(c['seconds'] for c in records)
        if durations:
            evidence['latency_seconds'] = {'min': durations[0], 'median': median(durations),
                'p95': durations[min(len(durations)-1, int(.95*len(durations)))], 'max': durations[-1]}
        (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
        lines = ['# Recorded API demonstration', '',
                 'This is a saved transcript of real API/model execution against a disposable world. It is not live execution, a Godot playthrough or a screen recording.', '',
                 f"Results: {evidence['passed']}/{evidence['total']} scenario checks; {evidence['trace_checks_passed']}/{evidence['trace_checks_total']} trace checks. Release readiness is unassessed.", '']
        for c in records:
            lines.extend([f"## Attempt {c['attempt']} — {c['id']} (NPC {c['npc_id']})", '',
                          f"Player: {c['message']}", '', f"NPC: {c['dialogue']}", '',
                          f"Result: {'PASS' if c['passed'] else 'FAIL'}; {c['seconds']} seconds.", '',
                          '```json', json.dumps(c['decision_trace'], indent=2), '```', ''])
        (output / 'transcript.md').write_text('\n'.join(lines))
    save()
    try:
        # Version metadata is optional evidence; provider execution below is mandatory.
        try:
            base = settings.embedding_base_url.rstrip('/')
            tags = httpx.get(base + '/api/tags', timeout=5).json()
            evidence['ollama_models'] = [{k: model.get(k) for k in ('name', 'digest', 'modified_at')}
                for model in tags.get('models', []) if model.get('name') in {settings.llm_model, settings.embedding_model + ':latest', settings.embedding_model}]
            evidence['ollama_version'] = httpx.get(base + '/api/version', timeout=5).json().get('version')
        except (httpx.HTTPError, ValueError, AttributeError):
            evidence['ollama_metadata'] = 'unavailable; configured provider still required'
        with TemporaryDirectory(prefix='npc-decision-demo-') as temporary:
            engine = create_engine('sqlite:///' + str(Path(temporary) / 'world.db'), connect_args={'check_same_thread': False})
            Base.metadata.create_all(engine)
            app = FastAPI()
            app.include_router(api_router)
            def session():
                with Session(engine) as db:
                    yield db
            app.dependency_overrides[get_db] = session
            with Session(engine) as db:
                seed_world(db)
            with TestClient(app) as client:
                for attempt in range(1, args.attempts + 1):
                    with Session(engine) as db:
                        reset_world(db)
                        npc = db.get(NPC, 1)
                        npc.trust, npc.fear = STATES['helpful']
                        npc.aggression, npc.curiosity = .05, .3
                        db.commit()
                    claim_id, craftsman_memory_ids = None, set()
                    for case in cases:
                        npc_id = case.get('npc_id', 1)
                        if case.get('state'):
                            with Session(engine) as db:
                                npc = db.get(NPC, npc_id)
                                npc.trust, npc.fear = STATES[case['state']]
                                npc.aggression, npc.curiosity = .05, .3
                                db.commit()
                        start = time.monotonic()
                        response = client.post('/chat', json={'npc_id': npc_id, 'player_message': case['message']})
                        seconds = round(time.monotonic()-start, 3)
                        data = response.json()
                        trace = data.get('decision_trace', {})
                        with Session(engine) as db:
                            saved = db.scalar(select(Conversation).where(Conversation.npc_id == npc_id).order_by(Conversation.id.desc()))
                            checks = audit_trace(trace, saved, data)
                            if npc_id == 1:
                                craftsman_memory_ids.update(db.scalars(select(Memory.id).where(Memory.npc_id == 1)))
                        expected = response.status_code == 200 and not trace.get('validation', {}).get('rejected', True)
                        expected = expected and (not case.get('fact') or case['fact'] in trace['validation']['selected_fact_ids'])
                        expected = expected and (not case.get('kind') or data['validated_output']['answer_kind'] == case['kind'])
                        expected = expected and (not case.get('selection') or trace['behavior']['selection'] == case['selection'])
                        if case.get('recall_claim'):
                            expected = expected and claim_id is not None and claim_id in trace['context']['memory_retrieval']['selected_ids']
                        if case['id'] == 'B-02-claim':
                            claim_id = data.get('memory_classification', {}).get('memory_id')
                            expected = expected and trace['memory_write']['epistemic_status'] == 'claim'
                        if case.get('transfer'):
                            expected = expected and trace['outcome']['transfer'] is not None
                        if npc_id == 2:
                            checks['recipient_memory_isolation'] = not (craftsman_memory_ids & set(trace.get('context', {}).get('memory_retrieval', {}).get('selected_ids', [])))
                        safe = response.status_code == 200 and data.get('bow_quest', {}).get('phase') == 'available' and data.get('player_inventory') == ['water', 'food'] + ['rope'] * case.get('rope_count', 0)
                        record = {'attempt': attempt, 'id': case['id'], 'npc_id': npc_id,
                                  'message': case['message'], 'dialogue': data.get('final_dialogue'),
                                  'seconds': seconds, 'authority_safe': safe, 'expected_behavior': bool(expected),
                                  'trace_checks': checks, 'decision_trace': trace,
                                  'passed': bool(expected and safe and all(checks.values()))}
                        evidence['cases'].append(record)
                        save()
                        print(f"{'PASS' if record['passed'] else 'FAIL'} attempt {attempt} {case['id']} ({seconds}s)", flush=True)
            engine.dispose()
        evidence['finished'] = True
    except Exception as exc:
        evidence['runner_failure_type'] = type(exc).__name__  # never export transport credentials
        raise
    finally:
        evidence['finished_at'] = datetime.now(timezone.utc).isoformat()
        save()
    print(f"{evidence['passed']}/{evidence['total']} scenarios; {evidence['trace_checks_passed']}/{evidence['trace_checks_total']} trace checks", flush=True)
    return 0 if evidence['finished'] and evidence['passed'] == evidence['total'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
