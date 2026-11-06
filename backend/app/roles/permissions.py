"""Pure role permission evaluation."""

from enum import Enum
from typing import Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion


class RoleAction(str, Enum):
    SPEAK = "speak"
    REQUEST_MATERIALS = "request_materials"
    CRAFT_ITEM = "craft_item"
    REFUSE = "refuse"
    ATTACK = "attack"
    DECLARE_WAR = "declare_war"


class PermissionStatus(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"


class PermissionReason(str, Enum):
    ALLOWED = "role.permission:allowed"
    UNKNOWN_ROLE = "role.permission:unknown_role"
    ACTION_DENIED = "role.permission:action_denied"
    ACTION_NOT_ALLOWED = "role.permission:action_not_allowed"
    TARGET_DENIED = "role.permission:target_denied"
    MISSING_WORKSHOP = "role.permission:missing_workshop"
    MISSING_MATERIALS = "role.permission:missing_materials"
    ACTIVE_GRANT = "role.permission:active_grant"


class RoleProposal(ContractEnvelope):
    proposal_id: Identifier
    action: RoleAction
    target_id: Identifier | None = None
    required_material_ids: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def unique_materials(self):
        if len(set(self.required_material_ids)) != len(self.required_material_ids):
            raise ValueError("required_material_ids must be unique")
        return self


class WorkshopView(ContractValue):
    workshop_id: Identifier
    available: bool = Field(strict=True)


class CooperationGrantView(ContractValue):
    grant_id: Identifier
    action: RoleAction
    target_id: Identifier | None = None


class RoleWorldView(ContractEnvelope):
    entity_ids: tuple[Identifier, ...]
    workshops: tuple[WorkshopView, ...]
    available_material_ids: tuple[Identifier, ...]
    active_grants: tuple[CooperationGrantView, ...] = ()

    @model_validator(mode="after")
    def unique_world_refs(self):
        for field_name in ("entity_ids", "available_material_ids"):
            values = getattr(self, field_name)
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} must be unique")
        if len({workshop.workshop_id for workshop in self.workshops}) != len(self.workshops):
            raise ValueError("workshops must be unique")
        if len({grant.grant_id for grant in self.active_grants}) != len(self.active_grants):
            raise ValueError("active_grants must be unique")
        return self


class RoleProfile(ContractEnvelope):
    profile: PolicyVersion
    role_id: Identifier
    known_role_ids: tuple[Identifier, ...]
    peaceful: bool = Field(strict=True)
    allowed_actions: tuple[RoleAction, ...]
    denied_actions: tuple[RoleAction, ...]
    allowed_target_ids: tuple[Identifier, ...]
    workshop_required_actions: tuple[RoleAction, ...] = ()
    material_required_actions: tuple[RoleAction, ...] = ()
    duties: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def unique_profile_values(self):
        for field_name in (
            "known_role_ids",
            "allowed_actions",
            "denied_actions",
            "allowed_target_ids",
            "workshop_required_actions",
            "material_required_actions",
            "duties",
        ):
            values = getattr(self, field_name)
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} must be unique")
        return self


class RolePermission(ContractEnvelope):
    proposal_id: Identifier
    profile: PolicyVersion
    role_id: Identifier
    status: PermissionStatus
    action: RoleAction
    target_id: Identifier | None = None
    reasons: tuple[PermissionReason, ...] = Field(min_length=1)
    grant_ids: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def unique_values(self):
        if len(set(self.reasons)) != len(self.reasons):
            raise ValueError("reasons must be unique")
        if len(set(self.grant_ids)) != len(self.grant_ids):
            raise ValueError("grant_ids must be unique")
        return self


RolePermissionResult: TypeAlias = RolePermission | DomainError


class EvaluateRolePermission(Protocol):
    def __call__(self, proposal: RoleProposal, world: RoleWorldView, profile: RoleProfile) -> RolePermissionResult: ...


def evaluate(
    proposal: RoleProposal,
    world: RoleWorldView,
    profile: RoleProfile,
    *,
    record_id: Identifier,
    created_at=None,
) -> RolePermissionResult:
    evidence_error = _validate_evidence(proposal, world, profile)
    if evidence_error is not None:
        return evidence_error

    grant_ids = tuple(
        grant.grant_id
        for grant in world.active_grants
        if grant.action == proposal.action and (grant.target_id is None or grant.target_id == proposal.target_id)
    )
    denial = _denial_reason(proposal, world, profile, grant_ids)
    status = PermissionStatus.DENIED if denial is not None else PermissionStatus.ALLOWED
    reasons = (denial,) if denial is not None else (PermissionReason.ALLOWED,)

    return RolePermission(
        schema_version=proposal.schema_version,
        record_id=record_id,
        trace_id=proposal.trace_id,
        causation_id=proposal.record_id,
        game_id=proposal.game_id,
        timeline_id=proposal.timeline_id,
        npc_id=proposal.npc_id,
        actor_id=proposal.actor_id,
        target_id=proposal.target_id,
        created_at=created_at or proposal.created_at,
        source_ids=(proposal.record_id, world.record_id, profile.record_id),
        policy_versions=(
            *tuple(version for version in proposal.policy_versions if version.policy_id != profile.profile.policy_id),
            profile.profile,
        ),
        proposal_id=proposal.proposal_id,
        profile=profile.profile,
        role_id=profile.role_id,
        status=status,
        action=proposal.action,
        reasons=reasons,
        grant_ids=grant_ids,
    )


def _validate_evidence(proposal: RoleProposal, world: RoleWorldView, profile: RoleProfile) -> DomainError | None:
    if proposal.game_id != world.game_id or proposal.timeline_id != world.timeline_id:
        return _error(proposal, world, profile, "Role world evidence is mismatched.")
    if proposal.game_id != profile.game_id or proposal.timeline_id != profile.timeline_id:
        return _error(proposal, world, profile, "Role profile evidence is mismatched.")
    policy_versions = {version.policy_id: version.version for version in proposal.policy_versions}
    if policy_versions.get(profile.profile.policy_id) != profile.profile.version:
        return _error(proposal, world, profile, "Role profile version is not present in proposal.")
    return None


def _denial_reason(
    proposal: RoleProposal,
    world: RoleWorldView,
    profile: RoleProfile,
    grant_ids: tuple[Identifier, ...],
) -> PermissionReason | None:
    if profile.role_id not in profile.known_role_ids:
        return PermissionReason.UNKNOWN_ROLE
    if profile.peaceful and proposal.action in (RoleAction.ATTACK, RoleAction.DECLARE_WAR):
        return PermissionReason.ACTION_DENIED
    if proposal.action in profile.denied_actions:
        return PermissionReason.ACTION_DENIED
    if proposal.action == RoleAction.REFUSE and grant_ids:
        return PermissionReason.ACTIVE_GRANT
    if proposal.action not in profile.allowed_actions:
        return PermissionReason.ACTION_NOT_ALLOWED
    if proposal.target_id is not None and proposal.target_id not in profile.allowed_target_ids:
        return PermissionReason.TARGET_DENIED
    if proposal.action in profile.workshop_required_actions and not any(workshop.available for workshop in world.workshops):
        return PermissionReason.MISSING_WORKSHOP
    if proposal.action in profile.material_required_actions:
        materials = set(world.available_material_ids)
        if not set(proposal.required_material_ids).issubset(materials):
            return PermissionReason.MISSING_MATERIALS
    return None


def _error(proposal: RoleProposal, world: RoleWorldView, profile: RoleProfile, message: str) -> DomainError:
    return DomainError(
        code=ErrorCode.INVALID_CONTRACT,
        stage="roles.permissions",
        retryable=False,
        source_ids=(proposal.record_id, world.record_id, profile.record_id),
        public_message=message,
    )

