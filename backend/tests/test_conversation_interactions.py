"""Pure transition policy tests for the conversation interaction boundary."""
import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from app.services.conversation import contracts as c

try:
    from app.services.conversation.interactions import InteractionPolicy
except ModuleNotFoundError:
    InteractionPolicy = None


FIXTURE = Path(__file__).parent / 'fixtures' / 'conversation' / 't05-valid.json'


class InteractionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(InteractionPolicy, 'T01 pure interaction transition policy is absent')
        self.policy = InteractionPolicy()
        self.raw = json.loads(FIXTURE.read_text())

    def _values(self, *, message=None, cues=None, states=None, pending=None, links=None, turn=None, revisions=None):
        context_raw = copy.deepcopy(self.raw['context'])
        proposal_raw = copy.deepcopy(self.raw['proposal'])
        if message is not None:
            context_raw['current_message']['text'] = message
            context_raw['current_message']['text_id'] = 'message:2'
        if cues is not None:
            proposal_raw['interaction_lifecycle_cues'] = cues
        context_raw['interaction_preconditions'] = states or {}
        if pending is not None:
            context_raw['pending_interactions'] = pending
        if links is not None:
            proposal_raw['interaction_links'] = links
        if turn is not None:
            context_raw['turn'] = turn
        if revisions is not None:
            context_raw['revisions'] = revisions
        context = c.ContextPacket.model_validate(context_raw)
        proposal = c.TurnProposal.model_validate(proposal_raw)
        current = {value.interaction_id: value for value in context.pending_interactions}
        return current, proposal, context

    def _plan(self, **kwargs):
        current, proposal, context = self._values(**kwargs)
        return self.policy.plan(current, proposal, context)

    def _status(self, plan, interaction_id):
        return next((t.replacement.status for t in plan.transitions
                     if t.replacement.interaction_id == interaction_id), None)

    def test_unlinked_new_concern_suspends_active_negotiation(self):
        current, _, context = self._values(message='I found a flower by the river.', cues=[])
        proposal = copy.deepcopy(self.raw['proposal'])
        proposal.update(
            concerns=[{'concern_id': 'concern:new', 'kind': 'other', 'message_spans': [
                {'text_id': 'message:2', 'start': 0, 'end': 21}]}],
            interaction_lifecycle_cues=[],
        )
        plan = self.policy.plan(current, c.TurnProposal.model_validate(proposal), context)
        self.assertEqual(self._status(plan, 'interaction:1'), 'suspended')
        self.assertEqual(self._status(plan, 'interaction:2'), None)
        transition = next(t for t in plan.transitions if t.replacement.interaction_id == 'interaction:1')
        self.assertEqual(transition.replacement.status_reason, 'topic_changed')
        self.assertEqual(transition.replacement.revision, 2)

    def test_explicit_cancel_targets_only_the_named_pending_interaction(self):
        cues = [self.raw['proposal']['interaction_lifecycle_cues'][0]]
        plan = self._plan(cues=cues)
        self.assertEqual(self._status(plan, 'interaction:1'), 'cancelled')
        self.assertEqual(self._status(plan, 'interaction:2'), None)
        self.assertIsNone(plan.clarification)

    def test_explicit_resume_requires_matching_current_server_evaluation(self):
        cue = self.raw['proposal']['interaction_lifecycle_cues'][1]
        state = copy.deepcopy(self.raw['context']['interaction_preconditions'])
        state['interaction:2']['outcome'] = 'satisfied'
        plan = self._plan(cues=[cue], states=state)
        self.assertEqual(self._status(plan, 'interaction:2'), 'active')
        resumed = next(t for t in plan.transitions if t.replacement.interaction_id == 'interaction:2')
        self.assertIsNone(resumed.replacement.status_reason)
        self.assertEqual(plan.consent_bindings, ())

    def test_missing_or_unavailable_evaluation_never_resumes(self):
        cue = self.raw['proposal']['interaction_lifecycle_cues'][1]
        unavailable = {'interaction:2': self.raw['unavailable_state']}
        for states in ({}, unavailable):
            with self.subTest(states=states):
                plan = self._plan(cues=[cue], states=states)
                self.assertIsNone(self._status(plan, 'interaction:2'))
                self.assertIsNotNone(plan.clarification)
                self.assertEqual(plan.consent_bindings, ())

    def test_only_matching_authoritative_failure_expires_interaction(self):
        failed = copy.deepcopy(self.raw['context']['interaction_preconditions']['interaction:2'])
        failed['outcome'] = 'failed'
        plan = self._plan(cues=[], states={'interaction:2': failed})
        self.assertEqual(self._status(plan, 'interaction:2'), 'expired')
        transition = next(t for t in plan.transitions if t.replacement.interaction_id == 'interaction:2')
        self.assertEqual(transition.replacement.status_reason, 'preconditions_changed')

    def test_changed_item_or_target_expires_only_after_current_failure_evaluation(self):
        for change in (
            {'item': 'axe'},
            {'target': {'reference_id': 'player:1', 'entity_kind': 'player', 'entity_id': 'player:1'}},
        ):
            with self.subTest(change=change):
                pending = copy.deepcopy(self.raw['context']['pending_interactions'])
                pending[0].update(change, precondition_fingerprint='fingerprint:changed')
                failed = copy.deepcopy(self.raw['context']['interaction_preconditions']['interaction:1'])
                failed.update(precondition_fingerprint='fingerprint:changed', outcome='failed')
                plan = self._plan(cues=[], states={'interaction:1': failed}, pending=pending)
                self.assertEqual(self._status(plan, 'interaction:1'), 'expired')

    def test_item_quantity_contract_rejects_changed_transfer_amount(self):
        pending = copy.deepcopy(self.raw['context']['pending_interactions'])
        pending[0]['quantity'] = 2
        with self.assertRaises(ValidationError):
            self._values(pending=pending, states={})

    def test_time_turn_and_unrelated_revision_churn_do_not_expire(self):
        turn = copy.deepcopy(self.raw['context']['turn'])
        turn.update(turn_id='turn:900', request_id='request:900', sequence=900)
        states = {}
        plan = self._plan(cues=[], states=states, turn=turn,
                          revisions={'resources': {'unrelated_inventory': 999}})
        self.assertFalse(any(t.replacement.status == 'expired' for t in plan.transitions))
        self.assertNotEqual(self._status(plan, 'interaction:2'), 'expired')

    def test_purpose_like_words_do_not_infer_failure_or_resume(self):
        pending = copy.deepcopy(self.raw['context']['pending_interactions'])
        pending[0].update(status='suspended', status_reason='topic_changed')
        concerns = [{'concern_id': 'concern:1', 'kind': 'question', 'message_spans': [
            {'text_id': 'message:2', 'start': 0, 'end': 2}]}]
        links = [{'link_id': 'link:1', 'question_id': 'question:1', 'concern_id': 'concern:1',
                  'source_spans': [{'text_id': 'message:2', 'start': 0, 'end': 2}]}]
        current, _, context = self._values(message='I might save it for later; that is my purpose.',
                                           cues=[], states={}, pending=pending)
        raw_proposal = copy.deepcopy(self.raw['proposal'])
        raw_proposal.update(concerns=concerns, interaction_links=links, interaction_lifecycle_cues=[])
        plan = self.policy.plan(current, c.TurnProposal.model_validate(raw_proposal), context)
        self.assertIsNone(self._status(plan, 'interaction:1'))
        self.assertIsNotNone(plan.clarification)
        self.assertFalse(any(t.replacement.status == 'expired' for t in plan.transitions))

    def test_multiple_suspended_references_are_clarified_without_newest_selection(self):
        pending = copy.deepcopy(self.raw['context']['pending_interactions'])
        extra = copy.deepcopy(pending[1])
        extra.update(interaction_id='interaction:3', question_id='question:3',
                     precondition_fingerprint='fingerprint:3')
        pending.append(extra)
        states = {}
        links = [
            {'link_id': 'link:2', 'question_id': 'question:2', 'concern_id': 'concern:1',
             'source_spans': [{'text_id': 'message:2', 'start': 0, 'end': 2}]},
            {'link_id': 'link:3', 'question_id': 'question:3', 'concern_id': 'concern:1',
             'source_spans': [{'text_id': 'message:2', 'start': 0, 'end': 2}]},
        ]
        # Add the concern referenced by both links; no cue identifies one target.
        proposal = copy.deepcopy(self.raw['proposal'])
        proposal['interaction_links'] = links
        proposal['concerns'] = [{'concern_id': 'concern:1', 'kind': 'question', 'message_spans': [
            {'text_id': 'message:2', 'start': 0, 'end': 2}]}]
        _, _, context = self._values(cues=[], states=states, pending=pending)
        proposal_value = c.TurnProposal.model_validate(proposal)
        current = {value.interaction_id: value for value in context.pending_interactions}
        plan = self.policy.plan(current, proposal_value, context)
        self.assertIsNotNone(plan.clarification)
        self.assertEqual(self._status(plan, 'interaction:2'), None)
        self.assertEqual(self._status(plan, 'interaction:3'), None)

    def test_second_active_item_negotiation_is_rejected(self):
        pending = copy.deepcopy(self.raw['context']['pending_interactions'])
        extra = copy.deepcopy(pending[0])
        extra.update(interaction_id='interaction:3', question_id='question:3',
                     precondition_fingerprint='fingerprint:3')
        pending.append(extra)
        with self.assertRaises(ValidationError):
            self._values(pending=pending)

    def _consent_values(self, *, message='Yes, give me the wood.', status='active', outcome='satisfied', operations=None,
                        bound=True):
        current, proposal, context = self._values(message=message, cues=[], states={})
        context_raw = context.model_dump(mode='python')
        context_raw['visible_recent_turns'] = [{
            'turn': {
                'turn_id': 'turn:1', 'request_id': 'request:1',
                'key': context_raw['turn']['key'], 'sequence': 1,
            },
            'player_message': {'text_id': 'player:1', 'text': 'Can I have some wood?'},
            'final_reply': {'text_id': 'question:1', 'text': 'Would you like this wood?'},
        }]
        pending = copy.deepcopy(context_raw['pending_interactions'][0])
        pending.update(status=status, status_reason=None if status == 'active' else {
            'suspended': 'topic_changed', 'cancelled': 'explicit_cancellation',
            'expired': 'preconditions_changed', 'fulfilled': 'operation_completed',
        }[status])
        context_raw['pending_interactions'] = [pending]
        context_raw['interaction_preconditions'] = {
            'interaction:1': {
                'schema_version': 1, 'interaction_id': 'interaction:1',
                'turn': context_raw['turn'], 'precondition_fingerprint': 'fingerprint:1',
                'authority': 'server_evaluated', 'outcome': outcome,
            }
        } if status in {'active', 'suspended'} else {}
        target = copy.deepcopy(pending['target'])
        source = {
            'kind': 'inventory', 'source_id': 'inventory:1', 'revision': 4,
            'game_scope': 'run:1', 'npc_id': 1, 'attribution': 'server', 'visibility': 'public',
        }
        capability = {
            'command_id': 'give_item',
            'parameter_schema': {'kind': 'single_item', 'allowed_items': ['wood', 'axe']},
            'allowed_target_references': [target], 'available': True,
            'safe_unavailable_reason': None,
            'relevant_preconditions': [{'precondition_id': 'precondition:1', 'source': source,
                                        'fingerprint': 'fingerprint:1'}],
            'supported_speech_acts': ['accept', 'request'],
        }
        context_raw['capabilities'] = [capability]
        op = {
            'candidate_id': 'operation:1', 'command_id': 'give_item',
            'arguments': {'item': 'wood'}, 'target': target,
            'source_spans': [{'text_id': 'message:2', 'start': 0, 'end': len(message)}],
            'modality': 'direct', 'pending_question_id': 'question:1',
        }
        if bound:
            pending['authorized_operation'] = {
                **op, 'candidate_id': 'offer:1',
                'source_spans': [{'text_id': 'question:1', 'start': 0, 'end': len(pending['question_text'])}],
            }
        context = c.ContextPacket.model_validate(context_raw)
        if operations is not None:
            op_list = operations
        else:
            op_list = [op]
        proposal_raw = copy.deepcopy(proposal.model_dump(mode='python'))
        proposal_raw['operation_candidates'] = op_list
        proposal_raw['interaction_links'] = []
        proposal = c.TurnProposal.model_validate(proposal_raw)
        current = {value.interaction_id: value for value in context.pending_interactions}
        return current, proposal, context

    def test_direct_answer_binds_exact_current_question_turn_span_and_preconditions(self):
        current, proposal, context = self._consent_values()
        plan = self.policy.plan(current, proposal, context)
        self.assertEqual(len(plan.consent_bindings), 1)
        binding, = plan.consent_bindings
        self.assertEqual(binding.interaction_id, 'interaction:1')
        self.assertEqual(binding.question_id, 'question:1')
        self.assertEqual(binding.question_turn_id, 'turn:1')
        self.assertEqual(binding.answering_turn, context.turn)
        self.assertEqual(binding.answer_span.resolve({'message:2': context.current_message.text}), context.current_message.text)
        self.assertEqual(binding.operation.arguments.item, 'wood')
        self.assertEqual(binding.checked_preconditions[0].fingerprint, 'fingerprint:1')

    def test_single_offer_consent_carries_stored_operation_and_separate_current_answer(self):
        current, proposal, context = self._consent_values()
        plan = self.policy.plan(current, proposal, context)
        binding, = plan.consent_bindings
        stored = current['interaction:1'].authorized_operation
        answered = next(value for value in proposal.operation_candidates
                        if value.pending_question_id == stored.pending_question_id)
        self.assertEqual(binding.operation, answered)
        self.assertEqual(binding.operation.source_spans[0].text_id, context.current_message.text_id)
        self.assertEqual((binding.operation.command_id, binding.operation.arguments,
                          binding.operation.target, binding.operation.modality,
                          binding.operation.pending_question_id),
                         (stored.command_id, stored.arguments, stored.target,
                          stored.modality, stored.pending_question_id))
        self.assertEqual(binding.operation.candidate_id, answered.candidate_id)
        self.assertEqual(binding.operation.source_spans[0].text_id, context.current_message.text_id)
        self.assertEqual(binding.answer_span, proposal.operation_candidates[0].source_spans[0])

    def test_missing_legacy_binding_never_infers_offer_from_affirmative_answer(self):
        current, proposal, context = self._consent_values(bound=False)
        plan = self.policy.plan(current, proposal, context)
        self.assertEqual(plan.consent_bindings, ())
        self.assertIsNotNone(plan.clarification)

    def test_single_offer_rejects_changed_command_direction(self):
        current, proposal, context = self._consent_values()
        raw = context.model_dump(mode='python')
        raw['capabilities'] = (*raw['capabilities'], {**raw['capabilities'][0], 'command_id': 'receive_item'})
        context = c.ContextPacket.model_validate(raw)
        raw_proposal = proposal.model_dump(mode='python')
        raw_proposal['operation_candidates'][0]['command_id'] = 'receive_item'
        plan = self.policy.plan(current, c.TurnProposal.model_validate(raw_proposal), context)
        self.assertEqual(plan.consent_bindings, ())
        self.assertIsNotNone(plan.clarification)

    def test_exact_activity_offer_is_carried_without_becoming_completed_activity(self):
        current, proposal, context = self._consent_values()
        raw = context.model_dump(mode='python')
        pending = raw['pending_interactions'][0]
        pending.update(kind='activity_offer', item=None, quantity=None)
        pending['authorized_operation'].update(command_id='begin_ship_inspection', arguments={})
        raw['capabilities'][0].update(command_id='begin_ship_inspection', parameter_schema={'kind': 'none'})
        context = c.ContextPacket.model_validate(raw)
        raw_proposal = proposal.model_dump(mode='python')
        raw_proposal['operation_candidates'][0].update(command_id='begin_ship_inspection', arguments={})
        current = {value.interaction_id: value for value in context.pending_interactions}
        plan = self.policy.plan(current, c.TurnProposal.model_validate(raw_proposal), context)
        binding, = plan.consent_bindings
        self.assertEqual(binding.operation.command_id, 'begin_ship_inspection')
        stored = current['interaction:1'].authorized_operation
        self.assertNotEqual(binding.operation.candidate_id, stored.candidate_id)
        self.assertEqual(binding.operation.source_spans[0].text_id, context.current_message.text_id)
        self.assertEqual((binding.operation.command_id, binding.operation.arguments,
                          binding.operation.target, binding.operation.modality,
                          binding.operation.pending_question_id),
                         (stored.command_id, stored.arguments, stored.target,
                          stored.modality, stored.pending_question_id))
        self.assertEqual(plan.transitions, ())

    def test_single_offer_never_binds_ambiguous_or_unsupported_proposals(self):
        for mode in ('quoted', 'hypothetical', 'negated', 'ambiguous', 'unsupported'):
            with self.subTest(mode=mode):
                current, proposal, context = self._consent_values()
                raw = proposal.model_dump(mode='python')
                extra = {**raw['operation_candidates'][0], 'candidate_id': 'operation:other'}
                if mode == 'unsupported':
                    extra.update(command_id='wait', arguments={})
                else:
                    extra['modality'] = mode
                raw['operation_candidates'] = (*raw['operation_candidates'], extra)
                plan = self.policy.plan(current, c.TurnProposal.model_validate(raw), context)
                self.assertEqual(plan.consent_bindings, ())
                self.assertIsNotNone(plan.clarification)

    def test_lifecycle_replacement_preserves_stored_offer_without_creating_consent(self):
        current, proposal, context = self._consent_values(operations=[])
        plan = self.policy.plan(current, proposal, context)
        replacement, = plan.transitions
        self.assertEqual(replacement.replacement.status, 'suspended')
        self.assertEqual(replacement.replacement.authorized_operation, current['interaction:1'].authorized_operation)
        self.assertEqual(plan.consent_bindings, ())

    def test_bare_confirmation_does_not_bind_after_interaction_is_suspended(self):
        current, proposal, context = self._consent_values(status='suspended')
        plan = self.policy.plan(current, proposal, context)
        self.assertEqual(plan.consent_bindings, ())
        self.assertIsNotNone(plan.clarification)

    def test_explicit_resume_with_missing_consent_requests_fresh_answer(self):
        current, proposal, context = self._consent_values(status='suspended', outcome='unavailable')
        proposal_raw = proposal.model_dump(mode='python')
        proposal_raw['operation_candidates'] = []
        proposal_raw['interaction_links'] = [{
            'link_id': 'link:resume', 'question_id': 'question:1', 'concern_id': 'concern:1',
            'source_spans': [{'text_id': 'message:2', 'start': 0, 'end': 6}],
        }]
        proposal_raw['concerns'] = [{
            'concern_id': 'concern:1', 'kind': 'request',
            'message_spans': [{'text_id': 'message:2', 'start': 0, 'end': 6}],
        }]
        proposal_raw['interaction_lifecycle_cues'] = [{
            'schema_version': 1, 'cue_id': 'cue:resume', 'turn': context.turn,
            'interaction_id': 'interaction:1', 'action': 'resume', 'modality': 'direct',
            'source_span': {'text_id': 'message:2', 'start': 0, 'end': 6}, 'source_text': 'resume',
        }]
        context_raw = context.model_dump(mode='python')
        context_raw['current_message']['text'] = 'resume'
        context_raw['current_message']['text_id'] = 'message:2'
        context_raw['interaction_preconditions']['interaction:1']['outcome'] = 'unavailable'
        context = c.ContextPacket.model_validate(context_raw)
        proposal_raw['interaction_lifecycle_cues'][0]['turn'] = context.turn
        proposal = c.TurnProposal.model_validate(proposal_raw)
        current = {value.interaction_id: value for value in context.pending_interactions}
        plan = self.policy.plan(current, proposal, context)
        self.assertEqual(plan.consent_bindings, ())
        self.assertIsNotNone(plan.clarification)

    def test_terminal_or_cancelled_confirmations_never_bind(self):
        for status in ('cancelled', 'expired', 'fulfilled'):
            with self.subTest(status=status):
                current, proposal, context = self._consent_values(status=status)
                plan = self.policy.plan(current, proposal, context)
                self.assertEqual(plan.consent_bindings, ())

    def test_multiple_supported_requests_create_choices_without_binding_or_queueing(self):
        message = 'Give me wood and wait.'
        current, proposal, context = self._consent_values(message=message, operations=[
            {'candidate_id': 'operation:1', 'command_id': 'give_item',
             'arguments': {'item': 'wood'},
             'target': {'reference_id': 'npc:1', 'entity_kind': 'npc', 'entity_id': '1'},
             'source_spans': [{'text_id': 'message:2', 'start': 0, 'end': 13}],
             'modality': 'direct', 'pending_question_id': None},
            {'candidate_id': 'operation:2', 'command_id': 'wait',
             'arguments': {},
             'target': {'reference_id': 'npc:1', 'entity_kind': 'npc', 'entity_id': '1'},
             'source_spans': [{'text_id': 'message:2', 'start': 18, 'end': 22}],
             'modality': 'direct', 'pending_question_id': None},
        ])
        context_raw = context.model_dump(mode='python')
        context_raw['capabilities'] = [*context_raw['capabilities'], {
            'command_id': 'wait', 'parameter_schema': {'kind': 'none'},
            'allowed_target_references': [current['interaction:1'].target.model_dump(mode='python')],
            'available': True, 'safe_unavailable_reason': None, 'relevant_preconditions': [],
            'supported_speech_acts': ['request'],
        }]
        context = c.ContextPacket.model_validate(context_raw)
        proposal = c.TurnProposal.model_validate(proposal.model_dump(mode='python'))
        plan = self.policy.plan(current, proposal, context)
        self.assertEqual(plan.consent_bindings, ())
        choices = [t.replacement for t in plan.transitions if t.replacement.kind == 'action_choice']
        self.assertEqual(len(choices), 1)
        self.assertEqual({value.candidate_id for value in choices[0].offered_operations}, {'operation:1', 'operation:2'})
        self.assertIsNone(choices[0].authorized_operation)
        self.assertIsNotNone(plan.clarification)

    def test_selection_binds_only_the_selected_offered_action(self):
        message = 'Give me wood and wait.'
        current, proposal, context = self._consent_values(message=message, operations=[
            {'candidate_id': 'operation:1', 'command_id': 'give_item',
             'arguments': {'item': 'wood'},
             'target': {'reference_id': 'npc:1', 'entity_kind': 'npc', 'entity_id': '1'},
             'source_spans': [{'text_id': 'message:2', 'start': 0, 'end': 13}],
             'modality': 'direct', 'pending_question_id': None},
            {'candidate_id': 'operation:2', 'command_id': 'wait',
             'arguments': {},
             'target': {'reference_id': 'npc:1', 'entity_kind': 'npc', 'entity_id': '1'},
             'source_spans': [{'text_id': 'message:2', 'start': 18, 'end': 22}],
             'modality': 'direct', 'pending_question_id': None},
        ])
        context_raw = context.model_dump(mode='python')
        context_raw['capabilities'] = [*context_raw['capabilities'], {
            'command_id': 'wait', 'parameter_schema': {'kind': 'none'},
            'allowed_target_references': [current['interaction:1'].target.model_dump(mode='python')],
            'available': True, 'safe_unavailable_reason': None, 'relevant_preconditions': [],
            'supported_speech_acts': ['request'],
        }]
        context = c.ContextPacket.model_validate(context_raw)
        plan = self.policy.plan(current, proposal, context)
        choice, = [t.replacement for t in plan.transitions if t.replacement.kind == 'action_choice']

        next_turn = {
            'turn_id': 'turn:3', 'request_id': 'request:3',
            'key': context.turn.key.model_dump(mode='python'), 'sequence': 3,
        }
        next_message = 'Do the second one.'
        next_context_raw = copy.deepcopy(context_raw)
        next_context_raw.update(turn=next_turn,
                                current_message={'text_id': 'message:3', 'text': next_message},
                                pending_interactions=[choice.model_dump(mode='python')],
                                visible_recent_turns=[{
                                    'turn': context.turn.model_dump(mode='python'),
                                    'player_message': context.current_message.model_dump(mode='python'),
                                    'final_reply': {'text_id': choice.question_id, 'text': choice.question_text},
                                }],
                                interaction_preconditions={choice.interaction_id: {
                                    'schema_version': 1, 'interaction_id': choice.interaction_id,
                                    'turn': next_turn,
                                    'precondition_fingerprint': choice.precondition_fingerprint,
                                    'authority': 'server_evaluated', 'outcome': 'satisfied',
                                }})
        next_context = c.ContextPacket.model_validate(next_context_raw)
        selected_raw = copy.deepcopy(proposal.model_dump(mode='python'))
        selected_raw['operation_candidates'] = [{
            'candidate_id': 'operation:2', 'command_id': 'wait', 'arguments': {},
            'target': {'reference_id': 'npc:1', 'entity_kind': 'npc', 'entity_id': '1'},
            'source_spans': [{'text_id': 'message:3', 'start': 0, 'end': len(next_message)}],
            'modality': 'direct', 'pending_question_id': choice.question_id,
        }]
        selected = c.TurnProposal.model_validate(selected_raw)
        plan = self.policy.plan({choice.interaction_id: choice}, selected, next_context)
        binding, = plan.consent_bindings
        self.assertEqual(binding.operation.candidate_id, 'operation:2')
        self.assertEqual(binding.answering_turn, next_context.turn)
        self.assertEqual(binding.answer_span.resolve({'message:3': next_message}), next_message)
        self.assertEqual(tuple(value.candidate_id for value in choice.offered_operations), ('operation:1', 'operation:2'))

    def test_old_plan_cannot_reuse_consent_after_interaction_is_fulfilled(self):
        current, proposal, context = self._consent_values()
        plan = self.policy.plan(current, proposal, context)
        fulfilled = copy.deepcopy(current['interaction:1'].model_dump(mode='python'))
        fulfilled.update(status='fulfilled', status_reason='operation_completed', revision=2)
        with self.assertRaises(ValueError):
            plan.validate_current({'interaction:1': c.PendingInteraction.model_validate(fulfilled)})


if __name__ == '__main__':
    unittest.main()
