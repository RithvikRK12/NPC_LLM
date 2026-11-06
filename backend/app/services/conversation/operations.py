"""Pure selection of one typed request for a later authoritative recheck.

No prose recognizers, provider calls, game services or state writes belong here.
ReadyToRecheck describes a request; only the transaction gateway can authorize
and execute it against current gameplay state.
"""
from app.services.conversation.contracts import (
    ClarificationRequired, ContextPacket, ConversationError, Denied, InteractionPlan,
    ItemArguments, ItemParameterSchema, NoArguments, NoOperation, OperationReceipt,
    NoParameterSchema, OperationDecision, OptionalResult, ReadyToRecheck, TurnProposal, TurnRef,
)
from .ports import OperationGateway


class OperationPolicy:
    def decide(
        self, proposal: TurnProposal, interaction_plan: InteractionPlan, context: ContextPacket,
    ) -> OperationDecision:
        if not isinstance(proposal, TurnProposal) or not isinstance(interaction_plan, InteractionPlan) or not isinstance(context, ContextPacket):
            raise TypeError('operation selection requires typed proposal, plan and context')
        if interaction_plan.turn != context.turn:
            return self._denied('RESOURCE_CHANGED', 'The request must be checked for the current turn.')
        current = {value.interaction_id: value for value in context.pending_interactions}
        texts = {context.current_message.text_id: context.current_message.text}
        try:
            proposal.validate_references(texts, context=context)
            interaction_plan.validate_current(current)
        except ValueError:
            return self._denied('INVALID_INPUT', 'The request does not match the current conversation evidence.')

        capabilities = {value.command_id: value for value in context.capabilities}
        supported = []
        denials = []
        ambiguous = False
        for operation in proposal.operation_candidates:
            if operation.modality == 'ambiguous':
                ambiguous = True
                continue
            if operation.modality != 'direct':
                continue
            descriptor = capabilities.get(operation.command_id)
            if descriptor is None:
                denials.append(self._denied('UNSUPPORTED_OPERATION', 'That action is not supported here.'))
                continue
            if not descriptor.available:
                denials.append(self._denied('OPERATION_UNAVAILABLE', descriptor.safe_unavailable_reason))
                continue
            if not set(descriptor.supported_speech_acts) & {'request', 'accept'}:
                denials.append(self._denied('UNSUPPORTED_OPERATION', 'That action cannot be requested here.'))
                continue
            if operation.target not in descriptor.allowed_target_references:
                denials.append(self._denied('UNSUPPORTED_OPERATION', 'That target is not supported for this action.'))
                continue
            valid_arguments = (
                isinstance(operation.arguments, ItemArguments) and
                isinstance(descriptor.parameter_schema, ItemParameterSchema) and
                operation.arguments.item in descriptor.parameter_schema.allowed_items
            ) or (
                isinstance(operation.arguments, NoArguments) and
                isinstance(descriptor.parameter_schema, NoParameterSchema)
            )
            if not valid_arguments:
                denials.append(self._denied('UNSUPPORTED_OPERATION', 'Those action parameters are not supported.'))
                continue
            supported.append((operation, descriptor))

        if interaction_plan.clarification is not None:
            return interaction_plan.clarification
        if ambiguous:
            return self._clarify(proposal, 'Please clarify which action you want me to take.')
        if len(supported) > 1:
            return self._clarify(proposal, 'Which action would you like me to do first?')
        if not supported:
            return denials[0] if denials else NoOperation(kind='no_operation')
        operation, descriptor = supported[0]
        if operation.pending_question_id is None:
            # A consent from a different operation cannot silently become a
            # fresh request, even when its target or command happens to match.
            if interaction_plan.consent_bindings:
                return self._clarify(proposal, 'Please confirm the exact action you want me to take.')
            return ReadyToRecheck(kind='ready_to_recheck', operation=operation,
                                  consent=None, checked_preconditions=descriptor.relevant_preconditions)

        bindings = [binding for binding in interaction_plan.consent_bindings
                    if binding.question_id == operation.pending_question_id and
                    self._same_request(operation, binding.operation)]
        if len(bindings) != 1:
            return self._clarify(proposal, 'Please confirm which pending request you want to continue.')
        binding = bindings[0]
        interaction = current.get(binding.interaction_id)
        state = context.interaction_preconditions.get(binding.interaction_id)
        if (interaction is None or state is None or state.outcome != 'satisfied' or
                binding.answering_turn != context.turn or
                binding.checked_preconditions != descriptor.relevant_preconditions):
            return self._clarify(proposal, 'Please confirm the request after its current requirements are checked.')
        replacement = next((value.replacement for value in interaction_plan.transitions
                            if value.replacement.interaction_id == binding.interaction_id), interaction)
        if replacement != interaction:
            return self._clarify(proposal, 'Please confirm the current pending request again.')
        try:
            answer = binding.answer_span.resolve(texts)
            if binding.answer_span not in operation.source_spans:
                raise ValueError('consent answer must cite the selected current candidate')
            binding.validate_against(interaction, texts, expected_answer=answer)
            question = next(value for value in context.visible_recent_turns
                            if value.turn == binding.question_turn)
            interaction.validate_question(question.turn, question.final_reply)
            if interaction.kind in {'item_negotiation', 'activity_offer'}:
                if (interaction.authorized_operation is None or
                        not self._same_request(binding.operation, interaction.authorized_operation)):
                    raise ValueError('consent requires the exact stored offer')
            elif interaction.kind == 'action_choice':
                if binding.operation.candidate_id != operation.candidate_id:
                    raise ValueError('consent must select the exact offered choice')
            elif binding.operation != operation:
                raise ValueError('consent must match exact current operation')
        except (ValueError, StopIteration):
            return self._clarify(proposal, 'Please confirm the exact pending request again.')
        # Keep the current answer operation so its source span remains attached
        # through the gateway's independent persisted consent check.
        return ReadyToRecheck(kind='ready_to_recheck', operation=binding.operation,
                              consent=binding, checked_preconditions=descriptor.relevant_preconditions)

    @staticmethod
    def _same_request(selected, bound):
        return (selected.command_id == bound.command_id and selected.target == bound.target and
                selected.arguments == bound.arguments and selected.modality == bound.modality and
                selected.pending_question_id == bound.pending_question_id)

    @staticmethod
    def _denied(code, explanation):
        return Denied(kind='denied', reason_code=code, safe_explanation=explanation)

    @staticmethod
    def _clarify(proposal, question):
        return ClarificationRequired(kind='clarification_required',
                                     concern_ids=tuple(value.concern_id for value in proposal.concerns),
                                     question=question)


class OperationService:
    """Recover a committed receipt or dispatch one typed decision exactly once.

    A returned ReadyToRecheck is still only a selected request. The injected
    gateway owns current authority checks and the atomic effect/receipt write.
    """

    def __init__(self, policy: OperationPolicy, gateway: OperationGateway):
        self._policy = policy
        self._gateway = gateway

    def execute(
        self, turn: TurnRef, fence: int, proposal: TurnProposal,
        interaction_plan: InteractionPlan, context: ContextPacket,
    ) -> OperationDecision | OperationReceipt | ConversationError:
        """Look up durable outcome first; invoke execution only for a ready request."""
        if turn != context.turn:
            return ConversationError(code='RESOURCE_CHANGED', stage='operation', retryable=True,
                turn=turn, safe_detail='The request belongs to a different current turn.')

        recovered = self._gateway.lookup_receipt(turn)
        if not isinstance(recovered, OptionalResult):
            return self._error(turn, 'The operation gateway returned an invalid receipt lookup.')
        if recovered.error is not None:
            return recovered.error
        if recovered.value is not None:
            if (isinstance(recovered.value, OperationReceipt) and
                    self._receipt_matches_turn(recovered.value, turn)):
                return recovered.value
            return self._error(turn, 'The recovered operation receipt does not match this turn.')

        decision = self._policy.decide(proposal, interaction_plan, context)
        if not isinstance(decision, ReadyToRecheck):
            return decision

        outcome = self._gateway.execute_once(turn, fence, decision)
        if isinstance(outcome, ConversationError):
            return outcome
        if not isinstance(outcome, OperationReceipt):
            return self._error(turn, 'The operation gateway returned an invalid receipt.')
        if not self._receipt_matches_turn(outcome, turn):
            return self._error(turn, 'The operation receipt does not match this turn.')
        try:
            outcome.verify_operation(decision.operation)
        except ValueError:
            return self._error(turn, 'The operation receipt does not match the selected request.')
        return outcome

    @staticmethod
    def _receipt_matches_turn(receipt: OperationReceipt, turn: TurnRef) -> bool:
        return (receipt.turn_id == turn.turn_id and receipt.game_scope == turn.key.game_scope and
                receipt.npc_id == turn.key.npc_id)

    @staticmethod
    def _error(turn: TurnRef, detail: str) -> ConversationError:
        return ConversationError(code='INTERNAL_FAILURE', stage='operation', retryable=False,
                                 turn=turn, safe_detail=detail)
