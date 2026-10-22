import ast
import importlib.util
import json
from pathlib import Path
import unittest

from app.services.conversation.shadow import (
    ShadowCandidate, ShadowReplayRunner, ShadowScenario,
    build_quality_samples, quadratic_weighted_kappa,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'conversation' / 'baseline-evaluation-v1.json'
REPLAY_SCRIPT = ROOT.parent / 'docs' / 'evidence' / 'conversation-redesign-release' / 't01' / 'configured_replay.py'
FORBIDDEN_IMPORT_ROOTS = {'fastapi', 'sqlalchemy'}
FORBIDDEN_SYMBOLS = {
    'OperationGateway', 'FinalizationStore', 'CanonWritePort',
    'InteractionWritePort', 'OperationService', 'Finalizer',
}


class ShadowReplayChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())

    def test_frozen_dataset_loads_as_immutable_shadow_scenarios(self):
        scenarios = tuple(ShadowScenario.from_mapping(row) for row in self.fixture['scenarios'])
        self.assertEqual(len(scenarios), 44)
        self.assertEqual({scenario.npc_role for scenario in scenarios}, {'craftsman', 'gatherer'})
        self.assertEqual(sum(len(scenario.turns) for scenario in scenarios), 176)
        with self.assertRaises(TypeError):
            scenarios[0].initial_state['player_inventory'] = ()
        with self.assertRaises(TypeError):
            scenarios[0].initial_state['quest_state']['bow'] = 'completed'
        with self.assertRaises(TypeError):
            scenarios[0].turns[0]['player_input'] = 'mutated'

    def test_replay_receives_frozen_model_settings_and_retains_fixture_category_counts(self):
        observed = []
        settings = self.fixture['model_settings']
        scenario = ShadowScenario.from_mapping(self.fixture['scenarios'][0])
        run = ShadowReplayRunner(lambda turn: observed.append(turn) or ShadowCandidate('Reply.'),
                                 model_settings=settings).run((scenario,))
        self.assertEqual(observed[0].model_settings['model'], settings['model'])
        self.assertEqual(len(run.model_settings_digest), 64)
        with self.assertRaises(TypeError):
            observed[0].model_settings['temperature'] = 1.0
        with self.assertRaises(TypeError):
            observed[0].model_settings['prompt_source_sha256']['backend/app/main.py'] = 'changed'

        report = json.loads((ROOT.parent / 'docs' / 'evidence' / 'conversation-redesign-baseline' /
                             't03' / 'fixture-report.json').read_text())
        counts = {}
        for row in self.fixture['scenarios']:
            for category in row['categories']:
                counts[category] = counts.get(category, 0) + 1
        self.assertEqual(counts, report['scenario_count_by_category'])
        scoreable_turns = {f"{row['id']}:{turn_id}" for row in self.fixture['scenarios']
                           for turn_id in row['scoreable_turn_ids']}
        self.assertTrue(all(set(rubric['denominator_turns']) <= scoreable_turns
                            for rubric in self.fixture['scoring_plan']['dimensions'].values()))

    def test_replay_has_no_mutation_dependencies_or_execution_fields(self):
        source = Path(__import__('app.services.conversation.shadow', fromlist=['__file__']).__file__).read_text()
        tree = ast.parse(source)
        imported_roots = set()
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_roots.add(node.module.split('.')[0])
                imported_names.update(alias.name for alias in node.names)
        self.assertFalse(FORBIDDEN_IMPORT_ROOTS & imported_roots)
        self.assertFalse(FORBIDDEN_SYMBOLS & imported_names)

        scenario = ShadowScenario.from_mapping(self.fixture['scenarios'][0])
        runner = ShadowReplayRunner(lambda _turn: ShadowCandidate('A careful answer.', origin='generated'))
        run = runner.run((scenario,))
        self.assertEqual(len(run.turns), len(scenario.turns))
        self.assertTrue(all(not turn.operation_executed for turn in run.turns))
        self.assertTrue(all(not turn.canon_published for turn in run.turns))
        self.assertTrue(all(not turn.interaction_written for turn in run.turns))

    def test_candidate_actions_remain_observations_and_do_not_mutate_frozen_state(self):
        observed = []

        def generate(turn):
            observed.append(turn)
            return ShadowCandidate('I can consider that request.', origin='generated',
                                   action_candidate='give_item')

        scenario = ShadowScenario.from_mapping(self.fixture['scenarios'][0])
        run = ShadowReplayRunner(generate).run((scenario,))
        self.assertEqual(len(observed), 4)
        self.assertTrue(all(turn.action_candidate == 'give_item' for turn in run.turns))
        self.assertTrue(all(not turn.operation_executed for turn in run.turns))
        self.assertEqual(run.initial_state_digest, run.final_state_digest)
        self.assertFalse(hasattr(observed[0], 'expected_mechanics'))

    def test_provider_errors_are_counted_without_silent_mock_substitution(self):
        calls = 0

        def generate(_turn):
            nonlocal calls
            calls += 1
            if calls == 2:
                return ShadowCandidate(None, origin='provider_error', error_type='ConnectError')
            return ShadowCandidate('A measured reply.', origin='generated')

        scenario = ShadowScenario.from_mapping(self.fixture['scenarios'][0])
        run = ShadowReplayRunner(generate).run((scenario,))
        self.assertEqual(run.origins['provider_error'], 1)
        self.assertEqual(run.origins['mock'], 0)
        self.assertEqual(run.turns[1].error_type, 'ConnectError')
        self.assertIsNone(run.turns[1].dialogue)

    def test_quality_samples_preserve_each_frozen_denominator_and_missing_outputs(self):
        scenarios = tuple(ShadowScenario.from_mapping(row) for row in self.fixture['scenarios'])
        run = ShadowReplayRunner(lambda _turn: ShadowCandidate('Measured reply.')).run(scenarios)
        samples = build_quality_samples(self.fixture, run)
        for dimension, rubric in self.fixture['scoring_plan']['dimensions'].items():
            rows = samples[dimension]
            self.assertEqual(len(rows), len(rubric['denominator_turns']))
            self.assertEqual([row['sample_ref'] for row in rows], rubric['denominator_turns'])
            self.assertTrue(all(row['candidate_dialogue'] == 'Measured reply.' for row in rows))
            self.assertTrue(all(row['status'] == 'scorable' for row in rows))
            self.assertEqual(rows[0]['anchors'], rubric['anchors'])

        failed = ShadowReplayRunner(lambda _turn: ShadowCandidate(None, origin='provider_error'))
        failed_samples = build_quality_samples(self.fixture, failed.run(scenarios))
        directness = failed_samples['directness']
        self.assertEqual(len(directness), 44)
        self.assertTrue(all(row['status'] == 'missing_candidate' for row in directness))
        self.assertTrue(all(row['candidate_dialogue'] is None for row in directness))

    def test_quadratic_weighted_kappa_reports_review_agreement(self):
        self.assertEqual(quadratic_weighted_kappa([1, 3, 5], [1, 3, 5]), 1.0)
        self.assertGreaterEqual(quadratic_weighted_kappa([1, 3, 5], [2, 3, 4]), 0.8)
        self.assertAlmostEqual(quadratic_weighted_kappa([1, 1, 5], [5, 5, 1]), -0.8)
        self.assertIsNone(quadratic_weighted_kappa([3], [3]))

    def test_shadow_turn_includes_only_frozen_events_scheduled_before_it(self):
        scenario_row = next(row for row in self.fixture['scenarios'] if row['id'] == 'craftsman-13')
        scenario = ShadowScenario.from_mapping(scenario_row)
        observed = []
        ShadowReplayRunner(lambda turn: observed.append(turn) or ShadowCandidate('Noted.')).run((scenario,))
        third_turn = next(turn for turn in observed if turn.turn_id == 't3')
        self.assertEqual(len(third_turn.events_before), 1)
        self.assertEqual(third_turn.events_before[0]['resource'], 'inventory:npc:1')
        with self.assertRaises(TypeError):
            third_turn.events_before[0]['resource'] = 'changed'

    def test_shadow_replay_retains_initial_visible_history_and_turn_speaker_order(self):
        scenario_row = next(row for row in self.fixture['scenarios'] if row['id'] == 'craftsman-05')
        scenario = ShadowScenario.from_mapping(scenario_row)
        observed = []
        ShadowReplayRunner(lambda turn: observed.append(turn) or ShadowCandidate('First reply.')).run((scenario,))
        self.assertEqual(observed[0].history, (('npc', 'I learned this skill from a travelling sailor.'),))
        self.assertEqual(observed[1].history[-2:], (
            ('player', scenario.turns[0]['player_input']), ('npc', 'First reply.')))


class ConfiguredReplayAdapterChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('configured_replay', REPLAY_SCRIPT)
        cls.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.adapter)
        cls.fixture = json.loads(FIXTURE.read_text())

    def test_payload_uses_frozen_input_state_and_dialogue_only_schema(self):
        from app.services.conversation.shadow import ShadowScenario, ShadowTurnInput

        scenario = ShadowScenario.from_mapping(self.fixture['scenarios'][0])
        turn = ShadowTurnInput(scenario.scenario_id, 't1', scenario.npc_role,
                               'Hello.', scenario.initial_state, (), self.fixture['model_settings'])
        payload = self.adapter.build_payload(turn, self.fixture['model_settings']['model'])
        self.assertEqual(payload['model'], self.fixture['model_settings']['model'])
        self.assertEqual(payload['temperature'], self.fixture['model_settings']['temperature'])
        self.assertEqual(payload['messages'][-1]['content'], 'Hello.')
        self.assertIn('player_inventory', payload['messages'][0]['content'])
        schema = payload['response_format']['json_schema']['schema']
        self.assertEqual(schema['required'], ['dialogue'])
        self.assertEqual(set(schema['properties']), {'dialogue'})
        self.assertEqual(schema['properties']['dialogue']['maxLength'], 240)
        alternate = self.adapter.build_payload(
            turn, self.fixture['model_settings']['model'], ordinary_output_limit=600,
        )
        self.assertEqual(
            alternate['response_format']['json_schema']['schema']['properties']['dialogue']['maxLength'],
            600,
        )
        story_scenario = next(row for row in self.fixture['scenarios']
                              if row['npc']['role'] == 'craftsman' and
                              any('story' in turn['player_input'].lower() for turn in row['turns']))
        story_turn = next(turn for turn in story_scenario['turns'] if 'story' in turn['player_input'].lower())
        story_input = ShadowTurnInput(
            story_scenario['id'], story_turn['id'], 'craftsman', story_turn['player_input'],
            story_scenario['initial_state'], (), self.fixture['model_settings'],
        )
        story_payload = self.adapter.build_payload(
            story_input, self.fixture['model_settings']['model'], ordinary_output_limit=600,
        )
        self.assertEqual(
            story_payload['response_format']['json_schema']['schema']['properties']['dialogue']['maxLength'],
            600,
        )
        with self.assertRaises(ValueError):
            self.adapter.run(ordinary_output_limit=600, output_dir=self.adapter.OUT_DIR)
        self.assertNotIn('api_key', json.dumps(payload).lower())

    def test_updated_character_guidance_replay_preserves_t04_direction_and_improved_variant_changes_only_guidance(self):
        from app.services.conversation.shadow import ShadowScenario, ShadowTurnInput
        from app.services.context.character_profiles import CHARACTER_DIRECTION, CHARACTER_DIRECTION_T04, project_profile

        for scenario_row in self.fixture['scenarios']:
            role = scenario_row['npc']['role']
            if role not in {'craftsman', 'gatherer'}:
                continue
            scenario = ShadowScenario.from_mapping(scenario_row)
            history = tuple((item.get('speaker', 'unknown'), item.get('text', ''))
                            for item in scenario.initial_state.get('visible_history', ()))
            turn = ShadowTurnInput(
                scenario.scenario_id, 't1', role, 'Tell me about your childhood.',
                scenario.initial_state, (), self.fixture['model_settings'], history,
            )
            prompt = self.adapter.build_prompt(turn, use_updated_profiles=True)
            projected = project_profile(role, turn.player_text,
                [{'role': 'user' if speaker == 'player' else 'assistant', 'content': text}
                 for speaker, text in history])
            self.assertIn(CHARACTER_DIRECTION_T04, prompt)
            self.assertIn(projected['revision'], prompt)
            self.assertIn(projected['core']['fixed_lore'], prompt)
            self.assertIn('do not echo', prompt.lower())
            improved = self.adapter.build_payload(
                turn, self.fixture['model_settings']['model'], ordinary_output_limit=600,
                use_updated_profiles=True, improved_guidance=True,
            )
            self.assertIn(CHARACTER_DIRECTION, improved['messages'][0]['content'])
            self.assertNotIn(CHARACTER_DIRECTION_T04, improved['messages'][0]['content'])
            self.assertEqual(
                improved['response_format']['json_schema']['schema']['properties']['dialogue']['maxLength'], 600,
            )

    def test_reply_parser_rejects_non_json_and_extra_fields(self):
        self.assertEqual(self.adapter.parse_reply('{"dialogue":"Hello."}'), 'Hello.')
        with self.assertRaises(ValueError):
            self.adapter.parse_reply('not JSON')
        with self.assertRaises(ValueError):
            self.adapter.parse_reply('{"dialogue":"Hello.","action":"give_item"}')

    def test_config_check_fails_closed_on_model_or_endpoint_mismatch(self):
        class Settings:
            llm_base_url = 'http://localhost:11434/v1'
            llm_model = 'llama3:latest'
            llm_structured_output = True
            llm_timeout_seconds = 120.0

        self.adapter.validate_settings(Settings(), self.fixture['model_settings'])
        Settings.llm_model = 'different-model'
        with self.assertRaises(ValueError):
            self.adapter.validate_settings(Settings(), self.fixture['model_settings'])

    def test_model_manifest_check_requires_frozen_tag_digest_and_server_version(self):
        frozen = self.fixture['model_settings']
        self.adapter.validate_model_manifest(
            [{'name': frozen['model'], 'digest': frozen['model_digest'].removeprefix('sha256:')}],
            frozen['ollama_version'], frozen,
        )
        with self.assertRaises(ValueError):
            self.adapter.validate_model_manifest(
                [{'name': frozen['model'], 'digest': 'sha256:changed'}],
                frozen['ollama_version'], frozen,
            )

    def test_human_calibration_generates_separate_balanced_reviewer_forms(self):
        scenarios = tuple(self.adapter.ShadowScenario.from_mapping(row) for row in self.fixture['scenarios'])
        run = self.adapter.ShadowReplayRunner(
            lambda _turn: self.adapter.ShadowCandidate('A grounded answer.') ,
            model_settings=self.fixture['model_settings'],
        ).run(scenarios)
        samples = self.adapter.build_quality_samples(self.fixture, run)
        template = self.adapter._reviewer_template(self.fixture, samples)
        forms = self.adapter.reviewer_forms(template)
        self.assertEqual(set(forms), {'reviewer_1', 'reviewer_2'})
        self.assertEqual(len(forms['reviewer_1']['samples']), 24)
        self.assertEqual(
            [row['sample_ref'] for row in forms['reviewer_1']['samples']],
            [row['sample_ref'] for row in forms['reviewer_2']['samples']],
        )
        self.assertTrue(all(row['score'] is None for form in forms.values() for row in form['samples']))
        self.assertTrue(all('reviewer_2_score' not in row for row in forms['reviewer_1']['samples']))
        template['replay_policy'] = {'policy_id': 'ordinary-dialogue-limit-600-chars-v1'}
        self.assertEqual(
            self.adapter.reviewer_forms(template)['reviewer_1']['replay_policy']['policy_id'],
            'ordinary-dialogue-limit-600-chars-v1',
        )

    def test_runner_adapter_has_no_game_or_persistence_imports(self):
        self.assertEqual(self.adapter.ROOT, ROOT.parent)
        tree = ast.parse(REPLAY_SCRIPT.read_text())
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split('.')[0])
        self.assertFalse({'sqlalchemy', 'fastapi', 'app.database', 'app.models'} & imported_roots)


if __name__ == '__main__':
    unittest.main()
