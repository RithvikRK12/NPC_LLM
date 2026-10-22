#!/usr/bin/env python3
"""Local-only dialogue shadow experiment; it has no game or persistence ports."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import platform
from pathlib import Path
import resource
import sys
from time import perf_counter
from urllib.parse import urlsplit, urlunsplit
import uuid

import httpx

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'backend'))

from app.config.settings import get_settings  # noqa: E402
from app.services.conversation.quality_experiments import (  # noqa: E402
    ExperimentManifest, SampleOutcome, build_scoring_rows, manifest_json,
    validate_manifest, write_blind_form, write_prompt_snapshot,
)
from app.services.conversation.shadow import ShadowTurnInput  # noqa: E402

FIXTURE = ROOT / 'backend/tests/fixtures/conversation/baseline-evaluation-v1.json'
FOCUSED = ROOT / 'backend/tests/fixtures/conversation/response-quality-focused-v2.json'
BASELINE_RESULTS = ROOT / 'docs/evidence/conversation-redesign-release/t01/configured-replay-results.json'
HISTORICAL_RUNNER = ROOT / 'docs/evidence/conversation-redesign-release/t01/configured_replay.py'


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument('--fixture', type=Path, default=FIXTURE,
                       help='frozen 44-scenario fixture JSON')
    value.add_argument('--baseline-results', type=Path, default=BASELINE_RESULTS,
                       help='frozen dialogue-only results used for fixed-context history')
    value.add_argument('--selection', choices=('smoke', 'full'), default='smoke',
                       help='24-turn focused smoke, including recall controls, or all 176 turns')
    value.add_argument('--mode', choices=('fixed_context', 'closed_loop'), required=True,
                       help='freeze recorded prior replies or accumulate this run’s replies')
    value.add_argument('--prompt-variant', choices=('t04', 'updated_profiles', 'improved_guidance'),
                       required=True, help='recorded dialogue-shadow prompt variant')
    value.add_argument('--endpoint', required=True,
                       help='credential-free loopback OpenAI-compatible endpoint')
    value.add_argument('--model-tag', required=True, help='exact installed local model tag')
    value.add_argument('--model-digest', required=True, help='exact installed local SHA-256 digest')
    value.add_argument('--quantization', required=True, help='exact installed quantization label')
    value.add_argument('--context-size', type=int, required=True, help='configured model context size')
    value.add_argument('--generation-limit-tokens', type=int, required=True,
                       help='bounded provider output token ceiling')
    value.add_argument('--serialized-contract-limit-characters', type=int, required=True,
                       help='bounded JSON response character ceiling')
    value.add_argument('--dialogue-limit-codepoints', type=int, default=240,
                       help='final dialogue ceiling in Unicode code points')
    value.add_argument('--condition', choices=('cold', 'warm'), required=True,
                       help='declared model load condition')
    value.add_argument('--repetition', type=int, required=True, help='positive repeat index')
    value.add_argument('--blind-label', choices=tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), required=True,
                       help='anonymous reviewer label, such as A or B')
    value.add_argument('--output-dir', type=Path, required=True,
                       help='new run directory; populated directories are rejected')
    value.add_argument('--timeout-seconds', type=float, default=120.0,
                       help='local request timeout; credentials remain in safe settings')
    value.add_argument('--hardware-description', default='Apple M5, 16 GB unified memory',
                       help='non-secret hardware description recorded in the manifest')
    return value


def _digest(value) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode()).hexdigest()


def _local_endpoint(endpoint: str) -> tuple[str, str]:
    parts = urlsplit(endpoint)
    if (parts.scheme not in {'http', 'https'} or parts.hostname not in {'localhost', '127.0.0.1', '::1'}
            or parts.username is not None or parts.password is not None or parts.query or parts.fragment):
        raise ValueError('endpoint must be a credential-free loopback URL')
    safe = urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip('/'), '', ''))
    path = parts.path.rstrip('/')
    if path.endswith('/v1'):
        path = path[:-3]
    origin = urlunsplit((parts.scheme, parts.netloc, path, '', '')).rstrip('/')
    return safe, origin


def verify_local_model(endpoint: str, model_tag: str, model_digest: str, quantization: str,
                       timeout: float) -> tuple[str, str]:
    safe, origin = _local_endpoint(endpoint)
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout, connect=min(timeout, 5.0))) as client:
            tags_response = client.get(origin + '/api/tags')
            tags_response.raise_for_status()
            version_response = client.get(origin + '/api/version')
            version_response.raise_for_status()
        models = tags_response.json().get('models', [])
        model = next((row for row in models if row.get('name') == model_tag), None)
        details = model.get('details', {}) if isinstance(model, dict) else {}
        actual_quantization = details.get('quantization_level') if isinstance(details, dict) else None
        if model is None or model.get('digest') != model_digest.removeprefix('sha256:'):
            raise ValueError('installed local model tag/digest does not match the requested identity')
        if actual_quantization != quantization:
            raise ValueError('installed local model quantization does not match the requested identity')
        version = version_response.json().get('version')
        if not isinstance(version, str) or not version:
            raise ValueError('local provider version is unavailable')
        return safe, version
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise RuntimeError('local model identity could not be verified') from None


def read_running_model(endpoint: str, model_tag: str, model_digest: str,
                       timeout: httpx.Timeout) -> dict:
    """Read active Ollama allocation; model max context is not runtime context."""
    _, origin = _local_endpoint(endpoint)
    response = httpx.get(origin + '/api/ps', timeout=timeout)
    response.raise_for_status()
    rows = response.json().get('models', [])
    model = next((row for row in rows if row.get('name') == model_tag), None)
    if not isinstance(model, dict) or model.get('digest') != model_digest.removeprefix('sha256:'):
        raise ValueError('the pinned model is not present in the local running-model report')
    context_size = model.get('context_length')
    if type(context_size) is not int or context_size <= 0:
        raise ValueError('the local provider did not report the active context size')
    return {
        'context_size': context_size,
        'model_size_bytes': model.get('size'),
        'model_size_vram_bytes': model.get('size_vram'),
    }


def _load_historical_runner():
    spec = importlib.util.spec_from_file_location('historical_configured_replay', HISTORICAL_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError('dialogue-shadow prompt adapter is unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _selected_scenarios(fixture: dict, selection: str) -> tuple[dict, ...]:
    if selection == 'full':
        return tuple(fixture['scenarios'])
    focused = json.loads(FOCUSED.read_text())
    by_id = {str(row['id']): row for row in fixture['scenarios']}
    selected = tuple(dict.fromkeys(ref.rsplit(':', 1)[0] for ref in focused['sample_refs']))
    if len(selected) != 6 or any(value not in by_id for value in selected):
        raise ValueError('focused selection no longer matches the frozen fixture')
    return tuple(by_id[value] for value in selected)


def _previous_history(scenario: dict, turn_index: int, baseline_turns: dict,
                     candidate_dialogue: dict, mode: str) -> tuple[tuple[str, str], ...]:
    history = [(str(row.get('speaker', 'unknown')), str(row.get('text', '')))
               for row in scenario['initial_state'].get('visible_history', ())]
    for previous in scenario['turns'][:turn_index]:
        turn_id = str(previous['id'])
        scenario_id = scenario['id']
        if mode == 'fixed_context':
            dialogue = baseline_turns.get((scenario_id, turn_id))
        else:
            dialogue = candidate_dialogue.get((scenario_id, turn_id))
        if dialogue is None:
            continue
        history.extend((('player', previous['player_input']), ('npc', dialogue)))
    return tuple(history)


def request_dialogue(transport, request_url: str, payload: dict, headers: dict,
                     timeout: httpx.Timeout, *, sample_ref: str, player_text: str,
                     history: tuple, input_sha256: str, dialogue_limit: int,
                     contract_limit: int) -> SampleOutcome:
    """Make one bounded dialogue-only request; provider failures stay explicit."""
    started = perf_counter()
    try:
        response = transport.post(request_url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        body = response.json()
        content = body['choices'][0]['message']['content']
        if not isinstance(content, str) or len(content) > contract_limit:
            raise ValueError('serialized response exceeded its configured character bound')
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError('duplicate JSON key')
                result[key] = value
            return result
        decoded = json.loads(content, object_pairs_hook=unique)
        if not isinstance(decoded, dict) or set(decoded) != {'dialogue'}:
            raise ValueError('provider output violates the dialogue-only schema')
        dialogue = decoded['dialogue']
        if not isinstance(dialogue, str) or not dialogue.strip():
            raise ValueError('provider output has no dialogue')
        if len(dialogue) > dialogue_limit:
            raise ValueError('dialogue exceeded its configured code-point bound')
        elapsed = perf_counter() - started
        usage = body.get('usage') or {}
        choice = body['choices'][0]
        return SampleOutcome(sample_ref=sample_ref, status='generated', origin='generated',
            dialogue=dialogue, error_category=None, elapsed_seconds=elapsed,
            available_tokens=usage.get('completion_tokens'), finish_reason=choice.get('finish_reason'),
            call_count=1,
            cutoff_suspected=(choice.get('finish_reason') == 'length' or len(dialogue) >= dialogue_limit),
            player_text=player_text, history=history, input_sha256=input_sha256)
    except Exception as exc:
        elapsed = perf_counter() - started
        category = 'timeout' if isinstance(exc, (httpx.TimeoutException, TimeoutError)) else type(exc).__name__
        status = ('provider_error' if isinstance(exc, (httpx.HTTPError, TimeoutError,
                 ConnectionError, OSError)) else 'invalid_output')
        return SampleOutcome(sample_ref=sample_ref, status=status, origin=None,
            dialogue=None, error_category=category, elapsed_seconds=elapsed, call_count=1,
            player_text=player_text, history=history, input_sha256=input_sha256)


def _run(args) -> dict:
    if args.output_dir.exists() and (not args.output_dir.is_dir() or any(args.output_dir.iterdir())):
        raise ValueError('run output directory is populated or not a directory')
    if (args.timeout_seconds <= 0 or args.repetition <= 0 or args.context_size <= 0 or
            not 1 <= args.generation_limit_tokens <= 16384 or
            not 1 <= args.serialized_contract_limit_characters <= 65536 or
            not 1 <= args.dialogue_limit_codepoints <= 600):
        raise ValueError('timeout, repetition, and bounded generation settings are invalid')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fixture_bytes = args.fixture.read_bytes()
    fixture = json.loads(fixture_bytes)
    baseline = json.loads(args.baseline_results.read_text())
    if baseline.get('fixture_sha256') != sha256(fixture_bytes).hexdigest():
        raise ValueError('baseline replay and fixture hashes do not match')
    safe_endpoint, provider_version = verify_local_model(args.endpoint, args.model_tag,
        args.model_digest, args.quantization, args.timeout_seconds)
    current = get_settings()
    timeout = httpx.Timeout(args.timeout_seconds, connect=min(args.timeout_seconds, 5.0))
    headers = {'Authorization': f'Bearer {current.llm_api_key}'} if current.llm_api_key else {}
    adapter = _load_historical_runner()
    raw_turns = {(row['scenario_id'], row['turn_id']): row.get('dialogue')
                 for row in baseline.get('turns', ())}
    scenarios = _selected_scenarios(fixture, args.selection)
    selected_refs = tuple(f"{scenario['id']}:{turn['id']}" for scenario in scenarios
                          for turn in scenario['turns'])
    started = datetime.now(timezone.utc)
    candidate_dialogue: dict[tuple[str, str], str] = {}
    outcomes: list[SampleOutcome] = []
    prompts = []
    candidate_identity = str(uuid.uuid4())
    before_state = _digest([scenario['initial_state'] for scenario in scenarios])
    began = perf_counter()

    for scenario in scenarios:
        for index, turn in enumerate(scenario['turns']):
            scenario_id, turn_id = scenario['id'], str(turn['id'])
            events = [*turn.get('events_before', ())]
            events.extend(event for event in scenario.get('external_events', ())
                          if str(event.get('before_turn_id')) == turn_id)
            history = _previous_history(scenario, index, raw_turns,
                                        candidate_dialogue, args.mode)
            shadow_turn = ShadowTurnInput(scenario_id=scenario_id, turn_id=turn_id,
                npc_role=scenario['npc']['role'], player_text=turn['player_input'],
                initial_state=scenario['initial_state'], history=history,
                model_settings={'model': args.model_tag, 'temperature': 0.2},
                events_before=tuple(events))
            updated = args.prompt_variant in {'updated_profiles', 'improved_guidance'}
            improved = args.prompt_variant == 'improved_guidance'
            prompt = adapter.build_prompt(shadow_turn, use_updated_profiles=updated,
                                          improved_guidance=improved)
            prompt_path = write_prompt_snapshot(args.output_dir / 'prompts',
                                                f'{scenario_id}:{turn_id}', prompt)
            prompts.append({'sample_ref': f'{scenario_id}:{turn_id}',
                            'prompt_sha256': sha256(prompt.encode()).hexdigest(),
                            'snapshot': str(prompt_path.relative_to(args.output_dir))})
            output_limit = args.dialogue_limit_codepoints
            payload = adapter.build_payload(shadow_turn, args.model_tag, output_limit, updated, improved)
            payload['max_tokens'] = args.generation_limit_tokens
            payload['response_format']['json_schema']['schema']['properties']['dialogue']['maxLength'] = output_limit
            sample_ref = f'{scenario_id}:{turn_id}'
            input_sha = _digest({'prompt': prompt, 'history': history, 'player': turn['player_input']})
            outcome = request_dialogue(httpx, safe_endpoint.rstrip('/') + '/chat/completions',
                payload, headers, timeout, sample_ref=sample_ref, player_text=turn['player_input'],
                history=history, input_sha256=input_sha,
                dialogue_limit=output_limit,
                contract_limit=args.serialized_contract_limit_characters)
            outcomes.append(outcome)
            if outcome.status == 'generated':
                candidate_dialogue[(scenario_id, turn_id)] = outcome.dialogue

    finished = datetime.now(timezone.utc)
    after_state = _digest([scenario['initial_state'] for scenario in scenarios])
    if before_state != after_state:
        raise RuntimeError('read-only experiment state changed')
    runtime_resources = read_running_model(args.endpoint, args.model_tag,
                                           args.model_digest, timeout)
    if runtime_resources['context_size'] != args.context_size:
        (args.output_dir / 'context-mismatch.json').write_text(json.dumps({
            'requested_context_size': args.context_size,
            'observed_context_size': runtime_resources['context_size'],
            'model_tag': args.model_tag,
            'model_digest': args.model_digest,
        }, indent=2) + '\n', encoding='utf-8', newline='\n')
        raise ValueError('requested context size differs from the active Ollama context; run evidence is incomplete')
    profile_hash = _digest({role: sha256((ROOT / 'backend/app/services/context/characters' / f'{role}.json').read_bytes()).hexdigest()
                            for role in ('craftsman', 'gatherer')})
    schema = {'dialogue': {'type': 'string', 'maximum': args.dialogue_limit_codepoints}}
    prompt_hash = _digest({'runner_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
                           'historical_prompt_adapter_sha256': sha256(HISTORICAL_RUNNER.read_bytes()).hexdigest(),
                           'variant': args.prompt_variant})
    prompt_snapshot_hash = _digest([row['prompt_sha256'] for row in prompts])
    context_hash = _digest([row.input_sha256 for row in outcomes])
    manifest = ExperimentManifest(schema_version=1, run_id=candidate_identity,
        input_mode=args.mode, dataset_sha256=sha256(fixture_bytes).hexdigest(),
        sample_refs=selected_refs, prompt_sha256=prompt_hash,
        prompt_snapshot_set_sha256=prompt_snapshot_hash, profile_sha256=profile_hash,
        schema_sha256=_digest(schema), context_sha256=context_hash, endpoint=safe_endpoint,
        model_tag=args.model_tag, model_digest=args.model_digest, quantization=args.quantization,
        provider_version=provider_version, temperature=0.2, seed=None,
        context_size=args.context_size, dialogue_limit_codepoints=args.dialogue_limit_codepoints,
        serialized_contract_limit_characters=args.serialized_contract_limit_characters,
        generation_limit_tokens=args.generation_limit_tokens,
        hardware=args.hardware_description, condition=args.condition, repetition=args.repetition,
        started_at=started.isoformat(), ended_at=finished.isoformat())
    validate_manifest(manifest)
    (args.output_dir / 'manifest.json').write_text(manifest_json(manifest) + '\n', encoding='utf-8',
                                                    newline='\n')
    run_rows = [{field: getattr(row, field) for field in row.__dataclass_fields__}
                for row in outcomes]
    (args.output_dir / 'outcomes.json').write_text(json.dumps(run_rows, ensure_ascii=False, indent=2) + '\n',
                                                     encoding='utf-8', newline='\n')
    (args.output_dir / 'prompt-index.json').write_text(json.dumps(prompts, ensure_ascii=False, indent=2) + '\n',
                                                         encoding='utf-8', newline='\n')
    scored_refs = {ref for rubric in fixture['scoring_plan']['dimensions'].values()
                   for ref in rubric['denominator_turns']}
    score_rows = build_scoring_rows(
        fixture, [row for row in outcomes if row.sample_ref in scored_refs])
    (args.output_dir / 'scoring-samples.json').write_text(json.dumps(score_rows, ensure_ascii=False, indent=2) + '\n',
                                                           encoding='utf-8', newline='\n')
    for dimension, rows in score_rows.items():
        write_blind_form(args.output_dir / f'blind-{dimension}.json', args.blind_label, rows)
    summary = {
        'origin': 'dialogue_shadow_generated', 'mode': args.mode,
        'sample_count': len(outcomes), 'generated': sum(row.status == 'generated' for row in outcomes),
        'missing_or_error': sum(row.status != 'generated' for row in outcomes),
        'cutoff_suspected': sum(row.cutoff_suspected for row in outcomes),
        'cutoff_suspected_refs': [row.sample_ref for row in outcomes if row.cutoff_suspected],
        'elapsed_wall_seconds': perf_counter() - began,
        'python_process_peak_rss_platform_units': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'ollama_model_size_bytes': runtime_resources['model_size_bytes'],
        'ollama_model_size_vram_bytes': runtime_resources['model_size_vram_bytes'],
        'ollama_active_context_size': runtime_resources['context_size'],
        'initial_state_digest': before_state, 'final_state_digest': after_state,
        'run_id': candidate_identity, 'prompt_variant': args.prompt_variant,
        'note': 'Dialogue shadow only; this is not the structured production path.',
    }
    (args.output_dir / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
                                                   encoding='utf-8', newline='\n')
    return summary


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        print(json.dumps(_run(args), ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError, OSError, httpx.HTTPError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
