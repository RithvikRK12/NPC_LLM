"""Pure safe fallback candidate selection."""

from enum import Enum
from typing import Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion


class FailureKind(str, Enum):
    MODEL_UNAVAILABLE = "model_unavailable"
    MODEL_INVALID_OUTPUT = "model_invalid_output"
    ROLE_DENIED = "role_denied"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    PATH_BLOCKED = "path_blocked"


class FallbackAction(str, Enum):
    SPEAK = "speak"
    IDLE = "idle"
    FACE_TARGET = "face_target"
    CRAFT_ITEM = "craft_item"
    GRANT_REWARD = "grant_reward"


class FallbackStatus(str, Enum):
    SELECTED = "selected"
    REJECTED = "rejected"


class FailureContext(ContractEnvelope):
    failure_id: Identifier
    kind: FailureKind
    failed_stage: Identifier
    allowed_target_ids: tuple[Identifier, ...]
    fallback_depth: int = Field(strict=True, ge=0)
    max_fallback_depth: int = Field(strict=True, ge=0)

    @model_validator(mode="after")
    def unique_targets_and_depth(self):
        if len(set(self.allowed_target_ids)) != len(self.allowed_target_ids):
            raise ValueError("allowed_target_ids must be unique")
        if self.fallback_depth > self.max_fallback_depth:
            raise ValueError("fallback_depth cannot exceed max_fallback_depth")
        return self


class SafeFallbackOption(ContractValue):
    fallback_id: Identifier
    failure_kinds: tuple[FailureKind, ...]
    action: FallbackAction
    target_id: Identifier | None = None
    public_message: str = Field(strict=True, min_length=1, max_length=300)
    effect_ids: tuple[Identifier, ...] = ()
    required_evidence_ids: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def unique_values(self):
        for field_name in ("failure_kinds", "effect_ids", "required_evidence_ids"):
            values = getattr(self, field_name)
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} must be unique")
        return self


class SafeBehaviorPolicy(ContractEnvelope):
    policy: PolicyVersion
    role_allowed_actions: tuple[FallbackAction, ...]
    options: tuple[SafeFallbackOption, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_policy_values(self):
        if len(set(self.role_allowed_actions)) != len(self.role_allowed_actions):
            raise ValueError("role_allowed_actions must be unique")
        if len({option.fallback_id for option in self.options}) != len(self.options):
            raise ValueError("options must be unique")
        return self


class FallbackCandidate(ContractEnvelope):
    failure_id: Identifier
    fallback_id: Identifier
    policy: PolicyVersion
    status: FallbackStatus
    action: FallbackAction
    target_id: Identifier | None = None
    public_message: str = Field(strict=True, min_length=1, max_length=300)
    effect_ids: tuple[Identifier, ...]
    evidence_ids: tuple[Identifier, ...]
    fallback_depth: int = Field(strict=True, ge=0)

    @model_validator(mode="after")
    def zero_effect_and_unique_evidence(self):
        if self.effect_ids:
            raise ValueError("fallback candidates must be zero-effect")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")
        return self


FallbackResult: TypeAlias = FallbackCandidate | DomainError


class BuildFallback(Protocol):
    def __call__(self, context: FailureContext, policy: SafeBehaviorPolicy) -> FallbackResult: ...


def build(
    context: FailureContext,
    policy: SafeBehaviorPolicy,
    *,
    record_id: Identifier,
    created_at=None,
) -> FallbackResult:
    evidence_error = _validate_evidence(context, policy)
    if evidence_error is not None:
        return evidence_error
    if context.fallback_depth >= context.max_fallback_depth:
        return _error(context, policy, ErrorCode.INVALID_CONTRACT, "Fallback chain limit has been reached.")

    for option in policy.options:
        if context.kind not in option.failure_kinds:
            continue
        option_error = _validate_option(context, policy, option)
        if option_error is None:
            return FallbackCandidate(
                schema_version=context.schema_version,
                record_id=record_id,
                trace_id=context.trace_id,
                causation_id=context.record_id,
                game_id=context.game_id,
                timeline_id=context.timeline_id,
                npc_id=context.npc_id,
                actor_id=context.actor_id,
                target_id=option.target_id,
                created_at=created_at or context.created_at,
                source_ids=(context.record_id, policy.record_id),
                policy_versions=(
                    *tuple(version for version in context.policy_versions if version.policy_id != policy.policy.policy_id),
                    policy.policy,
                ),
                failure_id=context.failure_id,
                fallback_id=option.fallback_id,
                policy=policy.policy,
                status=FallbackStatus.SELECTED,
                action=option.action,
                public_message=option.public_message,
                effect_ids=(),
                evidence_ids=option.required_evidence_ids,
                fallback_depth=context.fallback_depth + 1,
            )
        return option_error
    return _error(context, policy, ErrorCode.UNSUPPORTED_CAPABILITY, "No declared safe fallback is available for this failure.")


def _validate_evidence(context: FailureContext, policy: SafeBehaviorPolicy) -> DomainError | None:
    if context.game_id != policy.game_id or context.timeline_id != policy.timeline_id or context.npc_id != policy.npc_id:
        return _error(context, policy, ErrorCode.INVALID_CONTRACT, "Safe fallback policy evidence is mismatched.")
    policy_versions = {version.policy_id: version.version for version in context.policy_versions}
    if policy_versions.get(policy.policy.policy_id) != policy.policy.version:
        return _error(context, policy, ErrorCode.INVALID_CONTRACT, "Safe fallback policy version is not present in failure context.")
    return None


def _validate_option(context: FailureContext, policy: SafeBehaviorPolicy, option: SafeFallbackOption) -> DomainError | None:
    if option.action not in policy.role_allowed_actions:
        return _error(context, policy, ErrorCode.UNSUPPORTED_CAPABILITY, "Declared fallback action is not role-compatible.")
    if option.action in (FallbackAction.CRAFT_ITEM, FallbackAction.GRANT_REWARD):
        return _error(context, policy, ErrorCode.UNSUPPORTED_CAPABILITY, "Declared fallback action is not zero-effect safe.")
    if option.effect_ids:
        return _error(context, policy, ErrorCode.INVALID_CONTRACT, "Declared fallback must not carry effects.")
    if option.target_id is not None and option.target_id not in context.allowed_target_ids:
        return _error(context, policy, ErrorCode.UNGROUNDED_REFERENCE, "Declared fallback target is not available in trusted evidence.")
    if any(evidence_id not in context.source_ids and evidence_id != context.record_id for evidence_id in option.required_evidence_ids):
        return _error(context, policy, ErrorCode.UNGROUNDED_REFERENCE, "Declared fallback evidence is not available in trusted context.")
    return None


def _error(context: FailureContext, policy: SafeBehaviorPolicy, code: ErrorCode, message: str) -> DomainError:
    return DomainError(
        code=code,
        stage="control.fallback",
        retryable=False,
        source_ids=(context.record_id, policy.record_id),
        public_message=message,
    )

