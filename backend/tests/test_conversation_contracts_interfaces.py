"""T04 public-interface envelopes: detached values and explicit conflict checks."""
import copy
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path
import unittest

from pydantic import TypeAdapter, ValidationError

c = importlib.import_module('app.services.conversation.contracts')
FIXTURES = Path(__file__).parent / 'fixtures/conversation'
MODELS = {
    'lease_policy': 'LeasePolicy', 'lease': 'TurnLease',
    'interaction_plan': 'InteractionPlan', 'memory_plan': 'MemoryPlan',
    'continuity_plan': 'ContinuityPlan', 'clear_result': 'ClearResult',
    'world_result': 'WorldResult', 'summary_record': 'SummaryRecord',
    'provider_attempt': 'ProviderAttempt', 'turn_recovery': 'TurnRecovery', 'recovered_reply': 'RecoveredReply',
}


class ConversationInterfaceContractTests(unittest.TestCase):
    def setUp(self):
        for name in (*MODELS.values(), 'OptionalResult'):
            self.assertTrue(hasattr(c, name), f'T04 public interface value {name} is absent')
        self.valid = json.loads((FIXTURES / 't04-valid.json').read_text())
        self.rejected = json.loads((FIXTURES / 't04-rejected.json').read_text())

    def test_all_interface_values_roundtrip_and_reject_extra_fields(self):
        # Catches dropped scope/epoch/revision/fence fields and permissive schemas.
        for fixture, name in MODELS.items():
            with self.subTest(model=name):
                model = getattr(c, name)
                value = model.model_validate(self.valid[fixture])
                self.assertEqual(json.loads(value.model_dump_json()), self.valid[fixture])
                self.assertEqual(model.model_validate_json(value.model_dump_json()), value)
                with self.assertRaises(ValidationError):
                    model.model_validate({**self.valid[fixture], 'unowned_field': True})
                with self.assertRaises(ValidationError):
                    setattr(value, next(iter(model.model_fields)), None)
                self.assertIsInstance(model.model_json_schema(), dict)

    def test_rejected_shared_fixtures(self):
        # Catches malformed scope, lifecycle, lineage, bounds and stale digests.
        for case in self.rejected:
            with self.subTest(model=case['model'], label=case['label']):
                with self.assertRaises(ValidationError):
                    getattr(c, case['model']).model_validate(case['value'])

    def test_optional_success_none_is_distinct_from_failure_and_missing_branch(self):
        # Catches the legacy Result's inability to represent a successful no-work claim.
        model = c.OptionalResult[c.TurnLease]
        success = model.model_validate(self.valid['optional_none'])
        failure = model.model_validate(self.valid['optional_failure'])
        self.assertEqual((success.status, success.value, success.error), ('success', None, None))
        self.assertEqual(failure.status, 'failure')
        self.assertEqual(failure.error.code, 'STALE_SCOPE')
        self.assertEqual(model.success(None), success)
        self.assertEqual(model.failure(failure.error), failure)
        self.assertEqual(model.model_validate_json(success.model_dump_json()), success)
        lease = c.TurnLease.model_validate(self.valid['lease'])
        self.assertEqual(model.success(lease).value, lease)
        for raw in [{}, {'status':'success'}, {'status':'failure'},
                    {'status':'success','value':None,'error':self.valid['optional_failure']['error']},
                    {'status':'failure','value':self.valid['lease'],'error':self.valid['optional_failure']['error']}]:
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                model.model_validate(raw)
        # Existing nonoptional semantics and API stay frozen.
        with self.assertRaises(ValidationError):
            c.Result[c.TurnLease].success(None)
        self.assertEqual(c.Result.success(lease).value, lease)

    def test_lease_rejects_replaced_fence_expiry_and_wrong_stream_position(self):
        lease = c.TurnLease.model_validate(self.valid['lease'])
        now = datetime(2026, 10, 14, 10, 0, 1, tzinfo=timezone.utc)
        arguments = dict(key=lease.turn.key, fence=2, sequence=3, now=now)
        lease.validate_current(**arguments)
        for replacement in [dict(fence=3), dict(sequence=2),
                            dict(key=c.ConversationKey(game_scope='other',npc_id=7,epoch=3)),
                            dict(key=c.ConversationKey(game_scope='run-opaque',npc_id=7,epoch=4)),
                            dict(now=lease.expires_at), dict(now=now.replace(tzinfo=None))]:
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                lease.validate_current(**{**arguments, **replacement})

    def test_interaction_plan_cannot_overwrite_a_committed_transition(self):
        plan = c.InteractionPlan.model_validate(self.valid['interaction_plan'])
        old = copy.deepcopy(self.valid['interaction_plan']['transitions'][0]['replacement'])
        old.update(revision=1,status='active',status_reason=None)
        current = c.PendingInteraction.model_validate(old)
        plan.validate_current({current.interaction_id: current})
        fulfilled = c.PendingInteraction.model_validate({**old, 'revision':2, 'status':'fulfilled', 'status_reason':'operation_committed'})
        with self.assertRaises(ValueError):
            plan.validate_current({current.interaction_id: fulfilled})
        with self.assertRaises(ValueError):
            plan.validate_current({})

    def test_memory_corrections_require_link_and_expected_head(self):
        raw = copy.deepcopy(self.valid['memory_plan'])
        write = raw['writes'][0]
        write['record']['revision'] = 2
        write['expected_revision'] = 1
        with self.assertRaises(ValidationError):
            c.MemoryPlan.model_validate(raw)
        write['correction_link'] = 'correction:accepted-2'
        plan = c.MemoryPlan.model_validate(raw)
        plan.validate_current({'memory:1':1})
        with self.assertRaises(ValueError):
            plan.validate_current({'memory:1':2})
        with self.assertRaises(ValueError):
            plan.validate_current({})
        new = c.MemoryPlan.model_validate(self.valid['memory_plan'])
        new.validate_current({})
        with self.assertRaises(ValueError):
            new.validate_current({'memory:1':0})

    def test_continuity_rechecks_only_dependencies_and_exact_final_spans(self):
        plan = c.ContinuityPlan.model_validate(self.valid['continuity_plan'])
        resources = dict(plan.expected_revisions.resources)
        plan.validate_revisions(c.RevisionSet(resources={**resources, 'unrelated:world':99}))
        for stale in [{**resources,'event:9':5}, {'event:9':4}]:
            with self.assertRaises(ValueError):
                plan.validate_revisions(c.RevisionSet(resources=stale))
        reply = c.AssembledReply(text_id='final:3',final_text='x'*48,beats=('x'*48,),
            segment_spans={},evidence_dependencies=(),candidate_continuity_changes=())
        plan.validate_reply(reply)
        with self.assertRaises(ValueError):
            plan.validate_reply(c.AssembledReply(text_id='repaired:3',final_text='x'*48,beats=('x'*48,),
                segment_spans={},evidence_dependencies=(),candidate_continuity_changes=()))

    def test_summary_rechecks_epoch_correction_revisions_and_source_range(self):
        summary = c.SummaryRecord.model_validate(self.valid['summary_record'])
        self.assertEqual(summary.entries[0].memory.attributed_subject, 'player')
        self.assertEqual(summary.entries[0].memory.uncertainty, 'unverified')
        self.assertEqual((summary.source_range.first_sequence,summary.source_range.last_sequence),(1,3))
        summary.validate_current(summary.key, summary.source_revisions)
        stale = c.RevisionSet(resources={**summary.source_revisions.resources,'canon:harbor-story':2})
        with self.assertRaises(ValueError):
            summary.validate_current(summary.key, stale)
        with self.assertRaises(ValueError):
            summary.validate_current(c.ConversationKey(game_scope='run-opaque',npc_id=7,epoch=4), summary.source_revisions)

    def test_recovery_preserves_consumed_attempt_and_single_repair_budget(self):
        recovery = c.TurnRecovery.model_validate(self.valid['turn_recovery'])
        self.assertEqual(recovery.consumed_purposes, ('proposal',))
        self.assertFalse(recovery.repair_consumed)
        self.assertIsNone(recovery.attempts[0].output)
        raw = copy.deepcopy(self.valid['turn_recovery'])
        repair = {**self.valid['provider_attempt'], 'attempt_id':'attempt:repair:3', 'purpose':'repair', 'repair_kind':'final_response'}
        raw['attempts'].append(repair)
        self.assertTrue(c.TurnRecovery.model_validate(raw).repair_consumed)
        raw['attempts'].append({**repair,'attempt_id':'attempt:repair:again'})
        with self.assertRaises(ValidationError):
            c.TurnRecovery.model_validate(raw)
        # Old consumed dispatches survive a replacement fence; future fences do not.
        self.assertEqual(recovery.fence, 3)
        self.assertEqual(recovery.attempts[0].fence, 2)
        future = copy.deepcopy(self.valid['turn_recovery'])
        future['attempts'][0]['fence'] = 4
        with self.assertRaises(ValidationError):
            c.TurnRecovery.model_validate(future)
        for purpose, output in [('proposal',self.valid['persisted_proposal']),
                                ('composition',self.valid['persisted_candidate']),
                                ('repair',self.valid['persisted_candidate'])]:
            persisted = c.ProviderAttempt.model_validate({**self.valid['provider_attempt'],
                'purpose':purpose,'repair_kind':'final_response' if purpose == 'repair' else None,
                'status':'output_persisted','output':output})
            self.assertIsNotNone(persisted.output)
        for purpose, output in [('proposal',self.valid['persisted_candidate']),
                                ('composition',self.valid['persisted_proposal']),
                                ('repair',self.valid['persisted_proposal'])]:
            with self.subTest(purpose=purpose), self.assertRaises(ValidationError):
                c.ProviderAttempt.model_validate({**self.valid['provider_attempt'],
                    'purpose':purpose,'repair_kind':'final_response' if purpose == 'repair' else None,
                'status':'output_persisted','output':output})
        for changes in [{'status':'output_persisted'}, {'fence':0}, {'purpose':'summary'},
                        {'status':'dispatched','output':self.valid['clear_result']}]:
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                c.ProviderAttempt.model_validate({**self.valid['provider_attempt'], **changes})

    def test_proposal_format_repair_consumes_the_single_shared_repair_token(self):
        self.assertIn('repair_kind', c.ProviderAttempt.model_fields, 'repair attempts need an explicit output path')
        proposal_repair = c.ProviderAttempt.model_validate(self.valid['proposal_format_repair'])
        self.assertIsInstance(proposal_repair.output, c.TurnProposal)
        final_repair = c.ProviderAttempt.model_validate(self.valid['final_response_repair'])
        self.assertIsInstance(final_repair.output, c.CandidateReply)
        self.assertEqual((proposal_repair.purpose, final_repair.purpose), ('repair', 'repair'))
        for first, second in [(self.valid['proposal_format_repair'],self.valid['final_response_repair']),
                              (self.valid['final_response_repair'],self.valid['proposal_format_repair'])]:
            raw = copy.deepcopy(self.valid['turn_recovery'])
            raw['attempts'].append(first)
            recovery = c.TurnRecovery.model_validate(raw)
            self.assertEqual(recovery.consumed_purposes, ('proposal','repair'))
            self.assertTrue(recovery.repair_consumed)
            self.assertEqual(c.TurnRecovery.model_validate_json(recovery.model_dump_json()), recovery)
            raw['attempts'].append(second)
            with self.assertRaises(ValidationError):
                c.TurnRecovery.model_validate(raw)
        # A crash before repaired output persistence still consumes the shared token.
        raw = copy.deepcopy(self.valid['turn_recovery'])
        raw['attempts'].append({**self.valid['proposal_format_repair'],'status':'dispatched','output':None})
        self.assertTrue(c.TurnRecovery.model_validate(raw).repair_consumed)
        raw['attempts'].append(self.valid['final_response_repair'])
        with self.assertRaises(ValidationError):
            c.TurnRecovery.model_validate(raw)

    def test_recovery_clears_invalidated_payload_and_retains_only_scoped_receipt(self):
        raw = copy.deepcopy(self.valid['turn_recovery'])
        raw['status']['phase'] = 'invalidated'
        with self.assertRaises(ValidationError):
            c.TurnRecovery.model_validate(raw)
        raw.update(submission=None,attempts=[],receipt=self.valid['recovery_receipt'])
        recovery = c.TurnRecovery.model_validate(raw)
        self.assertEqual(recovery.status.phase, 'invalidated')
        self.assertEqual(recovery.receipt.turn_id, 'turn-3')
        raw['receipt']['game_scope']='new-run'
        with self.assertRaises(ValidationError):
            c.TurnRecovery.model_validate(raw)
        raw = copy.deepcopy(self.valid['turn_recovery'])
        raw['assembled_reply'] = self.valid['recovered_reply']
        self.assertEqual(c.TurnRecovery.model_validate(raw).assembled_reply.turn.turn_id, 'turn-3')
        for path, bad in [('fence',4), ('turn', {**self.valid['lease']['turn'],'turn_id':'other-turn'})]:
            broken = copy.deepcopy(raw)
            broken['assembled_reply'][path] = bad
            with self.subTest(path=path), self.assertRaises(ValidationError):
                c.TurnRecovery.model_validate(broken)
        raw['status']['phase']='invalidated'
        raw['submission']=None
        raw['attempts']=[]
        with self.assertRaises(ValidationError):
            c.TurnRecovery.model_validate(raw)
        for path, bad in [('request_id','wrong-request'), ('schema_version',2)]:
            raw = copy.deepcopy(self.valid['turn_recovery'])
            raw['submission'][path]=bad
            with self.subTest(path=path), self.assertRaises(ValidationError):
                c.TurnRecovery.model_validate(raw)

    def test_nested_data_is_detached_and_immutable(self):
        raw = self.valid['world_result']
        world = c.WorldResult.model_validate(raw)
        raw['state_projection']['nested']['items'].append('stone')
        self.assertEqual(world.state_projection['nested']['items'], ('wood',))
        with self.assertRaises(TypeError):
            world.state_projection['nested']['new'] = 'value'
        for raw in [{'bad':set()}, {'bad':float('inf')}]:
            with self.assertRaises(ValidationError):
                c.WorldResult.model_validate({**self.valid['world_result'], 'state_projection':raw})
        plan = c.ContinuityPlan.model_validate(self.valid['continuity_plan'])
        self.valid['continuity_plan']['memory_plan']['writes'][0]['record']['content'] = 'changed'
        self.assertEqual(plan.memory_plan.writes[0].record.content, 'The player says they repaired the mast.')
        with self.assertRaises(TypeError):
            plan.expected_revisions.resources['event:9'] = 9
        with self.assertRaises(ValidationError):
            plan.memory_plan.writes[0].record.content = 'changed'


class InteractionCueContractTests(unittest.TestCase):
    """T05 catches stale/current-message confusion and claimed authority leaks."""
    def setUp(self):
        for name in ('InteractionLifecycleCue', 'InteractionPreconditionState'):
            self.assertTrue(hasattr(c, name), f'T05 typed cue value {name} is absent')
        self.valid = json.loads((FIXTURES / 't05-valid.json').read_text())

    def test_versioned_values_and_composites_roundtrip(self):
        for model, raw in [(c.TurnProposal, self.valid['proposal']),
                           (c.ContextPacket, self.valid['context']),
                           (c.InteractionPreconditionState, self.valid['unavailable_state'])]:
            with self.subTest(model=model):
                value = model.model_validate(raw)
                self.assertEqual(json.loads(value.model_dump_json()), raw)
                self.assertEqual(model.model_validate_json(value.model_dump_json()), value)
                self.assertIsInstance(model.model_json_schema(), dict)
        context = c.ContextPacket.model_validate(self.valid['context'])
        proposal = c.TurnProposal.model_validate(self.valid['proposal'])
        proposal.validate_references({context.current_message.text_id: context.current_message.text}, context=context)
        self.assertEqual([p.status for p in context.pending_interactions], ['active', 'suspended'])
        self.assertEqual(proposal.operation_candidates, ())

    def test_rejected_t05_fixtures(self):
        for case in json.loads((FIXTURES / 't05-rejected.json').read_text()):
            with self.subTest(label=case['label']), self.assertRaises(ValidationError):
                getattr(c, case['model']).model_validate(case['value'])

    def test_cues_require_exact_current_message_and_known_pending_id(self):
        context = c.ContextPacket.model_validate(self.valid['context'])
        texts = {context.current_message.text_id: context.current_message.text}
        raw = self.valid['proposal']
        proposal = c.TurnProposal.model_validate(raw)
        with self.assertRaises(ValueError):
            proposal.validate_references(texts)
        for bad_texts in [{}, {'message:2':'x' * 60}, {'old-message':context.current_message.text}]:
            with self.subTest(texts=bad_texts), self.assertRaises(ValueError):
                proposal.validate_references(bad_texts, context=context)
        for change in [dict(interaction_id='unknown'), dict(source_text='Cancel the outing'),
                       dict(source_span={'text_id':'old-message','start':2,'end':17}),
                       dict(source_span={'text_id':'message:2','start':2,'end':99}),
                       dict(turn={**self.valid['context']['turn'],'turn_id':'old-turn'}),
                       dict(turn={**self.valid['context']['turn'],'key':{'game_scope':'other','npc_id':1,'epoch':0}})]:
            changed = copy.deepcopy(raw)
            changed['interaction_lifecycle_cues'][0].update(change)
            value = c.TurnProposal.model_validate(changed)
            with self.subTest(change=change), self.assertRaises(ValueError):
                value.validate_references({**texts,'old-message':context.current_message.text}, context=context)

    def test_precondition_state_cannot_be_attached_to_terminal_interaction(self):
        for status, reason in [('fulfilled','operation_committed'), ('cancelled','explicit_cancellation'),
                               ('expired','preconditions_changed')]:
            raw = copy.deepcopy(self.valid['context'])
            raw['pending_interactions'][0].update(status=status,status_reason=reason)
            with self.subTest(status=status), self.assertRaises(ValidationError):
                c.ContextPacket.model_validate(raw)

    def test_missing_or_unavailable_preconditions_do_not_change_pending_status(self):
        raw = copy.deepcopy(self.valid['context'])
        raw.pop('interaction_preconditions')
        missing = c.ContextPacket.model_validate(raw)
        self.assertEqual(dict(missing.interaction_preconditions), {})
        raw['interaction_preconditions'] = {'interaction:2':self.valid['unavailable_state']}
        unavailable = c.ContextPacket.model_validate(raw)
        self.assertEqual(unavailable.interaction_preconditions['interaction:2'].outcome, 'unavailable')
        self.assertEqual([p.status for p in unavailable.pending_interactions], ['active','suspended'])

    def test_new_nested_values_are_detached_and_immutable(self):
        raw = self.valid['context']
        context = c.ContextPacket.model_validate(raw)
        raw['interaction_preconditions']['interaction:1']['outcome'] = 'satisfied'
        self.assertEqual(context.interaction_preconditions['interaction:1'].outcome, 'failed')
        with self.assertRaises(TypeError):
            context.interaction_preconditions['interaction:1'] = context.interaction_preconditions['interaction:2']
        with self.assertRaises(ValidationError):
            context.interaction_preconditions['interaction:1'].outcome = 'satisfied'
        proposal = c.TurnProposal.model_validate(self.valid['proposal'])
        self.valid['proposal']['interaction_lifecycle_cues'][0]['source_span']['start'] = 1
        self.assertEqual(proposal.interaction_lifecycle_cues[0].source_span.start, 2)
        with self.assertRaises(ValidationError):
            proposal.interaction_lifecycle_cues[0].source_span.start = 1

    def test_old_frozen_envelopes_omit_empty_extensions(self):
        frozen = json.loads((FIXTURES / 't04-valid.json').read_text())
        proposal = c.TurnProposal.model_validate(frozen['persisted_proposal'])
        self.assertEqual(proposal.interaction_lifecycle_cues, ())
        self.assertEqual(json.loads(proposal.model_dump_json()), frozen['persisted_proposal'])
        raw = copy.deepcopy(self.valid['context'])
        raw.pop('interaction_preconditions')
        context = c.ContextPacket.model_validate(raw)
        self.assertEqual(json.loads(context.model_dump_json()), raw)


if __name__ == '__main__':
    unittest.main()
