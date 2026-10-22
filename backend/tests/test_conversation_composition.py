"""Pure exact-assembly cases; fixture budgets are test inputs, not defaults."""
import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.services.conversation import contracts as c

FIXTURES = Path(__file__).parent / 'fixtures/conversation'


class ReplyAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('app.services.conversation.composition'),
                             'ReplyAssembler is not implemented')
        self.module = importlib.import_module('app.services.conversation.composition')
        self.assembler = self.module.ReplyAssembler()
        self.raw = json.loads((FIXTURES / 'contracts-t02-valid.json').read_text())
        self.golden = json.loads((FIXTURES / 'composition-t01-golden.json').read_text())
        self.history = json.loads((FIXTURES / 'composition-t03-history.json').read_text())
        self.policy = c.ConversationPolicy(schema_version=1, policy_version='test:1', input_char_limit=500,
            total_deadline_seconds=10, provider_stage_budget_seconds=5, context_token_limit=1000,
            output_char_limit=600, beat_char_limit=80, queue_capacity=5, lease_duration_seconds=20,
            summary_trigger_turns=10, diagnostic_retention_seconds=100)
        self.source = dict(kind='inventory', source_id='inventory:1', revision=2, game_scope='run:1',
                           npc_id=1, attribution='server', visibility='public')
        self.fact = dict(kind='mechanical_fact', evidence_id='fact:1', content=self.golden['fact'],
                         sources=[self.source], created_at='2026-10-14T00:00:00Z')

    def candidate(self, segments=None, **updates):
        raw = copy.deepcopy(self.raw['candidate'])
        raw.update(segments=segments or raw['segments'], canon_candidates=[])
        raw.update(updates)
        return c.CandidateReply.model_validate(raw)

    def expressive(self, text, segment_id='prose'):
        return dict(kind='expressive', segment_id=segment_id, text=text, addressed_concern_ids=[])

    def slot(self, act='completed', **updates):
        return dict(kind='receipt_slot', segment_id='receipt-slot', receipt_id='receipt:1',
                    speech_act=act, renderer_id=f'receipt.{act}', **updates)

    def evidence(self, **updates):
        receipt = copy.deepcopy(self.raw['receipt'])
        raw = dict(turn=self.raw['turn'], text_id='final:1', facts=[self.fact], receipts=[receipt],
                   revisions={'resources': {'inventory:1': 2}}, resource_sources=[self.source],
                   receipt_sources=[dict(kind='operation_receipt', source_id='receipt:1',
                     revision=receipt['argument_digest'], game_scope='run:1', npc_id=1,
                     attribution='server', visibility='public')])
        raw.update(updates)
        return self.module.AssemblyEvidence.model_validate(raw)

    def assemble(self, candidate=None, evidence=None, policy=None):
        return self.assembler.assemble(candidate or self.candidate(), evidence or self.evidence(), policy or self.policy)

    def assert_error(self, result, code):
        self.assertIsNone(result.value)
        self.assertEqual(result.error.code, code)
        self.assertEqual(result.error.stage, 'composition.assemble')

    def test_exact_slots_keep_prose_and_server_owned_quantities(self):
        result = self.assemble().value
        self.assertIsNotNone(result)
        self.assertEqual(result.final_text, 'A🙂éZ ' + self.golden['fact'] + ' I gave you 1 wood.')
        self.assertEqual(''.join(result.beats), result.final_text)
        self.assertEqual([s.source_id for s in result.evidence_dependencies], ['inventory:1', 'receipt:1'])
        result.validate_segment_texts({'segment:1':'A🙂éZ', 'segment:2':self.golden['fact'], 'segment:3':'I gave you 1 wood.'})

    def test_receipt_golden_outcomes_never_upgrade_accepted_to_completed(self):
        for case in self.golden['receipts']:
            with self.subTest(case=case['label']):
                receipt = {**self.raw['receipt'], 'command_id':case['command'], 'outcome':case['outcome'],
                           'result':case['result'], 'activity_id':case['activity_id'], 'safe_reason_code':case['reason']}
                result = self.assemble(self.candidate([self.slot(case['outcome'])]), self.evidence(receipts=[receipt]))
                self.assertIsNone(result.error)
                self.assertEqual(result.value.final_text, case['want'])

    def test_command_golden_clauses_describe_actual_changed_flag(self):
        for case in self.golden['commands']:
            with self.subTest(case=case):
                receipt = {**self.raw['receipt'], 'command_id':case['command'],
                           'result':{'kind':'command', 'changed':case['changed']}}
                result = self.assemble(self.candidate([self.slot()]), self.evidence(receipts=[receipt]))
                self.assertEqual(result.value.final_text, case['want'])

    def test_unknown_fact_and_receipt_ids_fail_closed(self):
        for evidence in [self.evidence(facts=[]), self.evidence(receipts=[])]:
            self.assert_error(self.assemble(evidence=evidence), 'EVIDENCE_CHANGED')

    def test_stale_current_fact_and_missing_evidence_sources_fail_closed(self):
        for updates in [dict(revisions={'resources': {'inventory:1':3}}),
                        dict(revisions={'resources': {}}), dict(resource_sources=[]), dict(receipt_sources=[]),
                        dict(receipt_sources=[{**self.evidence().receipt_sources[0].model_dump(), 'revision':'different'}]),
                        dict(resource_sources=[{**self.source, 'revision':1}])]:
            with self.subTest(updates=updates):
                self.assert_error(self.assemble(evidence=self.evidence(**updates)), 'EVIDENCE_CHANGED')
        historical = {**self.raw['receipt'], 'after_revisions':{'resources':{'inventory:1':1}}}
        result = self.assemble(evidence=self.evidence(receipts=[historical]))
        self.assertIsNone(result.error)
        self.assertEqual(result.value.final_text, 'A🙂éZ ' + self.golden['fact'] + ' I gave you 1 wood.')

    def test_receipt_wrong_scope_npc_or_turn_cannot_support_speech(self):
        for update in [dict(game_scope='old'), dict(npc_id=2), dict(turn_id='turn:old')]:
            with self.subTest(update=update):
                self.assert_error(self.assemble(evidence=self.evidence(receipts=[{**self.raw['receipt'], **update}])), 'EVIDENCE_CHANGED')

    def inspection(self, outcome='accepted'):
        return {**self.raw['receipt'], 'command_id':'begin_ship_inspection', 'outcome':outcome,
                'result':{'kind':'activity', 'activity_id':'activity:1', 'stage':outcome},
                'activity_id':'activity:1', 'before_revisions':{'resources':{'activity:1':1}},
                'after_revisions':{'resources':{'activity:1':2}}}

    def activity_evidence(self, content, revision=3):
        source = {**self.source, 'kind':'activity', 'source_id':'activity:1', 'revision':revision}
        fact = {**self.fact, 'evidence_id':'activity-state:1', 'content':content, 'sources':[source]}
        evidence = self.evidence(facts=[fact], receipts=[self.inspection()],
            revisions={'resources':{'activity:1':3}}, resource_sources=[source])
        return evidence

    def test_historical_accepted_receipt_and_current_activity_render_separately(self):
        segments = [self.slot('accepted'), dict(kind='fact_slot', segment_id='current',
                    fact_id='activity-state:1', renderer_id='fact.exact')]
        for state in self.history['current_states']:
            with self.subTest(state=state):
                evidence = self.activity_evidence(state)
                receipt_before = evidence.receipts[0].model_dump_json()
                result = self.assemble(self.candidate(segments), evidence)
                self.assertIsNone(result.error)
                reply = result.value
                self.assertEqual(reply.final_text, self.history['accepted'] + ' ' + state)
                reply.validate_segment_texts({'receipt-slot':self.history['accepted'], 'current':state})
                self.assertEqual(''.join(reply.beats), reply.final_text)
                self.assertEqual([(s.source_id, s.revision) for s in reply.evidence_dependencies],
                    [('receipt:1', evidence.receipts[0].argument_digest), ('activity:1', 3)])
                self.assertEqual(evidence.receipts[0].model_dump_json(), receipt_before)
                self.assertEqual(evidence.receipts[0].outcome, 'accepted')

    def test_historical_receipt_needs_no_current_activity_projection(self):
        for outcome in ['accepted', 'completed']:
            for revisions in [{'resources':{'activity:1':3}}, {'resources':{}}]:
                with self.subTest(outcome=outcome, revisions=revisions):
                    evidence = self.evidence(facts=[], receipts=[self.inspection(outcome)],
                                             revisions=revisions, resource_sources=[])
                    result = self.assemble(self.candidate([self.slot(outcome)]), evidence)
                    self.assertIsNone(result.error)
                    self.assertEqual(result.value.final_text, self.history[outcome])
                    self.assertEqual(result.value.evidence_dependencies, evidence.receipt_sources)
                    result.value.validate_segment_texts({'receipt-slot':self.history[outcome]})

    def test_missing_or_stale_current_activity_cannot_publish_current_speech(self):
        candidate = self.candidate([self.slot('accepted'), dict(kind='fact_slot', segment_id='current',
            fact_id='activity-state:1', renderer_id='fact.exact')])
        stale = self.activity_evidence('The inspector is underway.', revision=2)
        missing = self.evidence(receipts=[self.inspection()], facts=[], revisions={'resources':{}}, resource_sources=[])
        for evidence in [stale, missing]:
            with self.subTest(evidence=evidence):
                self.assert_error(self.assemble(candidate, evidence), 'EVIDENCE_CHANGED')
        # Even a fresh activity fact cannot convert acceptance into receipt progress/completion.
        for act in ['progress', 'completed']:
            with self.subTest(act=act):
                self.assert_error(self.assemble(self.candidate([self.slot(act)]),
                    self.activity_evidence(self.history['current_states'][2])), 'INVALID_SCHEMA')

    def test_receipt_catalog_does_not_infer_current_state_at_commit_revision(self):
        for outcome in ['accepted', 'completed']:
            with self.subTest(outcome=outcome):
                source = {**self.source, 'kind':'activity', 'source_id':'activity:1'}
                evidence = self.evidence(receipts=[self.inspection(outcome)], facts=[],
                    revisions={'resources':{'activity:1':2}}, resource_sources=[source])
                reply = self.assemble(self.candidate([self.slot(outcome)]), evidence).value
                self.assertEqual(reply.final_text, self.history[outcome])
        wait = {**self.raw['receipt'], 'command_id':'wait', 'result':{'kind':'command','changed':True}}
        reply = self.assemble(self.candidate([self.slot()]), self.evidence(receipts=[wait])).value
        self.assertEqual(reply.final_text, self.history['wait'])

    def test_historical_receipt_authentication_still_fails_closed(self):
        receipt = self.inspection()
        original_source = self.evidence().receipt_sources[0].model_dump()
        for sources in [[], [{**original_source, 'revision':'wrong'}],
                        [{**original_source, 'kind':'activity'}],
                        [{**original_source, 'game_scope':'old'}],
                        [{**original_source, 'npc_id':2}],
                        [{**original_source, 'visibility':'server_private'}]]:
            with self.subTest(sources=sources):
                evidence = self.evidence(receipts=[receipt], facts=[], revisions={'resources':{}},
                    resource_sources=[], receipt_sources=sources)
                self.assert_error(self.assemble(self.candidate([self.slot('accepted')]), evidence), 'EVIDENCE_CHANGED')

    def test_fact_out_of_scope_private_or_nonfactual_provenance_is_rejected(self):
        for update in [dict(game_scope='old'), dict(npc_id=2), dict(visibility='server_private')]:
            source = {**self.source, **update}
            with self.subTest(update=update):
                self.assert_error(self.assemble(evidence=self.evidence(facts=[{**self.fact,'sources':[source]}],resource_sources=[source])), 'EVIDENCE_CHANGED')
        report = dict(kind='player_report', evidence_id='fact:1',content='I own 99 wood.',
                      sources=[{**self.source,'kind':'player_message'}],created_at=self.fact['created_at'],
                      attribution='player',uncertainty='unverified')
        self.assert_error(self.assemble(evidence=self.evidence(facts=[report])), 'EVIDENCE_CHANGED')

    def test_invalid_speech_act_and_progress_without_activity_projection_fail(self):
        for act in ['accepted','progress','rejected']:
            with self.subTest(act=act):
                self.assert_error(self.assemble(self.candidate([self.slot(act)])), 'INVALID_SCHEMA')
        accepted = {**self.raw['receipt'], 'command_id':'begin_ship_inspection', 'outcome':'accepted',
                    'result':{'kind':'activity','activity_id':'activity:1','stage':'accepted'}, 'activity_id':'activity:1'}
        self.assert_error(self.assemble(self.candidate([self.slot('completed')]), self.evidence(receipts=[accepted])), 'INVALID_SCHEMA')

    def test_repaired_final_span_map_relocates_unicode_canon_after_slot_expansion(self):
        candidate = self.candidate([self.raw['candidate']['segments'][1],self.raw['candidate']['segments'][0]],
                                   canon_candidates=self.raw['candidate']['canon_candidates'],
                                   source={**self.raw['candidate']['source'],'origin':'repaired','source_id':'repair:1'})
        reply = self.assemble(candidate).value
        span = reply.candidate_continuity_changes[0].supporting_span
        self.assertEqual(span.text_id, 'final:1')
        self.assertEqual(span.start, len(self.golden['fact']) + 2)
        self.assertEqual(span.resolve({reply.text_id:reply.final_text}), '🙂é')
        self.assertEqual(reply.segment_spans['segment:1'].start, len(self.golden['fact']) + 1)

    def test_long_story_and_unbroken_text_have_lossless_bounded_beats(self):
        for story in [('The sea remembers. '*25)+'🙂 The end.', 'x'*600, 'Fear can destroy your confidence. I have a soft spot for old stories.']:
            with self.subTest(story_length=len(story)):
                result = self.assemble(self.candidate([self.expressive(story)]))
                self.assertIsNone(result.error)
                self.assertEqual(result.value.final_text, story)
                self.assertEqual(''.join(result.value.beats), story)
                self.assertTrue(all(beat.strip() and len(beat)<=80 for beat in result.value.beats))
        reply = self.assemble(self.candidate([self.expressive('The sea remembers. '*25)])).value
        self.assertTrue(all(beat.endswith(' ') for beat in reply.beats[:-1]))

    def test_hard_600_character_maximum_never_truncates(self):
        at_limit = self.assemble(self.candidate([self.expressive('x'*600)]))
        self.assertEqual(at_limit.value.final_text, 'x'*600)
        self.assert_error(self.assemble(self.candidate([self.expressive('x'*601)])), 'INVALID_BOUNDS')
        with self.assertRaises(ValidationError):
            c.ConversationPolicy.model_validate({**self.policy.model_dump(), 'output_char_limit':601})
        policy = c.ConversationPolicy.model_validate({**self.policy.model_dump(), 'output_char_limit':80})
        # The inserted separator and server-rendered fact count toward the total.
        candidate = self.candidate([self.expressive('x'*30), self.raw['candidate']['segments'][1]])
        self.assert_error(self.assemble(candidate, policy=policy), 'INVALID_BOUNDS')

    def test_beats_retain_whitespace_when_a_nonblank_partition_exists(self):
        policy = c.ConversationPolicy.model_validate({**self.policy.model_dump(), 'beat_char_limit':5})
        for text in ['abcdefghij   ', 'aaaa       b', '   abcd   efghij  ']:
            with self.subTest(text=text):
                result = self.assemble(self.candidate([self.expressive(text)]), policy=policy)
                self.assertIsNone(result.error)
                self.assertEqual(''.join(result.value.beats), text)
                self.assertTrue(all(beat.strip() and len(beat)<=5 for beat in result.value.beats))
        self.assert_error(self.assemble(self.candidate([self.expressive('a          b')]), policy=policy), 'INVALID_BOUNDS')

    def test_short_reply_stays_in_one_readable_beat(self):
        reply = self.assemble(self.candidate([self.expressive('The sea remembers.')])).value
        self.assertEqual(reply.beats, ('The sea remembers.',))

    def test_policy_version_mismatch_is_rejected(self):
        source = {**self.raw['candidate']['source'], 'policy_versions':{'bounds':'old'}}
        self.assert_error(self.assemble(self.candidate(source=source)), 'EVIDENCE_CHANGED')

    def test_evidence_is_detached_immutable_and_rejects_duplicate_ids(self):
        raw = json.loads(self.evidence().model_dump_json())
        value = self.module.AssemblyEvidence.model_validate(raw)
        raw['facts'][0]['content'] = 'Changed'
        self.assertEqual(value.facts[0].content, self.golden['fact'])
        with self.assertRaises(ValidationError):
            value.text_id = 'changed'
        for field in ['facts','receipts','resource_sources','receipt_sources']:
            raw = json.loads(value.model_dump_json())
            raw[field] *= 2
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.module.AssemblyEvidence.model_validate(raw)

    def test_import_has_no_infrastructure_and_assembler_exposes_no_execution(self):
        script = "import sys; from app.services.conversation.composition import ReplyAssembler; assert not any(n.split('.')[0] in {'sqlalchemy','fastapi','httpx','openai'} for n in sys.modules); assert not hasattr(ReplyAssembler(), 'execute')"
        result = subprocess.run([sys.executable,'-c',script], capture_output=True,text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
