"""Prevalidated publication and bounded refresh outside the writer boundary.

The injected store owns authoritative rechecks and atomic publication. This
module cannot establish current ownership from detached observations or grant
mechanical authority. Receipt commit/recovery precedes this boundary; refreshing
speech never executes or changes the operation that produced its receipt.
"""
from typing import Protocol

from .contracts import (
    AssembledReply, ContinuityPlan, ConversationError, FinalTurnResult, TurnRef,
)
from .ports import FinalizationStore


class PublicationRefresh(Protocol):
    """Refresh evidence, reassemble and validate a replacement outside locks.

    The coordinator supplies this hook with its remaining deadline and already
    consumed generation/repair budgets. A hook may use grounded fallback instead
    of generation, and returns a typed failure when the budget cannot support
    another validated plan. Return both values together: an old continuity plan
    must not silently accompany changed final speech. No operation execution is
    permitted here. No callback is passed into the store transaction.
    """

    def __call__(
        self, turn: TurnRef, reply: AssembledReply,
        continuity_plan: ContinuityPlan, conflict: ConversationError,
    ) -> tuple[AssembledReply, ContinuityPlan] | ConversationError: ...


class Finalizer:
    """Submit accepted plans to the sole atomic publication port.

    The store must recheck active key, fence, oldest stream position, exact
    speech dependencies and canon/interaction/memory heads on every attempt.
    Relevant changes return EVIDENCE_CHANGED after releasing its transaction.
    Unrelated changes require no refresh. Storage/uncertain-commit and ownership
    failures remain lookup/recovery concerns and never dispatch regeneration.
    """

    def __init__(
        self, store: FinalizationStore, *, refresh: PublicationRefresh | None = None,
        max_refreshes: int = 1,
    ):
        if type(max_refreshes) is not int or max_refreshes < 0:
            raise ValueError('max_refreshes must be a nonnegative integer')
        self._store = store
        self._refresh = refresh
        self._max_refreshes = max_refreshes

    def commit(
        self, turn: TurnRef, fence: int, reply: AssembledReply,
        continuity_plan: ContinuityPlan,
    ) -> FinalTurnResult | ConversationError:
        """Recheck each replacement and return the durable result or safe error.

        A successful local precheck is never write authorization. In particular,
        reply dependencies are passed intact even if expected_revisions is
        empty; the store must resolve each exact reference independently.
        """
        remaining = self._max_refreshes
        while True:
            invalid = self._precheck(turn, fence, reply, continuity_plan)
            if invalid is not None:
                return invalid
            result = self._store.commit(turn, fence, reply, continuity_plan)
            if (not isinstance(result, ConversationError) or
                    result.code != 'EVIDENCE_CHANGED' or not result.retryable or
                    self._refresh is None or remaining == 0):
                return result
            # commit has returned; the store contract releases all locks before
            # this point. Provider/semantic work belongs only to the caller hook.
            remaining -= 1
            refreshed = self._refresh(turn, reply, continuity_plan, result)
            if isinstance(refreshed, ConversationError):
                return refreshed
            reply, continuity_plan = refreshed

    @staticmethod
    def _precheck(
        turn: TurnRef, fence: int, reply: AssembledReply,
        continuity_plan: ContinuityPlan,
    ) -> ConversationError | None:
        try:
            if (not isinstance(turn, TurnRef) or type(fence) is not int or fence <= 0 or
                    not isinstance(reply, AssembledReply) or
                    not isinstance(continuity_plan, ContinuityPlan) or continuity_plan.turn != turn):
                raise ValueError('publication identity or plan is invalid')
            continuity_plan.validate_reply(reply)
            if any(source.game_scope != turn.key.game_scope or
                   source.npc_id not in {None, turn.key.npc_id} or
                   source.visibility == 'server_private'
                   for source in reply.evidence_dependencies):
                raise ValueError('speech dependency is outside visible conversation scope')
        except ValueError:
            return ConversationError(code='INVALID_INPUT', stage='publication', retryable=False,
                turn=turn if isinstance(turn, TurnRef) else None,
                safe_detail='Publication requires an accepted reply and a matching continuity plan.')
        return None
