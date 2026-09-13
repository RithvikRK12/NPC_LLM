"""T01 structure/fake-boundary tests; fixture degrees are not algorithm evidence."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractValue, DomainError, ErrorCode
from app.domain.fuzzy.membership import (
    Fuzzify, MembershipInput, MembershipPolicy, Memberships, Triangle, Trapezoid, fuzzify,
)


FIXTURES = Path(__file__).parent / "fixtures" / "fuzzy"


class MembershipContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "membership-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "membership-t01-rejected.json").read_text())

    def test_golden_round_trip_input_policy_and_output(self):
        for model, key in ((MembershipInput, "input"), (MembershipPolicy, "policy"), (Memberships, "output")):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        policy = MembershipPolicy.model_validate(self.valid["policy"])
        self.assertIsInstance(policy.dimensions[0].labels[0].shape, Trapezoid)
        self.assertIsInstance(policy.dimensions[0].labels[1].shape, Triangle)

    def test_rejected_fixture_has_typed_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            MembershipPolicy.model_validate(self.rejected["policy"])
        self.assertEqual(caught.exception.errors()[0]["type"], "union_tag_invalid")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(rejection.stage, "fuzzy.membership")
        self.assertEqual(DomainError.model_validate_json(rejection.model_dump_json()), rejection)

    def test_missing_required_fields_are_rejected(self):
        for model, key, fields in (
            (MembershipInput, "input", ("candidate_state_id", "dimensions", "source_ids", "timeline_id")),
            (MembershipPolicy, "policy", ("policy", "dimensions", "schema_version")),
            (Memberships, "output", ("input_id", "candidate_state_id", "policy", "dimensions")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        payload = copy.deepcopy(self.valid["policy"])
        del payload["dimensions"][0]["labels"][0]["shape"]["d"]
        with self.assertRaises(ValidationError):
            MembershipPolicy.model_validate(payload)

    def test_shape_points_are_finite_and_strict(self):
        for value in (float("nan"), float("inf"), -float("inf"), "0.2", True):
            payload = copy.deepcopy(self.valid["policy"])
            payload["dimensions"][0]["labels"][0]["shape"]["a"] = value
            with self.subTest(value=value), self.assertRaises(ValidationError):
                MembershipPolicy.model_validate(payload)

    def test_normalized_inputs_and_output_degrees(self):
        for model, key, leaf in ((MembershipInput, "input", "value"), (Memberships, "output", "degree")):
            for value in (-0.1, 1.1, float("nan"), float("inf"), True, "0.4"):
                payload = copy.deepcopy(self.valid[key])
                target = payload["dimensions"][0]
                if key == "output":
                    target = target["labels"][0]
                target[leaf] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValidationError):
                    model.model_validate(payload)

    def test_unknown_fields_and_empty_dimensions_rejected(self):
        for model, key in ((MembershipInput, "input"), (MembershipPolicy, "policy"), (Memberships, "output")):
            for changes in ({"session": "unwanted"}, {"dimensions": []}):
                with self.subTest(key=key, changes=changes), self.assertRaises(ValidationError):
                    model.model_validate(self.valid[key] | changes)

    def test_fixture_decoding_and_fake_execution_do_not_mutate_inputs(self):
        original = copy.deepcopy(self.valid)
        candidate = MembershipInput.model_validate(self.valid["input"])
        policy = MembershipPolicy.model_validate(self.valid["policy"])
        expected = Memberships.model_validate(self.valid["output"])

        def fake(candidate: MembershipInput, policy: MembershipPolicy):
            self.assertEqual(candidate.candidate_state_id, expected.candidate_state_id)
            self.assertEqual(policy.policy, expected.policy)
            return expected

        fuzzify: Fuzzify = fake
        self.assertEqual(fuzzify(candidate, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["input"]["dimensions"][0]["value"] = 0.9
        self.valid["policy"]["dimensions"][0]["labels"][0]["shape"]["a"] = 0.1
        self.assertEqual(candidate.dimensions[0].value, 0.4)
        self.assertEqual(policy.dimensions[0].labels[0].shape.a, 0.0)
        with self.assertRaises(ValidationError):
            candidate.dimensions[0].value = 0.2
        with self.assertRaises(ValidationError):
            policy.dimensions[0].labels[0].shape.a = 0.1
        with self.assertRaises(TypeError):
            expected.dimensions[0].labels[0] = expected.dimensions[0].labels[0]

    def test_fake_rejection_uses_shared_error_value(self):
        rejection = DomainError.model_validate(self.rejected["error"])

        def fake(candidate: MembershipInput, policy: MembershipPolicy):
            return rejection

        fuzzify: Fuzzify = fake
        result = fuzzify(MembershipInput.model_validate(self.valid["input"]), MembershipPolicy.model_validate(self.valid["policy"]))
        self.assertIs(result, rejection)
        self.assertFalse(result.retryable)

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.domain.fuzzy.membership; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class FuzzifyPrimaryBehaviourTests(unittest.TestCase):
    def fixture(self, name):
        return json.loads((FIXTURES / name).read_text())

    def assert_fuzzifies_fixture(self, name):
        fixture = self.fixture(name)
        candidate = MembershipInput.model_validate(fixture["input"])
        policy = MembershipPolicy.model_validate(fixture["policy"])
        expected = Memberships.model_validate(fixture["output"])
        actual = fuzzify(candidate, policy, record_id=expected.record_id, created_at=expected.created_at)
        self.assertEqual(actual, expected)
        self.assertEqual(actual.model_dump(mode="json"), fixture["output"])

    def test_t01_valid_fixture_evaluates_overlapping_memberships(self):
        self.assert_fuzzifies_fixture("membership-t01-valid.json")

    def test_triangle_branch_reaches_configured_label_peak(self):
        self.assert_fuzzifies_fixture("membership-t02-triangle.json")

    def test_trapezoid_branch_reaches_configured_label_plateau(self):
        self.assert_fuzzifies_fixture("membership-t02-trapezoid.json")

    def test_multiple_dimensions_evaluate_configured_shape_branches(self):
        self.assert_fuzzifies_fixture("membership-t02-branches.json")

    def test_preserves_configured_dimension_and_label_order(self):
        fixture = self.fixture("membership-t01-valid.json")
        candidate = MembershipInput.model_validate(fixture["input"])
        policy = MembershipPolicy.model_validate(fixture["policy"])
        actual = fuzzify(candidate, policy, record_id="memberships:ordered")
        dimension = actual.dimensions[0]
        self.assertEqual(dimension.dimension, "fear")
        self.assertEqual([label.label for label in dimension.labels], ["LOW", "MEDIUM", "HIGH"])
        self.assertEqual(actual.policy, policy.policy)
        self.assertEqual(actual.input_id, candidate.record_id)
        self.assertEqual(actual.candidate_state_id, candidate.candidate_state_id)


class FuzzifyInvariantTests(unittest.TestCase):
    def fixture(self, name="membership-t01-valid.json"):
        return json.loads((FIXTURES / name).read_text())

    def fuzzify_payload(self, payload):
        return fuzzify(
            MembershipInput.model_validate(payload["input"]),
            MembershipPolicy.model_validate(payload["policy"]),
            record_id="memberships:invariant",
            created_at="2026-09-12T10:00:00Z",
        )

    def test_overlap_and_range_guarantees(self):
        result = self.fuzzify_payload(self.fixture())
        self.assertIsInstance(result, Memberships)
        labels = {label.label: label.degree for label in result.dimensions[0].labels}
        self.assertGreater(labels["LOW"], 0.0)
        self.assertGreater(labels["MEDIUM"], 0.0)
        self.assertEqual(labels["HIGH"], 0.0)
        self.assertTrue(all(0.0 <= degree <= 1.0 for degree in labels.values()))

    def test_trapezoid_shoulder_endpoints_are_included(self):
        for value, label in ((0.0, "LOW"), (1.0, "HIGH")):
            payload = self.fixture()
            payload["input"]["dimensions"][0]["value"] = value
            result = self.fuzzify_payload(payload)
            self.assertIsInstance(result, Memberships)
            degrees = {degree.label: degree.degree for degree in result.dimensions[0].labels}
            self.assertEqual(degrees[label], 1.0)
            self.assertTrue(all(0.0 <= degree <= 1.0 for degree in degrees.values()))

    def test_missing_dimension_returns_typed_error_without_output(self):
        payload = self.fixture()
        payload["input"]["dimensions"][0]["dimension"] = "unknown_dimension"
        result = self.fuzzify_payload(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.stage, "fuzzy.membership")
        self.assertFalse(hasattr(result, "dimensions"))

    def test_unordered_points_return_typed_error_without_mutating_inputs(self):
        payload = self.fixture()
        original = copy.deepcopy(payload)
        payload["policy"]["dimensions"][0]["labels"][1]["shape"] |= {"a": 0.75, "b": 0.5, "c": 0.25}
        candidate = MembershipInput.model_validate(payload["input"])
        policy = MembershipPolicy.model_validate(payload["policy"])
        result = fuzzify(candidate, policy, record_id="memberships:bad", created_at="2026-09-12T10:00:00Z")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(candidate.model_dump(mode="json"), original["input"])
        self.assertEqual(policy.dimensions[0].labels[1].shape.a, 0.75)

    def test_out_of_range_policy_points_return_typed_error(self):
        payload = self.fixture()
        payload["policy"]["dimensions"][0]["labels"][0]["shape"]["a"] = -0.1
        result = self.fuzzify_payload(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.source_ids, ("membership-input:001", "membership-policy:001"))


class InferenceHandoff(ContractValue):
    memberships: Memberships
    expected_timeline_id: str

    def active_degrees(self):
        if self.memberships.timeline_id != self.expected_timeline_id:
            return DomainError(code=ErrorCode.OLD_TIMELINE, stage="fuzzy.inference",
                               retryable=False, source_ids=(self.memberships.record_id,),
                               public_message="Memberships are from a different timeline.")
        return {
            (dimension.dimension, degree.label): degree.degree
            for dimension in self.memberships.dimensions
            for degree in dimension.labels
            if degree.degree > 0.0
        }


class FuzzifyAdjacentHandoffTests(unittest.TestCase):
    def fixture(self):
        return json.loads((FIXTURES / "membership-t01-valid.json").read_text())

    def result_from_fixture(self):
        fixture = self.fixture()
        return fuzzify(
            MembershipInput.model_validate(fixture["input"]),
            MembershipPolicy.model_validate(fixture["policy"]),
            record_id="memberships:handoff",
            created_at="2026-09-12T10:00:00Z",
        )

    def test_memberships_satisfy_next_inference_handoff_without_schema_changes(self):
        result = self.result_from_fixture()
        self.assertIsInstance(result, Memberships)
        before = result.model_dump(mode="json")
        handoff = InferenceHandoff(memberships=result, expected_timeline_id="timeline:002")
        self.assertEqual(handoff.active_degrees(), {("fear", "LOW"): 0.2, ("fear", "MEDIUM"): 0.6})
        self.assertEqual(result.model_dump(mode="json"), before)
        self.assertEqual(result.source_ids, ("membership-input:001", "candidate:001", "membership-policy:001"))

    def test_mismatched_policy_timeline_or_version_returns_typed_error(self):
        for update in (
            {"timeline_id": "timeline:old"},
            {"policy": {"policy_id": "fuzzy:membership", "version": "v2"}},
        ):
            fixture = self.fixture()
            fixture["policy"] |= update
            result = fuzzify(
                MembershipInput.model_validate(fixture["input"]),
                MembershipPolicy.model_validate(fixture["policy"]),
                record_id="memberships:rejected",
                created_at="2026-09-12T10:00:00Z",
            )
            self.assertIsInstance(result, DomainError)
            self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
            self.assertFalse(hasattr(result, "dimensions"))

    def test_next_handoff_rejects_old_timeline_memberships(self):
        result = self.result_from_fixture()
        self.assertIsInstance(result, Memberships)
        rejection = InferenceHandoff(memberships=result, expected_timeline_id="timeline:old").active_degrees()
        self.assertIsInstance(rejection, DomainError)
        self.assertEqual(rejection.code, ErrorCode.OLD_TIMELINE)
        self.assertEqual(rejection.source_ids, ("memberships:handoff",))


if __name__ == "__main__":
    unittest.main()
