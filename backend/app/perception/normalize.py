"""Pure perception normalization handoffs.

This module owns immutable observed/normalized signal value shapes. It does
not read live world state or trust client claims as authoritative facts.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, field_validator, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion, Position


SignalText = Annotated[str, Field(strict=True, min_length=1, max_length=2000)]
UnitName = Annotated[str, Field(strict=True, min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_:/.-]*$")]
FiniteSignalValue = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class SignalKind(str, Enum):
    DIALOGUE = "dialogue"
    ENTITY = "entity"
    ITEM = "item"
    QUEST = "quest"
    MEMORY = "memory"
    WORLD_EVENT = "world_event"


class EvidenceStatus(str, Enum):
    FACT = "fact"
    CLAIM = "claim"
    INTERPRETATION = "interpretation"


class SignalVisibility(str, Enum):
    DIRECT = "direct"
    INFORMED = "informed"
    REMEMBERED = "remembered"
    PRIVATE = "private"


class ObservationSignal(ContractValue):
    source_id: Identifier
    kind: SignalKind
    status: EvidenceStatus
    visibility: SignalVisibility
    observed_at: datetime
    subject_id: Identifier | None = None
    target_id: Identifier | None = None
    position: Position | None = None
    value: FiniteSignalValue | None = None
    unit: UnitName | None = None
    text: SignalText | None = None

    @field_validator("observed_at", mode="before")
    @classmethod
    def timestamp_shape(cls, value: object) -> object:
        if not isinstance(value, (datetime, str)):
            raise ValueError("observed_at must be an aware datetime or ISO timestamp")
        if isinstance(value, str) and "T" not in value:
            raise ValueError("observed_at must be an ISO timestamp containing T")
        return value

    @field_validator("observed_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("observed_at must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def numeric_unit_pair(self):
        if (self.value is None) != (self.unit is None):
            raise ValueError("value and unit must be supplied together")
        if self.text is None and self.value is None and self.position is None:
            raise ValueError("signal must include text, numeric value or position")
        return self


class ObservedSignals(ContractEnvelope):
    observation_id: Identifier
    signals: tuple[ObservationSignal, ...] = Field(min_length=1)


class NormalizedSignal(ContractValue):
    source_ids: tuple[Identifier, ...] = Field(min_length=1)
    kind: SignalKind
    status: EvidenceStatus
    visibility: SignalVisibility
    observed_at: datetime
    subject_id: Identifier | None = None
    target_id: Identifier | None = None
    position: Position | None = None
    value: FiniteSignalValue | None = None
    unit: UnitName | None = None
    text: SignalText | None = None

    @field_validator("observed_at", mode="before")
    @classmethod
    def timestamp_shape(cls, value: object) -> object:
        return ObservationSignal.timestamp_shape(value)

    @field_validator("observed_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        return ObservationSignal.utc_timestamp(value)

    @model_validator(mode="after")
    def source_and_value_invariants(self):
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("source_ids must be unique")
        if (self.value is None) != (self.unit is None):
            raise ValueError("value and unit must be supplied together")
        if self.text is None and self.value is None and self.position is None:
            raise ValueError("signal must include text, numeric value or position")
        return self


class NormalizationPolicy(ContractEnvelope):
    policy: PolicyVersion
    canonical_units: tuple[UnitName, ...]

    @model_validator(mode="after")
    def unique_units(self):
        if len(set(self.canonical_units)) != len(self.canonical_units):
            raise ValueError("canonical_units must be unique")
        return self


class NormalizedSignals(ContractEnvelope):
    observation_id: Identifier
    policy: PolicyVersion
    signals: tuple[NormalizedSignal, ...] = Field(min_length=1)


NormalizationResult: TypeAlias = NormalizedSignals | DomainError


class Normalize(Protocol):
    def __call__(
        self,
        observed: ObservedSignals,
        policy: NormalizationPolicy,
    ) -> NormalizationResult: ...


def normalize(
    observed: ObservedSignals,
    policy: NormalizationPolicy,
    *,
    record_id: Identifier,
    created_at: datetime | str | None = None,
) -> NormalizationResult:
    """Normalize accepted observations into deterministic immutable signals."""

    evidence_error = _validate_policy_evidence(observed, policy)
    if evidence_error is not None:
        return evidence_error

    canonical_units = set(policy.canonical_units)
    by_source: dict[Identifier, ObservationSignal] = {}
    for signal in observed.signals:
        if signal.unit is not None and signal.unit not in canonical_units:
            return _error(observed, policy, "Observed signal unit is not canonical.")
        existing = by_source.get(signal.source_id)
        if existing is None:
            by_source[signal.source_id] = signal
        elif existing != signal:
            return _error(observed, policy, "Duplicate source observations conflict.")

    normalized = tuple(_to_normalized(signal) for signal in by_source.values())
    return NormalizedSignals(
        schema_version=observed.schema_version,
        record_id=record_id,
        trace_id=observed.trace_id,
        causation_id=observed.record_id,
        game_id=observed.game_id,
        timeline_id=observed.timeline_id,
        npc_id=observed.npc_id,
        actor_id=observed.actor_id,
        target_id=observed.target_id,
        created_at=created_at or observed.created_at,
        source_ids=(observed.record_id, policy.record_id),
        policy_versions=(
            *tuple(version for version in observed.policy_versions if version.policy_id != policy.policy.policy_id),
            policy.policy,
        ),
        observation_id=observed.observation_id,
        policy=policy.policy,
        signals=normalized,
    )


def _to_normalized(signal: ObservationSignal) -> NormalizedSignal:
    return NormalizedSignal(
        source_ids=(signal.source_id,),
        kind=signal.kind,
        status=signal.status,
        visibility=signal.visibility,
        observed_at=signal.observed_at,
        subject_id=signal.subject_id,
        target_id=signal.target_id,
        position=signal.position,
        value=signal.value,
        unit=signal.unit,
        text=signal.text,
    )


def _validate_policy_evidence(observed: ObservedSignals, policy: NormalizationPolicy) -> DomainError | None:
    observed_versions = {version.policy_id: version.version for version in observed.policy_versions}
    if observed.game_id != policy.game_id or observed.timeline_id != policy.timeline_id:
        return _error(observed, policy, "Normalization policy evidence is mismatched.")
    if observed_versions.get(policy.policy.policy_id) != policy.policy.version:
        return _error(observed, policy, "Normalization policy evidence is mismatched.")
    return None


def _error(observed: ObservedSignals, policy: NormalizationPolicy, message: str) -> DomainError:
    return DomainError(
        code=ErrorCode.INVALID_CONTRACT,
        stage="perception.normalize",
        retryable=False,
        source_ids=(observed.record_id, policy.record_id),
        public_message=message,
    )
