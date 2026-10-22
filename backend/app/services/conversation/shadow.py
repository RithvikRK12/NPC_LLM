"""Read-only conversation replay primitives for evaluation shadow runs."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from time import perf_counter
from types import MappingProxyType
from typing import Any, Callable, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _digest(value: Any) -> str:
    def plain(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {key: plain(val) for key, val in item.items()}
        if isinstance(item, tuple):
            return [plain(val) for val in item]
        return item
    payload = json.dumps(plain(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return sha256(payload.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class ShadowTurnInput:
    scenario_id: str
    turn_id: str
    npc_role: str
    player_text: str
    initial_state: Mapping[str, Any]
    history: tuple[tuple[str, str], ...]
    model_settings: Mapping[str, Any]
    events_before: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class ShadowCandidate:
    dialogue: str | None
    origin: str = 'generated'
    action_candidate: str | None = None
    error_type: str | None = None


@dataclass(frozen=True)
class ShadowTurnResult:
    scenario_id: str
    turn_id: str
    dialogue: str | None
    origin: str
    elapsed_seconds: float
    action_candidate: str | None = None
    error_type: str | None = None
    operation_executed: bool = False
    canon_published: bool = False
    interaction_written: bool = False
    player_text: str = ''
    history: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ShadowRun:
    turns: tuple[ShadowTurnResult, ...]
    origins: Mapping[str, int]
    initial_state_digest: str
    final_state_digest: str
    model_settings_digest: str


@dataclass(frozen=True)
class ShadowScenario:
    scenario_id: str
    npc_role: str
    initial_state: Mapping[str, Any]
    turns: tuple[Mapping[str, Any], ...]
    expected_mechanics: Mapping[str, Any]
    external_events: tuple[Mapping[str, Any], ...] = ()

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> 'ShadowScenario':
        turns = tuple(_freeze(dict(turn)) for turn in row['turns'])
        if not 4 <= len(turns) <= 8:
            raise ValueError('shadow scenarios require four to eight turns')
        mechanics = _freeze(dict(row['expected_mechanics']))
        npc = row.get('npc', {})
        return cls(str(row.get('scenario_id', row.get('id'))), str(row.get('npc_role', npc.get('role'))),
                   _freeze(dict(row['initial_state'])), turns, mechanics,
                   tuple(_freeze(dict(event)) for event in row.get('external_events', ())))


class ShadowReplayRunner:
    """Runs generated candidates against frozen inputs; exposes no write ports."""
    def __init__(self, generate: Callable[[ShadowTurnInput], ShadowCandidate],
                 model_settings: Mapping[str, Any] | None = None):
        self._generate = generate
        self._model_settings = _freeze(dict(model_settings or {}))

    def run(self, scenarios: tuple[ShadowScenario, ...] | list[ShadowScenario]) -> ShadowRun:
        rows: list[ShadowTurnResult] = []
        origins: Counter[str] = Counter()
        before = _digest(tuple(s.initial_state for s in scenarios))
        for scenario in scenarios:
            history: list[tuple[str, str]] = [
                (str(item.get('speaker', 'unknown')), str(item.get('text', '')))
                for item in scenario.initial_state.get('visible_history', ())
            ]
            for index, turn in enumerate(scenario.turns):
                turn_id = str(turn.get('turn_id', turn.get('id', index + 1)))
                events_before = [*turn.get('events_before', ())]
                events_before.extend(event for event in scenario.external_events
                                     if str(event.get('before_turn_id')) == turn_id)
                request = ShadowTurnInput(scenario.scenario_id, turn_id, scenario.npc_role,
                                          str(turn.get('player_text', turn.get('player_input'))), scenario.initial_state,
                                          tuple(history), self._model_settings,
                                          tuple(_freeze(dict(event)) for event in events_before))
                started = perf_counter()
                try:
                    candidate = self._generate(request)
                except Exception as exc:
                    candidate = ShadowCandidate(None, origin='provider_error', error_type=type(exc).__name__)
                elapsed = perf_counter() - started
                origins[candidate.origin] += 1
                rows.append(ShadowTurnResult(scenario.scenario_id, turn_id, candidate.dialogue,
                                             candidate.origin, elapsed, candidate.action_candidate,
                                             candidate.error_type, player_text=request.player_text,
                                             history=request.history))
                if candidate.dialogue is not None:
                    history.extend((('player', str(turn.get('player_text', turn.get('player_input')))),
                                    ('npc', candidate.dialogue)))
        after = _digest(tuple(s.initial_state for s in scenarios))
        return ShadowRun(tuple(rows), MappingProxyType(origins), before, after,
                         _digest(self._model_settings))


def build_quality_samples(fixture: Mapping[str, Any], run: ShadowRun) -> Mapping[str, tuple[Mapping[str, Any], ...]]:
    """Join replay outputs to the frozen per-dimension score denominators.

    Missing model outputs remain explicit rows so provider failures cannot silently
    shrink a score denominator. Scenario paraphrases are not synthesized here;
    only the frozen turn references are scored.
    """
    results = {(turn.scenario_id, turn.turn_id): turn for turn in run.turns}
    scenarios = {str(row.get('id', row.get('scenario_id'))): row
                 for row in fixture['scenarios']}
    output: dict[str, tuple[Mapping[str, Any], ...]] = {}
    for dimension, rubric in fixture['scoring_plan']['dimensions'].items():
        samples: list[Mapping[str, Any]] = []
        for sample_ref in rubric['denominator_turns']:
            scenario_id, turn_id = str(sample_ref).rsplit(':', 1)
            scenario = scenarios.get(scenario_id)
            turn = results.get((scenario_id, turn_id))
            if scenario is None:
                raise ValueError(f'unknown frozen score reference: {sample_ref}')
            if turn is None:
                samples.append(MappingProxyType({
                    'sample_ref': sample_ref, 'dimension': dimension,
                    'status': 'missing_replay_turn', 'npc_role': scenario['npc']['role'],
                    'player_text': None, 'history': (), 'candidate_dialogue': None,
                    'candidate_origin': None, 'anchors': _freeze(dict(rubric['anchors'])),
                }))
                continue
            samples.append(MappingProxyType({
                'sample_ref': sample_ref, 'dimension': dimension,
                'status': 'scorable' if turn.dialogue is not None else 'missing_candidate',
                'npc_role': scenario['npc']['role'], 'player_text': turn.player_text,
                'history': turn.history, 'candidate_dialogue': turn.dialogue,
                'candidate_origin': turn.origin, 'anchors': _freeze(dict(rubric['anchors'])),
            }))
        output[dimension] = tuple(samples)
    return MappingProxyType(output)


def quadratic_weighted_kappa(left: list[int] | tuple[int, ...],
                             right: list[int] | tuple[int, ...],
                             low: int = 1, high: int = 5) -> float | None:
    """Return quadratic weighted Cohen's kappa for two ordinal review vectors."""
    if len(left) != len(right):
        raise ValueError('review vectors must have equal length')
    if len(left) < 2:
        return None
    if low >= high or any(type(score) is not int or not low <= score <= high
                          for score in (*left, *right)):
        raise ValueError('review scores must be integers within the configured scale')
    categories = tuple(range(low, high + 1))
    size = len(left)
    observed = sum(((a - b) / (high - low)) ** 2 for a, b in zip(left, right)) / size
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum(
        (left_counts[a] * right_counts[b] / (size * size)) * ((a - b) / (high - low)) ** 2
        for a in categories for b in categories
    )
    if expected == 0:
        return 1.0 if observed == 0 else 0.0
    return 1.0 - observed / expected
