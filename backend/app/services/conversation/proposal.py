"""Validate one detached proposal-stage output against its accepted context.

Provider and prompt adaptation live behind GenerationPort. This boundary owns
only strict contract revalidation and references to the exact ContextPacket;
it never interprets consent, persists state, or authorizes mechanics.
"""
from collections.abc import Mapping

from pydantic import ValidationError

from app.services.conversation import contracts as c
from app.services.conversation.ports import GenerationPort
from app.services.conversation.generation_errors import (
    GenerationCancelled,
    GenerationMalformed,
    GenerationUnavailable,
    GenerationVersionUnsupported,
)


class ProposalService:
    """Make one proposal call and validate its typed result fail-closed."""

    def __init__(self, generation: GenerationPort, policy: c.ConversationPolicy):
        self._generation = generation
        self._policy = policy

    def propose(self, context: c.ContextPacket, deadline: c.Deadline) -> c.Result[c.TurnProposal]:
        if deadline.expired():
            return _failure(context, 'DEADLINE_EXCEEDED', 'The proposal deadline elapsed.')
        stage_deadline = deadline.child(self._policy.provider_stage_budget_seconds)
        if stage_deadline.expired():
            return _failure(context, 'DEADLINE_EXCEEDED', 'The proposal deadline elapsed.')
        try:
            output = self._generation.generate('proposal', context, stage_deadline,
                                               self._policy.output_char_limit)
        except TimeoutError:
            return _failure(context, 'PROVIDER_TIMEOUT', 'The proposal generation timed out.')
        except GenerationUnavailable:
            return _failure(context, 'PROVIDER_UNAVAILABLE',
                            'The proposal provider is unavailable.', retryable=True)
        except GenerationCancelled:
            return _failure(context, 'INTERNAL_FAILURE',
                            'The proposal generation was cancelled.',
                            stage='proposal.cancelled', retryable=True)
        except GenerationVersionUnsupported:
            return _failure(context, 'PROVIDER_INVALID_OUTPUT',
                            'The proposal provider contract version is unsupported.',
                            stage='proposal.provider_version')
        except GenerationMalformed:
            return _failure(context, 'PROVIDER_INVALID_OUTPUT',
                            'The proposal provider response is malformed.',
                            stage='proposal.provider_output')
        if stage_deadline.expired():
            return _failure(context, 'PROVIDER_TIMEOUT', 'The proposal generation timed out.')

        try:
            # Round-trip through the strict contract to validate even objects
            # created with Pydantic's trusted model_construct/model_copy APIs.
            if not isinstance(output, c.TurnProposal):
                raise ValueError('provider output is not a TurnProposal')
            proposal = c.TurnProposal.model_validate(output.model_dump(mode='python'), strict=True)
            _validate_context_references(proposal, context)
        except (ValidationError, ValueError, TypeError, KeyError):
            return _failure(context, 'PROVIDER_INVALID_OUTPUT',
                            'The proposal has unsupported shape or references.')
        return c.Result[c.TurnProposal].success(proposal)


def _validate_context_references(proposal: c.TurnProposal, context: c.ContextPacket) -> None:
    texts = _context_texts(context)
    proposal.validate_references(texts, context=context)

    capabilities = {value.command_id: value for value in context.capabilities}
    allowed_targets = {
        target.reference_id: target
        for capability in context.capabilities
        for target in capability.allowed_target_references
    }
    for pending in context.pending_interactions:
        allowed_targets[pending.target.reference_id] = pending.target
        for offered in pending.offered_operations:
            allowed_targets[offered.target.reference_id] = offered.target

    known_questions = {value.question_id for value in context.pending_interactions}
    known_reference_ids = set(allowed_targets)
    known_topics = {value.evidence_id for value in context.active_canon}
    for reference in proposal.references:
        if isinstance(reference, c.ResolvedEntityReference):
            target = allowed_targets.get(reference.reference.reference_id)
            if target != reference.reference:
                raise ValueError('resolved entity reference is absent from current context')
            known_reference_ids.add(reference.reference.reference_id)
        elif isinstance(reference, c.ResolvedTopicReference):
            if reference.topic_id not in known_topics:
                raise ValueError('resolved topic is absent from current canon')
            known_reference_ids.add(reference.reference_id)

    for correction in proposal.correction_candidates:
        if correction.target_reference_id not in known_reference_ids:
            raise ValueError('correction targets an unknown reference')

    for link in proposal.interaction_links:
        if link.question_id not in known_questions:
            raise ValueError('interaction link points to an unknown question')

    for operation in proposal.operation_candidates:
        capability = capabilities.get(operation.command_id)
        if capability is None or not capability.available:
            raise ValueError('operation command is not currently available')
        if operation.target not in capability.allowed_target_references:
            raise ValueError('operation target is not currently allowed')
        if operation.pending_question_id is not None and operation.pending_question_id not in known_questions:
            raise ValueError('operation points to an unknown pending question')
        schema = capability.parameter_schema
        if isinstance(schema, c.NoParameterSchema):
            if not isinstance(operation.arguments, c.NoArguments):
                raise ValueError('operation arguments do not match capability schema')
        elif isinstance(operation.arguments, c.ItemArguments):
            if operation.arguments.item not in schema.allowed_items:
                raise ValueError('operation item is outside capability bounds')
        else:
            raise ValueError('operation arguments do not match capability schema')


def _context_texts(context: c.ContextPacket) -> Mapping[str, str]:
    texts: dict[str, str] = {}

    def bind(text_id: str, value: str) -> None:
        prior = texts.setdefault(text_id, value)
        if prior != value:
            raise ValueError('one context text ID resolves to conflicting content')

    bind(context.current_message.text_id, context.current_message.text)
    for turn in context.visible_recent_turns:
        bind(turn.player_message.text_id, turn.player_message.text)
        bind(turn.final_reply.text_id, turn.final_reply.text)
    for pending in context.pending_interactions:
        bind(pending.question_id, pending.question_text)
    return texts


def _failure(context: c.ContextPacket, code: c.ConversationErrorCode,
             detail: str, *, stage: str = 'proposal.propose',
             retryable: bool = False) -> c.Result[c.TurnProposal]:
    return c.Result[c.TurnProposal].failure(c.ConversationError(
        code=code, stage=stage, retryable=retryable, turn=context.turn,
        safe_detail=detail))
