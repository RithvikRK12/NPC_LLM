"""Pure operation selection never executes or infers consent from prose."""
import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError
from app.services.conversation import contracts as c
from app.services.conversation.interactions import InteractionPolicy
from app.services.conversation.operations import OperationService

try:
    from app.services.conversation.operations import OperationPolicy
except ModuleNotFoundError:
    OperationPolicy = None


class OperationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(OperationPolicy, 'pure operation policy is absent')
        self.policy = OperationPolicy()
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/t05-valid.json').read_text())
        self.context = raw['context']
        self.context.update(pending_interactions=[], interaction_preconditions={})
        self.context['current_message'] = {'text_id': 'message:2', 'text': 'Give me wood.'}
        self.proposal = raw['proposal']
        self.proposal['interaction_lifecycle_cues'] = []
        self.target = {'reference_id': 'npc:1', 'entity_kind': 'npc', 'entity_id': '1'}
        self.capability = {
            'command_id': 'give_item', 'parameter_schema': {'kind': 'single_item', 'allowed_items': ['wood']},
            'allowed_target_references': [self.target], 'available': True, 'safe_unavailable_reason': None,
            'relevant_preconditions': [], 'supported_speech_acts': ['request', 'accept'],
        }
        self.context['capabilities'] = [self.capability]
        self.operation = {
            'candidate_id': 'operation:1', 'command_id': 'give_item', 'arguments': {'item': 'wood'},
            'target': self.target, 'source_spans': [{'text_id': 'message:2', 'start': 0, 'end': 13}],
            'modality': 'direct', 'pending_question_id': None,
        }
        self.proposal['operation_candidates'] = [self.operation]

    def values(self):
        return c.TurnProposal.model_validate(self.proposal), c.ContextPacket.model_validate(self.context)

    def decide(self, plan=None):
        proposal, context = self.values()
        if plan is None:
            plan = InteractionPolicy().plan({p.interaction_id: p for p in context.pending_interactions}, proposal, context)
        return self.policy.decide(proposal, plan, context)

    def empty_plan(self):
        _, context = self.values()
        return c.InteractionPlan(turn=context.turn, transitions=(), consent_bindings=(), clarification=None)

    def pending(self, status='active', *, bound=True):
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/t05-valid.json').read_text())
        pending = raw['context']['pending_interactions'][0]
        pending.update(status=status, status_reason=None if status == 'active' else {
            'suspended': 'topic_changed', 'cancelled': 'explicit_cancellation',
            'expired': 'preconditions_changed', 'fulfilled': 'operation_completed',
        }[status])
        self.context['pending_interactions'] = [pending]
        self.context['visible_recent_turns'] = [{
            'turn': pending['originating_turn'], 'player_message': {'text_id': 'old:player', 'text': 'Wood?'},
            'final_reply': {'text_id': pending['question_id'], 'text': pending['question_text']},
        }]
        self.context['interaction_preconditions'] = {'interaction:1': {
            **raw['context']['interaction_preconditions']['interaction:1'], 'outcome': 'satisfied'}}
        self.operation['pending_question_id'] = 'question:1'
        if bound:
            pending['authorized_operation'] = {
                **copy.deepcopy(self.operation), 'candidate_id': 'offer:1',
                'source_spans': [{'text_id': 'question:1', 'start': 0, 'end': len(pending['question_text'])}],
            }

    def test_direct_supported_request_is_only_ready_for_gateway_recheck(self):
        result = self.decide()
        self.assertIsInstance(result, c.ReadyToRecheck)
        self.assertEqual(result.operation, self.values()[0].operation_candidates[0])
        self.assertIsNone(result.consent)

    def test_quoted_negated_hypothetical_requests_never_become_ready(self):
        for modality, message in [('quoted', 'He said "give me wood".'), ('negated', 'Do not give me wood.'),
                                  ('hypothetical', 'What if you gave me wood?')]:
            with self.subTest(modality=modality):
                self.operation['modality'] = modality
                self.context['current_message']['text'] = message
                self.assertIsInstance(self.decide(), c.NoOperation)

    def test_ambiguous_answer_requires_clarification(self):
        self.operation['modality'] = 'ambiguous'
        self.assertIsInstance(self.decide(), c.ClarificationRequired)

    def test_unrelated_purpose_words_and_generated_prose_never_transfer(self):
        self.proposal['operation_candidates'] = []
        self.context['current_message']['text'] = 'My purpose is to save wood for later.'
        self.proposal['reply'][0]['text'] = 'I gave you wood and trust you completely.'
        self.assertIsInstance(self.decide(), c.NoOperation)

    def test_unsupported_unavailable_target_parameter_and_speech_act_are_denied(self):
        for change in ['absent', 'unavailable', 'target', 'parameter', 'speech_act']:
            with self.subTest(change=change):
                self.setUp()
                if change == 'absent': self.context['capabilities'] = []
                if change == 'unavailable': self.capability.update(available=False, safe_unavailable_reason='No wood available.')
                if change == 'target': self.operation['target'] = {**self.target, 'entity_id': '2'}
                if change == 'parameter': self.operation['arguments'] = {'item': 'axe'}
                if change == 'speech_act': self.capability['supported_speech_acts'] = ['offer']
                self.assertIsInstance(self.decide(), c.Denied)

    def test_invalid_command_quantity_and_confidence_cannot_enter_policy(self):
        for change in [{'command_id': 'complete_inspection'}, {'arguments': {'item': 'wood', 'quantity': 2}}, {'confidence': 1.0}]:
            with self.subTest(change=change):
                self.proposal['operation_candidates'] = [{**self.operation, **change}]
                with self.assertRaises(ValidationError): self.values()

    def test_multiple_supported_actions_clarify_even_with_empty_plan(self):
        self.proposal['operation_candidates'].append({**self.operation, 'candidate_id': 'operation:2'})
        self.assertIsInstance(self.decide(self.empty_plan()), c.ClarificationRequired)

    def test_pending_answer_requires_exact_binding_and_current_satisfied_state(self):
        self.pending()
        self.assertIsInstance(self.decide(self.empty_plan()), c.ClarificationRequired)
        self.assertIsInstance(self.decide(), c.ReadyToRecheck)
        self.context['interaction_preconditions']['interaction:1']['outcome'] = 'unavailable'
        self.assertIsInstance(self.decide(), c.ClarificationRequired)

    def test_legacy_offer_without_stored_operation_cannot_become_ready(self):
        self.pending(bound=False)
        self.assertIsInstance(self.decide(), c.ClarificationRequired)
        # A fabricated application plan must not bypass the independent
        # operation boundary by supplying the terms missing from storage.
        proposal, context = self.values()
        pending = context.pending_interactions[0]
        binding = c.ConsentBinding(
            interaction_id=pending.interaction_id, question_id=pending.question_id,
            question_turn_id=pending.question_turn_id, question_turn=pending.originating_turn,
            answering_turn=context.turn, answer_span=proposal.operation_candidates[0].source_spans[0],
            operation=proposal.operation_candidates[0], checked_preconditions=(),
            precondition_fingerprint=pending.precondition_fingerprint,
        )
        forged_plan = c.InteractionPlan(turn=context.turn, transitions=(), consent_bindings=(binding,), clarification=None)
        self.assertIsInstance(self.policy.decide(proposal, forged_plan, context), c.ClarificationRequired)

    def test_single_offer_returns_persisted_terms_and_keeps_new_answer_span(self):
        self.pending()
        result = self.decide()
        self.assertIsInstance(result, c.ReadyToRecheck)
        proposal, context = self.values()
        operation = proposal.operation_candidates[0]
        self.assertEqual(result.operation.candidate_id, operation.candidate_id)
        self.assertEqual(result.operation.source_spans[0].text_id, 'message:2')
        self.assertEqual(result.consent.answer_span.text_id, 'message:2')
        stored = context.pending_interactions[0].authorized_operation
        self.assertEqual((result.operation.command_id, result.operation.arguments,
                          result.operation.target, result.operation.modality,
                          result.operation.pending_question_id),
                         (stored.command_id, stored.arguments, stored.target,
                          stored.modality, stored.pending_question_id))

    def test_stored_offer_is_not_authority_without_current_answer_or_preconditions(self):
        for change in ('no_answer', 'unsupported', 'ambiguous', 'preconditions', 'question'):
            with self.subTest(change=change):
                self.setUp()
                self.pending()
                if change == 'no_answer':
                    self.proposal['operation_candidates'] = []
                elif change == 'unsupported':
                    self.context['capabilities'] = []
                elif change == 'ambiguous':
                    self.operation['modality'] = 'ambiguous'
                elif change == 'preconditions':
                    self.context['interaction_preconditions'] = {}
                else:
                    self.context['visible_recent_turns'][0]['final_reply']['text'] = 'Changed question.'
                self.assertNotIsInstance(self.decide(), c.ReadyToRecheck)

    def test_single_offer_binding_cannot_change_direction_with_matching_item(self):
        self.pending()
        proposal, context = self.values()
        plan = InteractionPolicy().plan({p.interaction_id: p for p in context.pending_interactions}, proposal, context)
        self.context['capabilities'].append({**self.capability, 'command_id': 'receive_item'})
        self.operation['command_id'] = 'receive_item'
        self.assertIsInstance(self.decide(plan), c.ClarificationRequired)

    def test_suspended_or_terminal_question_never_authorizes(self):
        for status in ['suspended', 'cancelled', 'expired', 'fulfilled']:
            with self.subTest(status=status):
                self.setUp()
                self.pending(status)
                if status != 'suspended': self.context['interaction_preconditions'] = {}
                self.assertNotIsInstance(self.decide(self.empty_plan()), c.ReadyToRecheck)

    def test_stale_plan_or_binding_terms_cannot_authorize(self):
        self.pending()
        proposal, context = self.values()
        plan = InteractionPolicy().plan({p.interaction_id: p for p in context.pending_interactions}, proposal, context)
        self.operation['arguments'] = {'item': 'axe'}
        self.capability['parameter_schema']['allowed_items'].append('axe')
        self.assertIsInstance(self.decide(plan), c.ClarificationRequired)
        self.context['turn'].update(turn_id='turn:3', request_id='request:3', sequence=3)
        self.context['interaction_preconditions'] = {}
        self.assertIsInstance(self.decide(plan), c.Denied)

    def test_unresolved_or_out_of_range_current_message_spans_are_denied(self):
        for span in [{'text_id': 'old:message', 'start': 0, 'end': 1}, {'text_id': 'message:2', 'start': 0, 'end': 999}]:
            with self.subTest(span=span):
                self.operation['source_spans'] = [span]
                self.assertIsInstance(self.decide(self.empty_plan()), c.Denied)

    def test_conflicting_question_or_preconditions_cannot_reuse_a_binding(self):
        for change in ['question', 'preconditions', 'cancelled_transition']:
            with self.subTest(change=change):
                self.setUp()
                self.pending()
                proposal, context = self.values()
                current = {p.interaction_id: p for p in context.pending_interactions}
                plan = InteractionPolicy().plan(current, proposal, context)
                if change == 'question':
                    self.context['visible_recent_turns'][0]['final_reply']['text'] = 'Different question.'
                elif change == 'preconditions':
                    self.capability['relevant_preconditions'] = [{
                        'precondition_id': 'inventory:check', 'fingerprint': 'new:terms',
                        'source': {'kind': 'inventory', 'source_id': 'inventory:1', 'revision': 2,
                                   'game_scope': 'run:1', 'npc_id': 1, 'attribution': 'server', 'visibility': 'public'},
                    }]
                else:
                    pending = current['interaction:1'].model_dump(mode='python')
                    pending.update(status='cancelled', status_reason='explicit_cancellation', revision=2)
                    plan = c.InteractionPlan(
                        turn=context.turn, consent_bindings=plan.consent_bindings, clarification=None,
                        transitions=(c.InteractionTransition(expected_revision=1,
                                                             replacement=c.PendingInteraction.model_validate(pending)),),
                    )
                self.assertIsInstance(self.decide(plan), c.ClarificationRequired)

    def test_later_choice_rechecks_only_the_exact_selected_offer(self):
        self.proposal['operation_candidates'].append({**self.operation, 'candidate_id': 'operation:2'})
        proposal, context = self.values()
        choice_plan = InteractionPolicy().plan({}, proposal, context)
        self.assertIsInstance(self.policy.decide(proposal, choice_plan, context), c.ClarificationRequired)
        choice = choice_plan.transitions[0].replacement
        next_turn = {**self.context['turn'], 'turn_id': 'turn:3', 'request_id': 'request:3', 'sequence': 3}
        self.context.update(
            turn=next_turn,
            current_message={'text_id': 'message:3', 'text': 'The second one.'},
            pending_interactions=[choice.model_dump(mode='python')],
            visible_recent_turns=[{
                'turn': context.turn.model_dump(mode='python'),
                'player_message': context.current_message.model_dump(mode='python'),
                'final_reply': {'text_id': choice.question_id, 'text': choice.question_text},
            }],
            interaction_preconditions={choice.interaction_id: {
                'schema_version': 1, 'interaction_id': choice.interaction_id, 'turn': next_turn,
                'precondition_fingerprint': choice.precondition_fingerprint,
                'authority': 'server_evaluated', 'outcome': 'satisfied',
            }},
        )
        selected = {**self.operation, 'candidate_id': 'operation:2', 'pending_question_id': choice.question_id,
                    'source_spans': [{'text_id': 'message:3', 'start': 0, 'end': 15}]}
        self.proposal['operation_candidates'] = [selected]
        result = self.decide()
        self.assertIsInstance(result, c.ReadyToRecheck)
        self.assertTrue(result.operation.matches_offer(choice.offered_operations[1]))
        self.assertEqual(result.operation.source_spans[0].text_id, 'message:3')
        self.assertEqual(result.consent.answering_turn.turn_id, 'turn:3')
        self.assertEqual(result.consent.answer_span.text_id, 'message:3')
        self.assertEqual(len(self.proposal['operation_candidates']), 1)
        # Identical command terms do not let a plan substitute another option
        # for the exact choice identified by the current answer.
        binding = result.consent.model_dump(mode='python')
        binding['operation'] = choice.offered_operations[0]
        forged_plan = c.InteractionPlan(
            turn=result.consent.answering_turn, transitions=(),
            consent_bindings=(c.ConsentBinding.model_validate(binding),), clarification=None,
        )
        self.assertIsInstance(self.decide(forged_plan), c.ClarificationRequired)

    def test_policy_does_not_mutate_inputs(self):
        proposal, context = self.values()
        plan = self.empty_plan()
        before = [v.model_dump(mode='json') for v in (proposal, plan, context)]
        self.policy.decide(proposal, plan, context)
        self.assertEqual(before, [v.model_dump(mode='json') for v in (proposal, plan, context)])


class OperationServiceTests(unittest.TestCase):
    class Gateway:
        def __init__(self, receipt_result, execute_result=None):
            self.receipt_result = receipt_result
            self.execute_result = execute_result
            self.lookups = []
            self.executions = []

        def lookup_receipt(self, turn):
            self.lookups.append(turn)
            return self.receipt_result

        def execute_once(self, turn, fence, decision):
            self.executions.append((turn, fence, decision))
            return self.execute_result

    def setUp(self):
        helper = OperationPolicyTests()
        helper.setUp()
        self.policy = helper.policy
        self.proposal, self.context = helper.values()
        self.turn = self.context.turn
        self.plan = InteractionPolicy().plan({}, self.proposal, self.context)
        self.fence = 7

    def service(self, gateway):
        return OperationService(self.policy, gateway)

    def receipt(self):
        raw = json.loads((Path(__file__).parent / 'fixtures/conversation/contracts-t02-valid.json').read_text())['receipt']
        raw['turn_id'] = self.turn.turn_id
        return c.OperationReceipt.model_validate(raw)

    def test_ready_operation_uses_gateway_receipt_and_exact_typed_arguments(self):
        gateway = self.Gateway(c.OptionalResult.success(None), self.receipt())
        result = self.service(gateway).execute(self.turn, self.fence, self.proposal, self.plan, self.context)
        self.assertEqual(result, self.receipt())
        self.assertEqual(gateway.lookups, [self.turn])
        self.assertEqual(len(gateway.executions), 1)
        turn, fence, decision = gateway.executions[0]
        self.assertEqual((turn, fence), (self.turn, self.fence))
        self.assertIsInstance(decision, c.ReadyToRecheck)
        self.assertEqual(decision.operation.command_id, 'give_item')
        self.assertEqual(decision.operation.arguments.item, 'wood')

    def test_retry_returns_existing_receipt_without_reexecution(self):
        receipt = self.receipt()
        gateway = self.Gateway(c.OptionalResult.success(receipt))
        result = self.service(gateway).execute(self.turn, self.fence, self.proposal, self.plan, self.context)
        self.assertIs(result, receipt)
        self.assertEqual(gateway.lookups, [self.turn])
        self.assertEqual(gateway.executions, [])

    def test_malformed_recovered_receipt_is_a_typed_gateway_failure(self):
        gateway = self.Gateway(c.OptionalResult.success(object()))
        result = self.service(gateway).execute(self.turn, self.fence, self.proposal, self.plan, self.context)
        self.assertIsInstance(result, c.ConversationError)
        self.assertEqual(result.code, 'INTERNAL_FAILURE')
        self.assertEqual(gateway.executions, [])

    def test_nonready_decision_never_calls_gateway_execution(self):
        report = c.ReportedStatement(statement_id='report:1', attribution='player', content='Give me wood.',
            source_spans=(c.TextSpan(text_id='message:2', start=0, end=13),))
        self.proposal = self.proposal.model_copy(update={'operation_candidates': (), 'reports': (report,)})
        self.proposal = self.proposal.model_copy(update={'reply': (
            c.ExpressiveSegment(kind='expressive', segment_id='reply:1',
                text='The report says “give me wood,” but it is not an instruction.', addressed_concern_ids=()),
        )})
        self.plan = InteractionPolicy().plan({}, self.proposal, self.context)
        gateway = self.Gateway(c.OptionalResult.success(None))
        result = self.service(gateway).execute(self.turn, self.fence, self.proposal, self.plan, self.context)
        self.assertIsInstance(result, c.NoOperation)
        self.assertEqual(gateway.executions, [])

    def test_denied_typed_operation_never_calls_gateway_execution(self):
        context = self.context.model_copy(update={'capabilities': ()})
        plan = InteractionPolicy().plan({}, self.proposal, context)
        gateway = self.Gateway(c.OptionalResult.success(None))
        result = self.service(gateway).execute(self.turn, self.fence, self.proposal, plan, context)
        self.assertIsInstance(result, c.Denied)
        self.assertEqual(gateway.executions, [])

    def test_receipt_lookup_error_stops_before_policy_or_execution(self):
        error = c.ConversationError(code='STORAGE_UNAVAILABLE', stage='operation', retryable=True,
                                    turn=self.turn, safe_detail='Operation receipt lookup is unavailable.')
        gateway = self.Gateway(c.OptionalResult.failure(error))
        result = self.service(gateway).execute(self.turn, self.fence, self.proposal, self.plan, self.context)
        self.assertEqual(result, error)
        self.assertEqual(gateway.executions, [])
