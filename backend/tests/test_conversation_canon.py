"""Pure canon admission policy tests (no provider or persistence)."""
import importlib
import unittest

c = importlib.import_module('app.services.conversation.contracts')
from app.services.conversation.canon import CanonPolicy, CanonReply


class Rules:
    def __init__(self, rejected=(), grounded=True):
        self.rejected = set(rejected)
        self.grounded = grounded

    def validated_claim(self, candidate, final_text, span_text, evidence):
        return candidate.candidate_id not in self.rejected

    def needs_affordance_grounding(self, candidate, span_text):
        return any(word in (candidate.content + ' ' + span_text).lower()
                   for word in ('shop', 'cache', 'recipe'))

    def affordance_is_grounded(self, candidate, span_text, evidence):
        return self.grounded and bool(evidence)

    def category_for(self, candidate):
        return 'background'


def make_candidate(cid, text, kind='add', subject='npc', predicate='biography', content=None):
    content = content or text
    return c.CanonCandidate(candidate_id=cid, kind=kind, subject=subject, predicate=predicate,
        content=content, supporting_span=c.TextSpan(text_id='segment:1', start=0, end=len(text)),
        expected_revision=0 if kind == 'revise' else None,
        correction_candidate_id='correction:1' if kind == 'revise' else None)


def make_reply(text, candidate):
    final_span = c.TextSpan(text_id='final:1', start=0, end=len(text))
    assembled = c.AssembledReply(text_id='final:1', final_text=text, beats=(text,),
        segment_spans={'segment:1': final_span},
        evidence_dependencies=(), candidate_continuity_changes=(
            c.ContinuityChangeRef(candidate_id=candidate.candidate_id, supporting_span=final_span),))
    candidate_reply = c.CandidateReply(segments=(c.ExpressiveSegment(kind='expressive', segment_id='segment:1',
            text=text, addressed_concern_ids=()),),
        source=c.ReplySource(origin='generated', source_id='provider:1', schema_version=1, policy_versions={}),
        canon_candidates=(candidate,))
    return CanonReply(candidate_reply, assembled)


class CanonPolicyTests(unittest.TestCase):
    def test_admits_only_exact_validated_final_speech_additions_as_narrative(self):
        text = 'My father taught me to mend things.'
        candidate = make_candidate('claim:1', text, subject='npc:7', predicate='background')
        reply = make_reply(text, candidate)
        change, = CanonPolicy(Rules()).plan(reply, (), ())
        self.assertEqual(change.kind, 'add')
        self.assertEqual(change.content, candidate.content)
        self.assertEqual(change.supporting_span.resolve({'final:1': text}), text)
        self.assertEqual((change.origin, change.authority), ('generated', 'narrative_only'))

    def test_rejects_candidate_missing_from_final_span_map(self):
        text = 'I dreamed of sailing.'
        candidate = make_candidate('claim:1', text)
        reply = make_reply(text, candidate)
        assembled = reply.assembled.model_copy(update={'candidate_continuity_changes': ()})
        self.assertEqual(CanonPolicy(Rules()).plan(CanonReply(reply.candidate_reply, assembled), (), ()), ())

    def test_rejects_failed_validation_and_stale_or_mismatched_spans(self):
        text = 'My aunt lived here.'
        candidate = make_candidate('claim:1', text)
        reply = make_reply(text, candidate)
        self.assertEqual(CanonPolicy(Rules(rejected={'claim:1'})).plan(reply, (), ()), ())
        bad_ref = c.ContinuityChangeRef(candidate_id='claim:1',
            supporting_span=c.TextSpan(text_id='final:1', start=0, end=4))
        bad_reply = reply.assembled.model_copy(update={'candidate_continuity_changes': (bad_ref,)})
        self.assertEqual(CanonPolicy(Rules()).plan(CanonReply(reply.candidate_reply, bad_reply), (), ()), ())

    def test_rejects_final_ref_not_linked_to_fresh_source_segment_mapping(self):
        claim = 'My father taught me to mend things.'
        candidate = make_candidate('claim:1', claim)
        assembled = c.AssembledReply(text_id='final:1', final_text=claim + ' ' + claim,
            beats=(claim + ' ' + claim,),
            segment_spans={'segment:1': c.TextSpan(text_id='final:1', start=0, end=len(claim))},
            evidence_dependencies=(), candidate_continuity_changes=(
                c.ContinuityChangeRef(candidate_id='claim:1', supporting_span=c.TextSpan(
                    text_id='final:1', start=len(claim) + 1, end=2 * len(claim) + 1)),))
        source = c.CandidateReply(segments=(c.ExpressiveSegment(kind='expressive', segment_id='segment:1',
                text=claim, addressed_concern_ids=()),),
            source=c.ReplySource(origin='generated', source_id='provider:1', schema_version=1, policy_versions={}),
            canon_candidates=(candidate,))
        self.assertEqual(CanonPolicy(Rules()).plan(CanonReply(source, assembled), (), ()), ())

    def test_authored_identity_wins_and_revisions_are_left_to_t02(self):
        text = 'I am a blacksmith.'
        candidate = make_candidate('claim:1', text, subject='npc:7', predicate='identity', content='I am a baker.')
        reply = make_reply(text, candidate)
        authored = c.CanonRecord(canon_id='auth:1', revision=0, game_scope='run:1', npc_id=7,
            subject='npc:7', predicate='identity', content='I am a blacksmith.', category='identity',
            origin='authored', authority='authored', status='active', supersedes_revision=None,
            introduced_turn_id='turn:0', accepted_claim_evidence=c.TextSpan(text_id='seed:1',start=0,end=1))
        self.assertEqual(CanonPolicy(Rules()).plan(reply, (authored,), ()), ())
        revise = make_candidate('claim:2', text, kind='revise')
        self.assertEqual(CanonPolicy(Rules()).plan(make_reply(text, revise), (), ()), ())

    def test_allows_relatives_and_historical_places_but_requires_grounding_for_affordances(self):
        for claim in ('My sister lives far away.', 'I once dreamed of sailing beyond the island.'):
            candidate = make_candidate('claim:' + str(len(claim)), claim)
            self.assertEqual(len(CanonPolicy(Rules()).plan(make_reply(claim, candidate), (), ())), 1)
        for claim in ('My sister runs a shop north of the well.', 'I left a cache by the old tree.', 'I know a recipe for moon bread.'):
            candidate = make_candidate('claim:' + str(len(claim)), claim)
            self.assertEqual(CanonPolicy(Rules()).plan(make_reply(claim, candidate), (), ()), ())
            evidence = (c.SourceRef(kind='authored_content', source_id='world:1', revision=1,
                game_scope='run:1', npc_id=7, attribution='server', visibility='server_private'),)
            grounded_assembled = c.AssembledReply(text_id='final:1', final_text=claim, beats=(claim,),
                segment_spans={'segment:1': c.TextSpan(text_id='final:1', start=0, end=len(claim))},
                evidence_dependencies=evidence, candidate_continuity_changes=(
                    c.ContinuityChangeRef(candidate_id=candidate.candidate_id,
                        supporting_span=c.TextSpan(text_id='final:1', start=0, end=len(claim))),))
            grounded_reply = make_reply(claim, candidate)
            grounded_assembled = grounded_assembled.model_copy(update={'evidence_dependencies': evidence})
            self.assertEqual(len(CanonPolicy(Rules()).plan(CanonReply(grounded_reply.candidate_reply, grounded_assembled), (), ())), 1)
        self.assertEqual(CanonPolicy(Rules(grounded=False)).plan(
            make_reply('I know a recipe for moon bread.', make_candidate('claim:recipe', 'I know a recipe for moon bread.')), (), ()), ())


if __name__ == '__main__':
    unittest.main()


# T02 fixtures deliberately distinguish semantic acceptance from exact content
# support: both speeches contain the new biography, only one accepts it.
import json
from pathlib import Path

T02 = json.loads((Path(__file__).resolve().parents[2] /
    'docs/evidence/conversation-redesign-canon/t02-correction-fixtures.json').read_text())


class CorrectionRules(Rules):
    def validated_correction(self, candidate, correction, head, final_text,
                             span_text, correction_texts, evidence):
        return (span_text == T02['accepted_speech'] and
                correction_texts == (T02['player_message'],) and
                correction.content == T02['replacement_content'] and
                candidate.content == T02['replacement_content'])


def t02_head(revision=2, status='active', origin='generated'):
    return c.CanonRecord(canon_id=T02['canon_id'], revision=revision,
        game_scope='run:1', npc_id=7, subject='npc:7', predicate='biography',
        content=T02['old_content'], category='background', origin=origin,
        authority='authored' if origin == 'authored' else 'narrative_only',
        status=status, supersedes_revision=revision - 1 if revision else None,
        introduced_turn_id='turn:old',
        accepted_claim_evidence=c.TextSpan(text_id='final:old', start=0, end=len(T02['old_content'])))


def t02_reply(text=None, expected_revision=2, target=None):
    text = text or T02['accepted_speech']
    candidate = make_candidate('revise:aunt', text, kind='revise',
        subject='npc:7', content=T02['replacement_content']).model_copy(update={
            'expected_revision': expected_revision, 'correction_candidate_id': T02['correction_id']})
    reply = make_reply(text, candidate)
    source = c.SourceRef(kind='player_message', source_id='message:correction',
        revision=0, game_scope='run:1', npc_id=7, attribution='player:1', visibility='public')
    correction = c.CorrectionCandidate(correction_id=T02['correction_id'],
        target_reference_id=target or T02['canon_id'], attribution='player:1',
        content=T02['replacement_content'], source_spans=(c.TextSpan(
            text_id='message:correction', start=0, end=len(T02['player_message'])),))
    return CanonReply(reply.candidate_reply,
        reply.assembled.model_copy(update={'evidence_dependencies': (source,)}),
        corrections=(correction,), correction_texts={'message:correction': T02['player_message']})


class CanonCorrectionTests(unittest.TestCase):
    def test_accepted_correction_keeps_head_identity_and_superseded_lineage(self):
        head = t02_head()
        previous = t02_head(revision=1, status='superseded')
        before = (previous.model_dump(), head.model_dump())
        changes = CanonPolicy(CorrectionRules()).plan(t02_reply(), (previous, head), ())
        self.assertEqual(len(changes), 1)
        change, = changes
        self.assertIsInstance(change, c.ReviseCanonChange)
        self.assertEqual((change.canon_id, change.expected_revision, change.correction_link),
                         ('canon:smithing', 2, 'correction:aunt'))
        self.assertEqual((change.content, change.category, change.origin, change.authority),
                         ('I learned smithing from my aunt.', 'background', 'generated', 'narrative_only'))
        self.assertEqual(change.supporting_span.resolve({'final:1': T02['accepted_speech']}),
                         T02['accepted_speech'])
        self.assertEqual((previous.model_dump(), head.model_dump()), before)

    def test_contradiction_only_remains_attributed_correction_without_revision(self):
        reply = t02_reply(T02['contradiction_only_speech'])
        self.assertEqual(CanonPolicy(CorrectionRules()).plan(reply, (t02_head(),), ()), ())
        self.assertEqual(reply.corrections[0].attribution, 'player:1')
        self.assertEqual(reply.corrections[0].content, T02['replacement_content'])

    def test_revision_fails_closed_without_acceptance_checker(self):
        self.assertEqual(CanonPolicy(Rules()).plan(t02_reply(), (t02_head(),), ()), ())
        class FailedChecker(CorrectionRules):
            def validated_correction(self, *args):
                raise RuntimeError('semantic checker unavailable')
        self.assertEqual(CanonPolicy(FailedChecker()).plan(t02_reply(), (t02_head(),), ()), ())
        class TruthyChecker(CorrectionRules):
            def validated_correction(self, *args):
                return 'accepted'
        self.assertEqual(CanonPolicy(TruthyChecker()).plan(t02_reply(), (t02_head(),), ()), ())

    def test_revision_requires_exact_link_target_and_attributed_player_evidence(self):
        from dataclasses import replace
        reply = t02_reply()
        correction, = reply.corrections
        source, = reply.assembled.evidence_dependencies
        cases = (
            replace(reply, corrections=()),
            replace(reply, corrections=(correction, correction)),
            t02_reply(target='canon:unrelated'),
            replace(reply, correction_texts={}),
            replace(reply, correction_texts={'message:correction': 'short'}),
            replace(reply, assembled=reply.assembled.model_copy(update={'evidence_dependencies': ()})),
            replace(reply, assembled=reply.assembled.model_copy(update={
                'evidence_dependencies': (source.model_copy(update={'kind': 'interpretation'}),)})),
            replace(reply, assembled=reply.assembled.model_copy(update={
                'evidence_dependencies': (source.model_copy(update={'attribution': 'player:other'}),)})),
            replace(reply, assembled=reply.assembled.model_copy(update={
                'evidence_dependencies': (source.model_copy(update={'game_scope': 'run:other'}),)})),
            replace(reply, assembled=reply.assembled.model_copy(update={
                'evidence_dependencies': (source.model_copy(update={'npc_id': 8}),)})),
        )
        for index, case in enumerate(cases):
            with self.subTest(case=index):
                self.assertEqual(CanonPolicy(CorrectionRules()).plan(case, (t02_head(),), ()), ())

    def test_concurrent_or_ambiguous_heads_reject_expected_revision(self):
        for heads in ((), (t02_head(revision=3),), (t02_head(status='superseded'),),
                      (t02_head(), t02_head(revision=3))):
            with self.subTest(heads=heads):
                self.assertEqual(CanonPolicy(CorrectionRules()).plan(t02_reply(), heads, ()), ())
        self.assertEqual(CanonPolicy(CorrectionRules()).plan(t02_reply(expected_revision=1),
            (t02_head(),), ()), ())

    def test_authored_identity_cannot_be_rewritten_by_accepted_correction(self):
        authored = t02_head(origin='authored')
        self.assertEqual(CanonPolicy(CorrectionRules()).plan(t02_reply(), (authored,), ()), ())
        self.assertEqual(CanonPolicy(CorrectionRules()).plan(t02_reply(), (t02_head(),), (authored,)), ())

    def test_ordinary_followup_cannot_silently_change_accepted_biography(self):
        text = 'I learned smithing from my neighbor.'
        candidate = make_candidate('claim:later', text, subject='npc:7')
        self.assertEqual(CanonPolicy(CorrectionRules()).plan(make_reply(text, candidate),
            (t02_head(),), ()), ())

    def test_rebuilt_final_span_rejects_draft_offsets_and_admits_fresh_offsets(self):
        from dataclasses import replace
        reply = t02_reply()
        prefix = 'Let me correct that. '
        speech = T02['accepted_speech']
        final_span = c.TextSpan(text_id='final:rebuilt', start=len(prefix), end=len(prefix) + len(speech))
        fresh = c.AssembledReply(text_id='final:rebuilt', final_text=prefix + speech,
            beats=(prefix + speech,), segment_spans={'segment:1': final_span},
            evidence_dependencies=reply.assembled.evidence_dependencies,
            candidate_continuity_changes=(c.ContinuityChangeRef(candidate_id='revise:aunt',
                supporting_span=final_span),))
        changes = CanonPolicy(CorrectionRules()).plan(replace(reply, assembled=fresh), (t02_head(),), ())
        self.assertEqual(len(changes), 1)
        change, = changes
        self.assertEqual(change.supporting_span, final_span)
        stale = fresh.model_copy(update={'candidate_continuity_changes': (
            c.ContinuityChangeRef(candidate_id='revise:aunt', supporting_span=c.TextSpan(
                text_id='final:rebuilt', start=0, end=len(speech))),)})
        self.assertEqual(CanonPolicy(CorrectionRules()).plan(replace(reply, assembled=stale),
            (t02_head(),), ()), ())

    def test_failed_claim_validation_and_practical_affordance_block_revisions(self):
        self.assertEqual(CanonPolicy(CorrectionRules(rejected={'revise:aunt'})).plan(
            t02_reply(), (t02_head(),), ()), ())
        class PracticalCorrection(CorrectionRules):
            def needs_affordance_grounding(self, candidate, span_text):
                return True
        self.assertEqual(CanonPolicy(PracticalCorrection(grounded=False)).plan(
            t02_reply(), (t02_head(),), ()), ())
