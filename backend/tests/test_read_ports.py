"""P01 deterministic examples of fully specialized protocols; no live adapters."""

import asyncio
from datetime import datetime, timezone
import inspect
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractValue, DomainError, ErrorCode, Identifier, RevisionSet
from app.ports import (
    CandidateIdScore, Clock, EmbeddingNamespace, EmbeddingProvider, IdSource,
    MemoryReader, ModelProvider, Result, Vector, VectorBatch, VectorIndex, WorldReader,
)


# Synthetic owning-module handoffs demonstrate type specialization, not a
# proposed production memory/world schema. Production types remain owner work.
class Scope(ContractValue):
    timeline_id: Identifier
    npc_id: Identifier
    lifecycle: str


class WorldFixture(ContractValue):
    scope: Scope
    revisions: RevisionSet
    visible_ids: tuple[Identifier, ...]


class MemoryFixture(ContractValue):
    scope: Scope
    memory_id: Identifier
    summary: str


class RequestFixture(ContractValue):
    prompt: str


class ProposalFixture(ContractValue):
    text: str


def unavailable(code: ErrorCode) -> DomainError:
    return DomainError(code=code, stage="fake_provider", retryable=True,
                       source_ids=(), public_message="Provider is unavailable.")


class ReadFake:
    def __init__(self, world: WorldFixture, records: tuple[MemoryFixture, ...]):
        self.world = world
        self.records = records

    def read_context(self, trigger: Scope) -> Result[WorldFixture]:
        if trigger != self.world.scope:
            return unavailable(ErrorCode.OLD_TIMELINE)
        return self.world

    def query_scope(self, filters: Scope, limit: int) -> tuple[MemoryFixture, ...]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        return tuple(record for record in self.records if record.scope == filters)[:limit]


class ModelFake:
    def __init__(self, available: bool):
        self.available = available
        self.calls = 0

    async def generate(self, request: RequestFixture) -> Result[ProposalFixture]:
        self.calls += 1
        await asyncio.sleep(0)
        return ProposalFixture(text=request.prompt) if self.available else unavailable(ErrorCode.MODEL_UNAVAILABLE)


class EmbeddingFake:
    """Fixed vector fixtures stand in for semantic provider responses."""

    def __init__(self, available: bool):
        self.available = available

    def embed_query(self, text: str, namespace: EmbeddingNamespace) -> Result[Vector]:
        if not self.available:
            return unavailable(ErrorCode.EMBEDDING_UNAVAILABLE)
        fixture = {"first": (1.0, 0.0), "second": (0.0, 1.0)}[text]
        return Vector(namespace=namespace, values=fixture)

    def embed_documents(self, texts: tuple[str, ...], namespace: EmbeddingNamespace) -> Result[VectorBatch]:
        if not self.available:
            return unavailable(ErrorCode.EMBEDDING_UNAVAILABLE)
        vectors = tuple(self.embed_query(text, namespace) for text in texts)
        assert all(isinstance(vector, Vector) for vector in vectors)
        return VectorBatch(namespace=namespace, vectors=vectors)


class IndexFake:
    def __init__(self, namespace: EmbeddingNamespace, scope: Scope, ready: bool = True):
        self.namespace, self.scope, self.ready = namespace, scope, ready

    def search(self, scope: Scope, vector: Vector, limit: int) -> Result[tuple[CandidateIdScore, ...]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if not self.ready or vector.namespace != self.namespace:
            return unavailable(ErrorCode.INDEX_NOT_READY)
        if scope != self.scope:
            return ()
        return (CandidateIdScore(memory_id="memory:1", score=0.75),)[:limit]


class FixedClock:
    def now_utc(self) -> datetime:
        return datetime(2026, 9, 12, 10, tzinfo=timezone.utc)


class SequentialIds:
    def __init__(self):
        self.sequence = 0

    def new_id(self) -> Identifier:
        self.sequence += 1
        return f"fixture:{self.sequence}"


class ReadPortTests(unittest.TestCase):
    def setUp(self):
        self.scope = Scope(timeline_id="timeline:1", npc_id="npc:1", lifecycle="active")
        self.namespace = EmbeddingNamespace(model_id="fixture", model_revision="v1", dimension=2,
                                            preprocessing_revision="v1")
        self.memory = MemoryFixture(scope=self.scope, memory_id="memory:1", summary="Observed fixture.")
        self.world = WorldFixture(scope=self.scope, revisions=RevisionSet(npc_id="npc:1", base_npc_state_revision=3),
                                  visible_ids=("npc:2",))

    def test_read_only_world_and_memory_specializations(self):
        fake = ReadFake(self.world, (self.memory,))
        reader: WorldReader[Scope, WorldFixture] = fake
        memory_reader: MemoryReader[Scope, MemoryFixture] = fake
        self.assertIsInstance(reader, WorldReader)
        self.assertIsInstance(memory_reader, MemoryReader)
        before = (fake.world.model_dump_json(), fake.records)
        result = reader.read_context(self.scope)
        self.assertIsInstance(result, WorldFixture)
        self.assertEqual(result.revisions.base_npc_state_revision, 3)
        self.assertEqual(result.revisions.npc_id, result.scope.npc_id)
        self.assertEqual(memory_reader.query_scope(self.scope, 1), (self.memory,))
        self.assertEqual(before, (fake.world.model_dump_json(), fake.records))
        for protocol in (WorldReader, MemoryReader):
            self.assertFalse(any(name in protocol.__dict__ for name in ("commit", "save", "delete", "begin")))

    def test_absent_memory_and_scope_isolation(self):
        reader: MemoryReader[Scope, MemoryFixture] = ReadFake(self.world, (self.memory, self.memory))
        self.assertEqual(len(reader.query_scope(self.scope, 1)), 1)
        for field, value in (("timeline_id", "timeline:old"), ("npc_id", "npc:other"), ("lifecycle", "superseded")):
            with self.subTest(field=field):
                other = Scope.model_validate(self.scope.model_dump() | {field: value})
                self.assertEqual(reader.query_scope(other, 5), ())
        self.assertEqual(ReadFake(self.world, ()).query_scope(self.scope, 5), ())
        with self.assertRaises(ValueError):
            reader.query_scope(self.scope, 0)

    def test_embedding_batches_keep_order_cardinality_and_namespace(self):
        provider: EmbeddingProvider = EmbeddingFake(True)
        self.assertIsInstance(provider, EmbeddingProvider)
        result = provider.embed_documents(("first", "second"), self.namespace)
        self.assertIsInstance(result, VectorBatch)
        self.assertEqual(tuple(vector.values for vector in result.vectors), ((1.0, 0.0), (0.0, 1.0)))
        self.assertTrue(all(vector.namespace == result.namespace for vector in result.vectors))
        self.assertEqual(provider.embed_documents((), self.namespace).vectors, ())
        self.assertEqual(provider.embed_query("first", self.namespace), result.vectors[0])

    def test_embedding_unavailability_has_no_fabricated_vector(self):
        provider: EmbeddingProvider = EmbeddingFake(False)
        for result in (provider.embed_documents(("first",), self.namespace), provider.embed_query("first", self.namespace)):
            self.assertIsInstance(result, DomainError)
            self.assertEqual(result.code, ErrorCode.EMBEDDING_UNAVAILABLE)
            self.assertFalse(hasattr(result, "values"))

    def test_vector_shape_namespace_and_finite_validation(self):
        for values in ((1.0,), (1.0, 0.0, 0.0), (True, 0.0), ("1", 0.0), (float("nan"), 0.0), (float("inf"), 0.0)):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                Vector(namespace=self.namespace, values=values)
        for field, value in (("dimension", 0), ("dimension", True), ("model_id", "bad id"), ("model_revision", "")):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                EmbeddingNamespace.model_validate(self.namespace.model_dump() | {field: value})
        other = EmbeddingNamespace.model_validate(self.namespace.model_dump() | {"preprocessing_revision": "v2"})
        with self.assertRaises(ValidationError):
            VectorBatch(namespace=self.namespace, vectors=(Vector(namespace=other, values=(1.0, 0.0)),))

    def test_provider_values_are_immutable_and_isolate_input(self):
        values = [1.0, 0.0]
        vector = Vector(namespace=self.namespace, values=values)
        vectors = [vector]
        batch = VectorBatch(namespace=self.namespace, vectors=vectors)
        values[0] = 99.0
        vectors.clear()
        self.assertEqual(batch.vectors[0].values, (1.0, 0.0))
        with self.assertRaises(ValidationError):
            batch.vectors[0].namespace.dimension = 3
        with self.assertRaises(TypeError):
            batch.vectors[0].values[0] = 0.0

    def test_index_returns_candidate_ids_and_typed_not_ready(self):
        index: VectorIndex[Scope] = IndexFake(self.namespace, self.scope)
        self.assertIsInstance(index, VectorIndex)
        vector = Vector(namespace=self.namespace, values=(1.0, 0.0))
        result = index.search(self.scope, vector, 1)
        self.assertEqual(result, (CandidateIdScore(memory_id=self.memory.memory_id, score=0.75),))
        self.assertFalse(hasattr(result[0], "summary"))
        other = Scope(timeline_id="timeline:old", npc_id="npc:1", lifecycle="active")
        self.assertEqual(index.search(other, vector, 1), ())
        for field in ("model_id", "model_revision", "preprocessing_revision"):
            namespace = EmbeddingNamespace.model_validate(self.namespace.model_dump() | {field: "different"})
            result = index.search(self.scope, Vector(namespace=namespace, values=(1.0, 0.0)), 1)
            self.assertEqual(result.code, ErrorCode.INDEX_NOT_READY)
        self.assertEqual(IndexFake(self.namespace, self.scope, False).search(self.scope, vector, 1).code, ErrorCode.INDEX_NOT_READY)

    def test_candidate_validation(self):
        for score in (float("nan"), float("inf"), -1.1, 1.1, True, "0.5"):
            with self.subTest(score=score), self.assertRaises(ValidationError):
                CandidateIdScore(memory_id="memory:1", score=score)
        with self.assertRaises(ValidationError):
            CandidateIdScore(memory_id="bad id", score=0.5)

    def test_injected_clock_and_ids_are_deterministic(self):
        clock: Clock = FixedClock()
        ids: IdSource = SequentialIds()
        self.assertIsInstance(clock, Clock)
        self.assertIsInstance(ids, IdSource)
        self.assertEqual(clock.now_utc(), clock.now_utc())
        self.assertIs(clock.now_utc().tzinfo, timezone.utc)
        self.assertEqual((ids.new_id(), ids.new_id()), ("fixture:1", "fixture:2"))

    def test_import_is_infrastructure_free(self):
        result = subprocess.run([sys.executable, "-c", "import sys; import app.ports; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss'} for name in sys.modules)"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class AsyncModelPortTests(unittest.IsolatedAsyncioTestCase):
    async def test_async_model_success_and_unavailable(self):
        self.assertTrue(inspect.iscoroutinefunction(ModelProvider.generate))
        for available in (True, False):
            fake = ModelFake(available)
            provider: ModelProvider[RequestFixture, ProposalFixture] = fake
            self.assertIsInstance(provider, ModelProvider)
            pending = provider.generate(RequestFixture(prompt="fixture prompt"))
            self.assertTrue(inspect.isawaitable(pending))
            self.assertEqual(fake.calls, 0)
            result = await pending
            self.assertEqual(fake.calls, 1)
            if available:
                self.assertEqual(result, ProposalFixture(text="fixture prompt"))
            else:
                self.assertIsInstance(result, DomainError)
                self.assertEqual(result.code, ErrorCode.MODEL_UNAVAILABLE)

    async def test_cancellation_propagates(self):
        task = asyncio.create_task(ModelFake(True).generate(RequestFixture(prompt="fixture")))
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task


if __name__ == "__main__":
    unittest.main()
