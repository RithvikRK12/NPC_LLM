"""Pure T01 conformance: no database, provider, HTTP or wall clock."""
import importlib
import copy
import json
from pathlib import Path
import unittest

from pydantic import TypeAdapter, ValidationError

try:
    c = importlib.import_module('app.services.conversation.contracts')
except ModuleNotFoundError as exc:
    if exc.name not in {'app.services.conversation', 'app.services.conversation.contracts'}:
        raise
    c = None

FIXTURE = Path(__file__).parent / 'fixtures/conversation/contracts-t01-valid.json'
POLICY = dict(schema_version=1, policy_version='test-measurement-1', input_char_limit=500,
              total_deadline_seconds=10.0, provider_stage_budget_seconds=4.0,
              context_token_limit=1000, output_char_limit=600, beat_char_limit=200,
              queue_capacity=3, lease_duration_seconds=20.0, summary_trigger_turns=8,
              diagnostic_retention_seconds=60.0)


class ConversationContractsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(c, 'T01 conversation contracts implementation is absent')
        self.fixture = json.loads(FIXTURE.read_text())

    def test_identity_roundtrip_preserves_scope_epoch_and_sequence(self):
        value = c.TurnSubmission.model_validate(self.fixture['submission'])
        self.assertEqual(json.loads(value.model_dump_json()), self.fixture['submission'])
        turn = c.TurnRef.model_validate(self.fixture['turn'])
        self.assertEqual(turn.key.epoch, 0)
        self.assertEqual(turn.sequence, 1)
        self.assertEqual(turn.key.game_scope, 'run-opaque')

    def test_identity_rejects_player_selector_legacy_mapping_and_unknown_fields(self):
        for name, raw in [('player_id', 1), ('game_id', 'run-opaque'), ('extra', 'ignored')]:
            with self.subTest(name=name), self.assertRaises(ValidationError):
                c.TurnSubmission.model_validate({**self.fixture['submission'], name: raw})
        with self.assertRaises(ValidationError):
            c.ConversationKey(game_id='single-player', timeline_id='run-opaque', npc_id=1)

    def test_unknown_or_coerced_versions_are_rejected(self):
        for version in [2, '1', True, 1.0, None]:
            for cls, raw in [(c.TurnSubmission, self.fixture['submission']), (c.ConversationPolicy, POLICY)]:
                with self.subTest(cls=cls.__name__, version=version), self.assertRaises(ValidationError):
                    cls.model_validate({**raw, 'schema_version': version})

    def test_identity_integer_bounds_and_opaque_identifiers(self):
        for field, bad in [('npc_id', 0), ('npc_id', True), ('npc_id', '1'), ('epoch', -1), ('epoch', 2**53), ('game_scope', '')]:
            with self.subTest(field=field, bad=bad), self.assertRaises(ValidationError):
                c.ConversationKey.model_validate({**self.fixture['submission']['key'], field: bad})
        for bad in [0, True, '1', 2**53]:
            with self.subTest(sequence=bad), self.assertRaises(ValidationError):
                c.TurnRef.model_validate({**self.fixture['turn'], 'sequence': bad})

    def test_request_bound_counts_unicode_codepoints_and_keeps_exact_text(self):
        for message in ['🙂' * 500, '  hi\n']:
            value = c.TurnSubmission.model_validate({**self.fixture['submission'], 'player_message': message})
            self.assertEqual(value.player_message, message)
        for bad in ['', ' \n\t', '🙂' * 501, 123]:
            with self.subTest(bad=repr(bad)[:30]), self.assertRaises(ValidationError):
                c.TurnSubmission.model_validate({**self.fixture['submission'], 'player_message': bad})

    def test_resources_are_detached_immutable_and_json_roundtrippable(self):
        original = {'inventory:player:1': 'revision-a', 'canon:npc:1': 0}
        value = c.RevisionSet(resources=original)
        original['inventory:player:1'] = 'revision-b'
        self.assertEqual(value.resources['inventory:player:1'], 'revision-a')
        with self.assertRaises(TypeError):
            value.resources['canon:npc:1'] = 3
        with self.assertRaises(ValidationError):
            value.resources = {}
        self.assertEqual(c.RevisionSet.model_validate_json(value.model_dump_json()), value)
        for bad in [True, -1, {}, '', 2**53]:
            with self.subTest(token=bad), self.assertRaises(ValidationError):
                c.RevisionSet(resources={'resource:1': bad})

    def test_nested_values_cannot_mutate(self):
        value = c.TurnSubmission.model_validate(self.fixture['submission'])
        with self.assertRaises(ValidationError):
            value.key.epoch = 1
        evidence = TypeAdapter(c.Evidence).validate_python(self.fixture['evidence'][0])
        self.assertIsInstance(evidence.sources, tuple)
        with self.assertRaises(ValidationError):
            evidence.sources[0].revision = 'changed'

    def test_unicode_span_resolves_codepoints_and_exact_reference(self):
        # A + astral emoji + e + combining accent: four code points.
        span = c.TextSpan(text_id='message:1', start=1, end=4)
        self.assertEqual(span.resolve({'message:1': 'A🙂e\u0301Z'}, expected_text='🙂e\u0301'), '🙂e\u0301')
        with self.assertRaises(ValueError):
            span.resolve({'message:1': 'A🙂e\u0301Z'}, expected_text='🙂é')
        with self.assertRaises(ValueError):
            span.resolve({'other': 'A🙂e\u0301Z'})
        with self.assertRaises(ValueError):
            span.resolve({'message:1': 'A🙂'})
        for start, end in [(-1, 2), (2, 1), (1, 1), (True, 2), (0, 2**53)]:
            with self.subTest(start=start, end=end), self.assertRaises(ValidationError):
                c.TextSpan(text_id='message:1', start=start, end=end)

    def test_all_six_evidence_tags_roundtrip_and_limit_mechanical_eligibility(self):
        adapter = TypeAdapter(c.Evidence)
        for raw, eligible in zip(self.fixture['evidence'], [True, True, True, False, False, False]):
            with self.subTest(tag=raw['kind']):
                value = adapter.validate_python(raw)
                self.assertEqual(json.loads(adapter.dump_json(value)), raw)
                self.assertIs(value.mechanical_eligible, eligible)
        for kind in ['unknown', 'MechanicalFact']:
            with self.assertRaises(ValidationError):
                adapter.validate_python({**self.fixture['evidence'][0], 'kind': kind})

    def test_reports_and_generated_canon_cannot_inhabit_mechanical_tags(self):
        adapter = TypeAdapter(c.Evidence)
        for original in self.fixture['evidence'][3:]:
            for target in ['mechanical_fact', 'verified_event', 'authored_knowledge']:
                with self.subTest(original=original['kind'], target=target), self.assertRaises(ValidationError):
                    adapter.validate_python({**original, 'kind': target})
        for raw in self.fixture['evidence'][3:]:
            with self.assertRaises(ValidationError):
                adapter.validate_python({**raw, 'authority': 'mechanical'})
        for raw in self.fixture['evidence']:
            with self.assertRaises(ValidationError):
                adapter.validate_python({**raw, 'sources': []})

    def test_source_scope_visibility_and_attribution_are_explicit(self):
        raw = self.fixture['evidence'][0]['sources'][0]
        for field, bad in [('kind', 'generated'), ('visibility', 'unrestricted'), ('attribution', ''), ('npc_id', 0)]:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                c.SourceRef.model_validate({**raw, field: bad})
        for field in ['attribution', 'visibility', 'game_scope', 'revision']:
            altered = dict(raw)
            del altered[field]
            with self.subTest(missing=field), self.assertRaises(ValidationError):
                c.SourceRef.model_validate(altered)

    def test_timestamps_are_aware_utc_and_reject_numeric_or_naive_values(self):
        raw = self.fixture['evidence'][0]
        value = TypeAdapter(c.Evidence).validate_python({**raw, 'created_at': '2026-10-14T05:30:00+05:30'})
        self.assertEqual(value.created_at.isoformat(), '2026-10-14T00:00:00+00:00')
        for bad in ['2026-10-14T00:00:00', 123, '123', True]:
            with self.subTest(timestamp=bad), self.assertRaises(ValidationError):
                TypeAdapter(c.Evidence).validate_python({**raw, 'created_at': bad})

    def test_policy_requires_explicit_finite_positive_tuning(self):
        value = c.ConversationPolicy(**POLICY)
        self.assertEqual(c.ConversationPolicy.model_validate_json(value.model_dump_json()), value)
        for field in POLICY.keys() - {'schema_version', 'policy_version', 'input_char_limit'}:
            missing = dict(POLICY)
            del missing[field]
            with self.subTest(missing=field), self.assertRaises(ValidationError):
                c.ConversationPolicy(**missing)
            for bad in [0, -1, True, float('inf'), float('nan')]:
                with self.subTest(field=field, bad=bad), self.assertRaises(ValidationError):
                    c.ConversationPolicy(**{**POLICY, field: bad})

    def test_policy_accepts_600_but_rejects_any_larger_dialogue_limit(self):
        value = c.ConversationPolicy(**POLICY)
        self.assertEqual(value.output_char_limit, 600)
        with self.assertRaises(ValidationError):
            c.ConversationPolicy(**{**POLICY, 'output_char_limit': 601})
        for field, bad in [('input_char_limit', 501), ('beat_char_limit', 801), ('provider_stage_budget_seconds', 11.0), ('negotiation_timeout_seconds', 1.0)]:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                c.ConversationPolicy(**{**POLICY, field: bad})

    def test_deadline_uses_only_injected_monotonic_clock(self):
        now = [100.0]
        deadline = c.Deadline.after(10.0, clock=lambda: now[0])
        self.assertEqual(deadline.remaining(), 10.0)
        self.assertFalse(deadline.expired())
        now[0] = 103.5
        self.assertEqual(deadline.remaining(), 6.5)
        stage = deadline.child(4.0)
        now[0] = 108.0
        self.assertEqual(stage.remaining(), 0.0)
        self.assertTrue(stage.expired())
        self.assertEqual(deadline.remaining(), 2.0)
        capped = deadline.child(20.0)
        now[0] = 110.0
        self.assertEqual(capped.remaining(), 0.0)
        self.assertTrue(deadline.expired())
        for bad in [0, -1, True, float('inf'), float('nan')]:
            with self.subTest(duration=bad), self.assertRaises(ValueError):
                c.Deadline.after(bad, clock=lambda: 0.0)
        with self.assertRaises(ValueError):
            c.Deadline.after(1.0, clock=lambda: float('nan'))

    def test_deadline_is_immutable_and_rejects_invalid_clock_during_use(self):
        now = [1.0]
        value = c.Deadline.after(1.0, clock=lambda: now[0])
        with self.assertRaises((AttributeError, TypeError)):
            value.expires_at = 30.0
        now[0] = float('inf')
        with self.assertRaises(ValueError):
            value.remaining()

    def test_error_roundtrip_has_safe_detail_and_optional_known_turn(self):
        raw = dict(code='STALE_SCOPE', stage='admission', retryable=False,
                   turn=self.fixture['turn'], safe_detail='Refresh the current world.')
        value = c.ConversationError(**raw)
        self.assertEqual(json.loads(value.model_dump_json()), raw)
        self.assertIsNone(c.ConversationError(**{**raw, 'turn': None}).turn)
        for field, bad in [('code', 'SOME_EXCEPTION'), ('safe_detail', ' '), ('exception', 'secret'), ('retryable', 1)]:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                c.ConversationError(**{**raw, field: bad})


class InteractionOperationContractsTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((FIXTURE.parent / 'contracts-t02-valid.json').read_text())

    def _pending(self, **updates):
        return {**copy.deepcopy(self.raw['pending']),
                'authorized_operation': copy.deepcopy(self.raw['operation']), **updates}

    def test_single_item_offer_roundtrip_preserves_both_transfer_directions(self):
        self.assertIn('authorized_operation', c.PendingInteraction.model_fields)
        for command in ('give_item', 'receive_item'):
            with self.subTest(command=command):
                raw = self._pending()
                raw['authorized_operation']['command_id'] = command
                value = c.PendingInteraction.model_validate(raw)
                restored = c.PendingInteraction.model_validate_json(value.model_dump_json())
                self.assertEqual(restored.authorized_operation.command_id, command)
                self.assertEqual(restored.authorized_operation.arguments.item, 'wood')
                self.assertEqual(json.loads(value.model_dump_json()), raw)
                raw['authorized_operation']['arguments']['item'] = 'axe'
                self.assertEqual(value.authorized_operation.arguments.item, 'wood')
                with self.assertRaises(ValidationError):
                    value.authorized_operation.command_id = 'wait'

    def test_single_activity_offer_preserves_exact_parameterless_command(self):
        operation = {**self.raw['operation'], 'command_id': 'begin_ship_inspection', 'arguments': {}}
        raw = self._pending(kind='activity_offer', item=None, quantity=None,
                            authorized_operation=operation)
        value = c.PendingInteraction.model_validate_json(json.dumps(raw))
        self.assertEqual(value.authorized_operation.command_id, 'begin_ship_inspection')
        self.assertEqual(value.authorized_operation.arguments.model_dump(), {})

    def test_binding_rejects_malformed_or_mismatched_executable_terms(self):
        changes = [
            {'command_id': 'complete_inspection'},
            {'command_id': 'wait'},
            {'command_id': 'wait', 'arguments': {}},
            {'arguments': {}}, {'arguments': {'item': 'axe'}},
            {'arguments': {'item': 'wood', 'quantity': 2}},
            {'target': {**self.raw['operation']['target'], 'entity_id': '2'}},
            {'pending_question_id': None}, {'pending_question_id': 'question:old'},
            *({'modality': mode} for mode in ('quoted', 'hypothetical', 'negated', 'ambiguous')),
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                c.PendingInteraction.model_validate(self._pending(
                    authorized_operation={**self.raw['operation'], **change}))
        for quantity in (None, 0, 2, True):
            with self.subTest(quantity=quantity), self.assertRaises(ValidationError):
                c.PendingInteraction.model_validate(self._pending(quantity=quantity))
        with self.assertRaises(ValidationError):
            c.PendingInteraction.model_validate(self._pending(kind='activity_offer', item=None, quantity=None))

    def test_choices_and_clarifications_cannot_pre_authorize_one_option(self):
        for kind in ('clarification', 'action_choice'):
            raw = self._pending(kind=kind, item=None, quantity=None)
            if kind == 'action_choice':
                raw.update(required_response_kind='choice', offered_operations=[
                    self.raw['operation'],
                    {**self.raw['operation'], 'candidate_id': 'operation:2', 'command_id': 'receive_item'},
                ])
            with self.subTest(kind=kind), self.assertRaises(ValidationError):
                c.PendingInteraction.model_validate(raw)

    def test_legacy_missing_binding_remains_decodable_without_inferred_direction(self):
        self.assertIn('authorized_operation', c.PendingInteraction.model_fields)
        for optional in ({}, {'authorized_operation': None}):
            value = c.PendingInteraction.model_validate({**self.raw['pending'], **optional})
            self.assertIsNone(value.authorized_operation)
            restored = c.PendingInteraction.model_validate_json(value.model_dump_json())
            self.assertIsNone(restored.authorized_operation)

    def test_consent_cannot_substitute_a_different_stored_offer(self):
        pending = c.PendingInteraction.model_validate(self._pending())
        turn = self.raw['turn']
        raw = dict(
            interaction_id=pending.interaction_id, question_id=pending.question_id,
            question_turn_id=pending.question_turn_id, question_turn=turn,
            answering_turn={**turn, 'turn_id': 'turn:2', 'request_id': 'request:2', 'sequence': 2},
            answer_span={'text_id': 'answer:2', 'start': 0, 'end': 3},
            operation=self.raw['operation'], checked_preconditions=[],
            precondition_fingerprint=pending.precondition_fingerprint,
        )
        c.ConsentBinding.model_validate(raw).validate_against(pending, {'answer:2': 'yes'}, expected_answer='yes')
        for change in ({'command_id': 'receive_item'},):
            with self.subTest(change=change), self.assertRaises(ValueError):
                c.ConsentBinding.model_validate({**raw, 'operation': {**self.raw['operation'], **change}}).validate_against(
                    pending, {'answer:2': 'yes'}, expected_answer='yes')
        for change in ({'candidate_id': 'operation:other'},
                       {'source_spans': [{'text_id': 'answer:2', 'start': 0, 'end': 3}]}):
            with self.subTest(change=change):
                c.ConsentBinding.model_validate({**raw, 'operation': {**self.raw['operation'], **change}}).validate_against(
                    pending, {'answer:2': 'yes'}, expected_answer='yes')


if __name__ == '__main__':
    unittest.main()
