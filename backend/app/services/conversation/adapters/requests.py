"""Adapt existing deterministic player-request rules to conversation contracts.

This parser proposes exact commands only. Ownership, eligibility, scoped consent
and atomic effects remain with the existing policies and transaction gateway.
"""
import hashlib
import json
import re
from app.services.conversation import contracts as c
from app.services.validation.items import requested_transfer, transfer_answer
from app.services.craftsman_intent import resolve_craftsman_intent


def request_operation(context):
    text = context.current_message.text
    # Generated modality labels cannot turn a quotation or hypothetical into intent.
    if re.search(r'["“”]|^\s*\'|\b(?:imagine|hypothetic\w*|suppose|pretend|(?:he|she|they|someone|somebody) said|if)\b', text, re.I):
        return None
    if re.search(r"\b(?:don't|do not|never)\b.*\b(?:give|share|take|receive)\b", text, re.I):
        return None
    caps = {cap.command_id: cap for cap in context.capabilities}
    command = None
    arguments = c.NoArguments()
    question = None
    transfer = requested_transfer(text)
    choices = [value for value in context.pending_interactions if value.kind == 'action_choice' and value.status == 'active']
    selected = None
    if len(choices) == 1 and not re.search(r"\b(?:not|never|don't)\b", text, re.I):
        words = set(re.findall(r'[a-z]+', text.lower()))
        matches = [offer for offer in choices[0].offered_operations
                   if isinstance(offer.arguments,c.ItemArguments) and offer.arguments.item in words
                   and (transfer is None or transfer == (offer.command_id,offer.arguments.item))]
        if len(matches) == 1:
            selected = matches[0]
            command = selected.command_id
            arguments = selected.arguments
            question = choices[0].question_id
    if selected is not None:
        pass
    elif transfer:
        command, item = transfer
        if item == 'bow' and re.search(r'\b(?:make|craft)\b', text, re.I):
            command = 'discuss_bow'
        else:
            arguments = c.ItemArguments(item=item)
    else:
        active = [value for value in context.pending_interactions
                  if value.kind == 'item_negotiation' and value.status == 'active']
        if len(active) == 1:
            pending = active[0]
            answer = transfer_answer(text, [pending.item], [], pending_item=pending.item)
            if answer and answer.action == 'give_item' and pending.authorized_operation:
                command = 'give_item'; arguments = c.ItemArguments(item=pending.item)
                question = pending.question_id
        if command is None and 'report_wreck' in caps:
            state = {'outing_active': False, 'inspection_complete': False,
                     'offer_pending': False, 'wreck_reported': False}
            for fact in context.visible_facts:
                if any(source.source_id == 'activity:ship_inspection' for source in fact.sources):
                    state.update(json.loads(fact.content))
            command = resolve_craftsman_intent(text, (), state).get('command')
    descriptor = caps.get(command)
    if descriptor is None or not descriptor.available or not descriptor.allowed_target_references:
        return None
    if isinstance(arguments, c.ItemArguments) and arguments.item not in descriptor.parameter_schema.allowed_items:
        return None
    return c.OperationCandidate(candidate_id=selected.candidate_id if selected else 'server:request',command_id=command,arguments=arguments,
        target=descriptor.allowed_target_references[0],
        source_spans=(c.TextSpan(text_id=context.current_message.text_id,start=0,end=len(text)),),
        modality='direct',pending_question_id=question)


def request_proposal(context):
    pending = context.pending_interactions
    cue = context.current_message.text.lower().strip(' .!?')
    if len(pending) == 1 and cue in {'cancel', 'never mind', 'nevermind', 'forget it', 'resume my request'}:
        action = 'resume' if cue == 'resume my request' else 'cancel'
        span = c.TextSpan(text_id=context.current_message.text_id,start=0,end=len(context.current_message.text))
        return c.TurnProposal(concerns=(),references=(),reports=(),correction_candidates=(),
            operation_candidates=(),interaction_links=(),canon_candidates=(),
            interaction_lifecycle_cues=(c.InteractionLifecycleCue(schema_version=1,cue_id='server:lifecycle',
                turn=context.turn,interaction_id=pending[0].interaction_id,action=action,
                modality='direct',source_span=span,source_text=context.current_message.text),),
            reply=(c.ExpressiveSegment(kind='expressive',segment_id='server:lifecycle-reply',
                text='All right, that request is cancelled.' if action=='cancel' else 'All right. Tell me why you need it.',
                addressed_concern_ids=()),))
    operation = request_operation(context)
    if operation is None:
        return None
    concerns = (); links = ()
    if operation.pending_question_id:
        concerns = (c.Concern(concern_id='server:purpose',kind='request',message_spans=operation.source_spans),)
        links = (c.InteractionLink(link_id='server:purpose-link',question_id=operation.pending_question_id,
            concern_id='server:purpose',source_spans=operation.source_spans),)
    return c.TurnProposal(concerns=concerns,references=(),reports=(),correction_candidates=(),
        operation_candidates=(operation,),interaction_links=links,canon_candidates=(),
        reply=(c.ExpressiveSegment(kind='expressive',segment_id='server:request-reply',
            text='All right.',addressed_concern_ids=()),))


def is_role_question(context):
    """Identify the narrow occupational question whose answer must stay conversational."""
    return bool(re.fullmatch(r'\s*what do you do\s*[?!.]*\s*',
                             context.current_message.text, re.I))


def guard_role_question_proposal(context, result):
    """Keep model-written speech while removing any operation guessed for a role question."""
    if not is_role_question(context) or not isinstance(result, c.Result) or result.error is not None:
        return result
    proposal = result.value
    if not isinstance(proposal, c.TurnProposal) or not proposal.operation_candidates:
        return result
    return c.Result.success(proposal.model_copy(update={
        'operation_candidates': (), 'interaction_links': (),
    }))


def item_negotiation(context, proposal, plan):
    operations = proposal.operation_candidates
    if len(operations) != 1 or plan.clarification is not None:
        return plan
    operation = operations[0]
    actual = request_operation(context)
    chosen = next((value for value in context.pending_interactions if value.kind == 'action_choice'
                   and value.question_id == operation.pending_question_id), None)
    if (operation.command_id != 'give_item' or (operation.pending_question_id is not None and chosen is None)
            or actual is None or actual.command_id != operation.command_id or actual.arguments != operation.arguments):
        return plan
    question_id = f'fallback:{context.turn.turn_id}'
    question = f'Before I give you the {operation.arguments.item}, why do you need it?'
    terms = operation.model_dump(mode='json')
    fingerprint = 'item:' + hashlib.sha256(json.dumps(terms,sort_keys=True).encode()).hexdigest()
    record = c.PendingInteraction(interaction_id=f'item:{context.turn.turn_id}',key=context.turn.key,
        kind='item_negotiation',originating_turn=context.turn,target=operation.target,
        item=operation.arguments.item,quantity=1,question_text=question,question_id=question_id,
        question_turn_id=context.turn.turn_id,required_response_kind='purpose',
        precondition_fingerprint=fingerprint,revision=0,status='active',status_reason=None,
        authorized_operation=operation.model_copy(update={'pending_question_id': question_id}))
    transitions = plan.transitions
    if chosen is not None:
        transitions = (*transitions,c.InteractionTransition(expected_revision=chosen.revision,
            replacement=chosen.model_copy(update={'status':'fulfilled','status_reason':'choice_selected',
                                                  'revision':chosen.revision+1})))
    return c.InteractionPlan(turn=context.turn,transitions=(*transitions,
        c.InteractionTransition(expected_revision=None,replacement=record)),consent_bindings=(),
        clarification=c.ClarificationRequired(kind='clarification_required',concern_ids=(),question=question))
