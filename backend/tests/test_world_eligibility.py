"""T01 world eligibility contract and fake-boundary tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode
from app.domain.world.eligibility import (
    CheckEligibility,
    EligibilityStatus,
    EligibilityResult,
    EntityView,
    InteractionEvent,
    InteractionPolicy,
    PredicateName,
    WorldView,
    check_eligibility,
)


FIXTURES = Path(__file__).parent / "fixtures" / "world"
CONTRACT_FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


class WorldEligibilityContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "eligibility-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "eligibility-t01-rejected.json").read_text())

    def test_golden_round_trip_event_world_policy_and_result(self):
        for model, key in (
            (InteractionEvent, "event"),
            (WorldView, "world"),
            (InteractionPolicy, "policy"),
            (EligibilityResult, "result"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        event = InteractionEvent.model_validate(self.valid["event"])
        self.assertEqual(event.reported_actor_position.area_id, "area:village")
        self.assertEqual(event.kind.value, "speak")

    def test_rejected_fixture_has_unsupported_variant_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            InteractionEvent.model_validate(self.rejected["event"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(rejection.stage, "domain.world.eligibility")
        self.assertEqual(DomainError.model_validate_json(rejection.model_dump_json()), rejection)

    def test_missing_required_fields_are_rejected(self):
        for model, key, fields in (
            (InteractionEvent, "event", ("interaction_id", "kind", "expected_revisions", "source_ids")),
            (WorldView, "world", ("revisions", "actor_position", "targets")),
            (InteractionPolicy, "policy", ("policy_id", "version", "rules")),
            (EligibilityResult, "result", ("interaction_id", "status", "predicates", "policy_id")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)

    def test_duplicate_targets_rules_predicates_and_interactions_are_rejected(self):
        payload = copy.deepcopy(self.valid["world"])
        payload["targets"].append(copy.deepcopy(payload["targets"][0]))
        with self.assertRaises(ValidationError):
            WorldView.model_validate(payload)
        target = copy.deepcopy(self.valid["world"]["targets"][0])
        target["interaction_kinds"].append("speak")
        with self.assertRaises(ValidationError):
            EntityView.model_validate(target)
        payload = copy.deepcopy(self.valid["policy"])
        payload["rules"].append(copy.deepcopy(payload["rules"][0]))
        with self.assertRaises(ValidationError):
            InteractionPolicy.model_validate(payload)
        payload = copy.deepcopy(self.valid["result"])
        payload["predicates"].append(copy.deepcopy(payload["predicates"][0]))
        with self.assertRaises(ValidationError):
            EligibilityResult.model_validate(payload)

    def test_distance_visibility_and_booleans_are_strict(self):
        for value in (-0.1, "2", True, float("nan"), float("inf")):
            payload = copy.deepcopy(self.valid["policy"])
            payload["rules"][0]["max_distance"] = value
            with self.subTest(value=value), self.assertRaises(ValidationError):
                InteractionPolicy.model_validate(payload)
        payload = copy.deepcopy(self.valid["world"])
        payload["targets"][0]["visibility"] = "omniscient"
        with self.assertRaises(ValidationError):
            WorldView.model_validate(payload)
        payload = copy.deepcopy(self.valid["result"])
        payload["predicates"][0]["passed"] = "true"
        with self.assertRaises(ValidationError):
            EligibilityResult.model_validate(payload)

    def test_fixture_decoding_and_fake_execution_do_not_mutate_inputs(self):
        original = copy.deepcopy(self.valid)
        event = InteractionEvent.model_validate(self.valid["event"])
        world = WorldView.model_validate(self.valid["world"])
        policy = InteractionPolicy.model_validate(self.valid["policy"])
        expected = EligibilityResult.model_validate(self.valid["result"])

        def fake(event: InteractionEvent, world: WorldView, policy: InteractionPolicy):
            self.assertEqual(event.interaction_id, expected.interaction_id)
            self.assertEqual(world.revisions.npc_id, event.expected_revisions.npc_id)
            self.assertEqual(policy.policy_id, expected.policy_id)
            return expected

        check: CheckEligibility = fake
        self.assertEqual(check(event, world, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["event"]["kind"] = "trade"
        self.valid["world"]["targets"][0]["visibility"] = "private"
        self.valid["policy"]["rules"][0]["max_distance"] = 99.0
        self.assertEqual(event.kind.value, "speak")
        self.assertEqual(world.targets[0].visibility.value, "direct")
        self.assertEqual(policy.rules[0].max_distance, 2.0)
        with self.assertRaises(ValidationError):
            event.kind = "trade"
        with self.assertRaises(TypeError):
            world.targets[0].interaction_kinds[0] = world.targets[0].interaction_kinds[0]

    def test_fake_rejection_uses_shared_error_value(self):
        rejection = DomainError.model_validate(self.rejected["error"])

        def fake(event: InteractionEvent, world: WorldView, policy: InteractionPolicy):
            return rejection

        check: CheckEligibility = fake
        result = check(
            InteractionEvent.model_validate(self.valid["event"]),
            WorldView.model_validate(self.valid["world"]),
            InteractionPolicy.model_validate(self.valid["policy"]),
        )
        self.assertIs(result, rejection)
        self.assertFalse(result.retryable)

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.domain.world.eligibility; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class WorldEligibilityBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "eligibility-t01-valid.json").read_text())

    def _check(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return check_eligibility(
            InteractionEvent.model_validate(data["event"]),
            WorldView.model_validate(data["world"]),
            InteractionPolicy.model_validate(data["policy"]),
        )

    def test_valid_t01_fixture_evaluates_exact_eligible_result(self):
        result = self._check()
        self.assertEqual(result.model_dump(mode="json"), self.valid["result"])

    def test_primary_behaviour_returns_all_named_predicates_in_order(self):
        result = self._check()
        self.assertEqual(result.status, EligibilityStatus.ELIGIBLE)
        self.assertEqual(
            tuple(predicate.name for predicate in result.predicates),
            (
                PredicateName.TARGET_EXISTS,
                PredicateName.ACTOR_POSITION_ACCEPTED,
                PredicateName.TARGET_POSITION_ACCEPTED,
                PredicateName.IN_RANGE,
                PredicateName.VISIBLE,
                PredicateName.OPERATION_PERMITTED,
            ),
        )
        self.assertTrue(all(predicate.passed for predicate in result.predicates))
        by_name = {predicate.name: predicate for predicate in result.predicates}
        self.assertEqual(by_name[PredicateName.TARGET_EXISTS].evidence_ids, ("world-view:001",))
        self.assertEqual(by_name[PredicateName.ACTOR_POSITION_ACCEPTED].evidence_ids, ("world-view:001",))
        self.assertEqual(by_name[PredicateName.TARGET_POSITION_ACCEPTED].evidence_ids, ("world-view:001",))
        self.assertEqual(by_name[PredicateName.IN_RANGE].evidence_ids, ("world-view:001", "interaction-policy:001"))
        self.assertEqual(by_name[PredicateName.VISIBLE].evidence_ids, ("world-view:001",))
        self.assertEqual(
            by_name[PredicateName.OPERATION_PERMITTED].evidence_ids,
            ("world-view:001", "interaction-policy:001"),
        )

    def test_reported_position_is_not_used_for_actor_position_acceptance_or_range(self):
        payload = copy.deepcopy(self.valid)
        payload["event"]["reported_actor_position"] = {
            "x": 500.0,
            "y": 500.0,
            "area_id": "area:wilderness",
            "spatial_revision": 999,
        }
        result = self._check(payload)
        by_name = {predicate.name: predicate for predicate in result.predicates}
        self.assertEqual(result.status, EligibilityStatus.ELIGIBLE)
        self.assertTrue(by_name[PredicateName.ACTOR_POSITION_ACCEPTED].passed)
        self.assertTrue(by_name[PredicateName.IN_RANGE].passed)

    def test_non_direct_visibility_can_succeed_when_rule_allows_indirect_evidence(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["targets"][0]["visibility"] = "informed"
        payload["policy"]["rules"][0]["require_direct_visibility"] = False
        result = self._check(payload)
        by_name = {predicate.name: predicate for predicate in result.predicates}
        self.assertEqual(result.status, EligibilityStatus.ELIGIBLE)
        self.assertTrue(by_name[PredicateName.VISIBLE].passed)

    def test_permitted_request_item_branch_uses_matching_rule_and_target_kind(self):
        payload = copy.deepcopy(self.valid)
        payload["event"]["kind"] = "request_item"
        payload["event"]["interaction_id"] = "interaction:request-item"
        payload["event"]["record_id"] = "interaction-event:request-item"
        payload["world"]["targets"][0]["position"]["x"] = 2.5
        result = self._check(payload)
        by_name = {predicate.name: predicate for predicate in result.predicates}
        self.assertEqual(result.record_id, "eligibility-result:request-item")
        self.assertEqual(result.status, EligibilityStatus.ELIGIBLE)
        self.assertTrue(by_name[PredicateName.IN_RANGE].passed)
        self.assertTrue(by_name[PredicateName.OPERATION_PERMITTED].passed)

    def test_failed_primary_predicates_make_ineligible_without_generated_prose(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["targets"][0]["position"]["x"] = 4.1
        payload["world"]["targets"][0]["visibility"] = "remembered"
        payload["world"]["targets"][0]["interaction_kinds"] = ["request_item"]
        result = self._check(payload)
        by_name = {predicate.name: predicate for predicate in result.predicates}
        self.assertEqual(result.status, EligibilityStatus.INELIGIBLE)
        self.assertFalse(by_name[PredicateName.IN_RANGE].passed)
        self.assertFalse(by_name[PredicateName.VISIBLE].passed)
        self.assertFalse(by_name[PredicateName.OPERATION_PERMITTED].passed)
        self.assertEqual(by_name[PredicateName.IN_RANGE].evidence_ids, ())
        self.assertEqual(result.policy_id, "world:interaction")
        self.assertEqual(result.policy_version, "v1")

    def test_real_checker_does_not_mutate_inputs(self):
        original = copy.deepcopy(self.valid)
        result = self._check()
        self.assertEqual(self.valid, original)
        with self.assertRaises(ValidationError):
            result.predicates[0].passed = False


class WorldEligibilityInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "eligibility-t01-valid.json").read_text())

    def _check(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return check_eligibility(
            InteractionEvent.model_validate(data["event"]),
            WorldView.model_validate(data["world"]),
            InteractionPolicy.model_validate(data["policy"]),
        )

    def test_forged_actor_ownership_is_typed_rejection(self):
        payload = copy.deepcopy(self.valid)
        payload["event"]["actor_id"] = "player:forged"
        result = self._check(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.stage, "domain.world.eligibility")
        self.assertFalse(result.retryable)
        self.assertEqual(result.source_ids, ("interaction-event:001", "world-view:001"))

    def test_forged_world_location_evidence_is_typed_rejection(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["timeline_id"] = "timeline:forged"
        result = self._check(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Interaction evidence does not match authoritative world view.")

    def test_missing_authoritative_actor_or_target_evidence_is_typed_rejection(self):
        for envelope, field in (("event", "actor_id"), ("event", "target_id"), ("world", "actor_id"), ("world", "target_id")):
            payload = copy.deepcopy(self.valid)
            payload[envelope][field] = None
            with self.subTest(envelope=envelope, field=field):
                result = self._check(payload)
                self.assertIsInstance(result, DomainError)
                self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
                self.assertEqual(result.public_message, "Interaction evidence is incomplete.")

    def test_missing_policy_evidence_is_typed_rejection(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["timeline_id"] = "timeline:other"
        result = self._check(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.source_ids, ("interaction-event:001", "interaction-policy:001"))

    def test_supported_remote_channel_absent_is_ineligible_without_effects(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["targets"][0]["position"]["area_id"] = "area:mountain"
        payload["world"]["targets"][0]["position"]["spatial_revision"] = 8
        result = self._check(payload)
        self.assertIsInstance(result, EligibilityResult)
        by_name = {predicate.name: predicate for predicate in result.predicates}
        self.assertEqual(result.status, EligibilityStatus.INELIGIBLE)
        self.assertTrue(by_name[PredicateName.TARGET_EXISTS].passed)
        self.assertTrue(by_name[PredicateName.ACTOR_POSITION_ACCEPTED].passed)
        self.assertFalse(by_name[PredicateName.TARGET_POSITION_ACCEPTED].passed)
        self.assertFalse(by_name[PredicateName.IN_RANGE].passed)
        self.assertFalse(by_name[PredicateName.VISIBLE].passed)
        self.assertEqual(by_name[PredicateName.TARGET_POSITION_ACCEPTED].evidence_ids, ())
        self.assertEqual(by_name[PredicateName.IN_RANGE].evidence_ids, ())

    def test_missing_target_entity_is_ineligible_fallback(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["targets"] = []
        result = self._check(payload)
        self.assertIsInstance(result, EligibilityResult)
        by_name = {predicate.name: predicate for predicate in result.predicates}
        self.assertEqual(result.status, EligibilityStatus.INELIGIBLE)
        self.assertFalse(by_name[PredicateName.TARGET_EXISTS].passed)
        self.assertFalse(by_name[PredicateName.TARGET_POSITION_ACCEPTED].passed)
        self.assertFalse(by_name[PredicateName.IN_RANGE].passed)
        self.assertFalse(by_name[PredicateName.VISIBLE].passed)
        self.assertFalse(by_name[PredicateName.OPERATION_PERMITTED].passed)
        self.assertEqual(result.source_ids, ("interaction-event:001", "world-view:001", "interaction-policy:001"))

    def test_distance_boundary_is_inclusive_and_beyond_boundary_fails(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["targets"][0]["position"]["x"] = 3.0
        boundary = self._check(payload)
        self.assertIsInstance(boundary, EligibilityResult)
        self.assertEqual(boundary.status, EligibilityStatus.ELIGIBLE)

        payload["world"]["targets"][0]["position"]["x"] = 3.0001
        outside = self._check(payload)
        self.assertIsInstance(outside, EligibilityResult)
        by_name = {predicate.name: predicate for predicate in outside.predicates}
        self.assertEqual(outside.status, EligibilityStatus.INELIGIBLE)
        self.assertFalse(by_name[PredicateName.IN_RANGE].passed)
        self.assertEqual(by_name[PredicateName.IN_RANGE].evidence_ids, ())


class WorldEligibilityHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "eligibility-t01-valid.json").read_text())
        self.c01_values = json.loads((CONTRACT_FIXTURES / "c01-values.json").read_text())

    def _check(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return check_eligibility(
            InteractionEvent.model_validate(data["event"]),
            WorldView.model_validate(data["world"]),
            InteractionPolicy.model_validate(data["policy"]),
        )

    def test_result_satisfies_c01_envelope_handoff_without_schema_changes(self):
        result = self._check()
        self.assertIsInstance(result, EligibilityResult)
        payload = result.model_dump(mode="json")
        envelope = ContractEnvelope.model_validate({field: payload[field] for field in ContractEnvelope.model_fields})
        self.assertEqual(envelope.schema_version, self.c01_values["envelope"]["schema_version"])
        self.assertEqual(envelope.causation_id, "interaction-event:001")
        self.assertEqual(envelope.source_ids, ("interaction-event:001", "world-view:001", "interaction-policy:001"))
        self.assertEqual(envelope.policy_versions[0].policy_id, "world:interaction")
        self.assertEqual(envelope.policy_versions[0].version, "v1")
        self.assertEqual(result.status, EligibilityStatus.ELIGIBLE)

    def test_next_handoff_can_consume_immutable_eligibility_identity(self):
        result = self._check()
        self.assertIsInstance(result, EligibilityResult)

        def fake_application_interaction_handoff(eligibility: EligibilityResult):
            self.assertEqual(eligibility.interaction_id, "interaction:001")
            self.assertEqual(eligibility.status, EligibilityStatus.ELIGIBLE)
            self.assertEqual(eligibility.policy_id, "world:interaction")
            self.assertEqual(eligibility.policy_version, "v1")
            return eligibility.record_id

        self.assertEqual(fake_application_interaction_handoff(result), "eligibility-result:001")

    def test_mismatched_source_policy_version_is_typed_rejection(self):
        payload = copy.deepcopy(self.valid)
        payload["event"]["policy_versions"][0]["version"] = "v0"
        result = self._check(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Interaction policy evidence is missing or mismatched.")
        self.assertEqual(result.source_ids, ("interaction-event:001", "interaction-policy:001"))

    def test_mismatched_source_timeline_is_typed_rejection(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["timeline_id"] = "timeline:old"
        result = self._check(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Interaction policy evidence is missing or mismatched.")
        self.assertEqual(result.source_ids, ("interaction-event:001", "interaction-policy:001"))


if __name__ == "__main__":
    unittest.main()
