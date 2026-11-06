"""Pure inventory effect planning.

The planner validates ownership and catalog facts, then emits immutable
transfer/consumption effects. It does not mutate repositories or ORM models.
"""

from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion, RevisionSet


Quantity = Annotated[int, Field(strict=True, ge=1, le=1000)]


class InventoryOperation(str, Enum):
    TRANSFER = "transfer"
    CONSUME = "consume"


class InventoryEffectKind(str, Enum):
    TRANSFER = "transfer"
    CONSUMPTION = "consumption"


class CatalogItem(ContractValue):
    item_id: Identifier
    stackable: bool = Field(strict=True)


class OwnerQuantity(ContractValue):
    owner_id: Identifier
    item_id: Identifier
    quantity: Annotated[int, Field(strict=True, ge=0, le=1000)]


class InventoryRequest(ContractEnvelope):
    request_id: Identifier
    operation: InventoryOperation
    item_id: Identifier
    quantity: Quantity
    from_owner_id: Identifier
    to_owner_id: Identifier | None = None
    expected_revisions: RevisionSet
    idempotency_key: Identifier

    @model_validator(mode="after")
    def operation_shape(self):
        if self.operation == InventoryOperation.TRANSFER:
            if self.to_owner_id is None:
                raise ValueError("transfer requires to_owner_id")
            if self.to_owner_id == self.from_owner_id:
                raise ValueError("transfer requires distinct owners")
        if self.operation == InventoryOperation.CONSUME and self.to_owner_id is not None:
            raise ValueError("consumption must not specify to_owner_id")
        return self


class OwnershipView(ContractEnvelope):
    revisions: RevisionSet
    catalog: tuple[CatalogItem, ...]
    quantities: tuple[OwnerQuantity, ...]
    applied_effect_ids: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def unique_facts(self):
        if len({item.item_id for item in self.catalog}) != len(self.catalog):
            raise ValueError("catalog must contain unique item_id values")
        quantity_keys = {(quantity.owner_id, quantity.item_id) for quantity in self.quantities}
        if len(quantity_keys) != len(self.quantities):
            raise ValueError("quantities must contain unique owner/item pairs")
        if len(set(self.applied_effect_ids)) != len(self.applied_effect_ids):
            raise ValueError("applied_effect_ids must be unique")
        return self


class OwnerDelta(ContractValue):
    owner_id: Identifier
    item_id: Identifier
    before_quantity: Annotated[int, Field(strict=True, ge=0, le=1000)]
    delta: Annotated[int, Field(strict=True, ge=-1000, le=1000)]
    after_quantity: Annotated[int, Field(strict=True, ge=0, le=1000)]

    @model_validator(mode="after")
    def balanced_quantity(self):
        if self.before_quantity + self.delta != self.after_quantity:
            raise ValueError("after_quantity must equal before_quantity plus delta")
        if self.delta == 0:
            raise ValueError("delta must be nonzero")
        return self


class InventoryEffect(ContractEnvelope):
    effect_id: Identifier
    request_id: Identifier
    kind: InventoryEffectKind
    item_id: Identifier
    quantity: Quantity
    owner_deltas: tuple[OwnerDelta, ...] = Field(min_length=1)
    expected_revisions: RevisionSet
    policy: PolicyVersion

    @model_validator(mode="after")
    def conservation(self):
        if len({(delta.owner_id, delta.item_id) for delta in self.owner_deltas}) != len(self.owner_deltas):
            raise ValueError("owner_deltas must be unique by owner/item")
        if any(delta.item_id != self.item_id for delta in self.owner_deltas):
            raise ValueError("owner_deltas must reference the effect item_id")
        total = sum(delta.delta for delta in self.owner_deltas)
        if self.kind == InventoryEffectKind.TRANSFER and total != 0:
            raise ValueError("transfer deltas must conserve quantity")
        if self.kind == InventoryEffectKind.CONSUMPTION and total != -self.quantity:
            raise ValueError("consumption deltas must remove exactly the requested quantity")
        return self


InventoryPlanResult: TypeAlias = InventoryEffect | DomainError


class PlanInventoryEffect(Protocol):
    def __call__(self, request: InventoryRequest, view: OwnershipView) -> InventoryPlanResult: ...


def plan(
    request: InventoryRequest,
    view: OwnershipView,
    *,
    record_id: Identifier,
) -> InventoryPlanResult:
    evidence_error = _validate_evidence(request, view)
    if evidence_error is not None:
        return evidence_error

    effect_id = _effect_id(request)
    if effect_id in view.applied_effect_ids:
        return _error(ErrorCode.IDEMPOTENCY_CONFLICT, "Inventory effect was already applied.", (request.record_id, view.record_id))
    if request.item_id not in {item.item_id for item in view.catalog}:
        return _error(ErrorCode.UNGROUNDED_REFERENCE, "Inventory item is not present in the catalog.", (request.record_id, view.record_id))

    source_before = _quantity(view, request.from_owner_id, request.item_id)
    if source_before < request.quantity:
        return _error(ErrorCode.EFFECT_PRECONDITION_FAILED, "Inventory owner does not have enough quantity.", (request.record_id, view.record_id))

    if request.operation == InventoryOperation.TRANSFER:
        assert request.to_owner_id is not None
        target_before = _quantity(view, request.to_owner_id, request.item_id)
        deltas = (
            OwnerDelta(owner_id=request.from_owner_id, item_id=request.item_id, before_quantity=source_before, delta=-request.quantity, after_quantity=source_before - request.quantity),
            OwnerDelta(owner_id=request.to_owner_id, item_id=request.item_id, before_quantity=target_before, delta=request.quantity, after_quantity=target_before + request.quantity),
        )
        kind = InventoryEffectKind.TRANSFER
    else:
        deltas = (
            OwnerDelta(owner_id=request.from_owner_id, item_id=request.item_id, before_quantity=source_before, delta=-request.quantity, after_quantity=source_before - request.quantity),
        )
        kind = InventoryEffectKind.CONSUMPTION

    policy = request.policy_versions[-1]
    return InventoryEffect(
        schema_version=request.schema_version,
        record_id=record_id,
        trace_id=request.trace_id,
        causation_id=request.record_id,
        game_id=request.game_id,
        timeline_id=request.timeline_id,
        npc_id=request.npc_id,
        actor_id=request.actor_id,
        target_id=request.target_id,
        created_at=request.created_at,
        source_ids=(request.record_id, view.record_id),
        policy_versions=request.policy_versions,
        effect_id=effect_id,
        request_id=request.request_id,
        kind=kind,
        item_id=request.item_id,
        quantity=request.quantity,
        owner_deltas=deltas,
        expected_revisions=request.expected_revisions,
        policy=policy,
    )


def _validate_evidence(request: InventoryRequest, view: OwnershipView) -> DomainError | None:
    if (
        request.game_id != view.game_id
        or request.timeline_id != view.timeline_id
        or request.npc_id != view.npc_id
        or request.actor_id != view.actor_id
        or request.target_id != view.target_id
    ):
        return _error(ErrorCode.INVALID_CONTRACT, "Inventory ownership evidence is mismatched.", (request.record_id, view.record_id))
    if request.expected_revisions != view.revisions:
        return _error(ErrorCode.STALE_REVISION, "Inventory ownership revisions are stale.", (request.record_id, view.record_id))
    return None


def _quantity(view: OwnershipView, owner_id: Identifier, item_id: Identifier) -> int:
    for quantity in view.quantities:
        if quantity.owner_id == owner_id and quantity.item_id == item_id:
            return quantity.quantity
    return 0


def _effect_id(request: InventoryRequest) -> Identifier:
    return f"inventory-effect:{request.idempotency_key}"


def _error(code: ErrorCode, message: str, source_ids: tuple[Identifier, ...]) -> DomainError:
    return DomainError(
        code=code,
        stage="domain.world.inventory",
        retryable=False,
        source_ids=source_ids,
        public_message=message,
    )
