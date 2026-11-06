"""Narrow in-process boundaries for conversation orchestration.

These protocols describe detached contract values only. Adapters own database,
provider and authoritative game-service details behind these boundaries.
"""
from datetime import datetime
from typing import Literal, Mapping, Protocol, runtime_checkable

from app.services.conversation.contracts import (
    AssembledReply,
    CandidateReply,
    CapabilityDescriptor,
    ClearResult,
    ContinuityPlan,
    ConversationError,
    ConversationKey,
    ContextPacket,
    Deadline,
    FinalTurnResult,
    LeasePolicy,
    MemoryRecord,
    OperationReceipt,
    OptionalResult,
    ProviderAttempt,
    ReadyToRecheck,
    RecoveredReply,
    SourceRange,
    SummaryRecord,
    TurnLease,
    TurnProposal,
    TurnRef,
    TurnRecovery,
    TurnStatus,
    TurnSubmission,
    VisibleFact,
    VisibleTurn,
    WorldResult,
)


Visibility = Literal['public', 'npc_private']
GenerationPurpose = Literal['proposal', 'composition', 'repair']
GenerationResult = TurnProposal | CandidateReply | AssembledReply
TraceValue = str | int | float | bool | None


@runtime_checkable
class WorldReadPort(Protocol):
    """Read detached, visibility-filtered mechanical/event facts."""

    def read_facts(
        self,
        game_scope: str,
        npc_id: int,
        epoch: int,
        visibility: Visibility,
    ) -> tuple[VisibleFact, ...]: ...


@runtime_checkable
class ContextReadPort(Protocol):
    """Assemble finalized prior turns and visible evidence for one explicit scope."""

    def read_context(
        self,
        turn: TurnRef,
        game_scope: str,
        visibility: Visibility,
    ) -> ContextPacket: ...


@runtime_checkable
class MemoryReadPort(Protocol):
    """Read scoped, attributed continuity values; never raw rejected drafts."""

    def read_memories(
        self,
        game_scope: str,
        npc_id: int,
        epoch: int,
        visibility: Visibility,
    ) -> tuple[MemoryRecord, ...]: ...


@runtime_checkable
class CapabilityReadPort(Protocol):
    """Return safe public capability descriptors, never authorization evidence."""

    def read_capabilities(
        self,
        game_scope: str,
        npc_id: int,
        visibility: Visibility,
    ) -> tuple[CapabilityDescriptor, ...]: ...


@runtime_checkable
class GenerationPort(Protocol):
    """Generate a typed candidate within the deadline and dialogue code-point limit."""

    def generate(
        self,
        purpose: GenerationPurpose,
        context: ContextPacket,
        deadline: Deadline,
        dialogue_codepoint_limit: int,
    ) -> GenerationResult: ...


@runtime_checkable
class ClockPort(Protocol):
    """Expose process-local monotonic time and UTC wall time for detached stamps."""

    def monotonic(self) -> float: ...

    def utc_now(self) -> datetime: ...


@runtime_checkable
class TracePort(Protocol):
    """Best-effort structured stage trace using detached scalar attributes."""

    def record(
        self,
        turn: TurnRef | None,
        stage: str,
        values: Mapping[str, TraceValue],
    ) -> None: ...


# T02 uses the immutable application envelopes frozen in contracts/T04.
@runtime_checkable
class TurnStore(Protocol):
    """Atomic scoped admission and read-only retry lookup.

    Admission compares the active scope/epoch, uniquely binds request ID to its
    payload digest, and allocates a unique sequence before work is scheduled.
    Same ID/payload replays its status; changed payload conflicts. Lookup never
    admits work, generates speech or executes an operation. Cleared identities
    return invalidated tombstones without recovering erased text or drafts.
    """

    def submit(self, submission: TurnSubmission) -> TurnStatus | ConversationError: ...

    def lookup(self, key: ConversationKey, request_id: str) -> TurnStatus | ConversationError: ...

    def claim_next(
        self, key: ConversationKey, worker_id: str, lease_policy: LeasePolicy,
    ) -> OptionalResult[TurnLease]:
        """Claim only the oldest nonterminal turn, advancing its durable fence.

        Busy/empty is successful None, never permission to bypass an earlier
        turn. Release all locks before returning. Replacement retains consumed
        attempts, outputs, phase and any receipt; time never expires consent.
        """
        ...

    def pending(self, key: ConversationKey) -> tuple[TurnStatus, ...] | ConversationError:
        """Read the scoped durable pending queue in sequence order, without work."""
        ...

    def recover(self, turn: TurnRef) -> TurnRecovery | ConversationError:
        """Read a previously claimed turn, its budgets, output and receipt.

        This observation grants no write authority. Historical fences remain on
        stored outputs after replacement. Cleared tombstones expose no erased
        conversational payload; a different active scope cannot recover it.
        """
        ...

    def record_attempt(
        self, turn: TurnRef, fence: int, attempt: ProviderAttempt,
    ) -> ProviderAttempt | ConversationError:
        """Atomically consume a stage before provider dispatch, under the fence.

        Uniquely bind attempt ID and one attempt per purpose to the turn. The
        repair purpose consumes one shared token across proposal_format and
        final_response. Exact identity replay cannot consume twice; a new fence
        cannot reset consumed stages. Commit before making any provider call.
        """
        ...

    def save_attempt_output(
        self, turn: TurnRef, fence: int, attempt: ProviderAttempt,
    ) -> ProviderAttempt | ConversationError:
        """Persist typed output only for its recorded dispatch and current fence.

        Preserve attempt identity, purpose/repair kind and original fence. Output
        is immutable on replay and isolated from accepted conversation history.
        A lost output leaves the consumed dispatch durable for safe recovery.
        """
        ...

    def save_reply(
        self, turn: TurnRef, fence: int, reply: AssembledReply,
    ) -> RecoveredReply | ConversationError:
        """Persist scoped recoverable assembly under the current write fence.

        This is draft recovery data, never publication. Clear/reset removes it;
        recovered historical assembly still requires full finalization recheck.
        """
        ...


@runtime_checkable
class OperationGateway(Protocol):
    """One fenced authoritative operation and immutable receipt per turn.

    In one short writer transaction, check active scope/epoch, current fence and
    earliest nonterminal stream position; recover an existing receipt before
    considering execution. Otherwise recheck deterministic authority, exact
    terms and consent, and atomically commit effects, receipt and resolved phase.
    A typed rejection records no effect; infrastructure failure rolls back all
    writes. Clear preserves committed receipts but prohibits old-epoch writes.
    No provider call or shared ORM session crosses this boundary.
    """

    def execute_once(
        self,
        turn: TurnRef,
        fence: int,
        decision: ReadyToRecheck,
    ) -> OperationReceipt | ConversationError: ...

    def lookup_receipt(self, turn: TurnRef) -> OptionalResult[OperationReceipt]:
        """Read only the exact scoped turn receipt, including after chat clear.

        Successful None means no committed receipt was found. An uncertain
        commit must be resolved here before considering execution again. A new
        game's active scope cannot recover an old run's receipt.
        """
        ...


@runtime_checkable
class FinalizationStore(Protocol):
    """Sole atomic publisher of accepted speech and conversational continuity.

    Recheck scope/epoch/fence/oldest position, actual canon/interaction/memory
    CAS heads and every exact speech dependency inside the writer transaction.
    Unrelated revision churn is harmless. Never overwrite operation-committed
    negotiation state. Publish transcript, canon lineage, attributed memories,
    interaction transitions, immutable final result and terminal status together,
    or none. Provider/reassembly work occurs after releasing the transaction.
    """

    def commit(
        self, turn: TurnRef, fence: int, reply: AssembledReply,
        continuity_plan: ContinuityPlan,
    ) -> FinalTurnResult | ConversationError: ...


@runtime_checkable
class LifecycleStore(Protocol):
    """Atomic lifecycle boundaries serialized with authoritative game writes."""

    def clear(self, key: ConversationKey) -> ClearResult | ConversationError:
        """CAS the expected key, advance epoch and invalidate every old turn.

        Delete transcript/results/drafts/attempt outputs/summaries/reports/
        interpretations/negotiations. Retain only minimal digest/identity/status
        tombstones, canon origin metadata, authored identity, relationships,
        encounters and committed mechanics/receipts. Late writes fail.
        """
        ...

    def new_game(self, expected_scope: str) -> WorldResult | ConversationError:
        """CAS active scope, replace it and reset run-scoped state and canon.

        Invalidate old queued/active/async work under the common writer boundary.
        Historical audit receipts cannot enter new-run recovery or gameplay.
        """
        ...


@runtime_checkable
class SummaryStore(Protocol):
    """Recoverable summary scheduling and revision-checked detached publication.

    Summary generation runs outside transactions and the mandatory turn path.
    Finalization/source corrections durably mark keys dirty; missed in-process
    notifications cannot lose refresh work. A failed refresh retains the prior
    valid record or permits scoped unsummarized retrieval.
    """

    def dirty_keys(self, game_scope: str) -> tuple[ConversationKey, ...] | ConversationError: ...

    def read_sources(
        self, key: ConversationKey, source_range: SourceRange,
    ) -> tuple[VisibleTurn, ...] | ConversationError: ...

    def lookup_summary(self, key: ConversationKey) -> OptionalResult[SummaryRecord]: ...

    def publish(
        self, summary: SummaryRecord, expected_revision: int | None,
    ) -> SummaryRecord | ConversationError:
        """Atomically CAS the summary head and recheck key/source/correction heads.

        None expects absence; otherwise advance the supplied head by one. Verify
        finalized source identity/range and source revisions in this transaction.
        Clear/reset or stale source/canon/correction heads reject publication;
        success clears the durable dirty marker for those checked revisions.
        """
        ...
