"""Pure memory lifecycle review and mutation planning."""

from datetime import datetime
from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion
from app.memory.classify import Importance, MemoryCategory
from app.memory.reconcile import EpistemicStatus, EvidenceAuthority


class MemoryLifecycleState(str, Enum):
    ACTIVE = "active"
    RETRIEVAL_EXPIRED = "retrieval_expired"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"
    ARCHIVED = "archived"
    DELETED = "deleted"


class LifecycleAction(str, Enum):
    KEEP = "keep"
    DECAY_SALIENCE = "decay_salience"
    EXPIRE_FOR_RETRIEVAL = "expire_for_retrieval"
    ARCHIVE = "archive"
    DELETE = "delete"
    PROTECT = "protect"


class MemoryRecordView(ContractEnvelope):
    memory_id: Identifier
    category: MemoryCategory
    status: EpistemicStatus
    authority: EvidenceAuthority
    lifecycle: MemoryLifecycleState
    importance: Importance
    salience: Importance
    occurred_at: datetime
    last_accessed_at: datetime | None = None
    superseded_by_memory_id: Identifier | None = None
    protected_provenance: bool = Field(strict=True)


class MemoryRecordSet(ContractEnvelope):
    records: tuple[MemoryRecordView, ...]

    @model_validator(mode="after")
    def unique_records(self):
        if len({record.memory_id for record in self.records}) != len(self.records):
            raise ValueError("records must contain unique memory_id values")
        return self


class CategoryRetentionRule(ContractValue):
    category: MemoryCategory
    retrieval_ttl_hours: Annotated[int | None, Field(ge=1, le=100000)] = None
    archive_after_hours: Annotated[int | None, Field(ge=1, le=100000)] = None
    delete_after_hours: Annotated[int | None, Field(ge=1, le=100000)] = None
    salience_decay_per_day: Annotated[float, Field(strict=True, allow_inf_nan=False, ge=0, le=1)] = 0

    @model_validator(mode="after")
    def ordered_retention(self):
        values = [value for value in (self.retrieval_ttl_hours, self.archive_after_hours, self.delete_after_hours) if value is not None]
        if values != sorted(values):
            raise ValueError("retention windows must be ordered retrieval <= archive <= delete")
        return self


class RetentionPolicy(ContractEnvelope):
    policy: PolicyVersion
    default_retrieval_ttl_hours: Annotated[int | None, Field(ge=1, le=100000)] = None
    default_archive_after_hours: Annotated[int | None, Field(ge=1, le=100000)] = None
    default_delete_after_hours: Annotated[int | None, Field(ge=1, le=100000)] = None
    allow_deletion: bool = Field(strict=True)
    protect_authoritative_provenance: bool = Field(strict=True)
    rules: tuple[CategoryRetentionRule, ...] = ()

    @model_validator(mode="after")
    def unique_rules(self):
        if len({rule.category for rule in self.rules}) != len(self.rules):
            raise ValueError("rules must contain one entry per category")
        return self


class LifecycleMutation(ContractValue):
    memory_id: Identifier
    action: LifecycleAction
    from_lifecycle: MemoryLifecycleState
    to_lifecycle: MemoryLifecycleState
    from_salience: Importance
    to_salience: Importance
    reason: Identifier


class LifecyclePlan(ContractEnvelope):
    reviewed_at: datetime
    policy: PolicyVersion
    mutations: tuple[LifecycleMutation, ...]

    @model_validator(mode="after")
    def unique_mutations(self):
        if len({mutation.memory_id for mutation in self.mutations}) != len(self.mutations):
            raise ValueError("mutations must contain one action per memory")
        return self


LifecycleReviewResult: TypeAlias = LifecyclePlan | DomainError


class ReviewMemoryLifecycle(Protocol):
    def __call__(self, records: MemoryRecordSet, now: datetime, policy: RetentionPolicy) -> LifecycleReviewResult: ...


def review(
    records: MemoryRecordSet,
    now: datetime,
    policy: RetentionPolicy,
    *,
    record_id: Identifier,
) -> LifecycleReviewResult:
    if now.utcoffset() is None:
        return _error(records, policy, "Lifecycle review time must include a timezone.")
    evidence_error = _validate_evidence(records, policy)
    if evidence_error is not None:
        return evidence_error

    mutations = tuple(_mutation(record, now, policy) for record in records.records)
    return LifecyclePlan(
        schema_version=records.schema_version,
        record_id=record_id,
        trace_id=records.trace_id,
        causation_id=records.record_id,
        game_id=records.game_id,
        timeline_id=records.timeline_id,
        npc_id=records.npc_id,
        actor_id=records.actor_id,
        target_id=records.target_id,
        created_at=now,
        source_ids=(records.record_id, policy.record_id),
        policy_versions=(
            *tuple(version for version in records.policy_versions if version.policy_id != policy.policy.policy_id),
            policy.policy,
        ),
        reviewed_at=now,
        policy=policy.policy,
        mutations=mutations,
    )


def _mutation(record: MemoryRecordView, now: datetime, policy: RetentionPolicy) -> LifecycleMutation:
    age_hours = max((now - record.occurred_at).total_seconds() / 3600.0, 0.0)
    rule = next((candidate for candidate in policy.rules if candidate.category == record.category), None)
    retrieval_ttl = _choose(rule.retrieval_ttl_hours if rule else None, policy.default_retrieval_ttl_hours)
    archive_after = _choose(rule.archive_after_hours if rule else None, policy.default_archive_after_hours)
    delete_after = _choose(rule.delete_after_hours if rule else None, policy.default_delete_after_hours)
    decay = rule.salience_decay_per_day if rule else 0.0
    decayed_salience = max(0.0, record.salience - decay * (age_hours / 24.0))
    protected = record.protected_provenance or (
        policy.protect_authoritative_provenance and record.authority == EvidenceAuthority.AUTHORITATIVE
    )

    if record.lifecycle == MemoryLifecycleState.DELETED:
        return _make(record, LifecycleAction.KEEP, record.lifecycle, record.lifecycle, record.salience, record.salience, "memory:already_deleted")
    if protected and delete_after is not None and age_hours >= delete_after:
        target = MemoryLifecycleState.ARCHIVED if record.lifecycle != MemoryLifecycleState.ARCHIVED else record.lifecycle
        return _make(record, LifecycleAction.PROTECT, record.lifecycle, target, record.salience, decayed_salience, "memory:protected_provenance")
    if policy.allow_deletion and delete_after is not None and age_hours >= delete_after:
        return _make(record, LifecycleAction.DELETE, record.lifecycle, MemoryLifecycleState.DELETED, record.salience, decayed_salience, "memory:retention_delete")
    if archive_after is not None and age_hours >= archive_after:
        return _make(record, LifecycleAction.ARCHIVE, record.lifecycle, MemoryLifecycleState.ARCHIVED, record.salience, decayed_salience, "memory:retention_archive")
    if retrieval_ttl is not None and age_hours >= retrieval_ttl and record.lifecycle == MemoryLifecycleState.ACTIVE:
        return _make(record, LifecycleAction.EXPIRE_FOR_RETRIEVAL, record.lifecycle, MemoryLifecycleState.RETRIEVAL_EXPIRED, record.salience, decayed_salience, "memory:retrieval_expired")
    if decayed_salience != record.salience:
        return _make(record, LifecycleAction.DECAY_SALIENCE, record.lifecycle, record.lifecycle, record.salience, decayed_salience, "memory:salience_decay")
    return _make(record, LifecycleAction.KEEP, record.lifecycle, record.lifecycle, record.salience, record.salience, "memory:retained")


def _make(
    record: MemoryRecordView,
    action: LifecycleAction,
    from_lifecycle: MemoryLifecycleState,
    to_lifecycle: MemoryLifecycleState,
    from_salience: float,
    to_salience: float,
    reason: Identifier,
) -> LifecycleMutation:
    return LifecycleMutation(
        memory_id=record.memory_id,
        action=action,
        from_lifecycle=from_lifecycle,
        to_lifecycle=to_lifecycle,
        from_salience=from_salience,
        to_salience=to_salience,
        reason=reason,
    )


def _choose(primary: int | None, fallback: int | None) -> int | None:
    return primary if primary is not None else fallback


def _validate_evidence(records: MemoryRecordSet, policy: RetentionPolicy) -> DomainError | None:
    if records.game_id != policy.game_id or records.timeline_id != policy.timeline_id or records.npc_id != policy.npc_id:
        return _error(records, policy, "Lifecycle policy evidence is mismatched.")
    versions = {version.policy_id: version.version for version in records.policy_versions}
    if versions.get(policy.policy.policy_id) != policy.policy.version:
        return _error(records, policy, "Lifecycle policy version is not present in records.")
    return None


def _error(records: MemoryRecordSet, policy: RetentionPolicy, message: str) -> DomainError:
    return DomainError(
        code=ErrorCode.INVALID_CONTRACT,
        stage="memory.lifecycle",
        retryable=False,
        source_ids=(records.record_id, policy.record_id),
        public_message=message,
    )
