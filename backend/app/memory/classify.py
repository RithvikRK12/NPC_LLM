"""Pure memory classification for approved conversations and verified events."""

from enum import Enum
import re
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion
from app.memory.reconcile import EpistemicStatus, EvidenceAuthority


MemoryText = Annotated[str, Field(strict=True, min_length=1, max_length=1200)]
Importance = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=0, le=1)]


class ClassificationSourceKind(str, Enum):
    APPROVED_CONVERSATION = "approved_conversation"
    VERIFIED_EVENT = "verified_event"
    REJECTED_OUTPUT = "rejected_output"
    PROVIDER_FAILURE = "provider_failure"


class VerifiedEventType(str, Enum):
    ITEM_TRANSFERRED = "item_transferred"
    QUEST_PROGRESS = "quest_progress"
    QUEST_COMPLETED = "quest_completed"


class MemoryCategory(str, Enum):
    ITEM_TRANSFER = "item_transfer"
    QUEST_PROGRESS = "quest_progress"
    QUEST_COMPLETION = "quest_completion"
    ITEM_REQUEST = "item_request"
    COMMITMENT = "commitment"
    PREFERENCE = "preference"
    PERSONAL_FACT = "personal_fact"
    ROUTINE = "routine"
    EXCLUDED = "excluded"


class ApprovedConversationOrEvent(ContractEnvelope):
    source_kind: ClassificationSourceKind
    player_text: MemoryText | None = None
    approved_dialogue: MemoryText | None = None
    verified_event_type: VerifiedEventType | None = None
    subject_id: Identifier | None = None
    predicate: Identifier | None = None
    object_id: Identifier | None = None
    object_text: MemoryText | None = None
    grounded: bool = Field(strict=True)

    @model_validator(mode="after")
    def source_shape(self):
        if self.source_kind == ClassificationSourceKind.VERIFIED_EVENT:
            if self.verified_event_type is None or self.subject_id is None or self.predicate is None:
                raise ValueError("verified event classification requires typed event fields")
        elif self.verified_event_type is not None:
            raise ValueError("only verified events carry verified_event_type")
        if self.source_kind == ClassificationSourceKind.APPROVED_CONVERSATION and self.player_text is None:
            raise ValueError("approved conversation requires player_text")
        return self


class ImportancePolicy(ContractEnvelope):
    policy: PolicyVersion
    minimum_importance: Importance
    authoritative_event_importance: Importance
    player_claim_importance: Importance
    request_change_importance: Importance
    routine_importance: Importance
    exclude_greetings: bool = Field(strict=True)


class MemoryDecision(ContractEnvelope):
    memory_id: Identifier | None
    category: MemoryCategory
    important: bool = Field(strict=True)
    importance: Importance
    reason: Identifier
    summary: MemoryText
    subject_id: Identifier | None
    predicate: Identifier | None
    object_id: Identifier | None = None
    object_text: MemoryText | None = None
    status: EpistemicStatus
    authority: EvidenceAuthority
    policy: PolicyVersion

    @model_validator(mode="after")
    def durable_memory_identity(self):
        if self.important and self.memory_id is None:
            raise ValueError("important memory decisions require memory_id")
        if self.status == EpistemicStatus.FACT and self.authority != EvidenceAuthority.AUTHORITATIVE:
            raise ValueError("fact memories require authoritative evidence")
        return self


ClassificationResult: TypeAlias = MemoryDecision | DomainError


class ClassifyMemory(Protocol):
    def __call__(self, source: ApprovedConversationOrEvent, policy: ImportancePolicy) -> ClassificationResult: ...


def classify(
    source: ApprovedConversationOrEvent,
    policy: ImportancePolicy,
    *,
    record_id: Identifier,
    memory_id: Identifier | None = None,
) -> ClassificationResult:
    evidence_error = _validate_evidence(source, policy)
    if evidence_error is not None:
        return evidence_error

    if source.source_kind in (ClassificationSourceKind.REJECTED_OUTPUT, ClassificationSourceKind.PROVIDER_FAILURE):
        return _decision(source, policy, record_id, None, MemoryCategory.EXCLUDED, 0.0, "memory:excluded_failed_output", "Rejected or failed model output is not durable memory.", None, None, None, None, EpistemicStatus.INTERPRETATION, EvidenceAuthority.INFERRED)

    if source.source_kind == ClassificationSourceKind.VERIFIED_EVENT:
        return _verified_event(source, policy, record_id, memory_id)

    text = (source.player_text or "").strip()
    if policy.exclude_greetings and _is_greeting(text):
        return _decision(source, policy, record_id, None, MemoryCategory.EXCLUDED, 0.0, "memory:excluded_greeting", "Greeting excluded from durable memory.", None, None, None, None, EpistemicStatus.INTERPRETATION, EvidenceAuthority.INFERRED)

    statement = _player_statement(text)
    if statement is not None:
        category, predicate = statement
        summary = f"Player stated (unverified {category.value}): {text[:430]}"
        return _decision(source, policy, record_id, memory_id, category, policy.player_claim_importance, "memory:player_claim", summary, source.actor_id, predicate, source.object_id, text, EpistemicStatus.CLAIM, EvidenceAuthority.REPORTED)

    return _decision(source, policy, record_id, None, MemoryCategory.ROUTINE, policy.routine_importance, "memory:routine", "No durable player statement or authoritative event.", None, None, None, None, EpistemicStatus.INTERPRETATION, EvidenceAuthority.INFERRED)


def _verified_event(source: ApprovedConversationOrEvent, policy: ImportancePolicy, record_id: Identifier, memory_id: Identifier | None) -> MemoryDecision:
    category = {
        VerifiedEventType.ITEM_TRANSFERRED: MemoryCategory.ITEM_TRANSFER,
        VerifiedEventType.QUEST_PROGRESS: MemoryCategory.QUEST_PROGRESS,
        VerifiedEventType.QUEST_COMPLETED: MemoryCategory.QUEST_COMPLETION,
    }[source.verified_event_type]
    summary = {
        VerifiedEventType.ITEM_TRANSFERRED: "Verified ownership-checked item transfer.",
        VerifiedEventType.QUEST_PROGRESS: "Authoritative quest progress changed.",
        VerifiedEventType.QUEST_COMPLETED: "Authoritative quest completion recorded.",
    }[source.verified_event_type]
    assert source.subject_id is not None and source.predicate is not None
    return _decision(source, policy, record_id, memory_id, category, policy.authoritative_event_importance, "memory:verified_event", summary, source.subject_id, source.predicate, source.object_id, source.object_text, EpistemicStatus.FACT, EvidenceAuthority.AUTHORITATIVE)


def _decision(
    source: ApprovedConversationOrEvent,
    policy: ImportancePolicy,
    record_id: Identifier,
    memory_id: Identifier | None,
    category: MemoryCategory,
    importance: float,
    reason: Identifier,
    summary: str,
    subject_id: Identifier | None,
    predicate: Identifier | None,
    object_id: Identifier | None,
    object_text: str | None,
    status: EpistemicStatus,
    authority: EvidenceAuthority,
) -> MemoryDecision:
    important = importance >= policy.minimum_importance
    return MemoryDecision(
        schema_version=source.schema_version,
        record_id=record_id,
        trace_id=source.trace_id,
        causation_id=source.record_id,
        game_id=source.game_id,
        timeline_id=source.timeline_id,
        npc_id=source.npc_id,
        actor_id=source.actor_id,
        target_id=source.target_id,
        created_at=source.created_at,
        source_ids=(source.record_id, policy.record_id),
        policy_versions=(
            *tuple(version for version in source.policy_versions if version.policy_id != policy.policy.policy_id),
            policy.policy,
        ),
        memory_id=memory_id if important else None,
        category=category,
        important=important,
        importance=importance,
        reason=reason,
        summary=summary,
        subject_id=subject_id,
        predicate=predicate,
        object_id=object_id,
        object_text=object_text,
        status=status,
        authority=authority,
        policy=policy.policy,
    )


def _validate_evidence(source: ApprovedConversationOrEvent, policy: ImportancePolicy) -> DomainError | None:
    if source.game_id != policy.game_id or source.timeline_id != policy.timeline_id or source.npc_id != policy.npc_id:
        return _error(source, policy, "Memory classification policy evidence is mismatched.")
    versions = {version.policy_id: version.version for version in source.policy_versions}
    if versions.get(policy.policy.policy_id) != policy.policy.version:
        return _error(source, policy, "Memory classification policy version is not present in source.")
    return None


def _is_greeting(text: str) -> bool:
    return bool(re.fullmatch(r"(?i)\s*(hi|hello|hey|yo|thanks|thank you|good morning|good evening)[!. ]*\s*", text))


def _player_statement(text: str) -> tuple[MemoryCategory, Identifier] | None:
    if "?" in text or re.match(r"(?i)^(what|why|how|when|where|can|could|would|do|is)\b", text):
        return None
    for category, predicate, pattern in (
        (MemoryCategory.COMMITMENT, "committed_to", r"\bi (?:promise|will help|will bring|will return|owe you)\b"),
        (MemoryCategory.PREFERENCE, "prefers", r"\bi (?:prefer|like|love|dislike|hate|am afraid of|don't like|do not like)\b"),
        (MemoryCategory.PERSONAL_FACT, "stated_personal_fact", r"\b(?:my name is|i live in|i come from|i work as)\b"),
    ):
        if re.search(pattern, text, re.I):
            return category, predicate
    return None


def _error(source: ApprovedConversationOrEvent, policy: ImportancePolicy, message: str) -> DomainError:
    return DomainError(
        code=ErrorCode.INVALID_CONTRACT,
        stage="memory.classify",
        retryable=False,
        source_ids=(source.record_id, policy.record_id),
        public_message=message,
    )
