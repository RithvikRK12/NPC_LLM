#!/usr/bin/env python3
"""Read-only local Llama schema screen for proposal, composition, and repair."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from time import monotonic, perf_counter
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'backend'))

from app.services.conversation import contracts as c  # noqa: E402
from app.services.conversation.composition import CompositionService  # noqa: E402
from app.services.llm.structured import StructuredGenerationAdapter  # noqa: E402

ENDPOINT = 'http://127.0.0.1:11434/v1'
MODEL_TAG = 'llama3:latest'
MODEL_DIGEST = '365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1'
QUANTIZATION = 'Q4_0'
OUTPUT = ROOT / 'docs/evidence/llm-response-improvement/runs/llama3-structured-stages-screen-r1.json'


def _verify_local_model() -> dict:
    parts = urlsplit(ENDPOINT)
    if parts.hostname not in {'127.0.0.1', 'localhost', '::1'} or parts.username or parts.password:
        raise RuntimeError('structured schema screen must use a credential-free loopback endpoint')
    origin = f'{parts.scheme}://{parts.netloc}'
    with httpx.Client(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
        tags = client.get(origin + '/api/tags')
        tags.raise_for_status()
        version = client.get(origin + '/api/version')
        version.raise_for_status()
        process = client.get(origin + '/api/ps')
        process.raise_for_status()
    models = tags.json().get('models', [])
    model = next((value for value in models if value.get('name') == MODEL_TAG), None)
    if not isinstance(model, dict) or model.get('digest') != MODEL_DIGEST:
        raise RuntimeError('installed local model tag/digest did not match the pinned screen identity')
    if model.get('details', {}).get('quantization_level') != QUANTIZATION:
        raise RuntimeError('installed local model quantization did not match the pinned screen identity')
    running = process.json().get('models', [])
    active = next((value for value in running if value.get('name') == MODEL_TAG), None)
    if not isinstance(active, dict) or active.get('digest') != MODEL_DIGEST:
        raise RuntimeError('pinned local model is not loaded')
    if active.get('context_length') != 4096:
        raise RuntimeError('active local model context is not 4096')
    return {
        'provider_version': version.json().get('version'),
        'model_size_bytes': active.get('size'),
        'model_size_vram_bytes': active.get('size_vram'),
        'context_size': active.get('context_length'),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT,
                        help='new evidence JSON path; existing paths are rejected')
    args = parser.parse_args()
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    if output_path.exists():
        raise RuntimeError(f'evidence output already exists: {output_path}')
    model = _verify_local_model()
    fixture = json.loads((ROOT / 'backend/tests/fixtures/conversation/t05-valid.json').read_text())
    context = c.ContextPacket.model_validate(fixture['context'])
    settings = type('LocalSettings', (), {
        'llm_base_url': ENDPOINT,
        'llm_api_key': '',
        'llm_model': MODEL_TAG,
        'llm_timeout_seconds': 120.0,
        'llm_structured_output': True,
        'conversation_generation_token_limit': 2048,
        'conversation_contract_json_char_limit': 16384,
    })()
    adapter = StructuredGenerationAdapter(settings)
    stages = []
    for purpose in ('proposal', 'composition', 'repair'):
        started = perf_counter()
        try:
            output = adapter.generate(purpose, context,
                c.Deadline.after(120.0, clock=monotonic), 600)
        except Exception as exc:  # retain categorized failures without private provider text
            stage = {'purpose': purpose, 'status': type(exc).__name__,
                     'elapsed_seconds': perf_counter() - started}
            cause = exc.__cause__
            if isinstance(cause, ValidationError):
                stage['validation_issues'] = [
                    {'type': value['type'], 'message': value['msg'],
                     'location': list(value['loc'])}
                    for value in cause.errors(include_url=False)
                ]
            stages.append(stage)
            continue
        segment_count = len(output.reply) if isinstance(output, c.TurnProposal) else len(output.segments)
        stages.append({'purpose': purpose, 'status': type(output).__name__,
                       'segment_count': segment_count,
                       'elapsed_seconds': perf_counter() - started})
    receipt_fixture = json.loads((ROOT / 'backend/tests/fixtures/conversation/contracts-t02-valid.json').read_text())
    receipt_raw = dict(receipt_fixture['receipt'])
    receipt_raw.update(turn_id=context.turn.turn_id,
                       game_scope=context.turn.key.game_scope,
                       npc_id=context.turn.key.npc_id)
    receipt = c.OperationReceipt.model_validate(receipt_raw)
    bounded_context = c.ContextPacket.model_validate({
        **context.model_dump(mode='python'),
        'policy_versions': {**context.policy_versions, 'bounds': 'screen:1'},
    })
    proposal = c.TurnProposal.model_validate(fixture['proposal'])
    policy = c.ConversationPolicy(schema_version=1, policy_version='screen:1',
        input_char_limit=500, total_deadline_seconds=120.0,
        provider_stage_budget_seconds=120.0, context_token_limit=4096,
        output_char_limit=600, beat_char_limit=120, queue_capacity=4,
        lease_duration_seconds=30.0, summary_trigger_turns=8,
        diagnostic_retention_seconds=3600.0)
    class RecordingGeneration:
        def __init__(self, inner):
            self.inner = inner
            self.last_output = None

        def generate(self, purpose, stage_context, deadline, dialogue_codepoint_limit):
            self.last_output = self.inner.generate(purpose, stage_context, deadline,
                                                   dialogue_codepoint_limit)
            return self.last_output

    recording = RecordingGeneration(adapter)
    started = perf_counter()
    try:
        composed = CompositionService(recording, policy).compose(
            bounded_context, proposal, receipt, c.Deadline.after(120.0, clock=monotonic))
    except Exception as exc:
        stage = {'purpose': 'receipt_composition', 'status': type(exc).__name__,
                 'stage': 'composition.compose', 'elapsed_seconds': perf_counter() - started}
        cause = exc.__cause__
        if isinstance(cause, ValidationError):
            stage['validation_issues'] = [
                {'type': value['type'], 'message': value['msg'],
                 'location': list(value['loc'])}
                for value in cause.errors(include_url=False)
            ]
        stages.append(stage)
        composed = None
    receipt_candidate = recording.last_output
    receipt_candidate_summary = {}
    if isinstance(receipt_candidate, c.CandidateReply):
        receipt_candidate_summary = {
            'generated_segment_kinds': [value.kind for value in receipt_candidate.segments],
            'generated_receipt_slot_count': sum(isinstance(value, c.ReceiptSlot)
                                                for value in receipt_candidate.segments),
            'generated_source_schema_version': receipt_candidate.source.schema_version,
            'generated_policy_versions_match': receipt_candidate.source.policy_versions ==
                bounded_context.policy_versions,
        }
    if composed is not None and composed.value is not None:
        stages.append({'purpose': 'receipt_composition', 'status': type(composed.value).__name__,
                       'segment_count': len(composed.value.segments),
                       'receipt_slots': sum(isinstance(value, c.ReceiptSlot)
                                            for value in composed.value.segments),
                       **receipt_candidate_summary,
                       'elapsed_seconds': perf_counter() - started})
    elif composed is not None:
        stages.append({'purpose': 'receipt_composition', 'status': composed.error.code,
                       'stage': composed.error.stage,
                       **receipt_candidate_summary,
                       'elapsed_seconds': perf_counter() - started})
    record = {
        'schema_version': 1,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'endpoint': ENDPOINT,
        'model_tag': MODEL_TAG,
        'model_digest': MODEL_DIGEST,
        'quantization': QUANTIZATION,
        'generation_token_limit': 2048,
        'serialized_json_character_limit': 16384,
        'dialogue_codepoint_limit': 600,
        'context_fixture': 'backend/tests/fixtures/conversation/t05-valid.json',
        'context_fixture_sha256': hashlib.sha256(
            (ROOT / 'backend/tests/fixtures/conversation/t05-valid.json').read_bytes()).hexdigest(),
        'model': model,
        'stages': stages,
        'note': 'Direct structured adapter screen only; no application, database, or game state ports.',
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    accepted = all(stage['status'] in {'TurnProposal', 'CandidateReply'} and
                   stage.get('segment_count', 0) > 0 for stage in stages[:3])
    receipt_stage = stages[3]
    accepted = accepted and receipt_stage['status'] == 'CandidateReply' and receipt_stage.get('receipt_slots') == 1
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
