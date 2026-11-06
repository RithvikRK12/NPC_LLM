"""Pure quest recovery offer selection and grant planning."""

from datetime import datetime
from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion


Quantity = Annotated[int, Field(strict=True, ge=1, le=999)]


class BlockedStep(str, Enum):
    MATERIAL_ACCESS = "material_access"
    CRAFTING_ACCESS = "crafting_access"


class OfferKind(str, Enum):
    TRADE = "trade"
    FAVOUR = "favour"


class OfferStatus(str, Enum):
    OFFERED = "offered"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    INVALID = "invalid"


class CompletionEvidenceKind(str, Enum):
    VERIFIED_EVENT = "verified_event"
    PLAYER_CLAIM = "player_claim"


class QuestBlocker(ContractEnvelope):
    blocker_id: Identifier
    quest_run_id: Identifier
    blocked_step: BlockedStep
    refusing_npc_id: Identifier
    player_id: Identifier
    discretionary: bool = Field(strict=True)


class InventoryCost(ContractValue):
    item_id: Identifier
    quantity: Quantity


class RecoveryRoute(ContractValue):
    route_id: Identifier
    version: Identifier
    kind: OfferKind
    npc_id: Identifier
    blocked_step: BlockedStep
    costs: tuple[InventoryCost, ...] = ()
    required_available_item_ids: tuple[Identifier, ...] = ()
    completion_event_type: Identifier
    grant_effect_id: Identifier
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def unique_route_values(self):
        if len({cost.item_id for cost in self.costs}) != len(self.costs):
            raise ValueError("costs must be unique by item_id")
        if len(set(self.required_available_item_ids)) != len(self.required_available_item_ids):
            raise ValueError("required_available_item_ids must be unique")
        return self


class CompletionEvidence(ContractValue):
    evidence_id: Identifier
    kind: CompletionEvidenceKind
    event_type: Identifier
    actor_id: Identifier
    target_id: Identifier


class RecoveryWorldView(ContractEnvelope):
    available_item_ids: tuple[Identifier, ...]
    consumed_offer_ids: tuple[Identifier, ...] = ()
    completed_offer_ids: tuple[Identifier, ...] = ()
    completion_evidence: tuple[CompletionEvidence, ...] = ()

    @model_validator(mode="after")
    def unique_world_values(self):
        for field_name in ("available_item_ids", "consumed_offer_ids", "completed_offer_ids"):
            values = getattr(self, field_name)
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} must be unique")
        if len({evidence.evidence_id for evidence in self.completion_evidence}) != len(self.completion_evidence):
            raise ValueError("completion_evidence must be unique")
        return self


class RecoveryPolicy(ContractEnvelope):
    policy: PolicyVersion
    routes: tuple[RecoveryRoute, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_routes(self):
        if len({route.route_id for route in self.routes}) != len(self.routes):
            raise ValueError("routes must be unique")
        return self


class CooperationGrant(ContractValue):
    grant_id: Identifier
    quest_run_id: Identifier
    blocked_step: BlockedStep
    player_id: Identifier
    npc_id: Identifier
    source_offer_id: Identifier
    fulfilled: bool = Field(strict=True)


class RecoveryOffer(ContractValue):
    offer_id: Identifier
    route_id: Identifier
    route_version: Identifier
    kind: OfferKind
    status: OfferStatus
    npc_id: Identifier
    quest_run_id: Identifier
    blocked_step: BlockedStep
    costs: tuple[InventoryCost, ...]
    completion_event_type: Identifier
    grant: CooperationGrant
    expires_at: datetime | None = None


class RecoveryOfferSet(ContractEnvelope):
    blocker_id: Identifier
    policy: PolicyVersion
    offers: tuple[RecoveryOffer, ...]

    @model_validator(mode="after")
    def unique_offers(self):
        if len({offer.offer_id for offer in self.offers}) != len(self.offers):
            raise ValueError("offers must be unique")
        return self


RecoveryResult: TypeAlias = RecoveryOfferSet | DomainError


class SelectRecoveryOffers(Protocol):
    def __call__(self, blocker: QuestBlocker, world: RecoveryWorldView, policy: RecoveryPolicy) -> RecoveryResult: ...


def offers(
    blocker: QuestBlocker,
    world: RecoveryWorldView,
    policy: RecoveryPolicy,
    *,
    record_id: Identifier,
    created_at=None,
) -> RecoveryResult:
    evidence_error = _validate_evidence(blocker, world, policy)
    if evidence_error is not None:
        return evidence_error

    selected: list[RecoveryOffer] = []
    for route in policy.routes:
        route_error = _route_error(blocker, world, route)
        if route_error is None:
            selected.append(_offer(blocker, route, world))

    if not selected:
        return _error(blocker, world, policy, ErrorCode.NO_VIABLE_RECOVERY_ROUTE, "No viable recovery route is available.")

    return RecoveryOfferSet(
        schema_version=blocker.schema_version,
        record_id=record_id,
        trace_id=blocker.trace_id,
        causation_id=blocker.record_id,
        game_id=blocker.game_id,
        timeline_id=blocker.timeline_id,
        npc_id=blocker.npc_id,
        actor_id=blocker.actor_id,
        target_id=blocker.target_id,
        created_at=created_at or blocker.created_at,
        source_ids=(blocker.record_id, world.record_id, policy.record_id),
        policy_versions=(
            *tuple(version for version in blocker.policy_versions if version.policy_id != policy.policy.policy_id),
            policy.policy,
        ),
        blocker_id=blocker.blocker_id,
        policy=policy.policy,
        offers=tuple(selected),
    )


def _validate_evidence(blocker: QuestBlocker, world: RecoveryWorldView, policy: RecoveryPolicy) -> DomainError | None:
    if blocker.game_id != world.game_id or blocker.timeline_id != world.timeline_id:
        return _error(blocker, world, policy, ErrorCode.INVALID_CONTRACT, "Recovery world evidence is mismatched.")
    if blocker.game_id != policy.game_id or blocker.timeline_id != policy.timeline_id:
        return _error(blocker, world, policy, ErrorCode.INVALID_CONTRACT, "Recovery policy evidence is mismatched.")
    policy_versions = {version.policy_id: version.version for version in blocker.policy_versions}
    if policy_versions.get(policy.policy.policy_id) != policy.policy.version:
        return _error(blocker, world, policy, ErrorCode.INVALID_CONTRACT, "Recovery policy version is not present in blocker.")
    return None


def _route_error(blocker: QuestBlocker, world: RecoveryWorldView, route: RecoveryRoute) -> str | None:
    if route.npc_id != blocker.refusing_npc_id:
        return "wrong_npc"
    if route.blocked_step != blocker.blocked_step:
        return "wrong_step"
    offer_id = _offer_id(blocker, route)
    if offer_id in world.consumed_offer_ids or offer_id in world.completed_offer_ids:
        return "already_used"
    if route.expires_at is not None and route.expires_at <= blocker.created_at:
        return "expired"
    if any(item_id == blocker.blocked_step.value for item_id in route.required_available_item_ids):
        return "circular"
    available = set(world.available_item_ids)
    if not set(route.required_available_item_ids).issubset(available):
        return "missing_prerequisite"
    if route.kind == OfferKind.TRADE and not {cost.item_id for cost in route.costs}.issubset(available):
        return "missing_cost"
    return None


def _offer(blocker: QuestBlocker, route: RecoveryRoute, world: RecoveryWorldView) -> RecoveryOffer:
    offer_id = _offer_id(blocker, route)
    completed = _completion_evidence(blocker, route, world) is not None
    return RecoveryOffer(
        offer_id=offer_id,
        route_id=route.route_id,
        route_version=route.version,
        kind=route.kind,
        status=OfferStatus.COMPLETED if completed else OfferStatus.OFFERED,
        npc_id=route.npc_id,
        quest_run_id=blocker.quest_run_id,
        blocked_step=blocker.blocked_step,
        costs=route.costs,
        completion_event_type=route.completion_event_type,
        grant=CooperationGrant(
            grant_id=f"grant:{offer_id.split(':')[-1]}",
            quest_run_id=blocker.quest_run_id,
            blocked_step=blocker.blocked_step,
            player_id=blocker.player_id,
            npc_id=route.npc_id,
            source_offer_id=offer_id,
            fulfilled=False,
        ),
        expires_at=route.expires_at,
    )


def _completion_evidence(blocker: QuestBlocker, route: RecoveryRoute, world: RecoveryWorldView) -> CompletionEvidence | None:
    for evidence in world.completion_evidence:
        if (
            evidence.kind == CompletionEvidenceKind.VERIFIED_EVENT
            and evidence.event_type == route.completion_event_type
            and evidence.actor_id == blocker.player_id
            and evidence.target_id == route.npc_id
        ):
            return evidence
    return None


def _offer_id(blocker: QuestBlocker, route: RecoveryRoute) -> Identifier:
    return f"offer:{blocker.quest_run_id.split(':')[-1]}:{blocker.blocked_step.value}:{route.route_id.split(':')[-1]}"


def _error(blocker: QuestBlocker, world: RecoveryWorldView, policy: RecoveryPolicy, code: ErrorCode, message: str) -> DomainError:
    return DomainError(
        code=code,
        stage="domain.quest.recovery",
        retryable=False,
        source_ids=(blocker.record_id, world.record_id, policy.record_id),
        public_message=message,
    )

