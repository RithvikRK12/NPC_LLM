"""P01 read/provider boundaries, independent of storage and provider clients.

Owning modules specialize generic protocols with their immutable handoffs; this
module does not substitute a partial world or memory schema for those records.
Result[T] follows design section 3: a value or DomainError, never a normal
rejection exception. Protocol conformance is structural; runtime isinstance
checks check method presence only, not annotations or adapter behavior.
"""

from datetime import datetime
from typing import Annotated, Protocol, TypeAlias, TypeVar, runtime_checkable

from pydantic import Field, model_validator

from app.contracts import ContractValue, DomainError, Identifier


T = TypeVar("T")
Result: TypeAlias = T | DomainError
InputT = TypeVar("InputT", bound=ContractValue, contravariant=True)
OutputT = TypeVar("OutputT", bound=ContractValue, covariant=True)
ScopeT = TypeVar("ScopeT", bound=ContractValue, contravariant=True)
PositiveInt = Annotated[int, Field(strict=True, gt=0)]
FiniteFloat = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class EmbeddingNamespace(ContractValue):
    """Complete compatibility identity; revisions cannot be mixed."""

    model_id: Identifier
    model_revision: Identifier
    dimension: PositiveInt
    preprocessing_revision: Identifier


class Vector(ContractValue):
    namespace: EmbeddingNamespace
    values: tuple[FiniteFloat, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def matches_dimension(self) -> "Vector":
        if len(self.values) != self.namespace.dimension:
            raise ValueError("vector length must match embedding namespace dimension")
        return self


class VectorBatch(ContractValue):
    """Vectors preserve input document order and cardinality, including empty input."""

    namespace: EmbeddingNamespace
    vectors: tuple[Vector, ...]

    @model_validator(mode="after")
    def matches_namespace(self) -> "VectorBatch":
        if any(vector.namespace != self.namespace for vector in self.vectors):
            raise ValueError("all vectors must share the exact batch namespace")
        return self


class CandidateIdScore(ContractValue):
    """A derived candidate only; memory readers recheck authoritative scope.

    score is cosine similarity (higher is better), not raw FAISS distance or
    an unnormalized lexical rank. Adapters convert their metric accordingly.
    """

    memory_id: Identifier
    score: Annotated[float, Field(strict=True, ge=-1, le=1, allow_inf_nan=False)]


@runtime_checkable
class WorldReader(Protocol[InputT, OutputT]):
    """Specialize with trigger and WorldReadSet including values and revisions.

    Read only: never commits, mutates state or exposes database handles.
    """

    def read_context(self, trigger: InputT) -> Result[OutputT]: ...


@runtime_checkable
class MemoryReader(Protocol[ScopeT, OutputT]):
    """Specialize with MemoryQuery filters and complete MemoryRecord values.

    Recheck timeline, recipient/knowledge and lifecycle before returning at
    most limit records. No matches returns (), never an invented empty record.
    limit must be positive. Reads cannot commit or mutate authoritative data.
    """

    def query_scope(self, filters: ScopeT, limit: int) -> tuple[OutputT, ...]: ...


@runtime_checkable
class ModelProvider(Protocol[InputT, OutputT]):
    """Specialize with ModelRequest and untrusted RawProposal handoffs.

    Awaitable generation allows cancellation; cancellation propagates to the
    caller. Unavailability is MODEL_UNAVAILABLE; invalid provider output is
    MODEL_INVALID_OUTPUT. A success does not confer approval or authority.
    """

    async def generate(self, request: InputT) -> Result[OutputT]: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Real semantic vectors only; outages return EMBEDDING_UNAVAILABLE.

    Results match the requested namespace; batches preserve input order and
    cardinality. No hash/zero fallback is a successful embedding.
    """

    def embed_documents(self, texts: tuple[str, ...], namespace: EmbeddingNamespace) -> Result[VectorBatch]: ...

    def embed_query(self, text: str, namespace: EmbeddingNamespace) -> Result[Vector]: ...


@runtime_checkable
class VectorIndex(Protocol[ScopeT]):
    """Specialize scope with owning memory module's immutable search filters.

    Return at most positive limit candidates in descending cosine similarity.
    Scope includes timeline, recipient/knowledge and lifecycle restrictions.
    Never compare namespaces; an absent/incompatible index is INDEX_NOT_READY,
    while a ready index with no matches returns (). Results are not memories.
    """

    def search(self, scope: ScopeT, vector: Vector, limit: int) -> Result[tuple[CandidateIdScore, ...]]: ...


@runtime_checkable
class Clock(Protocol):
    """Return an aware UTC instant; no implicit system clock in consumers."""

    def now_utc(self) -> datetime: ...


@runtime_checkable
class IdSource(Protocol):
    """Return a new opaque Identifier; callers can inject deterministic IDs."""

    def new_id(self) -> Identifier: ...
