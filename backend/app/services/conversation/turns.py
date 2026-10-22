"""Conversation admission, ordered claims and durable recovery.

Callers supply validated immutable contract values. The store is the atomic
authority for active scope/NPC/epoch validation, request/payload deduplication,
sequence allocation and durable enqueue. A separate scope check or an in-memory
queue here would race that authority.
"""
from .contracts import (
    AssembledReply, ConversationError, ConversationKey, LeasePolicy, OptionalResult,
    ProviderAttempt, RecoveredReply, TurnLease, TurnRecovery, TurnRef, TurnStatus, TurnSubmission,
)
from .ports import ClockPort, TurnStore


class TurnService:
    """Expose the turn lifecycle through one injected durable store boundary.

    Expected store failures retain their typed retry guidance and known turn ref.
    The infrastructure adapter owns exception mapping and transaction recovery;
    this service never retries writes, dispatches generation or executes actions.
    """

    def __init__(self, store: TurnStore, *, clock: ClockPort | None = None):
        self._store = store
        self._clock = clock

    def submit(self, submission: TurnSubmission) -> TurnStatus | ConversationError:
        """Atomically validate and admit, or replay the existing scoped identity."""
        return self._store.submit(submission)

    def lookup(self, key: ConversationKey, request_id: str) -> TurnStatus | ConversationError:
        """Read pending/final/invalidated status without admission or generation."""
        return self._store.lookup(key, request_id)

    def claim_next(
        self, key: ConversationKey, worker_id: str, lease_policy: LeasePolicy,
    ) -> OptionalResult[TurnLease]:
        """Claim once through the store; busy never permits a later-turn claim.

        The key/worker check rejects a mismatched returned lease. An injected
        clock also checks its interval. Only the atomic store may establish
        authoritative expiry, earliest position and a current fence;
        every later write must still recheck them there, even after this check.
        """
        result = self._store.claim_next(key, worker_id, lease_policy)
        if result.error is not None or result.value is None:
            return result
        lease = result.value
        try:
            if lease.turn.key != key or lease.worker_id != worker_id:
                raise ValueError('lease belongs to another key or worker')
            if self._clock is not None:
                lease.validate_current(key=key, fence=lease.fence,
                    sequence=lease.turn.sequence, now=self._clock.utc_now())
        except ValueError:
            return OptionalResult.failure(ConversationError(code='LEASE_LOST', stage='claim',
                retryable=True, turn=lease.turn, safe_detail='Claimed ownership is no longer usable.'))
        return result

    def pending(self, key: ConversationKey) -> tuple[TurnStatus, ...] | ConversationError:
        """Scan durable pending work without scheduling or changing its phase."""
        return self._store.pending(key)

    def pending_keys(self) -> tuple[ConversationKey, ...] | ConversationError:
        """Enumerate active stream keys for process restart recovery."""
        scan = getattr(self._store, 'pending_keys', None)
        if not callable(scan):
            return ConversationError(code='STORAGE_UNAVAILABLE', stage='pending_scan',
                retryable=True, turn=None, safe_detail='Durable restart scan is unavailable.')
        return scan()

    def recover(self, turn: TurnRef) -> TurnRecovery | ConversationError:
        """Observe phase, budgets, output, assembly and receipt without authority.

        Inspect the receipt before considering an operation. Persisted outputs
        retain historical fences; absent output after dispatch leaves its budget
        consumed. The coordinator chooses safe recovery and rechecks publication.
        """
        return self._store.recover(turn)

    def record_attempt(
        self, turn: TurnRef, fence: int, attempt: ProviderAttempt,
    ) -> ProviderAttempt | ConversationError:
        """Commit attempt/repair consumption before any external dispatch.

        A returned identity replay is the same consumed attempt, not permission
        to dispatch again. Errors leave work pending; never dispatch on failure.
        """
        return self._store.record_attempt(turn, fence, attempt)

    def save_attempt_output(
        self, turn: TurnRef, fence: int, attempt: ProviderAttempt,
    ) -> ProviderAttempt | ConversationError:
        """Save recorded output under the current fence, outside accepted history."""
        return self._store.save_attempt_output(turn, fence, attempt)

    def save_reply(
        self, turn: TurnRef, fence: int, reply: AssembledReply,
    ) -> RecoveredReply | ConversationError:
        """Save recoverable draft assembly; this does not publish dialogue."""
        return self._store.save_reply(turn, fence, reply)
