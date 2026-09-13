"""Reusable write-port conformance checks for P03.

Production adapters can satisfy this suite by subclassing
WritePortConformanceMixin with unittest.TestCase and implementing factory().
The factory must return a fresh adapter seeded with the same fixture revisions
for every test method.
"""

import json
from pathlib import Path

from pydantic import ValidationError

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, RevisionSet, ScopedRevision
from app.ports import (
    AggregateRevision, CommitReceipt, CommitRequest, DeliveryBatch, DeliveryCursor,
    DeliveryStore, DurableEvent, NpcRevisionBasis, StateWriter, Transaction,
    UnitOfWork, WriteIdentity,
)


class Change(ContractValue):
    value: int


class Event(ContractValue):
    text: str


class Ids:
    def __init__(self):
        self.next = 0

    def new_id(self):
        self.next += 1
        return f"receipt:{self.next}"


class WritePortFixture:
    event_type = Event

    def __init__(self):
        self.envelope = json.loads((Path(__file__).parent / "fixtures/contracts/c01-values.json").read_text())["envelope"]
        self.timeline = self.envelope["timeline_id"]
        self.npc = self.envelope["npc_id"]
        self.cursor = DeliveryCursor(timeline_id=self.timeline, consumer_id="consumer:1", position=0)
        self.initial_revisions = (
            (self.timeline, AggregateRevision(kind="npc", scope_id=self.npc, revision=7)),
            (self.timeline, AggregateRevision(kind="quest", scope_id="quest:1", revision=2)),
            (self.timeline, AggregateRevision(kind="inventory", scope_id="irrelevant", revision=99)),
        )

    def request(self, operation="operation:1", base=7, value=8, event_id="event:1", **overrides):
        envelope = ContractEnvelope.model_validate(self.envelope | {"record_id": event_id})
        fields = dict(identity=WriteIdentity(timeline_id=self.timeline, actor_id="actor:1", operation_id=operation),
                      expected_revisions=RevisionSet(npc_id=self.npc, base_npc_state_revision=base,
                          quest=(ScopedRevision(scope_id="quest:1", revision=2),)),
                      npc_revision_basis=NpcRevisionBasis.BASE,
                      approved_changes=Change(value=value),
                      revision_advances=(AggregateRevision(kind="npc", scope_id=self.npc, revision=base + 1),),
                      events=(DurableEvent[Event](envelope=envelope, payload=Event(text="fixture event"),
                                                  consumers=("consumer:1",)),))
        return CommitRequest[Change, Event](**(fields | overrides))


class WritePortConformanceMixin:
    """TestCase mixin for UnitOfWork + DeliveryStore implementations."""

    fixture: WritePortFixture
    uow: UnitOfWork[Change, Event]
    store: DeliveryStore[Event]

    def make_ports(self, fixture: WritePortFixture):
        raise NotImplementedError

    def setUp(self):
        self.fixture = WritePortFixture()
        ports = self.make_ports(self.fixture)
        if isinstance(ports, tuple):
            self.uow, self.store = ports
        else:
            self.uow = ports
            self.store = ports

    def commit(self, request):
        with self.uow.begin() as tx:
            receipt = tx.state_writer.compare_and_commit(request)
            self.assertIsInstance(receipt, CommitReceipt)
            self.assertIsNone(tx.commit())
        return receipt

    def assert_no_visibility_before_application_commit(self):
        self.assertIsInstance(self.uow, UnitOfWork)
        self.assertIsInstance(self.store, DeliveryStore)
        with self.uow.begin() as tx:
            self.assertIsInstance(tx, Transaction)
            self.assertIsInstance(tx.state_writer, StateWriter)
            self.assertFalse(hasattr(tx.state_writer, "commit"))
            receipt = tx.state_writer.compare_and_commit(self.fixture.request())
            self.assertIsInstance(receipt, CommitReceipt)
            self.assertEqual(self.store.poll(self.fixture.cursor, 10).items, ())
            self.assertIsNone(tx.commit())
        self.assertEqual(len(self.store.poll(self.fixture.cursor, 10).items), 1)

    def assert_error_mapping_for_stale_and_invalid_cursor(self):
        request = self.fixture.request(expected_revisions=RevisionSet(
            npc_id=self.fixture.npc,
            base_npc_state_revision=7,
            quest=(ScopedRevision(scope_id="quest:1", revision=1),),
        ))
        with self.uow.begin() as tx:
            result = tx.state_writer.compare_and_commit(request)
            self.assertIsInstance(result, DomainError)
            self.assertEqual(result.code, ErrorCode.STALE_REVISION)
            self.assertIsNone(tx.commit())
        future = DeliveryCursor(timeline_id=self.fixture.timeline, consumer_id="consumer:1", position=1)
        result = self.store.poll(future, 10)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(self.store.poll(self.fixture.cursor, 10).items, ())

    def assert_cursor_retry_order_and_no_skip(self):
        self.commit(self.fixture.request())
        self.commit(self.fixture.request(operation="operation:2", base=8, event_id="event:2"))
        batch = self.store.poll(self.fixture.cursor, 1)
        self.assertEqual(batch, self.store.poll(self.fixture.cursor, 1))
        self.assertEqual(batch.items[0].sequence, 1)
        next_batch = self.store.poll(batch.next_cursor, 1)
        self.assertEqual(next_batch.items[0].sequence, 2)
        self.assertEqual(next_batch.items[0].event.envelope.record_id, "event:2")
        empty = self.store.poll(next_batch.next_cursor, 1)
        self.assertEqual(empty.items, ())
        self.assertEqual(empty.start_cursor, empty.next_cursor)
        for field, value in (("timeline_id", "other:timeline"), ("consumer_id", "consumer:other")):
            cursor = DeliveryCursor.model_validate(self.fixture.cursor.model_dump() | {field: value})
            self.assertEqual(self.store.poll(cursor, 10).items, ())
        future = DeliveryCursor(timeline_id=self.fixture.timeline, consumer_id="consumer:1", position=3)
        self.assertEqual(self.store.poll(future, 10).code, ErrorCode.INVALID_CONTRACT)
        for limit in (0, -1, True):
            self.assertEqual(self.store.poll(self.fixture.cursor, limit).code, ErrorCode.INVALID_CONTRACT)

    def test_protocols_and_no_visibility_before_application_commit(self):
        self.assert_no_visibility_before_application_commit()

    def test_explicit_implicit_and_exception_rollback_restore_all_data(self):
        for mode in ("explicit", "implicit", "exception"):
            with self.subTest(mode=mode):
                try:
                    with self.uow.begin() as tx:
                        self.assertIsInstance(tx.state_writer.compare_and_commit(self.fixture.request()), CommitReceipt)
                        if mode == "explicit":
                            tx.rollback()
                        elif mode == "exception":
                            raise RuntimeError("injected failure")
                except RuntimeError as exc:
                    self.assertEqual(str(exc), "injected failure")
                self.assertEqual(self.store.poll(self.fixture.cursor, 10).items, ())
        self.commit(self.fixture.request())

    def test_exact_retry_returns_original_receipt_before_stale_cas(self):
        request = self.fixture.request()
        prior = self.commit(request)
        with self.uow.begin() as tx:
            retry = tx.state_writer.compare_and_commit(CommitRequest[Change, Event].model_validate_json(request.model_dump_json()))
            self.assertEqual(retry, prior)
            self.assertIsNone(tx.commit())
        self.assertEqual(len(self.store.poll(self.fixture.cursor, 10).items), 1)
        with self.assertRaises(ValidationError):
            prior.receipt_id = "replacement"

    def test_changed_content_digest_is_conflict_without_partial_write(self):
        prior = self.commit(self.fixture.request())
        for request in (self.fixture.request(value=999), self.fixture.request(event_id="event:changed"),
                        self.fixture.request(base=8)):
            with self.subTest(request=request), self.uow.begin() as tx:
                result = tx.state_writer.compare_and_commit(request)
                self.assertIsInstance(result, DomainError)
                self.assertEqual(result.code, ErrorCode.IDEMPOTENCY_CONFLICT)
                self.assertIsNone(tx.commit())
        self.assertEqual(self.commit(self.fixture.request()), prior)
        self.assertEqual(len(self.store.poll(self.fixture.cursor, 10).items), 1)

    def test_relevant_cas_and_absent_aggregate_fail(self):
        for scope, revision in (("quest:1", 1), ("quest:missing", 0)):
            request = self.fixture.request(expected_revisions=RevisionSet(npc_id=self.fixture.npc,
                                           base_npc_state_revision=7,
                                           quest=(ScopedRevision(scope_id=scope, revision=revision),)))
            with self.uow.begin() as tx:
                result = tx.state_writer.compare_and_commit(request)
                self.assertEqual(result.code, ErrorCode.STALE_REVISION)
                self.assertIsNone(tx.commit())
            self.assertEqual(self.store.poll(self.fixture.cursor, 10).items, ())
        self.commit(self.fixture.request())
        with self.uow.begin() as tx:
            result = tx.state_writer.compare_and_commit(self.fixture.request(operation="operation:2", event_id="event:2"))
            self.assertEqual(result.code, ErrorCode.STALE_REVISION)

    def test_approved_revision_basis_is_distinct_from_base(self):
        self.commit(self.fixture.request())
        revisions = RevisionSet(npc_id=self.fixture.npc, base_npc_state_revision=7, approved_npc_state_revision=8)
        request = self.fixture.request(operation="operation:2", event_id="event:2", expected_revisions=revisions,
                                       npc_revision_basis="approved",
                                       revision_advances=(AggregateRevision(kind="npc", scope_id=self.fixture.npc,
                                                                           revision=9),))
        self.assertEqual(self.commit(request).revisions_before[0].revision, 8)
        with self.assertRaises(ValidationError):
            self.fixture.request(npc_revision_basis="approved")

    def test_competing_transactions_cannot_overwrite_committed_data(self):
        first, second = self.uow.begin(), self.uow.begin()
        first.state_writer.compare_and_commit(self.fixture.request())
        second.state_writer.compare_and_commit(self.fixture.request(operation="operation:2", event_id="event:2"))
        self.assertIsNone(first.commit())
        self.assertEqual(second.commit().code, ErrorCode.STALE_REVISION)
        self.assertEqual(len(self.store.poll(self.fixture.cursor, 10).items), 1)
        with self.assertRaises(RuntimeError):
            second.state_writer.compare_and_commit(self.fixture.request())

    def test_event_identity_cannot_be_reused_by_other_operation(self):
        self.commit(self.fixture.request())
        with self.uow.begin() as tx:
            result = tx.state_writer.compare_and_commit(self.fixture.request(operation="operation:2", base=8))
            self.assertEqual(result.code, ErrorCode.IDEMPOTENCY_CONFLICT)
        self.assertEqual(len(self.store.poll(self.fixture.cursor, 10).items), 1)

    def test_cursor_retry_order_no_skip_and_scope_isolation(self):
        self.assert_cursor_retry_order_and_no_skip()

    def test_delivery_batch_rejects_skipping_or_wrong_scope(self):
        self.commit(self.fixture.request())
        batch = self.store.poll(self.fixture.cursor, 1)
        for updates in ({"next_cursor": self.fixture.cursor.model_dump() | {"position": 2}},
                        {"next_cursor": self.fixture.cursor.model_dump() | {"position": 1, "consumer_id": "other"}},
                        {"items": [batch.items[0].model_dump() | {"sequence": 2}]}):
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                DeliveryBatch[Event].model_validate(batch.model_dump() | updates)

    def test_write_structure_rejects_unrelated_or_duplicate_revision_advances(self):
        for advances in ((AggregateRevision(kind="inventory", scope_id="irrelevant", revision=100),),
                         (AggregateRevision(kind="npc", scope_id=self.fixture.npc, revision=9),),
                         (AggregateRevision(kind="npc", scope_id=self.fixture.npc, revision=8),) * 2):
            with self.subTest(advances=advances), self.assertRaises(ValidationError):
                self.fixture.request(revision_advances=advances)
