"""Membership handoffs and pure fuzzification.

This module owns a minimal input projection, not state.extract's CandidateState.
Policy labels and dimensions are configured identifiers rather than a hardcoded
LOW/MEDIUM/HIGH vocabulary. T03 will own invariant hardening for invalid
authored points; T02 evaluates the accepted happy-path policy shapes.
"""

from datetime import datetime
from typing import Annotated, Literal, Protocol, TypeAlias

from pydantic import Field

from app.contracts import (
    ContractEnvelope,
    ContractValue,
    DomainError,
    ErrorCode,
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


def _triangle_degree(value: float, shape: Triangle) -> float:
    if value <= shape.a or value >= shape.c:
        return 0.0
    if value == shape.b:
        return 1.0
    if value < shape.b:
        return (value - shape.a) / (shape.b - shape.a)
    return (shape.c - value) / (shape.c - shape.b)


def _trapezoid_degree(value: float, shape: Trapezoid) -> float:
    if value < shape.a or value > shape.d:
        return 0.0
    if shape.b <= value <= shape.c:
        return 1.0
    if value < shape.b:
        if shape.a == shape.b:
            return 1.0
        return (value - shape.a) / (shape.b - shape.a)
    if shape.c == shape.d:
        return 1.0
    return (shape.d - value) / (shape.d - shape.c)


def _degree(value: float, shape: MembershipShape) -> float:
    if isinstance(shape, Triangle):
        degree = _triangle_degree(value, shape)
    else:
        degree = _trapezoid_degree(value, shape)
    return min(1.0, max(0.0, round(degree, 12)))


def _error(candidate: MembershipInput, policy: MembershipPolicy, message: str) -> DomainError:
    return DomainError(
        code=ErrorCode.INVALID_CONTRACT,
        stage="fuzzy.membership",
        retryable=False,
        source_ids=(candidate.record_id, policy.record_id),
        public_message=message,
    )


def _points(shape: MembershipShape) -> tuple[float, ...]:
    if isinstance(shape, Triangle):
        return (shape.a, shape.b, shape.c)
    return (shape.a, shape.b, shape.c, shape.d)


def _valid_shape(shape: MembershipShape) -> bool:
    points = _points(shape)
    if any(point < 0.0 or point > 1.0 for point in points):
        return False
    if isinstance(shape, Triangle):
        return shape.a < shape.b < shape.c
    return shape.a <= shape.b <= shape.c <= shape.d


def fuzzify(
    candidate: MembershipInput,
    policy: MembershipPolicy,
    *,
    record_id: Identifier,
    created_at: datetime | str | None = None,
) -> MembershipResult:
    """Evaluate configured membership labels for each provided input dimension."""

    if candidate.timeline_id != policy.timeline_id:
        return _error(candidate, policy, "Membership input and policy timelines do not match.")
    if policy.policy not in candidate.policy_versions or policy.policy not in policy.policy_versions:
        return _error(candidate, policy, "Membership policy version is not declared by the input and policy records.")

    policy_by_dimension = {definition.dimension: definition for definition in policy.dimensions}
    dimensions: list[DimensionMemberships] = []
    for named_input in candidate.dimensions:
        definition = policy_by_dimension.get(named_input.dimension)
        if definition is None:
            return _error(candidate, policy, "Membership policy does not define an input dimension.")
        if any(not _valid_shape(label.shape) for label in definition.labels):
            return _error(candidate, policy, "Membership policy contains unordered or out-of-range points.")
        dimensions.append(
            DimensionMemberships(
                dimension=named_input.dimension,
                labels=tuple(
                    LabelDegree(label=label.label, degree=_degree(named_input.value, label.shape))
                    for label in definition.labels
                ),
            )
        )

    return Memberships(
        schema_version=candidate.schema_version,
        record_id=record_id,
        trace_id=candidate.trace_id,
        causation_id=candidate.record_id,
        game_id=candidate.game_id,
        timeline_id=candidate.timeline_id,
        npc_id=candidate.npc_id,
        actor_id=candidate.actor_id,
        target_id=candidate.target_id,
        created_at=created_at or candidate.created_at,
        source_ids=(candidate.record_id, *candidate.source_ids, policy.record_id),
        policy_versions=policy.policy_versions,
        input_id=candidate.record_id,
        candidate_state_id=candidate.candidate_state_id,
        policy=policy.policy,
        dimensions=tuple(dimensions),
    )
