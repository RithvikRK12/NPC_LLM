"""T01 membership handoffs; fuzzification is intentionally not implemented yet.

This module owns a minimal input projection, not state.extract's CandidateState.
Policy labels and dimensions are configured identifiers rather than a hardcoded
LOW/MEDIUM/HIGH vocabulary. T01 validates record structure; T02/T03 will own
evaluation, point ordering, shoulders and cross-record policy applicability.
"""

from typing import Annotated, Literal, Protocol, TypeAlias

from pydantic import Field

from app.contracts import (
    ContractEnvelope,
    ContractValue,
    DomainError,
    Identifier,
    PolicyVersion,
)


NormalizedValue = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=0, le=1)]
FinitePoint = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class NamedInput(ContractValue):
    dimension: Identifier
    value: NormalizedValue


class MembershipInput(ContractEnvelope):
    """Immutable local view built from an upstream candidate's approved scope.

    candidate_state_id identifies the upstream record; envelope source_ids
    preserves its evidence. Dimensions contain only selected normalized inputs.
    No absolute game-state mutations or upstream extraction fields are owned here.
    """

    candidate_state_id: Identifier
    dimensions: tuple[NamedInput, ...] = Field(min_length=1)


class Triangle(ContractValue):
    kind: Literal["triangle"]
    a: FinitePoint
    b: FinitePoint
    c: FinitePoint


class Trapezoid(ContractValue):
    kind: Literal["trapezoid"]
    a: FinitePoint
    b: FinitePoint
    c: FinitePoint
    d: FinitePoint


MembershipShape: TypeAlias = Annotated[Triangle | Trapezoid, Field(discriminator="kind")]


class LabelDefinition(ContractValue):
    label: Identifier
    shape: MembershipShape


class DimensionDefinition(ContractValue):
    dimension: Identifier
    labels: tuple[LabelDefinition, ...] = Field(min_length=1)


class MembershipPolicy(ContractEnvelope):
    """Versioned authored membership configuration, before semantic activation.

    Decoding alone does not establish ordered points or compatibility with a
    selected input. Those checks belong to T03, before this policy is evaluated.
    """

    policy: PolicyVersion
    dimensions: tuple[DimensionDefinition, ...] = Field(min_length=1)


class LabelDegree(ContractValue):
    label: Identifier
    degree: NormalizedValue


class DimensionMemberships(ContractValue):
    dimension: Identifier
    labels: tuple[LabelDegree, ...] = Field(min_length=1)


class Memberships(ContractEnvelope):
    """Membership degrees with explicit input, candidate and policy identities."""

    input_id: Identifier
    candidate_state_id: Identifier
    policy: PolicyVersion
    dimensions: tuple[DimensionMemberships, ...] = Field(min_length=1)


MembershipResult: TypeAlias = Memberships | DomainError


class Fuzzify(Protocol):
    """Callable contract for T02; tests can supply a pure fake today.

    The owning caller supplies output identity/envelope context through its
    implementation's injected ID/clock sources. Ordinary rejection is a shared
    DomainError value, not a transport ValidationError or an internal exception.
    """

    def __call__(self, candidate: MembershipInput, policy: MembershipPolicy) -> MembershipResult: ...
