"""T03 continuity/result contracts and shared JSON fixtures."""
import importlib
import json
from pathlib import Path
import unittest
from pydantic import TypeAdapter, ValidationError

c = importlib.import_module('app.services.conversation.contracts')
FIXTURES = Path(__file__).parent / 'fixtures/conversation'

class ConversationContinuityContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / 't03-valid.json').read_text())
        self.rejected = json.loads((FIXTURES / 't03-rejected.json').read_text())

    def test_canon_and_revision_lineage_roundtrip(self):
        record = c.CanonRecord.model_validate(self.valid['canon_record'])
        self.assertEqual(record.revision, 2)
        change = TypeAdapter(c.CanonChange).validate_python(self.valid['canon_changes'][0])
        self.assertEqual(change.kind, 'revise')
        self.assertEqual(change.expected_revision, 1)
        self.assertEqual(change.correction_link, 'correction:accepted-1')
        with self.assertRaises(ValidationError):
            TypeAdapter(c.CanonChange).validate_python(self.rejected['canon_change_without_correction'])
        with self.assertRaises(ValidationError):
            c.CanonRecord.model_validate(self.rejected['generated_authority_escalation'])

    def test_memory_has_scope_epoch_uncertainty_lifecycle_and_sources(self):
        raw = self.valid['memory']
        record = c.MemoryRecord.model_validate(raw)
        self.assertEqual((record.game_scope, record.epoch), ('run-opaque', 3))
        raw['content'] = 'mutated after validation'
        self.assertEqual(record.content, 'The player says they repaired the mast.')
        with self.assertRaises(ValidationError):
            c.MemoryRecord.model_validate({**self.valid['memory'], 'epoch': -1})

    def test_validation_report_carries_evidence_and_revisions(self):
        report = c.ValidationReport.model_validate(self.valid['validation_report'])
        self.assertEqual(report.findings[0].affected_span.resolve({'final:3':'A🙂éB'}), 'A🙂é')
        self.assertEqual(report.checked_evidence_revisions.resources['event:9'], 4)

    def test_final_result_beats_preserve_every_codepoint_and_mock_origin(self):
        result = c.FinalTurnResult.model_validate(self.valid['final_turn_result'])
        self.assertEqual(''.join(result.dialogue_beats), result.final_dialogue)
        self.assertEqual(result.response_origin, 'mock')
        with self.assertRaises(ValidationError):
            c.FinalTurnResult.model_validate({**self.valid['final_turn_result'], **self.rejected['lossy_beats']})

    def test_final_result_state_is_detached_and_immutable(self):
        raw = self.valid['final_turn_result']
        result = c.FinalTurnResult.model_validate(raw)
        raw['state_projection']['health'] = 0
        self.assertEqual(result.state_projection['health'], 80)
        with self.assertRaises(TypeError):
            result.state_projection['health'] = 0
        for unsupported in [
            {'tags': {'a', 'b'}},
            {'payload': bytearray(b'hi')},
            {'payload': b'hi'},
            {'nested': {1: 'non-string key'}},
            {'number': float('nan')},
        ]:
            with self.subTest(unsupported=unsupported), self.assertRaises(ValidationError):
                c.FinalTurnResult.model_validate({
                    **self.valid['final_turn_result'],
                    'state_projection': unsupported,
                })

    def test_legacy_mapping_is_explicit_and_never_aliases_fields(self):
        mapping = c.LegacyConversationMapping.model_validate(self.valid['legacy_mapping'])
        self.assertEqual(mapping.to_key(), c.ConversationKey(game_scope='run-opaque', npc_id=7, epoch=3))
        with self.assertRaises(ValidationError):
            c.LegacyConversationMapping.model_validate(self.rejected['implicit_legacy_alias'])
        self.assertNotEqual(mapping.game_id, mapping.game_scope)
        self.assertNotEqual(mapping.timeline_id, str(mapping.epoch))

    def test_result_and_turn_status_values(self):
        status = c.TurnStatus.model_validate({'turn':self.valid['final_turn_result']['turn'],'phase':'finalized','response':self.valid['final_turn_result']})
        self.assertEqual(status.phase, 'finalized')
        success = c.Result.success(status)
        self.assertEqual(success.value, status)
        error = c.ConversationError(code='STALE_SCOPE',stage='lookup',retryable=False,safe_detail='Refresh the current world.')
        self.assertEqual(c.Result.failure(error).error, error)

if __name__ == '__main__':
    unittest.main()
