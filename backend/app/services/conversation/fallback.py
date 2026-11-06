"""Pure, receipt-first fallback reply rendering and publication checks."""
from app.services.conversation import contracts as c
from app.services.conversation.composition import AssemblyEvidence, _beats, _receipt_text
from app.services.conversation.validation import ResponseValidator


class FallbackPolicy:
    """Render a safe deterministic response when ordinary composition fails."""

    def __init__(self, policy: c.ConversationPolicy, validator: ResponseValidator | None = None):
        if not isinstance(policy, c.ConversationPolicy):
            raise TypeError('fallback requires the configured conversation policy')
        if validator is not None and not isinstance(validator, ResponseValidator):
            raise TypeError('fallback validator must be a ResponseValidator')
        self._policy = policy
        self._validator = validator or ResponseValidator()

    _OUTAGE_SPEECH = {
        1: "The workshop's gone quiet for a moment. Ask me again shortly.",
        2: "I need a moment to listen to the trail. Ask me again shortly.",
    }
    _DEFAULT_OUTAGE = "I need a moment. Please ask me again shortly."

    def render(self, context: c.ContextPacket, decision: c.OperationDecision | None,
               receipt: c.OperationReceipt | None,
               failure: c.ConversationError | None) -> c.Result[c.AssembledReply]:
        """Build an exact assembled reply without providers or side effects."""
        if context.policy_versions.get('bounds') != self._policy.policy_version:
            return c.Result.failure(c.ConversationError(code='EVIDENCE_CHANGED',
                stage='conversation.fallback', retryable=False, turn=context.turn,
                safe_detail='The fallback policy version changed.'))
        dependencies: tuple[c.SourceRef, ...] = ()
        if receipt is not None:
            key = context.turn.key
            if (receipt.turn_id, receipt.game_scope, receipt.npc_id) != (
                    context.turn.turn_id, key.game_scope, key.npc_id):
                return c.Result.failure(c.ConversationError(code='EVIDENCE_CHANGED',
                    stage='conversation.fallback', retryable=False, turn=context.turn,
                    safe_detail='The committed receipt does not belong to this turn.'))
            try:
                text = _receipt_text(receipt)
            except Exception:
                return c.Result.failure(c.ConversationError(code='EVIDENCE_CHANGED',
                    stage='conversation.fallback', retryable=False, turn=context.turn,
                    safe_detail='The mandatory committed outcome could not be rendered safely.'))
            dependencies = (c.SourceRef(kind='operation_receipt', source_id=receipt.receipt_id,
                revision=receipt.argument_digest, game_scope=key.game_scope, npc_id=key.npc_id,
                attribution='server', visibility='npc_private'),)
        elif isinstance(decision, c.ClarificationRequired):
            text = decision.question
        elif isinstance(decision, c.Denied):
            text = decision.safe_explanation
        else:
            text = self._OUTAGE_SPEECH.get(context.turn.key.npc_id, self._DEFAULT_OUTAGE)

        if len(text) > self._policy.output_char_limit:
            return c.Result.failure(c.ConversationError(code='INVALID_BOUNDS',
                stage='conversation.fallback', retryable=False, turn=context.turn,
                safe_detail='The complete fallback exceeds the configured output limit.'))
        beats = _beats(text, self._policy.beat_char_limit)
        if beats is None:
            return c.Result.failure(c.ConversationError(code='INVALID_BOUNDS',
                stage='conversation.fallback', retryable=False, turn=context.turn,
                safe_detail='The complete fallback cannot fit configured dialogue beats.'))

        text_id = f'fallback:{context.turn.turn_id}'
        reply = c.AssembledReply(text_id=text_id, final_text=text, beats=beats,
            response_origin='fallback',
            degradation_reason=(failure.code if isinstance(failure, c.ConversationError) else 'SAFE_FALLBACK'),
            segment_spans={'fallback': c.TextSpan(text_id=text_id, start=0, end=len(text))},
            evidence_dependencies=dependencies, candidate_continuity_changes=())
        receipt_sources = dependencies
        try:
            current_evidence = AssemblyEvidence(turn=context.turn, text_id=text_id,
                facts=(*context.character_profile, *context.active_canon, *context.reports,
                       *context.interpretations, *context.visible_facts),
                receipts=(receipt,) if receipt is not None else (), revisions=context.revisions,
                resource_sources=(), receipt_sources=receipt_sources)
            report = self._validator.check(reply, context, current_evidence)
        except Exception:
            return c.Result.failure(c.ConversationError(code='INTERNAL_FAILURE',
                stage='conversation.fallback', retryable=False, turn=context.turn,
                safe_detail='Fallback validation could not be completed safely.'))
        if report.findings:
            codes = ', '.join(sorted({finding.code for finding in report.findings}))
            return c.Result.failure(c.ConversationError(code='INVALID_SCHEMA',
                stage='conversation.fallback', retryable=False, turn=context.turn,
                safe_detail=f'Fallback reply failed response validation ({codes}).'))
        return c.Result.success(reply)
