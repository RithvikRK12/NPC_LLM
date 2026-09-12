"""T01 structure/fake-boundary tests; fixture degrees are not algorithm evidence."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import DomainError, ErrorCode
from app.domain.fuzzy.membership import (
    Fuzzify, MembershipInput, MembershipPolicy, Memberships, Triangle, Trapezoid,
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


if __name__ == "__main__":
    unittest.main()
