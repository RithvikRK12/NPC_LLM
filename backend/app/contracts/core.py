"""C01 transport values; no persistence, HTTP or domain-policy dependencies.

IDs are opaque ASCII tokens (including authored names and UUID strings), never
coerced from numbers or display names. Collection bounds are supplied by owning
boundaries/policies; this package checks shape and structural lineage only.
Reference existence, decision knowledge scope and server authority require the
owning application to validate against its authoritative context.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator


Identifier = Annotated[str, Field(strict=True, min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")]
# JSON numbers are parsed as IEEE-754 doubles by Godot; keep revisions within
# the exact integer range shared by the Python and Godot fixture readers.
Revision = Annotated[int, Field(strict=True, ge=0, le=9007199254740991)]
FiniteCoordinate = Annotated[float, Field(strict=True, allow_inf_nan=False)]


def _version_type(value: object) -> object:
    if type(value) is not int:
        raise ValueError("schema_version must be an integer")
    return value


SchemaVersion = Annotated[Literal[1], BeforeValidator(_version_type)]
SUPPORTED_SCHEMA_VERSION = 1


class ContractValue(BaseModel):
    """Validated immutable value; nested collections are tuples of frozen values.

    Construct through validation (including model_validate_json at transport
    boundaries). Pydantic's model_construct/model_copy(update=...) are trusted,
    unvalidated escape hatches and must not decode external values.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True, revalidate_instances="always")


class PolicyVersion(ContractValue):
    policy_id: Identifier
    version: Identifier


class ContractEnvelope(ContractValue):
    """Required provenance for persistent/transported handoffs.

    Source IDs must be present and nonempty. Policy versions must be explicit
    but may be empty when no policy has yet been applied. The direct
    causation ID must appear in source_ids. Bootstrap records therefore need an
    explicit originating event, rather than fabricated empty provenance.
    Aware ISO timestamps are normalized to UTC; naive times and epoch numbers
    are rejected. Entity ID resolution remains an application responsibility.
    """

    schema_version: SchemaVersion
    record_id: Identifier
    trace_id: Identifier
    causation_id: Identifier
    game_id: Identifier
    timeline_id: Identifier
    npc_id: Identifier
    actor_id: Identifier | None = None
    target_id: Identifier | None = None
    created_at: datetime
    source_ids: tuple[Identifier, ...] = Field(min_length=1)
    policy_versions: tuple[PolicyVersion, ...]

    @field_validator("created_at", mode="before")
    @classmethod
    def timestamp_shape(cls, value: object) -> object:
        if not isinstance(value, (datetime, str)):
            raise ValueError("created_at must be an aware datetime or ISO timestamp")
        # Numeric timestamp strings are also excluded.
        if isinstance(value, str) and "T" not in value:
            raise ValueError("created_at must be an ISO timestamp containing T")
        return value

    @field_validator("created_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("created_at must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def lineage(self) -> "ContractEnvelope":
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("source_ids must be unique")
        if self.causation_id not in self.source_ids:
            raise ValueError("causation_id must be included in source_ids")
        policy_ids = [policy.policy_id for policy in self.policy_versions]
        if len(set(policy_ids)) != len(policy_ids):
            raise ValueError("policy_versions must contain one version per policy_id")
        return self


class Position(ContractValue):
    """Accepted 2D Godot world-unit coordinates, separate from raw reports."""

    x: FiniteCoordinate
    y: FiniteCoordinate
    area_id: Identifier
    spatial_revision: Revision


class ScopedRevision(ContractValue):
    """Revision of one relevant aggregate, not a global world revision.

    scope_id denotes a quest run, inventory owner, relationship aggregate,
    policy record or controller according to its RevisionSet collection.
    """

    scope_id: Identifier
    revision: Revision


class RevisionSet(ContractValue):
    """Expected revisions for a single NPC and only its decision dependencies.

    Empty tuples mean that category is irrelevant, not revision zero. Before
    approval approved_npc_state_revision is absent. An approval records it
    separately from the base revision; equality permits a no-change approval.
    Spatial predicates use fresh Position values at execution boundaries.
    """

    npc_id: Identifier
    base_npc_state_revision: Revision
    approved_npc_state_revision: Revision | None = None
    quest: tuple[ScopedRevision, ...] = ()
    inventory: tuple[ScopedRevision, ...] = ()
    relationship: tuple[ScopedRevision, ...] = ()
    policy: tuple[ScopedRevision, ...] = ()
    controller: tuple[ScopedRevision, ...] = ()

    @model_validator(mode="after")
    def consistent_revisions(self) -> "RevisionSet":
        if self.approved_npc_state_revision is not None and self.approved_npc_state_revision < self.base_npc_state_revision:
            raise ValueError("approved NPC state revision cannot precede base revision")
        for category in ("quest", "inventory", "relationship", "policy", "controller"):
            references = getattr(self, category)
            if len({ref.scope_id for ref in references}) != len(references):
                raise ValueError(f"{category} contains duplicate scope_id references")
        return self


class ErrorCode(str, Enum):
    INVALID_CONTRACT = "INVALID_CONTRACT"
    UNKNOWN_ENUM = "UNKNOWN_ENUM"
    UNGROUNDED_REFERENCE = "UNGROUNDED_REFERENCE"
    KNOWLEDGE_SCOPE_VIOLATION = "KNOWLEDGE_SCOPE_VIOLATION"
    ROLE_DENIED = "ROLE_DENIED"
    BEHAVIOUR_REFUSED = "BEHAVIOUR_REFUSED"
    NO_VIABLE_RECOVERY_ROUTE = "NO_VIABLE_RECOVERY_ROUTE"
    STALE_REVISION = "STALE_REVISION"
    OLD_TIMELINE = "OLD_TIMELINE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_INVALID_OUTPUT = "MODEL_INVALID_OUTPUT"
    EMBEDDING_UNAVAILABLE = "EMBEDDING_UNAVAILABLE"
    INDEX_NOT_READY = "INDEX_NOT_READY"
    PATH_BLOCKED = "PATH_BLOCKED"
    UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"
    EFFECT_PRECONDITION_FAILED = "EFFECT_PRECONDITION_FAILED"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    POLICY_INVALID = "POLICY_INVALID"
    POLICY_INCONSISTENT = "POLICY_INCONSISTENT"


class DomainError(ContractValue):
    """Normal rejection value. Callers supply authored, safe public text.

    A transported result owns the envelope; errors can describe invalid or
    missing envelopes without fabricating lineage. source_ids is required but
    may be empty when no valid source reference was available.
    Raw exceptions, private snapshots and credential fields are not accepted;
    free-text content still requires redaction by its originating boundary.
    """

    code: ErrorCode
    stage: Identifier
    retryable: Annotated[bool, Field(strict=True)]
    source_ids: tuple[Identifier, ...]
    public_message: Annotated[str, Field(strict=True, min_length=1)]

    @field_validator("public_message")
    @classmethod
    def nonblank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("public_message must not be blank")
        return value
