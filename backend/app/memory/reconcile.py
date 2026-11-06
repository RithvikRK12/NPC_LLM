"""Pure memory reconciliation handoffs and planning."""

from datetime import datetime
from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion


MemoryText = Annotated[str, Field(strict=True, min_length=1, max_length=2000)]
Confidence = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=0, le=1)]


class EpistemicStatus(str, Enum):
    FACT = "fact"
    CLAIM = "claim"
    INTERPRETATION = "interpretation"
    RETRACTION = "retraction"


class EvidenceAuthority(str, Enum):
    AUTHORITATIVE = "authoritative"
    OBSERVED = "observed"
    REPORTED = "reported"
    INFERRED = "inferred"


class ReconciliationAction(str, Enum):
    RETAIN = "retain"
    LINK_CORRECTION = "link_correction"
    SUPERSEDE = "supersede"
    KEEP_CONFLICT = "keep_conflict"
    MARK_RETRACTED = "mark_retracted"


class MemoryRecord(ContractEnvelope):
    memory_id: Identifier
    subject_id: Identifier
    predicate: Identifier
    object_id: Identifier | None = None
    object_text: MemoryText | None = None
    status: EpistemicStatus
    authority: EvidenceAuthority
    confidence: Confidence
    occurred_at: datetime

    @model_validator(mode="after")
    def object_identity(self):
        if self.object_id is None and self.object_text is None:
            raise ValueError("memory object_id or object_text is required")
        return self


class RelatedRecords(ContractEnvelope):
    records: tuple[MemoryRecord, ...]

    @model_validator(mode="after")
    def unique_records(self):
        if len({record.memory_id for record in self.records}) != len(self.records):
            raise ValueError("records must contain unique memory_id values")
        return self


class ReconciliationPolicy(ContractEnvelope):
    policy: PolicyVersion
    authoritative_statuses: tuple[EpistemicStatus, ...]
    allow_claim_consolidation: bool = Field(strict=True)

    @model_validator(mode="after")
    def unique_authoritative_statuses(self):
        if len(set(self.authoritative_statuses)) != len(self.authoritative_statuses):
            raise ValueError("authoritative_statuses must be unique")
        return self


class MemoryLink(ContractValue):
    source_memory_id: Identifier
    target_memory_id: Identifier
    action: ReconciliationAction
    reason: Identifier


class ReconciliationPlan(ContractEnvelope):
    new_memory_id: Identifier
    policy: PolicyVersion
    retain_memory_ids: tuple[Identifier, ...]
    links: tuple[MemoryLink, ...]

    @model_validator(mode="after")
    def unique_retained_ids(self):
        if len(set(self.retain_memory_ids)) != len(self.retain_memory_ids):
            raise ValueError("retain_memory_ids must be unique")
        return self


ReconciliationResult: TypeAlias = ReconciliationPlan | DomainError


class Reconcile(Protocol):
    def __call__(
        self,
        new_record: MemoryRecord,
        related: RelatedRecords,
        policy: ReconciliationPolicy,
    ) -> ReconciliationResult: ...


def reconcile(
    new_record: MemoryRecord,
    related: RelatedRecords,
    policy: ReconciliationPolicy,
    *,
    record_id: Identifier,
    created_at: datetime | str | None = None,
) -> ReconciliationResult:
    evidence_error = _validate_evidence(new_record, related, policy)
    if evidence_error is not None:
        return evidence_error

    retain_ids = [record.memory_id for record in related.records]
    links: list[MemoryLink] = []
    for record in related.records:
        if _same_claim(new_record, record):
            if new_record.status == EpistemicStatus.RETRACTION:
                links.append(_link(new_record, record, ReconciliationAction.MARK_RETRACTED, "memory:retraction"))
            elif new_record.authority == EvidenceAuthority.AUTHORITATIVE and record.authority != EvidenceAuthority.AUTHORITATIVE:
                links.append(_link(new_record, record, ReconciliationAction.SUPERSEDE, "memory:authoritative_correction"))
            elif new_record.object_id != record.object_id or new_record.object_text != record.object_text:
                links.append(_link(new_record, record, ReconciliationAction.KEEP_CONFLICT, "memory:conflicting_evidence"))
            elif policy.allow_claim_consolidation and new_record.status == record.status:
                links.append(_link(new_record, record, ReconciliationAction.LINK_CORRECTION, "memory:duplicate_evidence"))
            else:
                links.append(_link(new_record, record, ReconciliationAction.RETAIN, "memory:unresolved_claim"))

    return ReconciliationPlan(
        schema_version=new_record.schema_version,
        record_id=record_id,
        trace_id=new_record.trace_id,
        causation_id=new_record.record_id,
        game_id=new_record.game_id,
        timeline_id=new_record.timeline_id,
        npc_id=new_record.npc_id,
        actor_id=new_record.actor_id,
        target_id=new_record.target_id,
        created_at=created_at or new_record.created_at,
        source_ids=(new_record.record_id, related.record_id, policy.record_id),
        policy_versions=(
            *tuple(version for version in new_record.policy_versions if version.policy_id != policy.policy.policy_id),
            policy.policy,
        ),
        new_memory_id=new_record.memory_id,
        policy=policy.policy,
        retain_memory_ids=tuple(retain_ids),
        links=tuple(links),
    )


def _same_claim(left: MemoryRecord, right: MemoryRecord) -> bool:
    return left.subject_id == right.subject_id and left.predicate == right.predicate


def _link(new_record: MemoryRecord, existing: MemoryRecord, action: ReconciliationAction, reason: Identifier) -> MemoryLink:
    return MemoryLink(source_memory_id=new_record.memory_id, target_memory_id=existing.memory_id, action=action, reason=reason)


def _validate_evidence(new_record: MemoryRecord, related: RelatedRecords, policy: ReconciliationPolicy) -> DomainError | None:
    policy_versions = {version.policy_id: version.version for version in new_record.policy_versions}
    if new_record.game_id != related.game_id or new_record.timeline_id != related.timeline_id:
        return _error(new_record, related, policy, "Related memory evidence is mismatched.")
    if new_record.game_id != policy.game_id or new_record.timeline_id != policy.timeline_id:
        return _error(new_record, related, policy, "Reconciliation policy evidence is mismatched.")
    if policy_versions.get(policy.policy.policy_id) != policy.policy.version:
        return _error(new_record, related, policy, "Reconciliation policy evidence is mismatched.")
    if new_record.status in policy.authoritative_statuses and new_record.authority != EvidenceAuthority.AUTHORITATIVE:
        return _error(new_record, related, policy, "Authoritative status requires authoritative evidence.")
    return None


def _error(new_record: MemoryRecord, related: RelatedRecords, policy: ReconciliationPolicy, message: str) -> DomainError:
    return DomainError(
        code=ErrorCode.INVALID_CONTRACT,
        stage="memory.reconcile",
        retryable=False,
        source_ids=(new_record.record_id, related.record_id, policy.record_id),
        public_message=message,
    )
