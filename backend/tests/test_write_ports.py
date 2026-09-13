"""P02/P03 write-port conformance for the deterministic reference fake."""

import unittest

from app.contracts import DomainError, ErrorCode
from app.ports.fakes import InMemoryTransaction, InMemoryUnitOfWork, _error

from port_conformance import Event, Ids, WritePortConformanceMixin


class InMemoryWritePortConformanceTests(WritePortConformanceMixin, unittest.TestCase):
    def make_ports(self, fixture):
        return InMemoryUnitOfWork(Ids(), fixture.event_type, fixture.initial_revisions)


class PrematureCommitTransaction(InMemoryTransaction):
    def _stage(self, request):
        result = super()._stage(request)
        if not isinstance(result, DomainError):
            self.commit()
        return result


class PrematureCommitUnitOfWork(InMemoryUnitOfWork):
    def begin(self):
        return PrematureCommitTransaction(self)


class CursorSkippingUnitOfWork(InMemoryUnitOfWork):
    def poll(self, cursor, limit):
        batch = super().poll(cursor, limit)
        if isinstance(batch, DomainError) or not batch.items:
            return batch
        skipped = cursor.model_copy(update={"position": cursor.position + 1})
        return super().poll(skipped, limit)


class WrongErrorMappingUnitOfWork(InMemoryUnitOfWork):
    def poll(self, cursor, limit):
        result = super().poll(cursor, limit)
        if isinstance(result, DomainError) and result.code == ErrorCode.INVALID_CONTRACT:
            return _error(ErrorCode.STALE_REVISION, "Wrong error code.")
        return result


class BrokenFakeDetectionTests(unittest.TestCase):
    def harness(self, adapter_type):
        test = InMemoryWritePortConformanceTests(methodName="runTest")
        test.setUp()
        test.uow = test.store = adapter_type(Ids(), Event, test.fixture.initial_revisions)
        return test

    def test_suite_detects_premature_commit_visibility(self):
        with self.assertRaises(AssertionError):
            self.harness(PrematureCommitUnitOfWork).assert_no_visibility_before_application_commit()

    def test_suite_detects_cursor_skipping(self):
        with self.assertRaises(AssertionError):
            self.harness(CursorSkippingUnitOfWork).assert_cursor_retry_order_and_no_skip()

    def test_suite_detects_wrong_error_mapping(self):
        with self.assertRaises(AssertionError):
            self.harness(WrongErrorMappingUnitOfWork).assert_error_mapping_for_stale_and_invalid_cursor()


if __name__ == "__main__":
    unittest.main()
