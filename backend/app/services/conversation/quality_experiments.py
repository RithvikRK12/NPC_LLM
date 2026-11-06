"""Immutable, local-only records and compatibility checks for response studies.

These records intentionally expose no game mutation, persistence, consent, or
finalization ports. Live orchestration belongs in the evidence runner.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
import math
import json
from pathlib import Path
import re
from typing import Literal
from urllib.parse import urlsplit

_SHA256 = re.compile(r'^(?:sha256:)?[0-9a-f]{64}$')
_LOCAL_HOSTS = {'localhost', '127.0.0.1', '::1'}
_FIXED_DENOMINATORS = {
    'directness': 44,
    'coverage': 12,
    'continuity': 16,
    'character_consistency': 44,
    'grounding': 44,
    'naturalness': 88,
}


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    schema_version: int
    run_id: str
    input_mode: Literal['fixed_context', 'closed_loop']
    dataset_sha256: str
    sample_refs: tuple[str, ...]
    prompt_sha256: str
    prompt_snapshot_set_sha256: str
    profile_sha256: str
    schema_sha256: str
    context_sha256: str
    endpoint: str
    model_tag: str
    model_digest: str
    quantization: str
    provider_version: str
    temperature: float
    seed: int | None
    context_size: int
    dialogue_limit_codepoints: int
    serialized_contract_limit_characters: int
    generation_limit_tokens: int
    hardware: str
    condition: Literal['cold', 'warm']
    repetition: int
    started_at: str
    ended_at: str


@dataclass(frozen=True, slots=True)
class SampleOutcome:
    sample_ref: str
    status: Literal['generated', 'missing_output', 'provider_error', 'invalid_output']
    origin: Literal['generated', 'repaired', 'fallback', 'mock'] | None
    dialogue: str | None
    error_category: str | None
    elapsed_seconds: float | None
    available_tokens: int | None = None
    finish_reason: str | None = None
    call_count: int = 1
    cutoff_suspected: bool = False
    player_text: str | None = None
    history: tuple[tuple[str, str], ...] = ()
    input_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.sample_ref:
            raise ValueError('sample reference is required')
        if self.status == 'generated' and (self.dialogue is None or self.origin is None):
            raise ValueError('generated outcomes require dialogue and origin')
        if self.status != 'generated' and self.dialogue is not None:
            raise ValueError('failed outcomes cannot carry candidate dialogue')
        if self.elapsed_seconds is not None and self.elapsed_seconds < 0:
            raise ValueError('elapsed time cannot be negative')
        if self.available_tokens is not None and self.available_tokens < 0:
            raise ValueError('token usage cannot be negative')
        if self.call_count < 0:
            raise ValueError('call count cannot be negative')


@dataclass(frozen=True, slots=True)
class ExperimentRun:
    manifest: ExperimentManifest
    outcomes: tuple[SampleOutcome, ...]

    def __post_init__(self) -> None:
        if len({value.sample_ref for value in self.outcomes}) != len(self.outcomes):
            raise ValueError('run outcomes must have unique sample references')
        if any(value.sample_ref not in self.manifest.sample_refs for value in self.outcomes):
            raise ValueError('run outcome is outside the manifest sample set')


@dataclass(frozen=True, slots=True)
class ComparisonReport:
    left_run_id: str
    right_run_id: str
    sample_count: int
    left_missing: int
    right_missing: int
    latency_comparable: bool
    changed_model_identity: bool
    changed_compatibility_settings: tuple[str, ...]
    input_snapshots_identical: bool


def validate_manifest(manifest: ExperimentManifest, *, output_directory: Path | None = None) -> None:
    if not isinstance(manifest, ExperimentManifest):
        raise ValueError('experiment manifest has an unsupported shape')
    if manifest.schema_version != 1 or not manifest.run_id:
        raise ValueError('manifest version and run ID are required')
    if not manifest.sample_refs or len(set(manifest.sample_refs)) != len(manifest.sample_refs):
        raise ValueError('manifest sample references must be nonempty and unique')
    for name in ('dataset_sha256', 'prompt_sha256', 'prompt_snapshot_set_sha256', 'profile_sha256',
                 'schema_sha256', 'context_sha256'):
        if not _SHA256.fullmatch(getattr(manifest, name)):
            raise ValueError(f'{name} must be a SHA-256 digest')
    if (not manifest.model_tag or not _SHA256.fullmatch(manifest.model_digest) or
            not manifest.quantization):
        raise ValueError('exact model tag, model digest, and quantization are required')
    if not manifest.provider_version or not manifest.hardware:
        raise ValueError('provider version and hardware description are required')
    try:
        parsed = urlsplit(manifest.endpoint)
        host = parsed.hostname
    except ValueError as exc:
        raise ValueError('endpoint is invalid') from exc
    if (parsed.scheme not in {'http', 'https'} or host not in _LOCAL_HOSTS or
            parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment):
        raise ValueError('inference must use a credential-free local endpoint')
    if (type(manifest.temperature) not in {int, float} or not math.isfinite(manifest.temperature) or
            not 0 <= manifest.temperature <= 2 or type(manifest.context_size) is not int or
            manifest.context_size <= 0 or type(manifest.dialogue_limit_codepoints) is not int or
            not 1 <= manifest.dialogue_limit_codepoints <= 600):
        raise ValueError('manifest generation bounds are invalid')
    if (manifest.serialized_contract_limit_characters <= 0 or
            manifest.serialized_contract_limit_characters > 65536):
        raise ValueError('serialized contract character limit is invalid')
    if manifest.generation_limit_tokens <= 0 or manifest.generation_limit_tokens > 16384:
        raise ValueError('generation token limit is invalid')
    if manifest.repetition <= 0:
        raise ValueError('repetition index must be positive')
    try:
        start = datetime.fromisoformat(manifest.started_at.replace('Z', '+00:00'))
        end = datetime.fromisoformat(manifest.ended_at.replace('Z', '+00:00'))
    except (TypeError, ValueError) as exc:
        raise ValueError('manifest timestamps must be ISO-8601') from exc
    if end < start:
        raise ValueError('manifest end timestamp precedes start timestamp')
    if output_directory is not None and output_directory.exists():
        if not output_directory.is_dir() or any(output_directory.iterdir()):
            raise ValueError('run output directory is populated or not a directory')


def compare_compatible_runs(left: ExperimentRun, right: ExperimentRun) -> ComparisonReport:
    validate_manifest(left.manifest)
    validate_manifest(right.manifest)
    a, b = left.manifest, right.manifest
    if a.sample_refs != b.sample_refs:
        raise ValueError('sample order differs between runs')
    if a.input_mode != b.input_mode:
        raise ValueError('input mode differs between runs')
    for name in ('dataset_sha256', 'prompt_sha256', 'profile_sha256', 'schema_sha256',
                 'endpoint', 'temperature', 'seed', 'dialogue_limit_codepoints',
                 'serialized_contract_limit_characters', 'generation_limit_tokens', 'provider_version',
                 'condition'):
        if getattr(a, name) != getattr(b, name):
            raise ValueError(f'{name.replace("_", " ")} differs between model-only runs')
    input_snapshots_identical = (a.prompt_snapshot_set_sha256 == b.prompt_snapshot_set_sha256 and
                                 a.context_sha256 == b.context_sha256)
    if a.input_mode == 'fixed_context' and not input_snapshots_identical:
        raise ValueError('fixed-context input snapshots differ between model-only runs')
    changed_model = (a.model_tag, a.model_digest, a.quantization) != (b.model_tag, b.model_digest, b.quantization)
    if not changed_model:
        raise ValueError('model-only comparison requires different pinned model identities')
    left_rows = {value.sample_ref: value for value in left.outcomes}
    right_rows = {value.sample_ref: value for value in right.outcomes}
    count = len(a.sample_refs)
    changed_compatibility = ('context_size',) if a.context_size != b.context_size else ()
    return ComparisonReport(
        left_run_id=a.run_id, right_run_id=b.run_id, sample_count=count,
        left_missing=sum(ref not in left_rows or left_rows[ref].status != 'generated' for ref in a.sample_refs),
        right_missing=sum(ref not in right_rows or right_rows[ref].status != 'generated' for ref in a.sample_refs),
        latency_comparable=a.hardware == b.hardware and a.condition == b.condition,
        changed_model_identity=changed_model,
        changed_compatibility_settings=changed_compatibility,
        input_snapshots_identical=input_snapshots_identical,
    )


def history_for_mode(input_mode: str, frozen_history: tuple, accumulated_history: tuple) -> tuple:
    if input_mode == 'fixed_context':
        return tuple(frozen_history)
    if input_mode == 'closed_loop':
        return tuple(accumulated_history)
    raise ValueError('unsupported input mode')


def build_scoring_rows(fixture: dict, outcomes: tuple[SampleOutcome, ...] | list[SampleOutcome]):
    """Join outcomes to the immutable six-dimension score plan without dropping errors."""
    by_ref = {value.sample_ref: value for value in outcomes}
    if len(by_ref) != len(outcomes):
        raise ValueError('outcome sample references must be unique')
    dimensions = fixture['scoring_plan']['dimensions']
    if set(dimensions) != set(_FIXED_DENOMINATORS):
        raise ValueError('frozen scoring dimensions changed')
    frozen_refs = {ref for rubric in dimensions.values() for ref in rubric['denominator_turns']}
    if set(by_ref) - frozen_refs:
        raise ValueError('outcome sample reference is outside the frozen score plan')
    scenarios = {str(row.get('id', row.get('scenario_id'))): row for row in fixture['scenarios']}
    result = {}
    for dimension, rubric in dimensions.items():
        refs = tuple(rubric['denominator_turns'])
        if dimension in _FIXED_DENOMINATORS and len(refs) != _FIXED_DENOMINATORS[dimension]:
            raise ValueError(f'frozen {dimension} denominator changed')
        rows = []
        for ref in refs:
            scenario_id, turn_id = str(ref).rsplit(':', 1)
            if scenario_id not in scenarios:
                raise ValueError(f'unknown frozen score reference: {ref}')
            sample = by_ref.get(ref)
            turn = next((row for row in scenarios[scenario_id]['turns']
                         if str(row.get('id', row.get('turn_id'))) == turn_id), None)
            if turn is None:
                raise ValueError(f'unknown frozen turn reference: {ref}')
            rows.append({
                'sample_ref': ref, 'dimension': dimension,
                'status': ('missing_candidate' if sample is None else
                           'scorable' if sample.status == 'generated' else sample.status),
                'cutoff_suspected': bool(sample and sample.cutoff_suspected),
                'npc_role': scenarios[scenario_id]['npc']['role'],
                'player_text': sample.player_text if sample and sample.player_text is not None else turn['player_input'],
                'history': sample.history if sample else (),
                'candidate_dialogue': sample.dialogue if sample and sample.status == 'generated' else None,
                'candidate_origin': sample.origin if sample and sample.status == 'generated' else None,
                'error_category': sample.error_category if sample else 'no_output_record',
                'anchors': dict(rubric['anchors']),
            })
        result[dimension] = tuple(rows)
    return result


def blind_review_form(candidate_id: str, rows: tuple[dict, ...]) -> dict:
    """Export candidate prose and labels without model or run identity."""
    if re.fullmatch(r'[A-Z]', candidate_id or '') is None or not rows:
        raise ValueError('blind form requires a candidate label and samples')
    return {
        'schema_version': 1,
        'candidate_label': candidate_id,
        'samples': tuple({key: row[key] for key in ('sample_ref', 'dimension', 'status',
                       'npc_role', 'player_text', 'history', 'candidate_dialogue', 'anchors')
                          if key in row} for row in rows),
    }


def manifest_json(manifest: ExperimentManifest) -> str:
    validate_manifest(manifest)
    return json.dumps({field.name: getattr(manifest, field.name) for field in fields(manifest)},
                      ensure_ascii=False, sort_keys=True, indent=2)


def write_prompt_snapshot(directory: Path, sample_ref: str, prompt: str) -> Path:
    """Create an immutable per-sample prompt snapshot using exclusive creation."""
    if not sample_ref or not isinstance(prompt, str) or not prompt:
        raise ValueError('prompt snapshot requires a sample reference and nonempty text')
    safe_name = re.sub(r'[^A-Za-z0-9_.-]+', '_', sample_ref).strip('._')
    if not safe_name:
        raise ValueError('sample reference cannot form a snapshot filename')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f'{safe_name}.prompt.txt'
    try:
        with target.open('x', encoding='utf-8', newline='') as handle:
            handle.write(prompt)
            handle.write('\n')
    except FileExistsError as exc:
        raise ValueError('prompt snapshot already exists; refusing overwrite') from exc
    return target


def write_blind_form(path: Path, candidate_label: str, rows: tuple[dict, ...]) -> Path:
    form = blind_review_form(candidate_label, rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x', encoding='utf-8', newline='') as handle:
            handle.write(json.dumps(form, ensure_ascii=False, indent=2))
            handle.write('\n')
    except FileExistsError as exc:
        raise ValueError('blind form already exists; refusing overwrite') from exc
    return path
