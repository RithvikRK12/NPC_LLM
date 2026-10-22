"""T06 validator projections are strict, scoped values, not authority."""
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from app.services.conversation import contracts as c


FIXTURE = Path(__file__).parent / 'fixtures/conversation/contracts-t06-valid.json'


class ValidatorProjectionContractTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(FIXTURE.read_text())

    def test_versioned_claims_bind_to_exact_final_reply_spans(self):
        claims = c.ValidatorClaimProjection.model_validate(self.raw['claims'])
        reply = c.AssembledReply.model_validate(self.raw['reply'])
        claims.validate_against(reply)
        self.assertEqual(c.ValidatorClaimProjection.model_validate_json(claims.model_dump_json()), claims)
        for span in [dict(text_id='reply:1', start=0, end=99), dict(text_id='other', start=0, end=12)]:
            malformed = {**self.raw['claims'], 'claims': [{**self.raw['claims']['claims'][0], 'span': span}]}
            with self.subTest(span=span), self.assertRaises((ValidationError, ValueError)):
                c.ValidatorClaimProjection.model_validate(malformed).validate_against(reply)

    def test_claim_coverage_is_explicit_and_tied_to_exact_text(self):
        raw = self.raw['claims']
        missing = dict(raw)
        missing.pop('coverage_status', None)
        with self.assertRaises(ValidationError):
            c.ValidatorClaimProjection.model_validate(missing)
        for status in ('partial', 'unavailable', 'complete'):
            projection = c.ValidatorClaimProjection.model_validate({**raw, 'coverage_status':status})
            self.assertEqual(projection.coverage_status, status)
        with self.assertRaises(ValidationError):
            c.ValidatorClaimProjection.model_validate({**raw, 'coverage_status':'maybe'})
        wrong_text = c.AssembledReply.model_validate({**self.raw['reply'], 'text_id':'reply:other'})
        with self.assertRaises(ValueError):
            c.ValidatorClaimProjection.model_validate({**raw, 'coverage_status':'complete'}).validate_against(wrong_text)

    def test_evidence_is_scoped_current_canonical_and_narrative_only(self):
        evidence = c.ValidatorEvidenceProjection.model_validate(self.raw['evidence'])
        self.assertEqual(c.ValidatorEvidenceProjection.model_validate_json(evidence.model_dump_json()), evidence)
        claims = c.ValidatorClaimProjection.model_validate(self.raw['claims'])
        comparisons = c.ValidatorComparisonProjection.model_validate(self.raw['comparisons'])
        for change in [
            {'claims': [{**self.raw['evidence']['claims'][0], 'visibility': 'server_private'}, *self.raw['evidence']['claims'][1:]]},
            {'claims': [{**self.raw['evidence']['claims'][0], 'authority': 'gameplay'}, *self.raw['evidence']['claims'][1:]]},
            {'claims': [{**self.raw['evidence']['claims'][0], 'authority': 'authored'}, *self.raw['evidence']['claims'][1:]]},
        ]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                c.ValidatorEvidenceProjection.model_validate({**self.raw['evidence'], **change})
        for altered_claims, altered_evidence in [
            (claims, c.ValidatorEvidenceProjection.model_validate({**self.raw['evidence'], 'game_scope': 'other'})),
            (claims, c.ValidatorEvidenceProjection.model_validate({**self.raw['evidence'], 'npc_id': 3})),
            (claims, c.ValidatorEvidenceProjection.model_validate({**self.raw['evidence'], 'claims': [{**self.raw['evidence']['claims'][0], 'canon_id': 'other'}, self.raw['evidence']['claims'][1]]})),
            (claims, c.ValidatorEvidenceProjection.model_validate({**self.raw['evidence'], 'claims': [{**self.raw['evidence']['claims'][0], 'revision': 7}, self.raw['evidence']['claims'][1]]})),
        ]:
            with self.assertRaises(ValueError):
                comparisons.validate_against(altered_claims, altered_evidence)

    def test_comparison_outcomes_are_explicit_and_unknown_is_not_support(self):
        comparisons = c.ValidatorComparisonProjection.model_validate(self.raw['comparisons'])
        claims = c.ValidatorClaimProjection.model_validate(self.raw['claims'])
        evidence = c.ValidatorEvidenceProjection.model_validate(self.raw['evidence'])
        comparisons.validate_against(claims, evidence)
        by_outcome = {item.outcome: item for item in comparisons.comparisons}
        self.assertEqual(set(by_outcome), {'supported', 'contradicted', 'unknown'})
        self.assertFalse(by_outcome['unknown'].is_consistent)
        self.assertFalse(by_outcome['contradicted'].is_consistent)
        self.assertTrue(by_outcome['supported'].is_consistent)
        self.assertEqual(comparisons.outcome_for('absent', 'canon:1', 3), 'unknown')
        with self.assertRaises(ValueError):
            comparisons.validate_against(claims, c.ValidatorEvidenceProjection.model_validate({**self.raw['evidence'], 'game_scope': 'other'}))
        with self.assertRaises(ValueError):
            comparisons.validate_against(c.ValidatorClaimProjection.model_validate({**self.raw['claims'], 'claims': []}), evidence)
        bad = {**self.raw['comparisons'], 'comparisons': [{**self.raw['comparisons']['comparisons'][0], 'outcome': 'maybe'}]}
        with self.assertRaises(ValidationError):
            c.ValidatorComparisonProjection.model_validate(bad)

    def test_nested_claim_and_evidence_values_are_immutable(self):
        claims = c.ValidatorClaimProjection.model_validate(self.raw['claims'])
        with self.assertRaises(ValidationError):
            claims.claims[0].subject = 'changed'
        evidence = c.ValidatorEvidenceProjection.model_validate(self.raw['evidence'])
        with self.assertRaises(ValidationError):
            evidence.claims[0].revision = 9


if __name__ == '__main__':
    unittest.main()
