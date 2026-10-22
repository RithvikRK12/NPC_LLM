import json
from pathlib import Path
import unittest


FIXTURE = Path(__file__).parent / 'fixtures' / 'conversation' / 'baseline-evaluation-v1.json'
REQUIRED_CATEGORIES = {
    'greeting_substantive_question',
    'emotion_practical_request',
    'personal_question_unfamiliar',
    'biography_continuity',
    'challenge_earlier_story',
    'topic_change_during_negotiation',
    'return_to_suspended_request',
    'retract_preference_or_report',
    'unsupported_capability',
    'hypothetical_request',
    'quoted_request',
    'repeat_question_frustration',
    'world_event_between_turns',
    'provider_failure',
    'repair_failure',
    'new_game_old_response',
    'chat_clear_old_response',
    'multiple_supported_actions',
}
SCORE_DIMENSIONS = {
    'directness', 'coverage', 'continuity', 'character_consistency',
    'grounding', 'naturalness',
}
EXPECTED_BY_CATEGORY = {
    'greeting_substantive_question': 'no_operation',
    'emotion_practical_request': 'no_operation_without_current_consent',
    'personal_question_unfamiliar': 'narrative_only_no_mechanical_effect',
    'biography_continuity': 'generated_canon_requires_validated_final_speech',
    'challenge_earlier_story': 'player_challenge_remains_report',
    'topic_change_during_negotiation': 'suspend_pending_interaction_without_expiry',
    'return_to_suspended_request': 'revalidate_terms_and_preconditions_before_action',
    'retract_preference_or_report': 'retract_attributed_report_no_authority_promotion',
    'unsupported_capability': 'deny_unsupported_capability_without_new_operation',
    'hypothetical_request': 'no_operation_for_hypothetical',
    'quoted_request': 'no_operation_for_quoted_request',
    'repeat_question_frustration': 'answer_current_question_no_unrequested_action',
    'world_event_between_turns': 'recheck_current_state_before_effect',
    'provider_failure': 'safe_fallback_no_false_success',
    'repair_failure': 'bounded_repair_failure_safe_fallback',
    'new_game_old_response': 'suppress_old_scope_response',
    'chat_clear_old_response': 'suppress_old_epoch_response',
    'multiple_supported_actions': 'clarify_one_action_without_queueing_the_other',
    'mixed_concern_transfer_offer': 'no_transfer_without_exact_current_consent',
    'single_supported_transfer_consent': 'one_exact_transfer_only_after_bound_consent',
    'precondition_changes_before_consent': 'invalidate_offer_after_relevant_precondition_change',
    'world_event_after_action_receipt': 'recover_receipt_without_duplicate_effect',
}


class BaselineScenarioChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())

    def test_fixture_freezes_at_least_forty_four_to_eight_turn_scenarios(self):
        scenarios = self.fixture['scenarios']
        ids = [scenario['id'] for scenario in scenarios]
        scopes = [scenario['initial_state']['game_scope'] for scenario in scenarios]
        self.assertGreaterEqual(len(scenarios), 40)
        self.assertEqual(self.fixture['scenario_count'], len(scenarios))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(scopes), len(set(scopes)))
        self.assertEqual({scenario['npc']['role'] for scenario in scenarios}, {'craftsman', 'gatherer'})
        self.assertTrue(all(4 <= len(scenario['turns']) <= 8 for scenario in scenarios))
        self.assertEqual(self.fixture['fixture_schema_version'], 1)
        settings = self.fixture['model_settings']
        self.assertEqual(settings['provider'], 'OpenAICompatibleProvider')
        self.assertEqual(settings['model'], 'llama3:latest')
        self.assertTrue(settings['model_digest'].startswith('sha256:'))
        self.assertEqual(settings['temperature'], 0.2)
        self.assertTrue(settings['structured_output'])
        self.assertIsNone(settings['max_tokens'])

    def test_fixture_covers_all_required_scenario_categories(self):
        categories = {category for scenario in self.fixture['scenarios']
                      for category in scenario['categories']}
        self.assertEqual(set(self.fixture['required_category_ids']), REQUIRED_CATEGORIES)
        self.assertTrue(REQUIRED_CATEGORIES <= categories,
                        f'missing categories: {sorted(REQUIRED_CATEGORIES - categories)}')

    def test_state_mechanics_and_injected_events_are_explicit(self):
        turn_refs = set()
        for scenario in self.fixture['scenarios']:
            state = scenario['initial_state']
            self.assertTrue(state['game_scope'])
            self.assertEqual(state['conversation_epoch'], 0)
            self.assertIsInstance(state['resource_revisions'], dict)
            self.assertIsInstance(state['player_inventory'], list)
            self.assertIsInstance(state['npc_inventory'], list)
            self.assertIn('expected_mechanics', scenario)
            mechanics = scenario['expected_mechanics']
            self.assertTrue(mechanics['outcome'])
            self.assertEqual(mechanics['outcome'], EXPECTED_BY_CATEGORY[scenario['categories'][0]])
            self.assertIs(type(mechanics['max_mutating_operations']), int)
            self.assertLessEqual(0, mechanics['max_mutating_operations'])
            self.assertLessEqual(mechanics['max_mutating_operations'], 1)
            turn_ids = {turn['id'] for turn in scenario['turns']}
            for event in scenario.get('external_events', []):
                self.assertIn(event['before_turn_id'], turn_ids)
            for turn in scenario['turns']:
                turn_refs.add(f"{scenario['id']}:{turn['id']}")
                self.assertTrue(turn['player_input'].strip())
                self.assertIsInstance(turn.get('events_before', []), list)
            for event in scenario.get('provider_events', []):
                self.assertIn(event['turn_id'], turn_ids)

        for dimension in self.fixture['scoring_plan']['dimensions'].values():
            refs = dimension['denominator_turns']
            self.assertTrue(refs)
            self.assertEqual(len(refs), len(set(refs)))
            self.assertTrue(set(refs) <= turn_refs)

    def test_lifecycle_provider_and_receipt_race_events_are_reproducible(self):
        scenarios = {scenario['categories'][0]: scenario for scenario in self.fixture['scenarios']}
        self.assertEqual({event['outcome'] for event in scenarios['provider_failure']['provider_events']},
                         {'connect_error'})
        self.assertEqual({event['stage'] for event in scenarios['repair_failure']['provider_events']},
                         {'proposal', 'repair'})
        new_game_events = {event['kind'] for event in scenarios['new_game_old_response']['external_events']}
        clear_events = {event['kind'] for event in scenarios['chat_clear_old_response']['external_events']}
        self.assertTrue({'new_game', 'old_response_arrived'} <= new_game_events)
        self.assertTrue({'clear_chat', 'old_response_arrived'} <= clear_events)
        receipt_events = {event['kind'] for event in scenarios['world_event_after_action_receipt']['external_events']}
        self.assertTrue({'operation_committed', 'provider_failure', 'delivery_retry'} <= receipt_events)

    def test_scoring_dimensions_are_separate_and_human_calibration_is_pending(self):
        scoring = self.fixture['scoring_plan']
        self.assertEqual(set(scoring['dimensions']), SCORE_DIMENSIONS)
        self.assertFalse(scoring.get('composite_score'))
        self.assertEqual(scoring['human_calibration']['status'], 'pending')
        for rubric in scoring['dimensions'].values():
            self.assertEqual(rubric['scale'], [1, 5])
            self.assertEqual(set(rubric['anchors']), {'1', '3', '5'})

    def test_policy_inventory_covers_all_tuning_controls_without_shipping_values(self):
        inventory = (Path(__file__).parents[2] / 'docs' / 'evidence' /
                     'conversation-redesign-baseline' / 't03' / 'policy-candidates.md').read_text()
        for control in ('total deadline', 'provider stage budget', 'context token limit',
                        'output character limit', 'beat character limit', 'queue capacity',
                        'lease duration', 'summary trigger', 'diagnostic retention'):
            self.assertIn(control, inventory.lower())
        self.assertIn('No shipping values are selected', inventory)


if __name__ == '__main__':
    unittest.main()
