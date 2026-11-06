"""Offline, advisory validation hooks for coverage, identity and style."""
import unittest

from app.services.conversation import contracts as c
from app.services.conversation.validation import ResponseValidator


def reply(text, text_id='final:quality'):
    return c.AssembledReply(text_id=text_id, final_text=text, beats=(text,),
        segment_spans={}, evidence_dependencies=(), candidate_continuity_changes=())


class ResponseQualityHooksTests(unittest.TestCase):
    def setUp(self):
        self.validator = ResponseValidator()

    def test_unaddressed_mixed_concern_is_advisory_even_when_some_coverage_exists(self):
        findings = self.validator.review_quality(reply('I can bring you rope.'),
            concern_ids=('concern:request', 'concern:emotion'),
            covered_concern_ids=('concern:request',))
        self.assertIn('CONCERN_UNADDRESSED', {item.code for item in findings})
        self.assertTrue(all(item.severity == 'advisory' for item in findings))
        self.assertTrue(all(item.category == 'coverage' for item in findings))

    def test_missing_coverage_assessment_is_marked_unassessed(self):
        findings = self.validator.review_quality(reply('Hello.'),
            concern_ids=('concern:1',), covered_concern_ids=None)
        self.assertIn('CONCERN_COVERAGE_UNASSESSED', {item.code for item in findings})

    def test_speaker_identity_mismatch_is_advisory(self):
        findings = self.validator.review_quality(reply('Hello.'),
            expected_speaker_id='npc:1', actual_speaker_id='npc:2')
        self.assertIn('SPEAKER_IDENTITY_MISMATCH', {item.code for item in findings})
        self.assertTrue(all(item.severity == 'advisory' for item in findings))

    def test_exact_repetition_is_flagged_but_repeated_fact_with_new_wording_is_not(self):
        repeated = self.validator.review_quality(reply('The tide is high.'),
            recent_replies=('The tide is high.',))
        self.assertIn('EXACT_RECENT_REPETITION', {item.code for item in repeated})
        purposeful = self.validator.review_quality(reply('The water has risen.'),
            recent_replies=('The tide is high.',))
        self.assertNotIn('EXACT_RECENT_REPETITION', {item.code for item in purposeful})

    def test_pacing_limit_is_injected_and_only_advisory(self):
        findings = self.validator.review_quality(reply('One two three four five.'),
            max_pacing_words=3)
        self.assertIn('PACING_LIMIT_EXCEEDED', {item.code for item in findings})
        self.assertTrue(all(item.severity == 'advisory' for item in findings))

    def test_invalid_assessment_ids_are_not_silently_used(self):
        findings = self.validator.review_quality(reply('Hello.'),
            concern_ids=('concern:1',), covered_concern_ids=('concern:other',))
        self.assertIn('QUALITY_ASSESSMENT_INVALID', {item.code for item in findings})


if __name__ == '__main__':
    unittest.main()
