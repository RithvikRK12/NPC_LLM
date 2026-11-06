"""Pure world interaction eligibility handoffs.

This module owns value shapes for target/range/visibility/operation checks.
It does not read live world state or trust reported client positions.
"""

from enum import Enum
from math import hypot
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion, Position, RevisionSet


InteractionText = Annotated[str, Field(strict=True, min_length=1, max_length=1000)]
Distance = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=0)]


class InteractionKind(str, Enum):
    SPEAK = "speak"
    REQUEST_ITEM = "request_item"
    GIVE_ITEM = "give_item"
    TRADE = "trade"
    ACCEPT_OFFER = "accept_offer"


class Visibility(str, Enum):
    DIRECT = "direct"
    INFORMED = "informed"
    REMEMBERED = "remembered"
    PRIVATE = "private"


class PredicateName(str, Enum):
    TARGET_EXISTS = "target_exists"
    ACTOR_POSITION_ACCEPTED = "actor_position_accepted"
    TARGET_POSITION_ACCEPTED = "target_position_accepted"
    IN_RANGE = "in_range"
    VISIBLE = "visible"
    OPERATION_PERMITTED = "operation_permitted"


class EligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"


class InteractionEvent(ContractEnvelope):
    """Untrusted client intent for a target interaction.

    reported_actor_position is diagnostic input only. Authoritative position
    evidence comes from WorldView records and must be checked later.
    """

    interaction_id: Identifier
    kind: InteractionKind
    expected_revisions: RevisionSet
    reported_actor_position: Position | None = None
    speech: InteractionText | None = None
    item_id: Identifier | None = None


class EntityView(ContractValue):
    entity_id: Identifier
    position: Position
    visibility: Visibility
    interaction_kinds: tuple[InteractionKind, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_interactions(self):
        if len(set(self.interaction_kinds)) != len(self.interaction_kinds):
            raise ValueError("interaction_kinds must be unique")
        return self


class WorldView(ContractEnvelope):
    """Authoritative local view for the eligibility boundary."""

    revisions: RevisionSet
    actor_position: Position
    targets: tuple[EntityView, ...]

    @model_validator(mode="after")
    def unique_targets(self):
        if len({target.entity_id for target in self.targets}) != len(self.targets):
            raise ValueError("targets must contain unique entity_id values")
        return self


class InteractionRule(ContractValue):
    kind: InteractionKind
    max_distance: Distance
    require_direct_visibility: bool = Field(strict=True)


class InteractionPolicy(ContractEnvelope):
    policy_id: Identifier
    version: Identifier
    rules: tuple[InteractionRule, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_rules(self):
        if len({rule.kind for rule in self.rules}) != len(self.rules):
            raise ValueError("rules must contain one entry per interaction kind")
        return self


class PredicateResult(ContractValue):
    name: PredicateName
    passed: bool = Field(strict=True)
    evidence_ids: tuple[Identifier, ...]


class EligibilityResult(ContractEnvelope):
    interaction_id: Identifier
    status: EligibilityStatus
    predicates: tuple[PredicateResult, ...] = Field(min_length=1)
    policy_id: Identifier
    policy_version: Identifier

    @model_validator(mode="after")
    def unique_predicates(self):
        if len({predicate.name for predicate in self.predicates}) != len(self.predicates):
            raise ValueError("predicates must be unique")
        return self


EligibilityCheckResult: TypeAlias = EligibilityResult | DomainError


class CheckEligibility(Protocol):
    def __call__(
        self,
        event: InteractionEvent,
        world: WorldView,
        policy: InteractionPolicy,
    ) -> EligibilityCheckResult: ...


PREDICATE_ORDER = (
    PredicateName.TARGET_EXISTS,
    PredicateName.ACTOR_POSITION_ACCEPTED,
    PredicateName.TARGET_POSITION_ACCEPTED,
    PredicateName.IN_RANGE,
    PredicateName.VISIBLE,
    PredicateName.OPERATION_PERMITTED,
)


def check_eligibility(
    event: InteractionEvent,
    world: WorldView,
    policy: InteractionPolicy,
) -> EligibilityCheckResult:
    """Evaluate local, authoritative world predicates for an interaction."""

    evidence_error = _validate_authoritative_evidence(event, world, policy)
    if evidence_error is not None:
        return evidence_error

    target = next((candidate for candidate in world.targets if candidate.entity_id == event.target_id), None)
    rule = next((candidate for candidate in policy.rules if candidate.kind == event.kind), None)

    target_exists = target is not None
    actor_position_accepted = True
    target_position_accepted = (
        target is not None
        and target.position.area_id == world.actor_position.area_id
        and target.position.spatial_revision == world.actor_position.spatial_revision
    )
    operation_permitted = target is not None and rule is not None and event.kind in target.interaction_kinds
    in_range = (
        target_position_accepted
        and rule is not None
        and _distance(world.actor_position, target.position) <= rule.max_distance
    )
    visible = (
        target_position_accepted
        and rule is not None
        and (
            target.visibility == Visibility.DIRECT
            if rule.require_direct_visibility
            else target.visibility != Visibility.PRIVATE
        )
    )

    predicate_values = {
        PredicateName.TARGET_EXISTS: (target_exists, (world.record_id,) if target_exists else ()),
        PredicateName.ACTOR_POSITION_ACCEPTED: (
            actor_position_accepted,
            (world.record_id,) if actor_position_accepted else (),
        ),
        PredicateName.TARGET_POSITION_ACCEPTED: (
            target_position_accepted,
            (world.record_id,) if target_position_accepted else (),
        ),
        PredicateName.IN_RANGE: (in_range, (world.record_id, policy.record_id) if in_range else ()),
        PredicateName.VISIBLE: (visible, (world.record_id,) if visible else ()),
        PredicateName.OPERATION_PERMITTED: (
            operation_permitted,
            (world.record_id, policy.record_id) if operation_permitted else (),
        ),
    }
    predicates = tuple(
        PredicateResult(name=name, passed=passed, evidence_ids=evidence_ids)
        for name in PREDICATE_ORDER
        for passed, evidence_ids in (predicate_values[name],)
    )
    status = EligibilityStatus.ELIGIBLE if all(predicate.passed for predicate in predicates) else EligibilityStatus.INELIGIBLE

    return EligibilityResult(
        schema_version=event.schema_version,
        record_id=f"eligibility-result:{event.interaction_id.split(':')[-1]}",
        trace_id=event.trace_id,
        causation_id=event.record_id,
        game_id=event.game_id,
        timeline_id=event.timeline_id,
        npc_id=event.npc_id,
        actor_id=event.actor_id,
        target_id=event.target_id,
        created_at=event.created_at,
        source_ids=(event.record_id, world.record_id, policy.record_id),
        policy_versions=(
            *tuple(item for item in event.policy_versions if item.policy_id != policy.policy_id),
            PolicyVersion(policy_id=policy.policy_id, version=policy.version),
        ),
        interaction_id=event.interaction_id,
        status=status,
        predicates=predicates,
        policy_id=policy.policy_id,
        policy_version=policy.version,
    )


def _distance(actor_position: Position, target_position: Position) -> float:
    return hypot(target_position.x - actor_position.x, target_position.y - actor_position.y)


def _validate_authoritative_evidence(
    event: InteractionEvent,
    world: WorldView,
    policy: InteractionPolicy,
) -> DomainError | None:
    if event.actor_id is None or event.target_id is None or world.actor_id is None or world.target_id is None:
        return _rejection(
            "Interaction evidence is incomplete.",
            (event.record_id, world.record_id),
        )
    if (
        event.game_id != world.game_id
        or event.timeline_id != world.timeline_id
        or event.npc_id != world.npc_id
        or event.actor_id != world.actor_id
        or event.target_id != world.target_id
    ):
        return _rejection(
            "Interaction evidence does not match authoritative world view.",
            (event.record_id, world.record_id),
        )
    event_policy_versions = {version.policy_id: version.version for version in event.policy_versions}
    if event.game_id != policy.game_id or event.timeline_id != policy.timeline_id or event_policy_versions.get(policy.policy_id) != policy.version:
        return _rejection(
            "Interaction policy evidence is missing or mismatched.",
            (event.record_id, policy.record_id),
        )
    return None


def _rejection(message: str, source_ids: tuple[Identifier, ...]) -> DomainError:
    return DomainError(
        code=ErrorCode.INVALID_CONTRACT,
        stage="domain.world.eligibility",
        retryable=False,
        source_ids=source_ids,
        public_message=message,
    )
