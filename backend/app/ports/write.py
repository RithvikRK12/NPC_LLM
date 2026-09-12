"""P02 application-owned short transactions and durable delivery contracts.

compare_and_commit stages a CAS-checked write in its enclosing transaction;
only Transaction.commit makes state, receipt and delivery intents visible.
No nested domain service receives the transaction owner. Transactions must not
span model generation, movement or other long-running external work.
"""

from enum import Enum
from typing import Generic, Protocol, TypeVar, runtime_checkable
from types import TracebackType

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, Identifier, Revision, RevisionSet
from .read import Result

ChangeT = TypeVar("ChangeT", bound=ContractValue)
EventT = TypeVar("EventT", bound=ContractValue)


class RevisionKind(str, Enum):
    NPC = "npc"
    QUEST = "quest"
    INVENTORY = "inventory"
    RELATIONSHIP = "relationship"
    POLICY = "policy"
    CONTROLLER = "controller"


class NpcRevisionBasis(str, Enum):
    BASE = "base"
    APPROVED = "approved"


class AggregateRevision(ContractValue):
    kind: RevisionKind
    scope_id: Identifier
    revision: Revision


class WriteIdentity(ContractValue):
    timeline_id: Identifier
    actor_id: Identifier
    operation_id: Identifier


class DurableEvent(ContractValue, Generic[EventT]):
    envelope: ContractEnvelope
    payload: EventT
    consumers: tuple[Identifier, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_consumers(self):
        if len(set(self.consumers)) != len(self.consumers):
            raise ValueError("consumers must be unique")
        return self


class CommitRequest(ContractValue, Generic[ChangeT, EventT]):
    """Immutable application-approved write, not an authorization decision.

    Revisions are compared only for the declared dependency set. Advances are
    explicit to avoid incrementing read-only dependencies (e.g. policy).
    The adapter computes the canonical payload digest from this whole request;
    caller-supplied digests must not bypass changed-content detection.
    """

    identity: WriteIdentity
    expected_revisions: RevisionSet
    npc_revision_basis: NpcRevisionBasis
    approved_changes: ChangeT
    revision_advances: tuple[AggregateRevision, ...]
    events: tuple[DurableEvent[EventT], ...]

    @model_validator(mode="after")
    def coherent_write(self):
        expected = expected_aggregates(self.expected_revisions, self.npc_revision_basis)
        before = {(item.kind, item.scope_id): item.revision for item in expected}
        seen = set()
        for item in self.revision_advances:
            key = (item.kind, item.scope_id)
            if key in seen or key not in before or item.revision != before[key] + 1:
                raise ValueError("each advance must increment one unique expected aggregate by one")
            seen.add(key)
        ids = [event.envelope.record_id for event in self.events]
        if len(set(ids)) != len(ids):
            raise ValueError("event IDs must be unique within a write")
        if any(event.envelope.timeline_id != self.identity.timeline_id for event in self.events):
            raise ValueError("event timeline must match write timeline")
        return self


def expected_aggregates(revisions: RevisionSet, basis: NpcRevisionBasis) -> tuple[AggregateRevision, ...]:
    revision = revisions.base_npc_state_revision
    if basis == NpcRevisionBasis.APPROVED:
        if revisions.approved_npc_state_revision is None:
            raise ValueError("approved revision basis requires an approved NPC revision")
        revision = revisions.approved_npc_state_revision
    values = [AggregateRevision(kind=RevisionKind.NPC, scope_id=revisions.npc_id, revision=revision)]
    for kind in RevisionKind:
        if kind != RevisionKind.NPC:
            values.extend(AggregateRevision(kind=kind, scope_id=item.scope_id, revision=item.revision)
                          for item in getattr(revisions, kind.value))
    return tuple(values)


class CommitReceipt(ContractValue):
    identity: WriteIdentity
    receipt_id: Identifier
    payload_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    revisions_before: tuple[AggregateRevision, ...]
    revision_advances: tuple[AggregateRevision, ...]
    event_ids: tuple[Identifier, ...]


class DeliveryCursor(ContractValue):
    timeline_id: Identifier
    consumer_id: Identifier
    position: Revision


class DeliveryItem(ContractValue, Generic[EventT]):
    sequence: int = Field(strict=True, gt=0)
    event: DurableEvent[EventT]


class DeliveryBatch(ContractValue, Generic[EventT]):
    start_cursor: DeliveryCursor
    next_cursor: DeliveryCursor
    items: tuple[DeliveryItem[EventT], ...]

    @model_validator(mode="after")
    def contiguous_scope(self):
        start, end = self.start_cursor, self.next_cursor
        if (start.timeline_id, start.consumer_id) != (end.timeline_id, end.consumer_id):
            raise ValueError("cursor scope cannot change")
        if end.position != start.position + len(self.items):
            raise ValueError("cursor must advance exactly over returned items")
        for sequence, item in enumerate(self.items, start.position + 1):
            if item.sequence != sequence:
                raise ValueError("delivery sequence cannot skip or reorder")
            if item.event.envelope.timeline_id != start.timeline_id or start.consumer_id not in item.event.consumers:
                raise ValueError("event must belong to cursor scope")
        return self


@runtime_checkable
class StateWriter(Protocol[ChangeT, EventT]):
    """Exact retries return the original receipt before CAS evaluation.

    Same identity with changed request -> IDEMPOTENCY_CONFLICT; mismatching
    relevant revisions -> STALE_REVISION. Failures stage no partial effects.
    """

    def compare_and_commit(self, request: CommitRequest[ChangeT, EventT]) -> Result[CommitReceipt]: ...


@runtime_checkable
class DeliveryStore(Protocol[EventT]):
    """Read committed intents without consuming/acknowledging them.

    Polling the same cursor retries the same ordered prefix. Start at position
    zero; advance only to a returned next_cursor after consumer processing.
    Invalid/future cursors -> INVALID_CONTRACT, never silently skip records.
    """

    def poll(self, cursor: DeliveryCursor, limit: int) -> Result[DeliveryBatch[EventT]]: ...


@runtime_checkable
class Transaction(Protocol[ChangeT, EventT]):
    @property
    def state_writer(self) -> StateWriter[ChangeT, EventT]: ...

    def commit(self) -> Result[None]: ...

    def rollback(self) -> None: ...

    def __enter__(self) -> "Transaction[ChangeT, EventT]": ...

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None,
                 traceback: TracebackType | None) -> None:
        """Rollback unless explicitly committed; never swallow exceptions."""
        ...


@runtime_checkable
class UnitOfWork(Protocol[ChangeT, EventT]):
    def begin(self) -> Transaction[ChangeT, EventT]: ...
