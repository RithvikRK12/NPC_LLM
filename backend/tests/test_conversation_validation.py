import unittest
import json
from pathlib import Path
from types import SimpleNamespace

from app.services.conversation import contracts as c
from app.services.conversation.validation import ResponseValidator


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.validator = ResponseValidator()

    def test_report_is_not_a_witnessed_event(self):
        findings = self.validator.check_text(
            'I saw the dragon fall.',
            evidence={'report:1': {'kind': 'player_report', 'content': 'The dragon fell.', 'attribution': 'player'}},
        )
        self.assertIn('UNSUPPORTED_EVENT_ATTRIBUTION', {f.code for f in findings})

    def test_harmless_idioms_do_not_trigger_mechanical_findings(self):
        findings = self.validator.check_text('I have a soft spot for you. Fear can destroy your confidence.')
        self.assertEqual(findings, ())

    def test_unknown_ids_are_blocked(self):
        findings = self.validator.check_text('The cache is here.', referenced_ids=('cache:unknown',), known_ids=())
        self.assertIn('UNKNOWN_REFERENCE', {f.code for f in findings})

    def test_resolved_evidence_source_id_is_known_dependency(self):
        source = c.SourceRef(kind='inventory', source_id='inventory:wood', revision=3,
            game_scope='run:1', npc_id=1, attribution='server', visibility='npc_private')
        fact = c.MechanicalFact(kind='mechanical_fact', evidence_id='fact:wood', content='You have 1 wood.',
            sources=(source,), created_at='2026-01-01T00:00:00Z')
        context = SimpleNamespace(visible_facts=(fact,), revisions=c.RevisionSet(resources={'inventory:wood': 3}))
        reply = c.AssembledReply(text_id='final:1', final_text='You have 1 wood.', beats=('You have 1 wood.',),
            segment_spans={}, evidence_dependencies=(source,), candidate_continuity_changes=())
        report = self.validator.check(reply, context, SimpleNamespace(facts=(fact,)))
        self.assertNotIn('UNKNOWN_REFERENCE', {f.code for f in report.findings})

    def test_canon_contradiction_is_blocked_from_typed_projections(self):
        reply, context, claims, evidence, comparisons = self.projection_inputs()
        report = self.validator.check(reply, context, SimpleNamespace(), claim_projection=claims,
            evidence_projection=evidence, comparison_projection=comparisons)
        self.assertIn('CANON_CONTRADICTION', {f.code for f in report.findings})

    def test_partial_or_unavailable_claim_coverage_blocks_canon_validation(self):
        reply, context, claims, evidence, comparisons = self.projection_inputs()
        for status in ('partial', 'unavailable'):
            with self.subTest(status=status):
                incomplete = c.ValidatorClaimProjection.model_validate({
                    **claims.model_dump(mode='json'), 'coverage_status':status})
                report = self.validator.check(reply, context, SimpleNamespace(),
                    claim_projection=incomplete, evidence_projection=evidence,
                    comparison_projection=comparisons)
                self.assertIn('CANON_COVERAGE_INCOMPLETE', {f.code for f in report.findings})

    def test_missing_and_unknown_canon_comparisons_fail_closed(self):
        reply, context, claims, evidence, _ = self.projection_inputs()
        omitted = c.ValidatorComparisonProjection(schema_version=1, game_scope='run:1', npc_id=2, comparisons=())
        report = self.validator.check(reply, context, SimpleNamespace(), claim_projection=claims,
            evidence_projection=evidence, comparison_projection=omitted)
        unknown = {f.code for f in report.findings}
        self.assertIn('CANON_COMPARISON_UNKNOWN', unknown)
        self.assertIn('CANON_COMPARISON_UNKNOWN', self.findings_for_outcome('unknown'))

    def projection_inputs(self):
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/contracts-t06-valid.json').read_text())
        reply = c.AssembledReply.model_validate(raw['reply'])
        context = SimpleNamespace(turn=SimpleNamespace(key=SimpleNamespace(game_scope='run:1', npc_id=2)),
            revisions=c.RevisionSet(resources={}))
        claims = c.ValidatorClaimProjection.model_validate(raw['claims'])
        evidence = c.ValidatorEvidenceProjection.model_validate(raw['evidence'])
        comparisons = c.ValidatorComparisonProjection.model_validate(raw['comparisons'])
        return reply, context, claims, evidence, comparisons

    def findings_for_outcome(self, outcome):
        reply, context, claims, evidence, comparisons = self.projection_inputs()
        comparisons = c.ValidatorComparisonProjection(schema_version=1, game_scope='run:1', npc_id=2,
            comparisons=tuple(item.model_copy(update={'outcome': outcome}) for item in comparisons.comparisons))
        report = self.validator.check(reply, context, SimpleNamespace(), claim_projection=claims,
            evidence_projection=evidence, comparison_projection=comparisons)
        return {f.code for f in report.findings}

    def test_unsupported_shop_cache_recipe_and_route_claims_are_blocked(self):
        for sentence in ('The shop is behind the inn.', 'The cache is in the cave.',
                         'The recipe is available here.', 'The route is north.'):
            with self.subTest(sentence=sentence):
                findings = self.validator.check_text(sentence)
                self.assertIn('UNSUPPORTED_WORLD_CLAIM', {f.code for f in findings})

    def test_correct_slot_does_not_excuse_contradictory_surrounding_text(self):
        findings = self.validator.check_text(
            'I gave you 1 wood. Actually, I kept the wood and gave you nothing.',
            evidence={'receipt:1': {'kind': 'verified_event', 'content': 'gave 1 wood', 'outcome': 'completed'}},
            referenced_ids=('receipt:1',), known_ids=('receipt:1',),
        )
        self.assertIn('CONTRADICTORY_MECHANICS', {f.code for f in findings})

    def test_check_blocks_contradiction_around_receipt_backed_outcome(self):
        source = c.SourceRef(kind='operation_receipt', source_id='receipt:give', revision=1,
            game_scope='run:1', npc_id=1, attribution='server', visibility='public')
        receipt = c.VerifiedEvent(evidence_id='event:give', kind='verified_event',
            content='The NPC gave the player 1 wood.', sources=(source,), created_at='2026-01-01T00:00:00Z')
        reply = c.AssembledReply(text_id='final:2',
            final_text='I gave you 1 wood. Actually, I kept it and gave you nothing.',
            beats=('I gave you 1 wood. Actually, I kept it and gave you nothing.',),
            segment_spans={}, evidence_dependencies=(source,), candidate_continuity_changes=())
        context = SimpleNamespace(revisions=c.RevisionSet(resources={}), facts=(receipt,))
        report = self.validator.check(reply, context, SimpleNamespace(facts=(receipt,)))
        self.assertIn('CONTRADICTORY_MECHANICS', {f.code for f in report.findings})

    def test_check_blocks_contradiction_around_actual_operation_receipt(self):
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/contracts-t02-valid.json').read_text())
        receipt = c.OperationReceipt.model_validate(raw['receipt'])
        source = c.SourceRef(kind='operation_receipt', source_id=receipt.receipt_id, revision=1,
            game_scope='run:1', npc_id=1, attribution='server', visibility='public')
        text = 'I gave you 1 wood. Actually, I kept the wood and gave you nothing.'
        reply = c.AssembledReply(text_id='final:receipt',
            final_text=text, beats=(text,),
            segment_spans={'receipt:slot': c.TextSpan(text_id='final:receipt', start=0,
                end=len('I gave you 1 wood.'))},
            evidence_dependencies=(source,), candidate_continuity_changes=())
        context = SimpleNamespace(revisions=c.RevisionSet(resources={}), receipts=(receipt,))
        report = self.validator.check(reply, context, SimpleNamespace(receipts=(receipt,)))
        self.assertIn('CONTRADICTORY_MECHANICS', {f.code for f in report.findings})

    def test_stale_and_private_evidence_dependencies_block(self):
        stale = c.SourceRef(kind='inventory', source_id='inventory:wood', revision=2,
            game_scope='run:1', npc_id=1, attribution='server', visibility='public')
        private = c.SourceRef(kind='quest', source_id='quest:hidden', revision=4,
            game_scope='run:1', npc_id=1, attribution='server', visibility='server_private')
        reply = c.AssembledReply(text_id='final:3', final_text='The quest is complete.',
            beats=('The quest is complete.',), segment_spans={}, evidence_dependencies=(stale, private),
            candidate_continuity_changes=())
        context = SimpleNamespace(revisions=c.RevisionSet(resources={'inventory:wood': 3, 'quest:hidden': 4}))
        report = self.validator.check(reply, context, SimpleNamespace())
        codes = {f.code for f in report.findings}
        self.assertIn('STALE_EVIDENCE', codes)
        self.assertIn('PRIVATE_EVIDENCE_REFERENCE', codes)

    def test_category_word_in_unrelated_evidence_does_not_ground_claim(self):
        findings = self.validator.check_text('The route is north.', evidence={
            'route:1': {'kind': 'authored_knowledge', 'content': 'The routes are south of the mill.'}
        })
        self.assertIn('UNSUPPORTED_WORLD_CLAIM', {f.code for f in findings})


if __name__ == '__main__':
    unittest.main()
