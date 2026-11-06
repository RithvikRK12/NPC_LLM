"""Behavioral contracts for the isolated, local-only quality experiment records."""
import unittest
import json
import importlib.util
from pathlib import Path
import tempfile
import httpx
from unittest.mock import patch

from app.services.conversation.quality_experiments import (
    ExperimentManifest,
    ExperimentRun,
    SampleOutcome,
    build_scoring_rows,
    blind_review_form,
    compare_compatible_runs,
    history_for_mode,
    validate_manifest,
    write_prompt_snapshot,
)


FIXTURE = Path(__file__).parent / 'fixtures/conversation/baseline-evaluation-v1.json'
FOCUSED_FIXTURE = Path(__file__).parent / 'fixtures/conversation/response-quality-focused-v2.json'
RUNNER_PATH = Path(__file__).parents[2] / 'docs/evidence/llm-response-improvement/run_experiment.py'
RUNNER_SPEC = importlib.util.spec_from_file_location('llm_response_quality_runner', RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(RUNNER)


def manifest(**updates):
    values = dict(
        schema_version=1, run_id='run-a', input_mode='fixed_context',
        dataset_sha256='a' * 64, sample_refs=('craftsman-01:t2', 'gatherer-04:t2'),
        prompt_sha256='b' * 64, prompt_snapshot_set_sha256='f' * 64,
        profile_sha256='c' * 64, schema_sha256='d' * 64,
        context_sha256='e' * 64, endpoint='http://127.0.0.1:11434/v1',
        model_tag='model:exact', model_digest='sha256:' + '1' * 64,
        quantization='Q4_K_M', provider_version='ollama-0.34.2', temperature=0.2,
        seed=None, context_size=8192, dialogue_limit_codepoints=600,
        serialized_contract_limit_characters=16384, generation_limit_tokens=2048,
        hardware='Apple M5, 16 GB unified memory', condition='warm', repetition=1,
        started_at='2026-10-19T12:00:00Z', ended_at='2026-10-19T12:01:00Z',
    )
    values.update(updates)
    return ExperimentManifest(**values)


class QualityExperimentTests(unittest.TestCase):
    class Response:
        def __init__(self, body, error=None):
            self.body = body
            self.error = error

        def raise_for_status(self):
            if self.error:
                raise self.error

        def json(self):
            return self.body

    class Transport:
        def __init__(self, response):
            self.response = response

        def post(self, _url, *, json, headers, timeout):
            self.payload = json
            return self.response

    def test_manifest_rejects_nonlocal_inference_endpoint(self):
        with self.assertRaisesRegex(ValueError, 'local endpoint'):
            validate_manifest(manifest(endpoint='https://api.example.test/v1'))
        with self.assertRaisesRegex(ValueError, 'loopback'):
            RUNNER._local_endpoint('http://10.0.0.4:11434/v1')

    def test_dialogue_shadow_fake_transport_records_valid_output_and_missing_errors(self):
        request = httpx.Request('POST', 'http://127.0.0.1/v1/chat/completions')
        ok = self.Transport(self.Response({'choices': [{'message': {'content': '{"dialogue":"A ripe pear."}'},
            'finish_reason': 'stop'}], 'usage': {'completion_tokens': 5}}))
        outcome = RUNNER.request_dialogue(ok, str(request.url), {}, {}, httpx.Timeout(2),
            sample_ref='gatherer-04:t2', player_text='What did you say?', history=(),
            input_sha256='a' * 64, dialogue_limit=600, contract_limit=2000)
        self.assertEqual(outcome.status, 'generated')
        self.assertEqual(outcome.dialogue, 'A ripe pear.')
        self.assertEqual(outcome.available_tokens, 5)

        missing = RUNNER.request_dialogue(self.Transport(self.Response({'choices': []})),
            str(request.url), {}, {}, httpx.Timeout(2), sample_ref='craftsman-01:t2',
            player_text='Question?', history=(), input_sha256='b' * 64,
            dialogue_limit=600, contract_limit=2000)
        self.assertEqual(missing.status, 'invalid_output')
        self.assertIsNone(missing.dialogue)

        outage = self.Transport(self.Response({}, httpx.ConnectError('private detail', request=request)))
        failed = RUNNER.request_dialogue(outage, str(request.url), {}, {}, httpx.Timeout(2),
            sample_ref='craftsman-01:t3', player_text='Question?', history=(),
            input_sha256='c' * 64, dialogue_limit=600, contract_limit=2000)
        self.assertEqual(failed.status, 'provider_error')
        self.assertEqual(failed.error_category, 'ConnectError')

    def test_dialogue_shadow_rejects_duplicate_json_keys_and_character_overflow(self):
        request_url = 'http://127.0.0.1/v1/chat/completions'
        common = dict(sample_ref='craftsman-01:t2', player_text='Question?', history=(),
                      input_sha256='d' * 64, dialogue_limit=3, contract_limit=2000)
        duplicate = self.Transport(self.Response({'choices': [{'message': {'content':
            '{"dialogue":"ok","dialogue":"no"}'}}]}))
        outcome = RUNNER.request_dialogue(duplicate, request_url, {}, {}, httpx.Timeout(2), **common)
        self.assertEqual(outcome.status, 'invalid_output')
        too_long = self.Transport(self.Response({'choices': [{'message': {'content':
            '{"dialogue":"long"}'}}]}))
        overflow = RUNNER.request_dialogue(too_long, request_url, {}, {}, httpx.Timeout(2), **common)
        self.assertEqual(overflow.status, 'invalid_output')

    def test_dialogue_shadow_preserves_valid_but_limit_reaching_output_as_cutoff_suspected(self):
        result = RUNNER.request_dialogue(
            self.Transport(self.Response({'choices': [{'message': {'content': '{"dialogue":"abcd"}'},
                'finish_reason': 'stop'}]})), 'http://127.0.0.1/v1/chat/completions', {}, {},
            httpx.Timeout(2), sample_ref='craftsman-01:t2', player_text='Question?', history=(),
            input_sha256='e' * 64, dialogue_limit=4, contract_limit=100)
        self.assertEqual(result.status, 'generated')
        self.assertEqual(result.dialogue, 'abcd')
        self.assertTrue(result.cutoff_suspected)

    def test_cli_orchestration_fake_run_writes_only_to_fresh_output_directory(self):
        class Settings:
            llm_api_key = None

        class Adapter:
            def build_prompt(self, turn, *, use_updated_profiles, improved_guidance):
                return f'{turn.npc_role}:{turn.turn_id}:{turn.player_text}'

            def build_payload(self, turn, model, max_tokens, updated, improved):
                return {'model': model, 'max_tokens': max_tokens,
                        'response_format': {'json_schema': {'schema': {'properties': {
                            'dialogue': {'maxLength': 240}}}}}}

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {'choices': [{'message': {'content': '{"dialogue":"I do not know."}'},
                                     'finish_reason': 'stop'}], 'usage': {'completion_tokens': 5}}

        class FakeProcessResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {'models': [{'name': 'fixture:local', 'digest': 'a' * 64,
                                    'context_length': 8192, 'size': 1024, 'size_vram': 1024}]}

        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / 'fresh-run'
            args = RUNNER.parser().parse_args([
                '--mode', 'fixed_context', '--prompt-variant', 't04',
                '--endpoint', 'http://127.0.0.1:11434/v1', '--model-tag', 'fixture:local',
                '--model-digest', 'a' * 64, '--quantization', 'Q4_K_M',
                '--context-size', '8192', '--generation-limit-tokens', '256',
                '--serialized-contract-limit-characters', '4096', '--condition', 'warm',
                '--repetition', '1', '--blind-label', 'A', '--output-dir', str(output),
            ])
            with patch.object(RUNNER, 'verify_local_model', return_value=(
                    'http://127.0.0.1:11434/v1', 'fake-ollama-1')) as verify, \
                 patch.object(RUNNER, 'get_settings', return_value=Settings()), \
                 patch.object(RUNNER, '_load_historical_runner', return_value=Adapter()), \
                 patch.object(RUNNER.httpx, 'post', return_value=FakeResponse()) as post, \
                 patch.object(RUNNER.httpx, 'get', return_value=FakeProcessResponse()):
                summary = RUNNER._run(args)

            self.assertEqual(summary['sample_count'], 24)
            self.assertEqual(summary['generated'], 24)
            self.assertEqual(summary['cutoff_suspected'], 0)
            self.assertEqual(post.call_count, 24)
            verify.assert_called_once()
            self.assertTrue((output / 'manifest.json').is_file())
            self.assertTrue((output / 'outcomes.json').is_file())
            self.assertTrue((output / 'prompts').is_dir())
            self.assertTrue((output / 'blind-grounding.json').is_file())
            self.assertEqual(len(tuple((output / 'prompts').iterdir())), 24)
            self.assertEqual({path.name for path in Path(root).iterdir()}, {'fresh-run'})

    def test_manifest_requires_pinned_model_identity_and_valid_generation_bounds(self):
        with self.assertRaisesRegex(ValueError, 'model digest'):
            validate_manifest(manifest(model_digest=''))
        with self.assertRaisesRegex(ValueError, 'generation token'):
            validate_manifest(manifest(generation_limit_tokens=0))

    def test_model_only_comparison_rejects_changed_prompt_or_context(self):
        left = ExperimentRun(manifest=manifest(), outcomes=())
        right = ExperimentRun(manifest=manifest(run_id='run-b', model_tag='other:exact',
            model_digest='sha256:' + '2' * 64, context_sha256='f' * 64), outcomes=())
        with self.assertRaisesRegex(ValueError, 'context'):
            compare_compatible_runs(left, right)

    def test_missing_outputs_remain_in_every_frozen_denominator(self):
        fixture = json.loads(FIXTURE.read_text())
        rows = build_scoring_rows(fixture, ())
        self.assertEqual({key: len(value) for key, value in rows.items()}, {
            'directness': 44, 'coverage': 12, 'continuity': 16,
            'character_consistency': 44, 'grounding': 44, 'naturalness': 88,
        })
        self.assertTrue(all(row['status'] == 'missing_candidate'
                            for values in rows.values() for row in values))
        extra = SampleOutcome(sample_ref='not-in-score-plan:t1', status='generated',
            origin='generated', dialogue='extra', error_category=None, elapsed_seconds=0.1)
        with self.assertRaisesRegex(ValueError, 'outside the frozen score plan'):
            build_scoring_rows(fixture, (extra,))

    def test_focused_selection_keeps_exact_twenty_four_turn_smoke_refs(self):
        focused = json.loads(FOCUSED_FIXTURE.read_text())
        expected = tuple(f'{scenario}:t{turn}' for scenario in (
            'craftsman-01', 'craftsman-02') for turn in range(1, 5)) + (
            'craftsman-04:t2', 'craftsman-04:t3') + tuple(f'{scenario}:t{turn}' for scenario in (
            'gatherer-01', 'gatherer-02', 'gatherer-04') for turn in range(1, 5))
        self.assertEqual(tuple(focused['sample_refs']), expected)
        self.assertEqual(len(expected), 22)
        self.assertEqual(len(RUNNER._selected_scenarios(json.loads(FIXTURE.read_text()), 'smoke')), 6)

    def test_fixed_context_freezes_history_and_closed_loop_uses_accumulated_history(self):
        original = (('player', 'What fruit do you like?'), ('npc', 'A ripe pear.'))
        generated = (('player', 'What fruit do you like?'), ('npc', 'A sweet plum.'))
        self.assertEqual(history_for_mode('fixed_context', original, generated), original)
        self.assertEqual(history_for_mode('closed_loop', original, generated), generated)

    def test_replay_history_sources_baseline_for_fixed_and_candidate_for_closed_loop(self):
        fixture = json.loads(FIXTURE.read_text())
        scenario = next(row for row in fixture['scenarios'] if row['id'] == 'craftsman-01')
        baseline = {('craftsman-01', 't1'): 'Recorded first answer.',
                    ('craftsman-01', 't2'): 'Recorded second answer.'}
        candidate = {('craftsman-01', 't1'): 'Candidate first answer.',
                     ('craftsman-01', 't2'): 'Candidate second answer.'}
        before = json.dumps(scenario['initial_state'], sort_keys=True)
        fixed = RUNNER._previous_history(scenario, 2, baseline, candidate, 'fixed_context')
        closed = RUNNER._previous_history(scenario, 2, baseline, candidate, 'closed_loop')
        self.assertEqual(fixed[-1], ('npc', 'Recorded second answer.'))
        self.assertEqual(closed[-1], ('npc', 'Candidate second answer.'))
        self.assertEqual(json.dumps(scenario['initial_state'], sort_keys=True), before)

    def test_manifest_refuses_populated_output_directory(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / 'already-used'
            output.mkdir()
            (output / 'raw.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'populated'):
                validate_manifest(manifest(), output_directory=output)

    def test_prompt_snapshots_are_created_once_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            path = write_prompt_snapshot(Path(root), 'craftsman-01:t2', 'Frozen prompt')
            self.assertEqual(path.read_text(), 'Frozen prompt\n')
            with self.assertRaisesRegex(ValueError, 'refusing overwrite'):
                write_prompt_snapshot(Path(root), 'craftsman-01:t2', 'Changed prompt')

    def test_blind_form_contains_candidate_text_without_run_or_model_identity(self):
        form = blind_review_form('A', ({'sample_ref': 'craftsman-01:t2', 'dimension': 'directness',
            'status': 'scorable', 'npc_role': 'craftsman', 'player_text': 'Question?', 'history': (),
            'candidate_dialogue': 'Answer.', 'candidate_origin': 'generated', 'model_tag': 'secret-model',
            'anchors': {'5': 'Direct'}},))
        serialized = json.dumps(form)
        self.assertIn('Answer.', serialized)
        self.assertNotIn('secret-model', serialized)
        self.assertNotIn('candidate_origin', serialized)
        with self.assertRaisesRegex(ValueError, 'candidate label'):
            blind_review_form('llama3:latest', ({'sample_ref': 'x'},))

    def test_compatible_model_only_comparison_keeps_missing_outcomes(self):
        left_manifest = manifest()
        right_manifest = manifest(run_id='run-b', model_tag='other:exact',
            model_digest='sha256:' + '2' * 64)
        outcome = SampleOutcome(sample_ref='craftsman-01:t2', status='missing_output',
            origin=None, dialogue=None, error_category='timeout', elapsed_seconds=3.0)
        control = SampleOutcome(sample_ref='gatherer-04:t2', status='generated',
            origin='generated', dialogue='A ripe pear.', error_category=None,
            elapsed_seconds=1.0)
        report = compare_compatible_runs(ExperimentRun(left_manifest, (outcome, control)),
            ExperimentRun(right_manifest, (control,)))
        self.assertEqual(report.sample_count, 2)
        self.assertEqual(report.left_missing, 1)
        self.assertEqual(report.right_missing, 1)

    def test_model_compatibility_context_change_is_reported_and_latency_requires_same_hardware(self):
        left = manifest()
        right = manifest(run_id='run-b', model_tag='other:exact',
            model_digest='sha256:' + '2' * 64, context_size=4096,
            hardware='different host')
        report = compare_compatible_runs(ExperimentRun(left, ()), ExperimentRun(right, ()))
        self.assertEqual(report.changed_compatibility_settings, ('context_size',))
        self.assertFalse(report.latency_comparable)

    def test_closed_loop_allows_and_labels_model_specific_history_divergence(self):
        left = manifest(input_mode='closed_loop')
        right = manifest(run_id='run-b', input_mode='closed_loop', model_tag='other:exact',
            model_digest='sha256:' + '2' * 64,
            prompt_snapshot_set_sha256='2' * 64, context_sha256='3' * 64)
        report = compare_compatible_runs(ExperimentRun(left, ()), ExperimentRun(right, ()))
        self.assertFalse(report.input_snapshots_identical)


if __name__ == '__main__':
    unittest.main()
