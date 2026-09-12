"""Deterministic P02 reference fake; no persistence or concurrency guarantee.

Snapshots isolate uncommitted values. A generation check rejects competing
commits conservatively; real adapters must implement their own atomic CAS.
"""

import hashlib
import json
from typing import Generic

from app.contracts import DomainError, ErrorCode, Identifier
from .read import IdSource, Result
from .write import (
    AggregateRevision, ChangeT, CommitReceipt, CommitRequest, DeliveryBatch,
    DeliveryCursor, DeliveryItem, EventT, RevisionKind, WriteIdentity,
    expected_aggregates,
)


def _error(code: ErrorCode, message: str) -> DomainError:
    return DomainError(code=code, stage="ports", retryable=code == ErrorCode.STALE_REVISION,
                       source_ids=(), public_message=message)


def request_digest(request: CommitRequest[ChangeT, EventT]) -> str:
    """Stable JSON encoding includes expected revisions, changes and all events."""
    serialized = json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class InMemoryUnitOfWork(Generic[ChangeT, EventT]):
    def __init__(self, ids: IdSource, initial_revisions: tuple[tuple[Identifier, AggregateRevision], ...] = ()):
        self._ids = ids
        self._revisions = {(timeline, item.kind, item.scope_id): item.revision for timeline, item in initial_revisions}
        if len(self._revisions) != len(initial_revisions):
            raise ValueError("duplicate initial revision")
        self._requests: dict[WriteIdentity, CommitRequest[ChangeT, EventT]] = {}
        self._receipts: dict[WriteIdentity, CommitReceipt] = {}
        self._delivery: dict[tuple[str, str], tuple[DeliveryItem[EventT], ...]] = {}
        self._event_ids: set[tuple[str, str]] = set()
        self._generation = 0

    @property
    def committed_requests(self) -> tuple[CommitRequest[ChangeT, EventT], ...]:
        return tuple(self._requests.values())

    def begin(self) -> "InMemoryTransaction[ChangeT, EventT]":
        return InMemoryTransaction(self)

    def poll(self, cursor: DeliveryCursor, limit: int) -> Result[DeliveryBatch[EventT]]:
        if type(limit) is not int or limit <= 0:
            return _error(ErrorCode.INVALID_CONTRACT, "Delivery limit must be positive.")
        items = self._delivery.get((cursor.timeline_id, cursor.consumer_id), ())
        if cursor.position > len(items):
            return _error(ErrorCode.INVALID_CONTRACT, "Delivery cursor is ahead of the stream.")
        selected = items[cursor.position:cursor.position + limit]
        next_cursor = DeliveryCursor(timeline_id=cursor.timeline_id, consumer_id=cursor.consumer_id,
                                     position=cursor.position + len(selected))
        return DeliveryBatch[EventT](start_cursor=cursor, next_cursor=next_cursor, items=selected)


class _ScopedWriter(Generic[ChangeT, EventT]):
    """Domain-facing writer deliberately has no public commit/rollback methods."""

    def __init__(self, transaction: "InMemoryTransaction[ChangeT, EventT]"):
        self._transaction = transaction

    def compare_and_commit(self, request: CommitRequest[ChangeT, EventT]) -> Result[CommitReceipt]:
        return self._transaction._stage(request)


class InMemoryTransaction(Generic[ChangeT, EventT]):
    def __init__(self, owner: InMemoryUnitOfWork[ChangeT, EventT]):
        self._owner = owner
        self._generation = owner._generation
        self._revisions = owner._revisions.copy()
        self._requests = owner._requests.copy()
        self._receipts = owner._receipts.copy()
        self._delivery = owner._delivery.copy()
        self._event_ids = owner._event_ids.copy()
        self._closed = False
        self._dirty = False
        self._writer = _ScopedWriter(self)

    @property
    def state_writer(self) -> _ScopedWriter[ChangeT, EventT]:
        return self._writer

    def _ensure_open(self):
        if self._closed:
            raise RuntimeError("transaction is closed")

    def _stage(self, request: CommitRequest[ChangeT, EventT]) -> Result[CommitReceipt]:
        self._ensure_open()
        digest = request_digest(request)
        prior = self._receipts.get(request.identity)
        if prior is not None:
            if prior.payload_digest == digest:
                return prior
            return _error(ErrorCode.IDEMPOTENCY_CONFLICT, "Operation identity was already used with different content.")
        expected = expected_aggregates(request.expected_revisions, request.npc_revision_basis)
        timeline = request.identity.timeline_id
        if any(self._revisions.get((timeline, item.kind, item.scope_id)) != item.revision for item in expected):
            return _error(ErrorCode.STALE_REVISION, "A relevant aggregate revision has changed or is absent.")
        event_keys = {(timeline, event.envelope.record_id) for event in request.events}
        if event_keys & self._event_ids:
            return _error(ErrorCode.IDEMPOTENCY_CONFLICT, "An event identity was already used by another operation.")
        receipt = CommitReceipt(identity=request.identity, receipt_id=self._owner._ids.new_id(),
                                payload_digest=digest, revisions_before=expected,
                                revision_advances=request.revision_advances,
                                event_ids=tuple(event.envelope.record_id for event in request.events))
        # Every rejection and validation happens before staged state changes.
        for item in request.revision_advances:
            self._revisions[timeline, item.kind, item.scope_id] = item.revision
        self._requests[request.identity] = request
        self._receipts[request.identity] = receipt
        self._event_ids.update(event_keys)
        for event in request.events:
            for consumer in event.consumers:
                key = (timeline, consumer)
                stream = self._delivery.get(key, ())
                self._delivery[key] = stream + (DeliveryItem[EventT](sequence=len(stream) + 1, event=event),)
        self._dirty = True
        return receipt

    def commit(self) -> Result[None]:
        self._ensure_open()
        if self._dirty and self._owner._generation != self._generation:
            self.rollback()
            return _error(ErrorCode.STALE_REVISION, "Another transaction committed first.")
        if self._dirty:
            self._owner._revisions = self._revisions
            self._owner._requests = self._requests
            self._owner._receipts = self._receipts
            self._owner._delivery = self._delivery
            self._owner._event_ids = self._event_ids
            self._owner._generation += 1
        self._closed = True
        return None

    def rollback(self) -> None:
        self._closed = True

    def __enter__(self) -> "InMemoryTransaction[ChangeT, EventT]":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if not self._closed:
            self.rollback()
