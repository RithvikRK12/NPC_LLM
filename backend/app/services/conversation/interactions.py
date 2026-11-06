"""Pure policy for pending interaction lifecycle transitions.

This module interprets typed proposal references against an accepted context
snapshot. It never persists changes, grants consent, or executes operations.
"""
import hashlib
import json
from collections.abc import Mapping

from app.services.conversation.contracts import (
    ClarificationRequired,
    ContextPacket,
    ConsentBinding,
    ItemArguments,
    InteractionPlan,
    InteractionTransition,
    NoParameterSchema,
    NoArguments,
    OperationCandidate,
    PendingInteraction,
    ItemParameterSchema,
    TurnProposal,
)


class InteractionPolicy:
    """Plan interaction status changes from explicit cues and current reads."""

    def plan(
        self,
        current: Mapping[str, PendingInteraction],
        proposal: TurnProposal,
        context: ContextPacket,
    ) -> InteractionPlan:
        """Return a scoped transition plan; never mutate the supplied snapshot.

        ``current`` must be the exact interaction snapshot used to build
        ``context``. A resume requires a direct, span-validated cue and a
        matching server-evaluated satisfied precondition. A matching failed
        evaluation is the only path to ``expired``.
        """
        if not isinstance(context, ContextPacket) or not isinstance(proposal, TurnProposal):
            raise TypeError('interaction planning requires typed proposal and context values')
        context_pending = {value.interaction_id: value for value in context.pending_interactions}
        if dict(current) != context_pending:
            raise ValueError('current interactions do not match the accepted context snapshot')
        if any(key != value.interaction_id for key, value in current.items()):
            raise ValueError('current interaction map keys must match interaction IDs')
        # This enforces the T05 current-message, turn, interaction-ID and exact
        # evidence-span checks before policy consumes any lifecycle cue.
        proposal.validate_references(
            {context.current_message.text_id: context.current_message.text}, context=context
        )

        cues = {cue.interaction_id: cue for cue in proposal.interaction_lifecycle_cues}
        capabilities = {value.command_id: value for value in context.capabilities}
        supported_operations = tuple(
            operation for operation in proposal.operation_candidates
            if operation.modality == 'direct' and self._supported(operation, capabilities)
        )
        links_by_question: dict[str, list[str]] = {}
        for link in proposal.interaction_links:
            links_by_question.setdefault(link.question_id, []).append(link.concern_id)

        linked_suspended = [
            interaction for interaction in current.values()
            if interaction.status == 'suspended' and interaction.question_id in links_by_question
        ]
        explicit_resumes = {
            interaction_id for interaction_id, cue in cues.items() if cue.action == 'resume'
        }
        linked_suspended_ids = {interaction.interaction_id for interaction in linked_suspended}
        selected_suspended_ids = explicit_resumes & linked_suspended_ids
        ambiguous = len(linked_suspended) > 1 and not selected_suspended_ids

        transitions: list[InteractionTransition] = []
        clarification = None
        if ambiguous:
            concern_ids = tuple(sorted({
                concern_id
                for interaction in linked_suspended
                for concern_id in links_by_question.get(interaction.question_id, ())
            }))
            clarification = ClarificationRequired(
                kind='clarification_required',
                concern_ids=concern_ids,
                question='Which pending request are you referring to?',
            )

        for interaction_id, interaction in current.items():
            if interaction.status not in {'active', 'suspended'}:
                continue
            state = context.interaction_preconditions.get(interaction_id)
            cue = cues.get(interaction_id)

            # Only a current, matching server-evaluated failed state can expire
            # a request. ContextPacket validates its identity and fingerprint.
            if state is not None and state.outcome == 'failed':
                replacement = self._replace(interaction, 'expired', 'preconditions_changed')
            elif cue is not None and cue.action == 'cancel':
                replacement = self._replace(interaction, 'cancelled', 'explicit_cancellation')
            elif interaction.status == 'suspended':
                if ambiguous and interaction in linked_suspended:
                    continue
                if cue is not None and cue.action == 'resume':
                    if state is not None and state.outcome == 'satisfied':
                        replacement = self._replace(interaction, 'active', None)
                    else:
                        clarification = clarification or ClarificationRequired(
                            kind='clarification_required',
                            concern_ids=tuple(sorted(set(links_by_question.get(interaction.question_id, ())))),
                            question='I can return to that request after checking its current requirements. Do you want to continue?',
                        )
                        continue
                elif interaction.question_id in links_by_question and selected_suspended_ids:
                    # An explicit cue selected another linked request. Do not
                    # let the extra model link silently affect this record.
                    continue
                elif interaction.question_id in links_by_question:
                    clarification = clarification or ClarificationRequired(
                        kind='clarification_required',
                        concern_ids=tuple(sorted(set(links_by_question[interaction.question_id]))),
                        question='Do you want to resume that pending request?',
                    )
                    continue
                else:
                    continue
            elif (interaction.question_id not in links_by_question and not any(
                    operation.pending_question_id == interaction.question_id
                    for operation in supported_operations)):
                # An unrelated concern is a topic shift. Purpose-like wording,
                # turn age, wall time, and revision changes do not affect this.
                replacement = self._replace(interaction, 'suspended', 'topic_changed')
            else:
                continue

            if replacement != interaction:
                transitions.append(InteractionTransition(
                    expected_revision=interaction.revision,
                    replacement=replacement,
                ))

        consent_bindings: list[ConsentBinding] = []
        choice_transitions: list[InteractionTransition] = []
        clarification = clarification or self._consent_and_choice(
            current=current,
            supported_operations=supported_operations,
            proposal=proposal,
            context=context,
            capabilities=capabilities,
            transitions=transitions,
            consent_bindings=consent_bindings,
            choice_transitions=choice_transitions,
        )

        return InteractionPlan(
            turn=context.turn,
            transitions=tuple((*transitions, *choice_transitions)),
            consent_bindings=tuple(consent_bindings),
            clarification=clarification,
        )

    @staticmethod
    def _supported(operation, capabilities: Mapping) -> bool:
        descriptor = capabilities.get(operation.command_id)
        if descriptor is None or not descriptor.available:
            return False
        if not set(descriptor.supported_speech_acts) & {'request', 'accept'}:
            return False
        if operation.target not in descriptor.allowed_target_references:
            return False
        if isinstance(operation.arguments, ItemArguments):
            return (isinstance(descriptor.parameter_schema, ItemParameterSchema) and
                    operation.arguments.item in descriptor.parameter_schema.allowed_items)
        return isinstance(operation.arguments, NoArguments) and isinstance(
            descriptor.parameter_schema, NoParameterSchema
        )

    @classmethod
    def _consent_and_choice(
        cls, *, current, supported_operations, proposal, context, capabilities,
        transitions, consent_bindings, choice_transitions,
    ):
        by_question = {value.question_id: value for value in current.values()}
        active_candidates = [
            operation for operation in supported_operations
            if operation.pending_question_id in by_question and
            by_question[operation.pending_question_id].status == 'active'
        ]
        if (any(operation.pending_question_id in by_question for operation in proposal.operation_candidates)
                and len(supported_operations) != len(proposal.operation_candidates)):
            # Filtering an unsupported or non-direct candidate must not turn
            # a mixed/ambiguous answer into consent for the surviving action.
            return ClarificationRequired(
                kind='clarification_required',
                concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                question='Please confirm one supported action for the current request.',
            )
        # A selection must resolve to exactly one operation that was offered
        # by an active action-choice question. Offers remain inert until this
        # exact current-turn selection is bound.
        selected = []
        for interaction in current.values():
            if interaction.kind != 'action_choice' or interaction.status != 'active':
                continue
            matches = [operation for operation in supported_operations
                       if operation.pending_question_id == interaction.question_id and
                       any(cls._same_offered_action(operation, offered)
                           for offered in interaction.offered_operations)]
            if len(matches) == 1:
                selected.append((interaction, matches[0]))
            elif len(matches) > 1:
                return ClarificationRequired(
                    kind='clarification_required',
                    concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                    question='Which offered action would you like me to do first?',
                )

        choices = [operation for operation in supported_operations
                   if operation.pending_question_id is None]
        if len(choices) > 1:
            # More than one actionable request is an offer list, never a queue.
            fingerprint_input = json.dumps(
                [value.model_dump(mode='json') for value in choices],
                sort_keys=True, separators=(',', ':'),
            ).encode('utf-8')
            fingerprint = 'choice:' + hashlib.sha256(fingerprint_input).hexdigest()
            turn_tag = hashlib.sha256(context.turn.turn_id.encode('utf-8')).hexdigest()[:20]
            question_id = f'fallback:{context.turn.turn_id}'
            interaction_id = f'interaction:choice:{turn_tag}'
            offered = tuple(OperationCandidate.model_validate({
                **value.model_dump(mode='python'), 'pending_question_id': question_id,
            }) for value in choices)
            record = PendingInteraction(
                interaction_id=interaction_id,
                key=context.turn.key,
                kind='action_choice',
                originating_turn=context.turn,
                target=offered[0].target,
                item=None,
                quantity=None,
                question_text='Which would you like me to do first?',
                question_id=question_id,
                question_turn_id=context.turn.turn_id,
                required_response_kind='choice',
                precondition_fingerprint=fingerprint,
                revision=0,
                status='active',
                status_reason=None,
                offered_operations=offered,
            )
            choice_transitions.append(InteractionTransition(expected_revision=None, replacement=record))
            return ClarificationRequired(
                kind='clarification_required',
                concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                question=record.question_text,
            )

        for interaction, operation in selected:
            if len(supported_operations) != 1:
                return ClarificationRequired(
                    kind='clarification_required',
                    concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                    question='Please choose only one action to do first.',
                )
            state = context.interaction_preconditions.get(interaction.interaction_id)
            descriptor = capabilities[operation.command_id]
            if state is None or state.outcome != 'satisfied':
                return ClarificationRequired(
                    kind='clarification_required',
                    concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                    question='I need to recheck that choice before I can continue. Would you like me to proceed?',
                )
            answer_span = operation.source_spans[0]
            offered = next(value for value in interaction.offered_operations
                           if cls._same_offered_action(operation, value))
            binding = cls._binding(interaction, operation, answer_span,
                                   descriptor.relevant_preconditions, context)
            if binding is None:
                return ClarificationRequired(
                    kind='clarification_required',
                    concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                    question='Please confirm that choice again so I can check its current requirements.',
                )
            consent_bindings.append(binding)

        # Only a sole supported direct action tied to the exact current active
        # question can create consent. Suspended/terminal questions and bare
        # affirmations without a matching operation never transfer consent.
        if not selected and len(active_candidates) == 1 and len(supported_operations) == 1:
            interaction = by_question[active_candidates[0].pending_question_id]
            operation = active_candidates[0]
            if interaction.kind in {'item_negotiation', 'activity_offer'}:
                stored = interaction.authorized_operation
                if stored is None or not cls._same_terms(operation, stored):
                    return ClarificationRequired(
                        kind='clarification_required',
                        concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                        question='Please confirm the exact terms of the current request.',
                    )
            state = context.interaction_preconditions.get(interaction.interaction_id)
            descriptor = capabilities[active_candidates[0].command_id]
            if state is None or state.outcome != 'satisfied':
                return ClarificationRequired(
                    kind='clarification_required',
                    concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                    question='I need to check the current requirements before continuing. Would you like to proceed?',
                )
            binding = cls._binding(interaction, operation,
                                   active_candidates[0].source_spans[0],
                                   descriptor.relevant_preconditions, context)
            if binding is not None:
                consent_bindings.append(binding)
            else:
                return ClarificationRequired(
                    kind='clarification_required',
                    concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                    question='Those terms do not match the current request. Please confirm what you want me to do.',
                )
        elif supported_operations and not selected and any(
                operation.pending_question_id in by_question for operation in supported_operations):
            return ClarificationRequired(
                kind='clarification_required',
                concern_ids=tuple(sorted({concern.concern_id for concern in proposal.concerns})),
                question='Which pending request are you confirming?',
            )
        return None

    @staticmethod
    def _same_terms(selected, stored) -> bool:
        # Candidate IDs and source spans describe each utterance. Compare the
        # action terms while keeping the current answer's provenance.
        return (
            selected.command_id == stored.command_id and
            selected.arguments == stored.arguments and
            selected.target == stored.target and
            selected.modality == stored.modality == 'direct' and
            selected.pending_question_id == stored.pending_question_id
        )

    @staticmethod
    def _same_offered_action(selected, offered) -> bool:
        return (
            selected.candidate_id == offered.candidate_id and
            selected.command_id == offered.command_id and
            selected.arguments == offered.arguments and
            selected.target == offered.target and
            selected.modality == 'direct' and offered.modality == 'direct'
        )

    @staticmethod
    def _binding(interaction, operation, answer_span, checked_preconditions, context):
        question_turn = next((value.turn for value in context.visible_recent_turns
                              if value.turn.turn_id == interaction.question_turn_id), None)
        if question_turn is None:
            return None
        question_value = next((value.final_reply for value in context.visible_recent_turns
                               if value.turn == question_turn), None)
        if question_value is None:
            return None
        try:
            interaction.validate_question(question_turn, question_value)
            binding = ConsentBinding(
                interaction_id=interaction.interaction_id,
                question_id=interaction.question_id,
                question_turn_id=interaction.question_turn_id,
                question_turn=question_turn,
                answering_turn=context.turn,
                answer_span=answer_span,
                operation=operation,
                checked_preconditions=checked_preconditions,
                precondition_fingerprint=interaction.precondition_fingerprint,
            )
            binding.validate_against(interaction,
                                     {context.current_message.text_id: context.current_message.text},
                                     expected_answer=answer_span.resolve({context.current_message.text_id: context.current_message.text}))
            return binding
        except ValueError:
            return None

    @staticmethod
    def _replace(interaction: PendingInteraction, status: str, reason: str | None) -> PendingInteraction:
        values = interaction.model_dump(mode='python')
        values.update(status=status, status_reason=reason, revision=interaction.revision + 1)
        return PendingInteraction.model_validate(values)
