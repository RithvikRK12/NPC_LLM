"""Pure policy registry bundle validation."""

from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion
from app.contracts import EngineAction
from app.domain.fuzzy.membership import DimensionDefinition
from app.domain.quest.recovery import OfferKind


PolicyPayload = dict[str, object]


class PolicyKind(str, Enum):
    PROFILE = "profile"
    BOUNDS = "bounds"
    FUZZY_RULES = "fuzzy_rules"
    FALLBACKS = "fallbacks"
    MAPPINGS = "mappings"
    RECOVERY_ROUTES = "recovery_routes"


class PolicyVersionSet(ContractEnvelope):
    required_versions: tuple[PolicyVersion, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_versions(self):
        if len({version.policy_id for version in self.required_versions}) != len(self.required_versions):
            raise ValueError("required_versions must contain one version per policy_id")
        return self


class PublishedPolicy(ContractValue):
    policy: PolicyVersion
    kind: PolicyKind
    payload: PolicyPayload


class PolicyCatalog(ContractEnvelope):
    policies: tuple[PublishedPolicy, ...]

    @model_validator(mode="after")
    def unique_policies(self):
        if len({policy.policy.policy_id for policy in self.policies}) != len(self.policies):
            raise ValueError("policies must contain one version per policy_id")
        return self


class PolicyBundleItem(ContractValue):
    policy: PolicyVersion
    kind: PolicyKind
    payload: PolicyPayload


class PolicyBundle(ContractEnvelope):
    bundle_id: Identifier
    items: tuple[PolicyBundleItem, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_bundle(self):
        if len({item.policy.policy_id for item in self.items}) != len(self.items):
            raise ValueError("items must contain one entry per policy_id")
        return self


PolicyRegistryResult: TypeAlias = PolicyBundle | DomainError


class LoadPolicyBundle(Protocol):
    def __call__(self, requested: PolicyVersionSet, catalog: PolicyCatalog) -> PolicyRegistryResult: ...


REQUIRED_KINDS = {
    PolicyKind.PROFILE,
    PolicyKind.BOUNDS,
    PolicyKind.FUZZY_RULES,
    PolicyKind.FALLBACKS,
    PolicyKind.MAPPINGS,
    PolicyKind.RECOVERY_ROUTES,
}
SAFE_FALLBACK_ACTIONS = {EngineAction.SPEAK.value, EngineAction.IDLE.value}


def load(
    requested: PolicyVersionSet,
    catalog: PolicyCatalog,
    *,
    record_id: Identifier,
    bundle_id: Identifier,
) -> PolicyRegistryResult:
    evidence_error = _validate_evidence(requested, catalog)
    if evidence_error is not None:
        return evidence_error

    catalog_by_id = {policy.policy.policy_id: policy for policy in catalog.policies}
    items: list[PolicyBundleItem] = []
    for version in requested.required_versions:
        published = catalog_by_id.get(version.policy_id)
        if published is None:
            return _error(requested, catalog, ErrorCode.UNGROUNDED_REFERENCE, "Requested policy is missing from catalog.")
        if published.policy.version != version.version:
            return _error(requested, catalog, ErrorCode.STALE_REVISION, "Requested policy version is not available.")
        validation_error = _validate_payload(published)
        if validation_error is not None:
            return _error(requested, catalog, validation_error[0], validation_error[1])
        items.append(PolicyBundleItem(policy=published.policy, kind=published.kind, payload=published.payload))

    kinds = {item.kind for item in items}
    if not REQUIRED_KINDS.issubset(kinds):
        return _error(requested, catalog, ErrorCode.POLICY_INCONSISTENT, "Policy bundle is missing required policy kinds.")

    return PolicyBundle(
        schema_version=requested.schema_version,
        record_id=record_id,
        trace_id=requested.trace_id,
        causation_id=requested.record_id,
        game_id=requested.game_id,
        timeline_id=requested.timeline_id,
        npc_id=requested.npc_id,
        actor_id=requested.actor_id,
        target_id=requested.target_id,
        created_at=requested.created_at,
        source_ids=(requested.record_id, catalog.record_id),
        policy_versions=tuple(item.policy for item in items),
        bundle_id=bundle_id,
        items=tuple(items),
    )


def _validate_evidence(requested: PolicyVersionSet, catalog: PolicyCatalog) -> DomainError | None:
    if requested.game_id != catalog.game_id or requested.timeline_id != catalog.timeline_id or requested.npc_id != catalog.npc_id:
        return _error(requested, catalog, ErrorCode.INVALID_CONTRACT, "Policy catalog evidence is mismatched.")
    return None


def _validate_payload(published: PublishedPolicy) -> tuple[ErrorCode, str] | None:
    payload = published.payload
    if published.kind == PolicyKind.PROFILE:
        actions = payload.get("allowed_actions")
        if not _nonempty_identifiers(actions):
            return ErrorCode.POLICY_INVALID, "Profile policy must declare allowed actions."
        unknown = set(actions) - {action.value for action in EngineAction}
        if unknown:
            return ErrorCode.UNSUPPORTED_CAPABILITY, "Profile policy declares an unknown engine action."
    elif published.kind == PolicyKind.BOUNDS:
        for field in ("emotion", "relationship"):
            bounds = payload.get(field)
            if not isinstance(bounds, dict) or not _valid_bounds(bounds):
                return ErrorCode.POLICY_INVALID, "Bounds policy contains inconsistent bounds."
    elif published.kind == PolicyKind.FUZZY_RULES:
        dimensions = payload.get("dimensions")
        if not isinstance(dimensions, list) or not dimensions:
            return ErrorCode.POLICY_INVALID, "Fuzzy policy must declare membership dimensions."
        for definition in dimensions:
            try:
                DimensionDefinition.model_validate(definition)
            except Exception:
                return ErrorCode.POLICY_INVALID, "Fuzzy policy contains invalid memberships."
    elif published.kind == PolicyKind.FALLBACKS:
        options = payload.get("options")
        if not isinstance(options, list) or not options:
            return ErrorCode.POLICY_INVALID, "Fallback policy must declare safe options."
        for option in options:
            if not isinstance(option, dict) or option.get("action") not in SAFE_FALLBACK_ACTIONS or option.get("effect_ids", []) != []:
                return ErrorCode.POLICY_INVALID, "Fallback policy contains an unsafe fallback."
    elif published.kind == PolicyKind.MAPPINGS:
        mappings = payload.get("commands")
        if not isinstance(mappings, list) or not mappings:
            return ErrorCode.POLICY_INVALID, "Mapping policy must declare command mappings."
        for mapping in mappings:
            if not isinstance(mapping, dict) or mapping.get("action") not in {action.value for action in EngineAction}:
                return ErrorCode.UNSUPPORTED_CAPABILITY, "Mapping policy declares an unknown engine action."
    elif published.kind == PolicyKind.RECOVERY_ROUTES:
        routes = payload.get("routes")
        if not isinstance(routes, list) or not routes:
            return ErrorCode.POLICY_INVALID, "Recovery policy must declare routes."
        for route in routes:
            if not _complete_route(route):
                return ErrorCode.POLICY_INVALID, "Recovery policy contains an incomplete route."
    return None


def _nonempty_identifiers(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _valid_bounds(value: dict) -> bool:
    low = value.get("min")
    high = value.get("max")
    return isinstance(low, (int, float)) and isinstance(high, (int, float)) and 0 <= low <= high <= 1


def _complete_route(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("kind") not in {kind.value for kind in OfferKind}:
        return False
    required = ("route_id", "version", "npc_id", "blocked_step", "completion_event_type", "grant_effect_id")
    return all(isinstance(value.get(field), str) and value[field] for field in required)


def _error(requested: PolicyVersionSet, catalog: PolicyCatalog, code: ErrorCode, message: str) -> DomainError:
    return DomainError(
        code=code,
        stage="policy.registry",
        retryable=False,
        source_ids=(requested.record_id, catalog.record_id),
        public_message=message,
    )
