"""T02 pure boundaries; literal fixtures, no database/provider/network."""
import copy
import json
from pathlib import Path
import unittest

from pydantic import TypeAdapter, ValidationError
from app.services.conversation import contracts as c

FIXTURE = Path(__file__).parent / 'fixtures/conversation/contracts-t02-valid.json'


class TurnValueContractsTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(c, 'TurnProposal'), 'T02 turn contracts are absent')
        self.raw = json.loads(FIXTURE.read_text())

    def proposal(self, **updates):
        raw = dict(concerns=[dict(concern_id='concern:1', kind='request', message_spans=[dict(text_id='message:1', start=2, end=6)])],
                   references=[dict(kind='resolved_entity', reference=self.raw['operation']['target'])],
                   reports=[], correction_candidates=[], operation_candidates=[self.raw['operation']],
                   interaction_links=[], reply=self.raw['candidate']['segments'],
                   canon_candidates=self.raw['candidate']['canon_candidates'])
        return {**raw, **updates}

    def context(self, **updates):
        raw = dict(turn=self.raw['turn'], current_message=dict(text_id='message:1', text='A🙂wood'),
                   character_profile=[], active_canon=[], visible_recent_turns=[], summaries=[], reports=[],
                   interpretations=[], visible_facts=[], capabilities=[], pending_interactions=[self.raw['pending']],
                   revisions={'resources': {}}, policy_versions={'bounds': 'test:1'})
        return {**raw, **updates}

    def test_fixture_roundtrips_all_public_composite_values(self):
        for name, cls in [('operation', c.OperationCandidate), ('pending', c.PendingInteraction),
                          ('candidate', c.CandidateReply), ('receipt', c.OperationReceipt)]:
            with self.subTest(name=name):
                value = cls.model_validate(self.raw[name])
                self.assertEqual(json.loads(value.model_dump_json()), self.raw[name])
        for cls, raw in [(c.TurnProposal, self.proposal()), (c.ContextPacket, self.context())]:
            value = cls.model_validate(raw)
            self.assertEqual(json.loads(value.model_dump_json()), raw)

    def test_segments_strict_union_rejects_code_quantities_and_mismatched_renderer(self):
        adapter = TypeAdapter(c.ReplySegment)
        for raw in self.raw['candidate']['segments']:
            self.assertEqual(json.loads(adapter.dump_json(adapter.validate_python(raw))), raw)
        for change in [dict(kind='template'), dict(renderer_id='{{inventory.wood}}'),
                       dict(renderer_id='eval'), dict(quantity=8), dict(text='quantity 8'),
                       dict(renderer_id='receipt.completed')]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                adapter.validate_python({**self.raw['candidate']['segments'][1], **change})
        for act, renderer in [('accepted','receipt.accepted'), ('progress','receipt.progress'), ('completed','receipt.completed'), ('rejected','receipt.rejected')]:
            value = adapter.validate_python({**self.raw['candidate']['segments'][2], 'speech_act':act, 'renderer_id':renderer})
            self.assertEqual(value.speech_act, act)
        with self.assertRaises(ValidationError):
            adapter.validate_python({**self.raw['candidate']['segments'][2], 'speech_act':'accepted'})

    def test_all_audited_commands_have_typed_arguments_only(self):
        for command in ['give_item', 'receive_item']:
            for item in ['saw','hammer','rope','axe','wood','fruits','water','food','string','bow']:
                value = c.OperationCandidate.model_validate({**self.raw['operation'], 'command_id':command, 'arguments':{'item':item}})
                self.assertEqual(value.arguments.item, item)
        for command in ['report_wreck','begin_ship_inspection','wait','resume','postpone','return']:
            value = c.OperationCandidate.model_validate({**self.raw['operation'], 'command_id':command, 'arguments':{}})
            self.assertEqual(value.arguments.model_dump(), {})
        for command, args in [('complete_inspection',{}), ('victory',{}), ('repair_ship',{}), ('give_item',{}),
                              ('give_item',{'item':'gold'}), ('give_item',{'item':'wood','quantity':1}),
                              ('give_item',{'item':1}), ('wait',{'item':'wood'}), ('wait',{'payload':{}})]:
            with self.subTest(command=command, args=args), self.assertRaises(ValidationError):
                c.OperationCandidate.model_validate({**self.raw['operation'], 'command_id':command, 'arguments':args})

    def test_proposal_describes_multiple_candidates_and_every_modality_without_authorizing(self):
        candidates = [{**self.raw['operation'], 'candidate_id':f'operation:{i}', 'modality':mode}
                      for i, mode in enumerate(['direct','quoted','hypothetical','negated','ambiguous'])]
        value = c.TurnProposal.model_validate(self.proposal(operation_candidates=candidates))
        self.assertEqual(len(value.operation_candidates), 5)
        for candidate in value.operation_candidates[1:]:
            with self.assertRaises(ValidationError):
                c.ReadyToRecheck(kind='ready_to_recheck', operation=candidate, consent=None, checked_preconditions=[])
        with self.assertRaises(ValidationError):
            c.OperationCandidate.model_validate({**self.raw['operation'], 'modality':'certain'})

    def test_decision_union_carries_only_one_ready_operation_and_no_authorization(self):
        adapter = TypeAdapter(c.OperationDecision)
        decisions = [dict(kind='no_operation'), dict(kind='clarification_required', concern_ids=['concern:1'], question='Which first?'),
                     dict(kind='denied', reason_code='UNAVAILABLE', safe_explanation='Please wait.'),
                     dict(kind='ready_to_recheck', operation=self.raw['operation'], consent=None, checked_preconditions=[])]
        for raw in decisions:
            self.assertEqual(json.loads(adapter.dump_json(adapter.validate_python(raw))), raw)
        for extra in [dict(operations=[self.raw['operation'],self.raw['operation']]), dict(authorized=True), dict(transaction_token='token')]:
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                adapter.validate_python({**decisions[-1], **extra})

    def test_pending_all_statuses_expiry_is_only_failed_preconditions(self):
        for status in ['active','suspended','cancelled','fulfilled','expired']:
            raw = {**self.raw['pending'], 'status':status,
                   'status_reason':None if status == 'active' else ('preconditions_changed' if status == 'expired' else 'explicit_transition')}
            self.assertEqual(c.PendingInteraction.model_validate(raw).status, status)
        for change in [dict(status='expired',status_reason='timeout'), dict(status='expired',status_reason=None),
                       dict(expires_at='2027-01-01T00:00:00Z'), dict(ttl_turns=2), dict(quantity=2)]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                c.PendingInteraction.model_validate({**self.raw['pending'], **change})

    def test_resumed_question_keeps_origin_and_binds_the_current_question_turn(self):
        pending = c.PendingInteraction.model_validate({**self.raw['pending'], 'question_id':'question:2','question_turn_id':'turn:2'})
        question_turn = c.TurnRef.model_validate({**self.raw['turn'],'turn_id':'turn:2','request_id':'request:2','sequence':2})
        question = c.TextValue(text_id='question:2',text='Would you like this wood?')
        pending.validate_question(question_turn, question)
        self.assertEqual(pending.originating_turn.turn_id, 'turn:1')
        for turn, text in [(c.TurnRef.model_validate(self.raw['turn']), question),
                           (question_turn, c.TextValue(text_id='question:2',text='Different terms.'))]:
            with self.assertRaises(ValueError):
                pending.validate_question(turn, text)
        consent_raw = self.consent()
        consent_raw.update(question_id='question:2',question_turn_id='turn:2',
                           question_turn=question_turn.model_dump(mode='json'),
                           answering_turn={**self.raw['turn'],'turn_id':'turn:3','request_id':'request:3','sequence':3},
                           operation={**self.raw['operation'],'pending_question_id':'question:2'})
        consent = c.ConsentBinding.model_validate(consent_raw)
        consent.validate_against(pending, {'answer:2':'yes'}, expected_answer='yes')
        with self.assertRaises(ValueError):
            c.ConsentBinding.model_validate(self.consent()).validate_against(pending, {'answer:2':'yes'},expected_answer='yes')

    def test_question_turn_cannot_precede_the_originating_turn(self):
        origin = {**self.raw['turn'], 'turn_id':'turn:2','request_id':'request:2','sequence':2}
        pending = c.PendingInteraction.model_validate({**self.raw['pending'],'originating_turn':origin})
        with self.assertRaises(ValueError):
            pending.validate_question(c.TurnRef.model_validate(self.raw['turn']),
                                      c.TextValue(text_id='question:1',text='Would you like this wood?'))

    def test_action_choice_options_are_detached_and_never_an_execution_queue(self):
        operations = [self.raw['operation'],{**self.raw['operation'],'candidate_id':'operation:2','arguments':{'item':'axe'}}]
        raw = {**self.raw['pending'], 'interaction_id':'interaction:2','kind':'action_choice','item':None,'quantity':None,
               'required_response_kind':'choice','offered_operations':operations}
        pending = c.PendingInteraction.model_validate(raw)
        operations.clear()
        self.assertEqual(len(pending.offered_operations), 2)
        self.assertIsInstance(pending.offered_operations, tuple)
        with self.assertRaises(ValidationError):
            pending.offered_operations[0].arguments.item = 'bow'
        raw['offered_operations'] = pending.model_dump(mode='json')['offered_operations']
        c.ContextPacket.model_validate(self.context(pending_interactions=[self.raw['pending'],pending.model_dump(mode='json')]))
        for updates in [dict(offered_operations=[]),dict(offered_operations=[self.raw['operation']]),
                        dict(offered_operations=[self.raw['operation']]*2),dict(required_response_kind='affirmation'),
                        dict(item='wood',quantity=1),dict(execution_queue=operations)]:
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                c.PendingInteraction.model_validate({**raw,**updates})

    def test_action_choice_options_require_direct_candidates_bound_to_current_question(self):
        offered = [self.raw['operation'],{**self.raw['operation'],'candidate_id':'operation:2','arguments':{'item':'axe'}}]
        raw = {**self.raw['pending'],'kind':'action_choice','item':None,'quantity':None,
               'required_response_kind':'choice','offered_operations':offered}
        for updates in [dict(modality='quoted'),dict(modality='hypothetical'),dict(modality='negated'),
                        dict(modality='ambiguous'),dict(pending_question_id=None),dict(pending_question_id='old:question')]:
            invalid = [offered[0],{**offered[1],**updates}]
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                c.PendingInteraction.model_validate({**raw,'offered_operations':invalid})

    def test_action_choice_consent_must_select_an_exact_offered_operation(self):
        pending = c.PendingInteraction.model_validate({**self.raw['pending'],'kind':'action_choice','item':None,'quantity':None,
                    'required_response_kind':'choice','offered_operations':[self.raw['operation'],
                    {**self.raw['operation'],'candidate_id':'operation:2','arguments':{'item':'axe'}}]})
        consent = self.consent()
        consent['operation'] = {**consent['operation'], 'source_spans': [consent['answer_span']]}
        c.ConsentBinding.model_validate(consent).validate_against(pending,{'answer:2':'yes'},expected_answer='yes')
        for updates in [dict(candidate_id='unoffered'),dict(command_id='receive_item'),dict(arguments={'item':'bow'}),
                        dict(source_spans=[dict(text_id='changed',start=0,end=1)])]:
            raw = copy.deepcopy(consent)
            raw['operation'] = {**raw['operation'],**updates}
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                c.ConsentBinding.model_validate(raw).validate_against(pending,{'answer:2':'yes'},expected_answer='yes')

    def test_consent_answer_must_follow_current_question_not_only_origin(self):
        self.assertIn('question_turn', c.ConsentBinding.model_fields, 'current question TurnRef is absent')
        pending = c.PendingInteraction.model_validate({**self.raw['pending'],'question_id':'question:3','question_turn_id':'turn:3'})
        question_turn = {**self.raw['turn'],'turn_id':'turn:3','request_id':'request:3','sequence':3}
        raw = self.consent()
        raw.update(question_id='question:3',question_turn_id='turn:3',question_turn=question_turn,
                   operation={**self.raw['operation'],'pending_question_id':'question:3'})
        # Answer 2 follows origin 1, but cannot answer question 3.
        for answering_sequence in [2,3]:
            with self.subTest(answering_sequence=answering_sequence), self.assertRaises(ValidationError):
                c.ConsentBinding.model_validate({**raw,'answering_turn':{**raw['answering_turn'],'sequence':answering_sequence}})
        raw['answering_turn'] = {**self.raw['turn'],'turn_id':'turn:4','request_id':'request:4','sequence':4}
        c.ConsentBinding.model_validate(raw).validate_against(pending,{'answer:2':'yes'},expected_answer='yes')
        for question_updates in [dict(turn_id='wrong:turn'),dict(key={**self.raw['turn']['key'],'epoch':1})]:
            with self.subTest(question_updates=question_updates), self.assertRaises(ValidationError):
                c.ConsentBinding.model_validate({**raw,'question_turn':{**question_turn,**question_updates}})
        earlier = {**raw,'question_id':'question:1','question_turn_id':'turn:1','question_turn':self.raw['turn'],
                   'operation':self.raw['operation']}
        with self.assertRaises(ValueError):
            c.ConsentBinding.model_validate(earlier).validate_against(
                c.PendingInteraction.model_validate({**self.raw['pending'],'originating_turn':question_turn}),
                {'answer:2':'yes'},expected_answer='yes')

    def test_context_enforces_scope_visibility_and_one_active_item_negotiation(self):
        other = {**self.raw['pending'], 'interaction_id':'interaction:2'}
        with self.assertRaises(ValidationError):
            c.ContextPacket.model_validate(self.context(pending_interactions=[self.raw['pending'],other]))
        other['status'] = 'suspended'
        other['status_reason'] = 'explicit_transition'
        self.assertEqual(len(c.ContextPacket.model_validate(self.context(pending_interactions=[self.raw['pending'],other])).pending_interactions), 2)
        other['key'] = {**other['key'], 'epoch':1}
        with self.assertRaises(ValidationError):
            c.ContextPacket.model_validate(self.context(pending_interactions=[other]))
        source = dict(kind='inventory',source_id='inventory:1',revision=1,game_scope='run:1',npc_id=1,attribution='server',visibility='server_private')
        fact = dict(kind='mechanical_fact',evidence_id='fact:1',content='wood',sources=[source],created_at='2026-10-14T00:00:00Z')
        with self.assertRaises(ValidationError):
            c.ContextPacket.model_validate(self.context(visible_facts=[fact]))

    def test_capability_schema_is_typed_and_is_only_a_view(self):
        raw = dict(command_id='give_item', parameter_schema={'kind':'single_item','allowed_items':['wood']},
                   allowed_target_references=[self.raw['operation']['target']], available=False,
                   safe_unavailable_reason='No wood is available.', relevant_preconditions=[], supported_speech_acts=['request'])
        value = c.CapabilityDescriptor.model_validate(raw)
        self.assertFalse(value.available)
        for change in [dict(parameter_schema={'type':'object','properties':{'quantity':{}}}), dict(available=1),
                       dict(parameter_schema={'kind':'none'}), dict(safe_unavailable_reason=None), dict(permission=True)]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                c.CapabilityDescriptor.model_validate({**raw, **change})
        no_args = {**raw,'command_id':'wait','parameter_schema':{'kind':'none'},'available':True,'safe_unavailable_reason':None}
        self.assertTrue(c.CapabilityDescriptor.model_validate(no_args).available)

    def test_proposal_reference_and_concern_ids_are_unique_and_linked(self):
        for change in [dict(concerns=self.proposal()['concerns'] * 2), dict(operation_candidates=[self.raw['operation']] * 2),
                       dict(reply=[{**self.raw['candidate']['segments'][0], 'addressed_concern_ids':['missing']}]),
                       dict(interaction_links=[dict(link_id='link:1',question_id='question:1',concern_id='missing',source_spans=[dict(text_id='message:1',start=2,end=6)])])]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                c.TurnProposal.model_validate(self.proposal(**change))
        unresolved = dict(kind='unresolved',reference_id='reference:1',text='it',source_spans=[dict(text_id='message:1',start=2,end=4)])
        self.assertEqual(c.TurnProposal.model_validate(self.proposal(references=[unresolved])).references[0].kind, 'unresolved')

    def test_exact_unicode_message_references_are_validated_against_supplied_text(self):
        value = c.TurnProposal.model_validate(self.proposal())
        value.validate_references({'message:1':'A🙂wood'})
        for texts in [{'other':'A🙂wood'}, {'message:1':'A🙂w'}]:
            with self.subTest(texts=texts), self.assertRaises(ValueError):
                value.validate_references(texts)
        report = dict(statement_id='report:1',attribution='player:1',content='wood',source_spans=[dict(text_id='message:1',start=2,end=6)])
        correction = dict(correction_id='correction:1',target_reference_id='canon:1',attribution='player:1',content='wood',source_spans=[dict(text_id='message:1',start=2,end=6)])
        linked = c.TurnProposal.model_validate(self.proposal(reports=[report],correction_candidates=[correction]))
        linked.validate_references({'message:1':'A🙂wood'})
        with self.assertRaises(ValueError):
            linked.validate_references({'message:1':'A🙂wo'})

    def test_candidate_requires_exact_segment_support_and_explicit_revision_link(self):
        value = c.CandidateReply.model_validate(self.raw['candidate'])
        self.assertEqual(value.canon_candidates[0].supporting_span.resolve({'segment:1':'A🙂éZ'}), '🙂é')
        for span in [dict(text_id='segment:2',start=0,end=1),dict(text_id='segment:1',start=1,end=99)]:
            bad = copy.deepcopy(self.raw['candidate'])
            bad['canon_candidates'][0]['supporting_span'] = span
            with self.assertRaises(ValidationError):
                c.CandidateReply.model_validate(bad)
        bad = copy.deepcopy(self.raw['candidate'])
        bad['canon_candidates'][0]['kind'] = 'revise'
        with self.assertRaises(ValidationError):
            c.CandidateReply.model_validate(bad)

    def assembled(self, **updates):
        return dict(text_id='reply:1',final_text='A🙂éZ',beats=['A🙂','éZ'],
                    segment_spans={'segment:1':dict(text_id='reply:1',start=0,end=5)},
                    evidence_dependencies=[],candidate_continuity_changes=[], **updates)

    def test_assembled_beats_partition_complete_text_and_span_map_is_detached(self):
        raw = self.assembled()
        value = c.AssembledReply.model_validate(raw)
        raw['segment_spans'].clear()
        self.assertEqual(value.segment_spans['segment:1'].end, 5)
        with self.assertRaises(TypeError):
            value.segment_spans['segment:2'] = value.segment_spans['segment:1']
        self.assertEqual(c.AssembledReply.model_validate_json(value.model_dump_json()), value)
        for updates in [dict(beats=['A🙂','Z']), dict(segment_spans={'segment:1':dict(text_id='old:reply',start=0,end=5)}),
                        dict(segment_spans={'segment:1':dict(text_id='reply:1',start=0,end=6)}),
                        dict(candidate_continuity_changes=[dict(candidate_id='candidate:1',supporting_span=dict(text_id='reply:1',start=0,end=6))])]:
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                c.AssembledReply.model_validate({**self.assembled(), **updates})
        value.validate_segment_texts({'segment:1':'A🙂éZ'})
        with self.assertRaises(ValueError):
            value.validate_segment_texts({'segment:1':'repaired text'})

    def consent(self, **updates):
        return dict(interaction_id='interaction:1',question_id='question:1',question_turn_id='turn:1',
                    question_turn=self.raw['turn'],
                    answering_turn={**self.raw['turn'],'turn_id':'turn:2','request_id':'request:2','sequence':2},
                    answer_span=dict(text_id='answer:2',start=0,end=3),operation=self.raw['operation'],
                    checked_preconditions=[],precondition_fingerprint='fingerprint:1', **updates)

    def test_consent_requires_exact_current_question_answer_terms_and_preconditions(self):
        value = c.ConsentBinding.model_validate(self.consent())
        pending = c.PendingInteraction.model_validate(self.raw['pending'])
        value.validate_against(pending, {'answer:2':'yes'}, expected_answer='yes')
        for updates in [dict(status='suspended',status_reason='explicit_transition'), dict(question_id='question:2'),
                        dict(precondition_fingerprint='changed'),dict(item='axe')]:
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                value.validate_against(c.PendingInteraction.model_validate({**self.raw['pending'],**updates}), {'answer:2':'yes'},expected_answer='yes')
        with self.assertRaises(ValueError):
            value.validate_against(pending, {'answer:2':'yep'},expected_answer='yes')
        with self.assertRaises(ValidationError):
            c.ReadyToRecheck(kind='ready_to_recheck',operation={**self.raw['operation'],'arguments':{'item':'axe'}},consent=value,checked_preconditions=[])

    def test_receipt_outcomes_cannot_promote_acceptance_to_completion(self):
        completed = c.OperationReceipt.model_validate(self.raw['receipt'])
        self.assertEqual(completed.outcome, 'completed')
        accepted = {**self.raw['receipt'], 'command_id':'begin_ship_inspection', 'outcome':'accepted',
                    'activity_id':'activity:1','result':dict(kind='activity',activity_id='activity:1',stage='accepted')}
        value = c.OperationReceipt.model_validate(accepted)
        self.assertFalse(value.completed)
        self.assertTrue(completed.completed)
        rejected = {**self.raw['receipt'],'outcome':'rejected','safe_reason_code':'UNAVAILABLE','result':{'kind':'rejection'},'event_ids':[]}
        self.assertEqual(c.OperationReceipt.model_validate(rejected).outcome, 'rejected')
        for updates in [dict(outcome='completed'),dict(result={'kind':'activity','activity_id':'activity:1','stage':'completed'}),dict(activity_id=None)]:
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                c.OperationReceipt.model_validate({**accepted,**updates})
        for updates in [dict(outcome='accepted'),dict(result={'kind':'item_transfer','item':'wood','quantity':2,'direction':'to_player'}),
                        dict(result={'kind':'item_transfer','item':'wood','quantity':True,'direction':'to_player'}),
                        dict(result={'kind':'item_transfer','item':'wood','quantity':1,'direction':'to_npc'}),
                        dict(result={'inventory':{'wood':9}}),dict(committed_at='2026-10-14T00:00:00')]:
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                c.OperationReceipt.model_validate({**self.raw['receipt'],**updates})

    def test_receipt_verifies_canonical_command_arguments_and_target(self):
        receipt = c.OperationReceipt.model_validate(self.raw['receipt'])
        self.assertTrue(hasattr(receipt, 'verify_operation'), 'receipt consistency check is absent')
        operation = c.OperationCandidate.model_validate(self.raw['operation'])
        receipt.verify_operation(operation)
        for updates in [dict(command_id='receive_item'),dict(arguments={'item':'axe'}),
                        dict(target={'reference_id':'npc:2','entity_kind':'npc','entity_id':'2'})]:
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                receipt.verify_operation(c.OperationCandidate.model_validate({**self.raw['operation'],**updates}))
        with self.assertRaises(ValueError):
            c.OperationReceipt.model_validate({**self.raw['receipt'],'argument_digest':'0'*64}).verify_operation(operation)

    def test_reply_metadata_origins_versions_and_nested_maps_are_strict(self):
        for origin in ['generated','repaired','fallback','mock']:
            raw = copy.deepcopy(self.raw['candidate'])
            raw['source']['origin'] = origin
            value = c.CandidateReply.model_validate(raw)
            raw['source']['policy_versions']['bounds'] = 'changed'
            self.assertEqual(value.source.policy_versions['bounds'], 'test:1')
            with self.assertRaises(TypeError):
                value.source.policy_versions['bounds'] = 'changed'
        for changes in [dict(origin='simulated'),dict(schema_version=2),dict(schema_version=True),
                        dict(policy_versions={'bounds':{}}),dict(provider_payload={})]:
            raw = copy.deepcopy(self.raw['candidate'])
            raw['source'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                c.CandidateReply.model_validate(raw)

    def test_non_item_pending_and_command_result_variants_remain_typed(self):
        for kind in ['activity_offer','clarification']:
            pending = c.PendingInteraction.model_validate({**self.raw['pending'],'kind':kind,'item':None,'quantity':None})
            self.assertEqual(pending.kind,kind)
        command = {**self.raw['receipt'],'command_id':'wait','result':{'kind':'command','changed':True}}
        self.assertTrue(c.OperationReceipt.model_validate(command).completed)
        complete_activity = {**self.raw['receipt'],'command_id':'begin_ship_inspection','activity_id':'activity:1',
                             'result':{'kind':'activity','activity_id':'activity:1','stage':'completed'}}
        self.assertTrue(c.OperationReceipt.model_validate(complete_activity).completed)

    def test_nested_values_and_policy_maps_are_detached_and_frozen(self):
        raw = self.context()
        value = c.ContextPacket.model_validate(raw)
        raw['policy_versions']['bounds'] = 'changed'
        raw['pending_interactions'][0]['target']['entity_id'] = 'changed'
        self.assertEqual(value.policy_versions['bounds'], 'test:1')
        self.assertEqual(value.pending_interactions[0].target.entity_id, '1')
        with self.assertRaises(TypeError):
            value.policy_versions['bounds'] = 'changed'
        with self.assertRaises(ValidationError):
            value.pending_interactions[0].target.entity_id = 'changed'
        self.assertIsInstance(value.pending_interactions, tuple)


if __name__ == '__main__':
    unittest.main()
