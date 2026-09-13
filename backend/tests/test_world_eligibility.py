"""T01 world eligibility contract and fake-boundary tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import DomainError, ErrorCode
from app.domain.world.eligibility import (
    CheckEligibility,
    EligibilityResult,
    EntityView,
    InteractionEvent,
    InteractionPolicy,
    WorldView,
)


FIXTURES = Path(__file__).parent / "fixtures" / "world"


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


if __name__ == "__main__":
    unittest.main()
