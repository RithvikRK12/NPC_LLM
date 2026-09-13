"""T01 world interaction eligibility handoffs.

This module owns value shapes for target/range/visibility/operation checks.
It does not read live world state, trust reported client positions, or decide
eligibility yet; T02/T03 own predicate evaluation and forged-evidence handling.
"""

from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, Identifier, Position, RevisionSet


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
