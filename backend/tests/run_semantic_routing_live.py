"""Held-out local-model evaluation through the real /chat route only.

Uses disposable in-memory SQLite databases and the configured local LLM. No
mock model, personal save, or hosted inference is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.router import api_router
from app.config.settings import get_settings
from app.database.base import Base
from app.database.seed import seed_world
from app.database.session import get_db
from app.models import BowQuest, CraftsmanEncounter, GathererEncounter, NPC, Player
from app.models.ship_repair_quest import ShipRepairQuest
from app.services.craftsman import defaults as craftsman_defaults
from app.services.gatherer import defaults as gatherer_defaults

app = FastAPI()
app.include_router(api_router)


def snapshot(db: Session, npc_id: int):
    npc, player = db.get(NPC, npc_id), db.get(Player, 1)
    bow = db.get(BowQuest, player.id)
    ship = db.get(ShipRepairQuest, player.id)
    encounter_model = CraftsmanEncounter if npc.role == 'craftsman' else GathererEncounter
    encounter = db.get(encounter_model, player.id)
    encounter_state = (encounter.state if encounter else
                       craftsman_defaults() if npc.role == 'craftsman' else gatherer_defaults())
    return {
        'player_inventory': list(player.inventory or []), 'npc_inventory': list(npc.inventory or []),
        'pending_item': npc.pending_item,
        'relationship': [npc.trust, npc.fear, npc.aggression, npc.curiosity],
        'bow_phase': bow.phase if bow else 'available', 'ship_phase': ship.phase if ship else 'not_started',
        'encounter_state': encounter_state,
    }


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)], 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='docs/evidence/semantic-chat-routing/report.json')
    args = parser.parse_args()
    settings = get_settings()
    if not settings.llm_base_url or settings.llm_model != 'llama3:willowbrook':
        raise SystemExit('Refusing live evaluation without configured local llama3:willowbrook.')
    fixture = json.loads((Path(__file__).parent / 'fixtures/semantic-routing-heldout-v1.json').read_text())
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'model': settings.llm_model,
              'provider': 'local OpenAI-compatible Ollama', 'temperature': 0,
              'routing_version': settings.conversation_routing_version,
              'fixture_version': fixture['version'], 'world': 'disposable in-memory SQLite',
              'cases': [], 'counts': {}}
    tracked_files = ['app/services/semantic_routing.py', 'app/services/llm/service.py',
                     'app/services/llm/openai_compatible.py', 'app/services/pipeline.py',
                     'app/services/validation/service.py', 'app/services/validation/items.py',
                     'app/services/prompts/builder.py']
    report['implementation_sha256'] = {name: hashlib.sha256((Path(__file__).parents[1] / name).read_bytes()).hexdigest()
                                       for name in tracked_files}
    report['fixture_sha256'] = hashlib.sha256((Path(__file__).parent / 'fixtures/semantic-routing-heldout-v1.json').read_bytes()).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    app.dependency_overrides.clear()
    for scenario in fixture['scenarios']:
        engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
        Base.metadata.create_all(engine)
        with Session(engine) as db, TestClient(app) as client:
            seed_world(db)
            app.dependency_overrides[get_db] = lambda: db
            npc_id = scenario['npc_id']
            if scenario.get('setup_pending_item'):
                item = scenario['setup_pending_item']
                response = client.post('/inventory/transfer', json={'npc_id': npc_id, 'item': item, 'direction': 'to_player'})
                if response.status_code != 200:
                    raise RuntimeError(f"pending setup failed: {response.status_code} {response.text}")
            if scenario.get('setup_offer_pending'):
                from app.services.craftsman import record
                player = db.get(Player, 1)
                row = record(db, player)
                row.state = row.state | {'wreck_reported': True, 'offer_pending': True, 'topic': 'ship'}
                db.commit()
            for index, case in enumerate(scenario['turns'], 1):
                before = snapshot(db, npc_id)
                started = time.perf_counter()
                response = client.post('/chat', json={'npc_id': npc_id, 'player_message': case['message']})
                elapsed = time.perf_counter() - started
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                after = snapshot(db, npc_id)
                trace = data.get('grounding_trace', {})
                interpretation = trace.get('accepted_interpretation', {})
                concerns = interpretation.get('concerns', [])
                kinds = sorted({c.get('kind') for c in concerns})
                operations = sorted({c.get('operation') for c in concerns if c.get('operation')})
                facts = sorted({fact for c in concerns for fact in c.get('fact_ids', [])})
                targets = sorted({c.get('target') for c in concerns if c.get('target')})
                answer_types = sorted({c.get('answer_type') for c in concerns if c.get('answer_type')})
                modalities = sorted({c.get('modality') for c in concerns})
                expected_kinds = set(case['kinds'])
                kind_match = expected_kinds == set(kinds)
                operation_match = not case.get('operation') or case['operation'] in operations
                facts_match = set(case.get('fact_ids', [])) <= set(facts)
                modality_match = not case.get('modality') or case['modality'] in modalities
                target_match = not case.get('target') or case['target'] in targets
                answer_type_match = not case.get('answer_type') or case['answer_type'] in answer_types
                interpretation_correct = response.status_code == 200 and kind_match and operation_match and facts_match and modality_match and target_match and answer_type_match
                mutated = before != after
                unauthorized = mutated and not case.get('mutation', False)
                rejected = bool(trace.get('rejected'))
                explicit_degradation = any(term in data.get('final_dialogue', '').casefold() for term in
                    ('could not understand that just now', "can't form a grounded reply"))
                fallback = rejected or explicit_degradation or response.status_code != 200
                record = {
                    'scenario': scenario['id'], 'turn': index, 'npc_id': npc_id, 'message': case['message'],
                    'status_code': response.status_code, 'expected_kinds': sorted(expected_kinds), 'actual_kinds': kinds,
                    'expected_operation': case.get('operation'), 'actual_operations': operations,
                    'expected_fact_ids': case.get('fact_ids', []), 'actual_fact_ids': facts,
                    'expected_fact_ids_specified': 'fact_ids' in case,
                    'expected_target': case.get('target'), 'actual_targets': targets,
                    'expected_answer_type': case.get('answer_type'), 'actual_answer_types': answer_types,
                    'expected_modality': case.get('modality'), 'actual_modalities': modalities,
                    'accepted_interpretation': interpretation,
                    'actual_purposes': sorted({c.get('purpose') for c in concerns if c.get('purpose')}),
                    'interpretation_correct': interpretation_correct, 'mixed_expected': len(expected_kinds) > 1,
                    'mixed_covered': expected_kinds <= set(kinds), 'mutated': mutated,
                    'expected_mutation': bool(case.get('mutation', False)),
                    'expected_mutation_completed': bool(case.get('mutation', False)) and mutated,
                    'unauthorized_mutation': unauthorized, 'grounding_rejected': rejected,
                    'fallback': fallback, 'interpretation_calls': trace.get('model_calls', {}).get('interpretation', 0),
                    'speech_calls': trace.get('model_calls', {}).get('speech_and_repair', 0),
                    'span_repairs': trace.get('interpretation_span_repairs', 0),
                    'interpretation_seconds': trace.get('interpretation_seconds'), 'end_to_end_seconds': round(elapsed, 3),
                    'reply': data.get('final_dialogue'), 'before': before, 'after': after,
                }
                report['cases'].append(record)
                output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
                print(json.dumps({k: record[k] for k in ('scenario', 'turn', 'npc_id', 'interpretation_correct',
                    'actual_kinds', 'unauthorized_mutation', 'grounding_rejected', 'interpretation_seconds', 'end_to_end_seconds')}, ensure_ascii=False), flush=True)
        app.dependency_overrides.clear()
        engine.dispose()
    cases = report['cases']
    interpretation_times = [c['interpretation_seconds'] for c in cases if c['interpretation_seconds'] is not None]
    e2e_times = [c['end_to_end_seconds'] for c in cases]
    mixed = [c for c in cases if c['mixed_expected']]
    by_npc = {}
    for case in cases:
        bucket = by_npc.setdefault(str(case['npc_id']), {'correct': 0, 'denominator': 0})
        bucket['correct'] += bool(case['interpretation_correct'])
        bucket['denominator'] += 1
    def dimension(name, expected_key, actual_key, *, exact=False, presence_key=None):
        selected = [c for c in cases if (c.get(presence_key, False) if presence_key else c.get(expected_key) is not None)]
        correct = 0
        for case in selected:
            expected_value, actual_value = case[expected_key], case.get(actual_key)
            if exact and isinstance(expected_value, list):
                correct += set(expected_value) == set(actual_value or [])
            elif isinstance(expected_value, list):
                correct += set(expected_value) <= set(actual_value or [])
            else:
                correct += expected_value in (actual_value or []) if isinstance(actual_value, list) else expected_value == actual_value
        return {'correct': correct, 'denominator': len(selected)}
    confusion = {}
    for case in cases:
        key = '+'.join(case['expected_kinds'])
        bucket = confusion.setdefault(key, {'count': 0, 'actual_kinds': {}})
        bucket['count'] += 1
        actual = '+'.join(case['actual_kinds']) or 'none'
        bucket['actual_kinds'][actual] = bucket['actual_kinds'].get(actual, 0) + 1
    report['counts'] = {
        'interpretation_accuracy': {'correct': sum(c['interpretation_correct'] for c in cases), 'denominator': len(cases)},
        'interpretation_accuracy_by_npc_id': by_npc,
        'operation_accuracy': dimension('operation_accuracy', 'expected_operation', 'actual_operations'),
        'fact_accuracy': dimension('fact_accuracy', 'expected_fact_ids', 'actual_fact_ids', exact=True,
                                   presence_key='expected_fact_ids_specified'),
        'target_accuracy': dimension('target_accuracy', 'expected_target', 'actual_targets'),
        'modality_accuracy': dimension('modality_accuracy', 'expected_modality', 'actual_modalities'),
        'pending_answer_accuracy': dimension('pending_answer_accuracy', 'expected_answer_type', 'actual_answer_types'),
        'concern_confusion': confusion,
        'unnecessary_fallback': {'count': sum(c['fallback'] for c in cases if 'clarification' not in c['expected_kinds']),
                                 'denominator': sum('clarification' not in c['expected_kinds'] for c in cases)},
        'grounding_failures': {'count': sum(c['grounding_rejected'] for c in cases), 'denominator': len(cases)},
        'mixed_concern_coverage': {'covered': sum(c['mixed_covered'] for c in mixed), 'denominator': len(mixed)},
        'unauthorized_mutations': {'count': sum(c['unauthorized_mutation'] for c in cases), 'denominator': len(cases)},
        'expected_mutation_completion': {
            'completed': sum(c.get('expected_mutation_completed', False) for c in cases),
            'denominator': sum(c.get('expected_mutation', False) for c in cases)},
        'interpretation_model_calls': sum(c['interpretation_calls'] for c in cases),
        'interpretation_extra_calls': sum(max(0, c['interpretation_calls'] - 1) for c in cases),
        'speech_model_calls': sum(c['speech_calls'] for c in cases),
        'interpretation_latency_seconds': {'p50': percentile(interpretation_times, .50), 'p95': percentile(interpretation_times, .95),
                                           'measured': len(interpretation_times)},
        'end_to_end_latency_seconds': {'p50': percentile(e2e_times, .50), 'p95': percentile(e2e_times, .95), 'measured': len(e2e_times)},
    }
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['counts'], indent=2), flush=True)


if __name__ == '__main__':
    main()
