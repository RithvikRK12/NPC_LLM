"""Policy registry contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode, PolicyVersion
from app.policy.registry import (
    LoadPolicyBundle,
    PolicyBundle,
    PolicyCatalog,
    PolicyKind,
    PolicyVersionSet,
    PublishedPolicy,
    load,
)


FIXTURES = Path(__file__).parent / "fixtures" / "policy"


class PolicyRegistryContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "registry-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "registry-t01-rejected.json").read_text())

    def test_golden_round_trip_requested_catalog_and_bundle(self):
        for model, key in (
            (PolicyVersionSet, "requested"),
            (PolicyCatalog, "catalog"),
            (PolicyBundle, "bundle"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        catalog = PolicyCatalog.model_validate(self.valid["catalog"])
        self.assertEqual(catalog.policies[0].kind, PolicyKind.PROFILE)

    def test_rejected_fixture_has_unsupported_kind_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            PolicyCatalog.model_validate(self.rejected["catalog"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.UNKNOWN_ENUM)
        self.assertEqual(rejection.stage, "policy.registry")

    def test_missing_required_fields_and_invalid_shapes_are_rejected(self):
        for model, key, fields in (
            (PolicyVersionSet, "requested", ("required_versions", "source_ids")),
            (PolicyCatalog, "catalog", ("policies", "source_ids")),
            (PolicyBundle, "bundle", ("bundle_id", "items")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        requested = copy.deepcopy(self.valid["requested"])
        requested["required_versions"].append(copy.deepcopy(requested["required_versions"][0]))
        with self.assertRaises(ValidationError):
            PolicyVersionSet.model_validate(requested)
        catalog = copy.deepcopy(self.valid["catalog"])
        catalog["policies"].append(copy.deepcopy(catalog["policies"][0]))
        with self.assertRaises(ValidationError):
            PolicyCatalog.model_validate(catalog)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        requested = PolicyVersionSet.model_validate(self.valid["requested"])
        catalog = PolicyCatalog.model_validate(self.valid["catalog"])
        expected = PolicyBundle.model_validate(self.valid["bundle"])

        def fake(requested: PolicyVersionSet, catalog: PolicyCatalog):
            self.assertEqual(requested.record_id, expected.causation_id)
            self.assertEqual(len(catalog.policies), len(expected.items))
            return expected

        loader: LoadPolicyBundle = fake
        self.assertEqual(loader(requested, catalog), expected)
        self.assertEqual(self.valid, original)
        self.valid["requested"]["required_versions"][0]["version"] = "v2"
        self.assertEqual(requested.required_versions[0].version, "v1")
        with self.assertRaises(ValidationError):
            requested.required_versions = ()

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.policy.registry; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class PolicyRegistryBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "registry-t01-valid.json").read_text())

    def _load(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return load(
            PolicyVersionSet.model_validate(data["requested"]),
            PolicyCatalog.model_validate(data["catalog"]),
            record_id="policy-bundle-record:001",
            bundle_id="policy-bundle:001",
        )

    def test_valid_fixture_loads_exact_bundle(self):
        result = self._load()
        self.assertIsInstance(result, PolicyBundle)
        self.assertEqual(result.model_dump(mode="json"), self.valid["bundle"])

    def test_all_required_policy_families_are_loaded_immutably(self):
        result = self._load()
        self.assertIsInstance(result, PolicyBundle)
        self.assertEqual({item.kind for item in result.items}, set(PolicyKind))
        self.assertEqual(tuple(version.policy_id for version in result.policy_versions), tuple(version["policy_id"] for version in self.valid["requested"]["required_versions"]))

    def test_catalog_mismatch_missing_policy_and_stale_version_return_typed_errors(self):
        payload = copy.deepcopy(self.valid)
        payload["catalog"]["timeline_id"] = "timeline:old"
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Policy catalog evidence is mismatched.")

        payload = copy.deepcopy(self.valid)
        payload["catalog"]["policies"] = payload["catalog"]["policies"][:-1]
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNGROUNDED_REFERENCE)

        payload = copy.deepcopy(self.valid)
        payload["catalog"]["policies"][0]["policy"]["version"] = "v0"
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.STALE_REVISION)


class PolicyRegistryInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "registry-t01-valid.json").read_text())

    def _load(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return load(
            PolicyVersionSet.model_validate(data["requested"]),
            PolicyCatalog.model_validate(data["catalog"]),
            record_id="policy-bundle-record:001",
            bundle_id="policy-bundle:001",
        )

    def test_missing_or_unknown_actions_rejected(self):
        payload = copy.deepcopy(self.valid)
        payload["catalog"]["policies"][0]["payload"]["allowed_actions"] = []
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Profile policy must declare allowed actions.")

        payload = copy.deepcopy(self.valid)
        payload["catalog"]["policies"][0]["payload"]["allowed_actions"] = ["teleport"]
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNSUPPORTED_CAPABILITY)

    def test_inconsistent_bounds_unsafe_fallback_and_unknown_mapping_rejected(self):
        payload = copy.deepcopy(self.valid)
        payload["catalog"]["policies"][1]["payload"]["emotion"] = {"min": 0.9, "max": 0.2}
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Bounds policy contains inconsistent bounds.")

        payload = copy.deepcopy(self.valid)
        payload["catalog"]["policies"][3]["payload"]["options"][0]["effect_ids"] = ["effect:grant_reward"]
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Fallback policy contains an unsafe fallback.")

        payload = copy.deepcopy(self.valid)
        payload["catalog"]["policies"][4]["payload"]["commands"][0]["action"] = "grant_item"
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Mapping policy declares an unknown engine action.")

    def test_invalid_memberships_and_incomplete_recovery_routes_rejected(self):
        payload = copy.deepcopy(self.valid)
        payload["catalog"]["policies"][2]["payload"]["dimensions"][0]["labels"][0]["shape"]["kind"] = "curve"
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Fuzzy policy contains invalid memberships.")

        payload = copy.deepcopy(self.valid)
        del payload["catalog"]["policies"][5]["payload"]["routes"][0]["grant_effect_id"]
        result = self._load(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Recovery policy contains an incomplete route.")

    def test_in_flight_decision_retains_loaded_versions_after_catalog_changes(self):
        result = self._load()
        self.assertIsInstance(result, PolicyBundle)
        payload = copy.deepcopy(self.valid)
        payload["catalog"]["policies"][0]["policy"]["version"] = "v2"
        self.assertEqual(result.policy_versions[0].version, "v1")
        self.assertEqual(result.items[0].policy.version, "v1")


class GatewayCodecInput(ContractEnvelope):
    bundle_id: str


def accept_gateway_codec_input(bundle: PolicyBundle, expected_timeline: str):
    if bundle.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="gateway.contract_codec",
            retryable=False,
            source_ids=(bundle.record_id,),
            public_message="Policy bundle timeline is no longer current.",
        )
    return GatewayCodecInput(
        schema_version=bundle.schema_version,
        record_id="gateway-codec-input:001",
        trace_id=bundle.trace_id,
        causation_id=bundle.record_id,
        game_id=bundle.game_id,
        timeline_id=bundle.timeline_id,
        npc_id=bundle.npc_id,
        actor_id=bundle.actor_id,
        target_id=bundle.target_id,
        created_at=bundle.created_at,
        source_ids=(bundle.record_id,),
        policy_versions=bundle.policy_versions,
        bundle_id=bundle.bundle_id,
    )


class PolicyRegistryHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "registry-t01-valid.json").read_text())

    def _bundle(self):
        result = load(
            PolicyVersionSet.model_validate(self.valid["requested"]),
            PolicyCatalog.model_validate(self.valid["catalog"]),
            record_id="policy-bundle-record:001",
            bundle_id="policy-bundle:001",
        )
        self.assertIsInstance(result, PolicyBundle)
        return result

    def test_policy_bundle_satisfies_gateway_contract_codec_handoff(self):
        bundle = self._bundle()
        handoff = accept_gateway_codec_input(bundle, "timeline:main")
        self.assertIsInstance(handoff, GatewayCodecInput)
        self.assertEqual(handoff.bundle_id, "policy-bundle:001")
        self.assertEqual(handoff.policy_versions, bundle.policy_versions)
        with self.assertRaises(ValidationError):
            handoff.bundle_id = "policy-bundle:other"

    def test_gateway_contract_codec_handoff_rejects_mismatched_timeline(self):
        bundle = self._bundle()
        result = accept_gateway_codec_input(bundle, "timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)
