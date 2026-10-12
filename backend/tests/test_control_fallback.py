"""Control fallback contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode, PolicyVersion
from app.control.fallback import (
    BuildFallback,
    FailureContext,
    FailureKind,
    FallbackAction,
    FallbackCandidate,
    SafeBehaviorPolicy,
    SafeFallbackOption,
    build,
)


FIXTURES = Path(__file__).parent / "fixtures" / "control"


class ControlFallbackContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "fallback-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "fallback-t01-rejected.json").read_text())

    def test_golden_round_trip_context_policy_and_candidate(self):
        for model, key in (
            (FailureContext, "context"),
            (SafeBehaviorPolicy, "policy"),
            (FallbackCandidate, "candidate"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        context = FailureContext.model_validate(self.valid["context"])
        self.assertEqual(context.kind, FailureKind.ROLE_DENIED)

    def test_rejected_fixture_has_unsupported_failure_kind_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            FailureContext.model_validate(self.rejected["context"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.UNKNOWN_ENUM)
        self.assertEqual(rejection.stage, "control.fallback")

    def test_missing_required_fields_and_invalid_values_are_rejected(self):
        for model, key, fields in (
            (FailureContext, "context", ("failure_id", "kind", "failed_stage", "fallback_depth", "max_fallback_depth")),
            (SafeBehaviorPolicy, "policy", ("policy", "role_allowed_actions", "options")),
            (FallbackCandidate, "candidate", ("failure_id", "fallback_id", "policy", "status", "action", "public_message")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        payload = copy.deepcopy(self.valid["context"])
        payload["fallback_depth"] = 3
        with self.assertRaises(ValidationError):
            FailureContext.model_validate(payload)
        option = copy.deepcopy(self.valid["policy"]["options"][0])
        option["effect_ids"] = ["effect:reward"]
        candidate = copy.deepcopy(self.valid["candidate"])
        candidate["effect_ids"] = ["effect:reward"]
        with self.assertRaises(ValidationError):
            FallbackCandidate.model_validate(candidate)
        self.assertEqual(SafeFallbackOption.model_validate(option).effect_ids, ("effect:reward",))

    def test_policy_option_uniqueness_and_immutability_fake_execution(self):
        policy = copy.deepcopy(self.valid["policy"])
        policy["role_allowed_actions"].append("speak")
        with self.assertRaises(ValidationError):
            SafeBehaviorPolicy.model_validate(policy)
        policy = copy.deepcopy(self.valid["policy"])
        policy["options"].append(copy.deepcopy(policy["options"][0]))
        with self.assertRaises(ValidationError):
            SafeBehaviorPolicy.model_validate(policy)

        original = copy.deepcopy(self.valid)
        context = FailureContext.model_validate(self.valid["context"])
        policy = SafeBehaviorPolicy.model_validate(self.valid["policy"])
        expected = FallbackCandidate.model_validate(self.valid["candidate"])

        def fake(context: FailureContext, policy: SafeBehaviorPolicy):
            self.assertEqual(context.failure_id, expected.failure_id)
            return expected

        builder: BuildFallback = fake
        self.assertEqual(builder(context, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["context"]["kind"] = "path_blocked"
        self.assertEqual(context.kind, FailureKind.ROLE_DENIED)
        with self.assertRaises(ValidationError):
            context.kind = FailureKind.PATH_BLOCKED

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.control.fallback; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class ControlFallbackBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "fallback-t01-valid.json").read_text())

    def _build(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return build(
            FailureContext.model_validate(data["context"]),
            SafeBehaviorPolicy.model_validate(data["policy"]),
            record_id="fallback-candidate:001",
        )

    def test_valid_fixture_builds_exact_candidate(self):
        result = self._build()
        self.assertIsInstance(result, FallbackCandidate)
        self.assertEqual(result.model_dump(mode="json"), self.valid["candidate"])

    def test_declared_safe_idle_fallback_from_trusted_evidence(self):
        payload = copy.deepcopy(self.valid)
        payload["context"]["kind"] = "path_blocked"
        payload["context"]["allowed_target_ids"] = []
        result = self._build(payload)
        self.assertIsInstance(result, FallbackCandidate)
        self.assertEqual(result.action, FallbackAction.IDLE)
        self.assertIsNone(result.target_id)
        self.assertEqual(result.effect_ids, ())

    def test_role_incompatible_fallback_is_rejected_without_trying_model(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["role_allowed_actions"] = ["idle"]
        result = self._build(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNSUPPORTED_CAPABILITY)
        self.assertEqual(result.public_message, "Declared fallback action is not role-compatible.")

    def test_policy_evidence_mismatch_returns_typed_error(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["timeline_id"] = "timeline:old"
        result = self._build(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Safe fallback policy evidence is mismatched.")

        payload = copy.deepcopy(self.valid)
        payload["policy"]["policy"]["version"] = "v2"
        result = self._build(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Safe fallback policy version is not present in failure context.")


class ControlFallbackInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "fallback-t01-valid.json").read_text())

    def _build(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return build(
            FailureContext.model_validate(data["context"]),
            SafeBehaviorPolicy.model_validate(data["policy"]),
            record_id="fallback-candidate:001",
        )

    def test_no_fabricated_target_or_evidence(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["options"][0]["target_id"] = "npc:missing"
        result = self._build(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNGROUNDED_REFERENCE)
        self.assertEqual(result.public_message, "Declared fallback target is not available in trusted evidence.")

        payload = copy.deepcopy(self.valid)
        payload["policy"]["options"][0]["required_evidence_ids"] = ["event:invented"]
        result = self._build(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Declared fallback evidence is not available in trusted context.")

    def test_no_reward_or_state_effect_can_be_fallback(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["options"][0]["action"] = "grant_reward"
        payload["policy"]["role_allowed_actions"].append("grant_reward")
        result = self._build(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Declared fallback action is not zero-effect safe.")

        payload = copy.deepcopy(self.valid)
        payload["policy"]["options"][0]["effect_ids"] = ["effect:grant_item"]
        result = self._build(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Declared fallback must not carry effects.")

    def test_unsupported_fallback_and_loop_limit_are_rejected(self):
        payload = copy.deepcopy(self.valid)
        payload["context"]["kind"] = "model_unavailable"
        result = self._build(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNSUPPORTED_CAPABILITY)

        payload = copy.deepcopy(self.valid)
        payload["context"]["fallback_depth"] = 2
        result = self._build(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Fallback chain limit has been reached.")


class ControlValidationInput(ContractEnvelope):
    failure_id: str
    fallback_id: str
    policy: PolicyVersion
    action: FallbackAction
    effect_ids: tuple[str, ...]


def accept_control_validate_input(candidate: FallbackCandidate, expected_policy: PolicyVersion, expected_timeline: str):
    if candidate.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="control.validate",
            retryable=False,
            source_ids=(candidate.record_id,),
            public_message="Fallback candidate timeline is no longer current.",
        )
    if candidate.policy != expected_policy:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="control.validate",
            retryable=False,
            source_ids=(candidate.record_id,),
            public_message="Fallback candidate policy does not match validator input.",
        )
    return ControlValidationInput(
        schema_version=candidate.schema_version,
        record_id="control-validate-input:001",
        trace_id=candidate.trace_id,
        causation_id=candidate.record_id,
        game_id=candidate.game_id,
        timeline_id=candidate.timeline_id,
        npc_id=candidate.npc_id,
        actor_id=candidate.actor_id,
        target_id=candidate.target_id,
        created_at=candidate.created_at,
        source_ids=(candidate.record_id,),
        policy_versions=candidate.policy_versions,
        failure_id=candidate.failure_id,
        fallback_id=candidate.fallback_id,
        policy=candidate.policy,
        action=candidate.action,
        effect_ids=candidate.effect_ids,
    )


class ControlFallbackHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "fallback-t01-valid.json").read_text())

    def _candidate(self):
        result = build(
            FailureContext.model_validate(self.valid["context"]),
            SafeBehaviorPolicy.model_validate(self.valid["policy"]),
            record_id="fallback-candidate:001",
        )
        self.assertIsInstance(result, FallbackCandidate)
        return result

    def test_fallback_candidate_satisfies_control_validate_handoff(self):
        candidate = self._candidate()
        handoff = accept_control_validate_input(candidate, candidate.policy, "timeline:main")
        self.assertIsInstance(handoff, ControlValidationInput)
        self.assertEqual(handoff.failure_id, "failure:role_denied")
        self.assertEqual(handoff.effect_ids, ())
        with self.assertRaises(ValidationError):
            handoff.action = FallbackAction.IDLE

    def test_control_validate_handoff_rejects_mismatched_policy_and_timeline(self):
        candidate = self._candidate()
        result = accept_control_validate_input(candidate, PolicyVersion(policy_id="control:fallback", version="v2"), "timeline:main")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        result = accept_control_validate_input(candidate, candidate.policy, "timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)

