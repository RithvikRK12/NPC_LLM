"""World inventory contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode, PolicyVersion, RevisionSet
from app.domain.world.inventory import (
    InventoryEffect,
    InventoryEffectKind,
    InventoryOperation,
    InventoryRequest,
    OwnershipView,
    PlanInventoryEffect,
    plan,
)


FIXTURES = Path(__file__).parent / "fixtures" / "world"


class WorldInventoryContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "inventory-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "inventory-t01-rejected.json").read_text())

    def test_golden_round_trip_request_view_and_effect(self):
        for model, key in (
            (InventoryRequest, "request"),
            (OwnershipView, "view"),
            (InventoryEffect, "effect"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        request = InventoryRequest.model_validate(self.valid["request"])
        self.assertEqual(request.operation, InventoryOperation.TRANSFER)

    def test_rejected_fixture_has_unsupported_operation_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            InventoryRequest.model_validate(self.rejected["request"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.UNKNOWN_ENUM)
        self.assertEqual(rejection.stage, "domain.world.inventory")

    def test_missing_required_fields_and_invalid_shapes_are_rejected(self):
        for model, key, fields in (
            (InventoryRequest, "request", ("request_id", "operation", "item_id", "quantity", "from_owner_id", "expected_revisions", "idempotency_key")),
            (OwnershipView, "view", ("revisions", "catalog", "quantities", "source_ids")),
            (InventoryEffect, "effect", ("effect_id", "request_id", "kind", "item_id", "quantity", "owner_deltas", "expected_revisions", "policy")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        request = copy.deepcopy(self.valid["request"])
        request["to_owner_id"] = None
        with self.assertRaises(ValidationError):
            InventoryRequest.model_validate(request)
        effect = copy.deepcopy(self.valid["effect"])
        effect["owner_deltas"][1]["delta"] = 2
        effect["owner_deltas"][1]["after_quantity"] = 2
        with self.assertRaises(ValidationError):
            InventoryEffect.model_validate(effect)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        request = InventoryRequest.model_validate(self.valid["request"])
        view = OwnershipView.model_validate(self.valid["view"])
        expected = InventoryEffect.model_validate(self.valid["effect"])

        def fake(request: InventoryRequest, view: OwnershipView):
            self.assertEqual(request.request_id, expected.request_id)
            self.assertEqual(view.revisions, expected.expected_revisions)
            return expected

        planner: PlanInventoryEffect = fake
        self.assertEqual(planner(request, view), expected)
        self.assertEqual(self.valid, original)
        self.valid["request"]["quantity"] = 2
        self.assertEqual(request.quantity, 1)
        with self.assertRaises(ValidationError):
            request.quantity = 2

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.domain.world.inventory; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class WorldInventoryBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "inventory-t01-valid.json").read_text())

    def _plan(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return plan(
            InventoryRequest.model_validate(data["request"]),
            OwnershipView.model_validate(data["view"]),
            record_id="inventory-effect-record:001",
        )

    def test_valid_fixture_produces_exact_transfer_effect(self):
        result = self._plan()
        self.assertIsInstance(result, InventoryEffect)
        self.assertEqual(result.model_dump(mode="json"), self.valid["effect"])

    def test_consumption_effect_removes_quantity_without_target_owner(self):
        payload = copy.deepcopy(self.valid)
        payload["request"]["operation"] = "consume"
        payload["request"]["request_id"] = "inventory-request:consume_energy"
        payload["request"]["item_id"] = "item:water"
        payload["request"]["quantity"] = 2
        payload["request"]["from_owner_id"] = "player:hero"
        payload["request"]["to_owner_id"] = None
        payload["request"]["idempotency_key"] = "consume_energy_001"
        result = self._plan(payload)
        self.assertIsInstance(result, InventoryEffect)
        self.assertEqual(result.kind, InventoryEffectKind.CONSUMPTION)
        self.assertEqual(result.effect_id, "inventory-effect:consume_energy_001")
        self.assertEqual(result.owner_deltas[0].before_quantity, 3)
        self.assertEqual(result.owner_deltas[0].delta, -2)
        self.assertEqual(result.owner_deltas[0].after_quantity, 1)

    def test_transfer_conserves_quantities_across_both_owners(self):
        result = self._plan()
        self.assertIsInstance(result, InventoryEffect)
        self.assertEqual(sum(delta.delta for delta in result.owner_deltas), 0)
        self.assertEqual({delta.owner_id for delta in result.owner_deltas}, {"npc:gatherer", "player:hero"})

    def test_world_mismatch_and_stale_revision_return_typed_errors(self):
        payload = copy.deepcopy(self.valid)
        payload["view"]["timeline_id"] = "timeline:old"
        result = self._plan(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Inventory ownership evidence is mismatched.")

        payload = copy.deepcopy(self.valid)
        payload["view"]["revisions"]["inventory"][0]["revision"] = 8
        result = self._plan(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.STALE_REVISION)


class WorldInventoryInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "inventory-t01-valid.json").read_text())

    def _plan(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return plan(
            InventoryRequest.model_validate(data["request"]),
            OwnershipView.model_validate(data["view"]),
            record_id="inventory-effect-record:001",
        )

    def test_unknown_item_absent_ownership_and_insufficient_quantity_reject(self):
        payload = copy.deepcopy(self.valid)
        payload["request"]["item_id"] = "item:ghost_key"
        result = self._plan(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNGROUNDED_REFERENCE)

        payload = copy.deepcopy(self.valid)
        payload["request"]["from_owner_id"] = "npc:broker"
        result = self._plan(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.EFFECT_PRECONDITION_FAILED)

        payload = copy.deepcopy(self.valid)
        payload["request"]["quantity"] = 3
        result = self._plan(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.EFFECT_PRECONDITION_FAILED)

    def test_repeated_effect_identity_is_rejected_before_second_transfer(self):
        payload = copy.deepcopy(self.valid)
        payload["view"]["applied_effect_ids"] = ["inventory-effect:give_fruits_001"]
        result = self._plan(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.IDEMPOTENCY_CONFLICT)

    def test_duplicate_catalog_quantity_and_invalid_quantity_shapes_reject(self):
        payload = copy.deepcopy(self.valid["view"])
        payload["catalog"].append(copy.deepcopy(payload["catalog"][0]))
        with self.assertRaises(ValidationError):
            OwnershipView.model_validate(payload)

        payload = copy.deepcopy(self.valid["view"])
        payload["quantities"].append(copy.deepcopy(payload["quantities"][0]))
        with self.assertRaises(ValidationError):
            OwnershipView.model_validate(payload)

        payload = copy.deepcopy(self.valid["request"])
        payload["quantity"] = 0
        with self.assertRaises(ValidationError):
            InventoryRequest.model_validate(payload)


class ApprovedEffect(ContractEnvelope):
    effect_id: str
    item_id: str
    owner_deltas: tuple[dict, ...]
    expected_revisions: RevisionSet
    policy: PolicyVersion


def accept_application_effect(effect: InventoryEffect, expected_timeline: str, expected_policy: PolicyVersion):
    if effect.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="application.effects",
            retryable=False,
            source_ids=(effect.record_id,),
            public_message="Inventory effect timeline is no longer current.",
        )
    if effect.policy != expected_policy:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="application.effects",
            retryable=False,
            source_ids=(effect.record_id,),
            public_message="Inventory effect policy does not match application input.",
        )
    return ApprovedEffect(
        schema_version=effect.schema_version,
        record_id="approved-effect:001",
        trace_id=effect.trace_id,
        causation_id=effect.record_id,
        game_id=effect.game_id,
        timeline_id=effect.timeline_id,
        npc_id=effect.npc_id,
        actor_id=effect.actor_id,
        target_id=effect.target_id,
        created_at=effect.created_at,
        source_ids=(effect.record_id,),
        policy_versions=effect.policy_versions,
        effect_id=effect.effect_id,
        item_id=effect.item_id,
        owner_deltas=tuple(delta.model_dump(mode="json") for delta in effect.owner_deltas),
        expected_revisions=effect.expected_revisions,
        policy=effect.policy,
    )


class WorldInventoryHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "inventory-t01-valid.json").read_text())

    def _effect(self):
        result = plan(
            InventoryRequest.model_validate(self.valid["request"]),
            OwnershipView.model_validate(self.valid["view"]),
            record_id="inventory-effect-record:001",
        )
        self.assertIsInstance(result, InventoryEffect)
        return result

    def test_inventory_effect_satisfies_application_effect_handoff(self):
        effect = self._effect()
        handoff = accept_application_effect(effect, "timeline:main", effect.policy)
        self.assertIsInstance(handoff, ApprovedEffect)
        self.assertEqual(handoff.effect_id, "inventory-effect:give_fruits_001")
        self.assertEqual(sum(delta["delta"] for delta in handoff.owner_deltas), 0)
        with self.assertRaises(ValidationError):
            handoff.effect_id = "inventory-effect:other"

    def test_application_effect_handoff_rejects_mismatched_policy_and_timeline(self):
        effect = self._effect()
        result = accept_application_effect(effect, "timeline:main", PolicyVersion(policy_id="inventory:plan", version="v2"))
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        result = accept_application_effect(effect, "timeline:reset", effect.policy)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)
