"""Role permission contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode, PolicyVersion
from app.roles.permissions import (
    EvaluateRolePermission,
    PermissionReason,
    PermissionStatus,
    RoleAction,
    RolePermission,
    RoleProfile,
    RoleProposal,
    RoleWorldView,
    evaluate,
)


FIXTURES = Path(__file__).parent / "fixtures" / "roles"


class RolesPermissionsContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "permissions-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "permissions-t01-rejected.json").read_text())

    def test_golden_round_trip_proposal_world_profile_and_permission(self):
        for model, key in (
            (RoleProposal, "proposal"),
            (RoleWorldView, "world"),
            (RoleProfile, "profile"),
            (RolePermission, "permission"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        proposal = RoleProposal.model_validate(self.valid["proposal"])
        self.assertEqual(proposal.action, RoleAction.CRAFT_ITEM)

    def test_rejected_fixture_has_unsupported_action_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            RoleProposal.model_validate(self.rejected["proposal"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.UNKNOWN_ENUM)
        self.assertEqual(rejection.stage, "roles.permissions")

    def test_missing_required_fields_and_duplicates_are_rejected(self):
        for model, key, fields in (
            (RoleProposal, "proposal", ("proposal_id", "action", "source_ids")),
            (RoleWorldView, "world", ("entity_ids", "workshops", "available_material_ids")),
            (RoleProfile, "profile", ("profile", "role_id", "known_role_ids", "allowed_actions", "denied_actions")),
            (RolePermission, "permission", ("proposal_id", "profile", "role_id", "status", "action", "reasons")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        proposal = copy.deepcopy(self.valid["proposal"])
        proposal["required_material_ids"].append("item:wood")
        with self.assertRaises(ValidationError):
            RoleProposal.model_validate(proposal)
        profile = copy.deepcopy(self.valid["profile"])
        profile["allowed_actions"].append("speak")
        with self.assertRaises(ValidationError):
            RoleProfile.model_validate(profile)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        proposal = RoleProposal.model_validate(self.valid["proposal"])
        world = RoleWorldView.model_validate(self.valid["world"])
        profile = RoleProfile.model_validate(self.valid["profile"])
        expected = RolePermission.model_validate(self.valid["permission"])

        def fake(proposal: RoleProposal, world: RoleWorldView, profile: RoleProfile):
            self.assertEqual(proposal.proposal_id, expected.proposal_id)
            self.assertEqual(profile.profile, expected.profile)
            return expected

        evaluator: EvaluateRolePermission = fake
        self.assertEqual(evaluator(proposal, world, profile), expected)
        self.assertEqual(self.valid, original)
        self.valid["proposal"]["action"] = "speak"
        self.assertEqual(proposal.action, RoleAction.CRAFT_ITEM)
        with self.assertRaises(ValidationError):
            proposal.action = RoleAction.SPEAK
        with self.assertRaises(TypeError):
            profile.allowed_actions[0] = RoleAction.ATTACK

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.roles.permissions; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class RolesPermissionsBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "permissions-t01-valid.json").read_text())

    def _evaluate(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return evaluate(
            RoleProposal.model_validate(data["proposal"]),
            RoleWorldView.model_validate(data["world"]),
            RoleProfile.model_validate(data["profile"]),
            record_id="role-permission:001",
        )

    def test_valid_fixture_produces_exact_permission(self):
        result = self._evaluate()
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.model_dump(mode="json"), self.valid["permission"])

    def test_allowlists_targets_and_duties_allow_safe_speech(self):
        payload = copy.deepcopy(self.valid)
        payload["proposal"]["proposal_id"] = "proposal:speak"
        payload["proposal"]["action"] = "speak"
        payload["proposal"]["required_material_ids"] = []
        payload["world"]["active_grants"] = []
        result = self._evaluate(payload)
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.status, PermissionStatus.ALLOWED)
        self.assertEqual(result.reasons, (PermissionReason.ALLOWED,))

    def test_active_cooperation_grant_is_recorded_for_matching_action(self):
        result = self._evaluate()
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.grant_ids, ("grant:craft_help",))

    def test_action_not_allowed_and_target_denied_are_explicit(self):
        payload = copy.deepcopy(self.valid)
        payload["proposal"]["action"] = "request_materials"
        payload["profile"]["allowed_actions"] = ["speak"]
        result = self._evaluate(payload)
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.status, PermissionStatus.DENIED)
        self.assertEqual(result.reasons, (PermissionReason.ACTION_NOT_ALLOWED,))

        payload = copy.deepcopy(self.valid)
        payload["proposal"]["target_id"] = "npc:intruder"
        result = self._evaluate(payload)
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.reasons, (PermissionReason.TARGET_DENIED,))

    def test_profile_and_world_mismatch_return_typed_errors(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["timeline_id"] = "timeline:old"
        result = self._evaluate(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Role world evidence is mismatched.")

        payload = copy.deepcopy(self.valid)
        payload["profile"]["profile"]["version"] = "v2"
        result = self._evaluate(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Role profile version is not present in proposal.")


class RolesPermissionsInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "permissions-t01-valid.json").read_text())

    def _evaluate(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return evaluate(
            RoleProposal.model_validate(data["proposal"]),
            RoleWorldView.model_validate(data["world"]),
            RoleProfile.model_validate(data["profile"]),
            record_id="role-permission:001",
        )

    def test_unknown_role_is_denied(self):
        payload = copy.deepcopy(self.valid)
        payload["profile"]["role_id"] = "role:unknown"
        result = self._evaluate(payload)
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.status, PermissionStatus.DENIED)
        self.assertEqual(result.reasons, (PermissionReason.UNKNOWN_ROLE,))

    def test_peaceful_role_cannot_attack_even_if_action_is_added_to_allowlist(self):
        payload = copy.deepcopy(self.valid)
        payload["proposal"]["action"] = "attack"
        payload["proposal"]["required_material_ids"] = []
        payload["profile"]["allowed_actions"].append("attack")
        result = self._evaluate(payload)
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.status, PermissionStatus.DENIED)
        self.assertEqual(result.reasons, (PermissionReason.ACTION_DENIED,))

    def test_missing_workshop_and_material_prerequisites_deny_crafting(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["workshops"][0]["available"] = False
        result = self._evaluate(payload)
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.reasons, (PermissionReason.MISSING_WORKSHOP,))

        payload = copy.deepcopy(self.valid)
        payload["world"]["available_material_ids"] = ["item:wood"]
        result = self._evaluate(payload)
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.reasons, (PermissionReason.MISSING_MATERIALS,))

    def test_ordinary_refusal_cannot_contradict_active_grant(self):
        payload = copy.deepcopy(self.valid)
        payload["proposal"]["action"] = "refuse"
        payload["proposal"]["required_material_ids"] = []
        payload["world"]["active_grants"] = [{"grant_id": "grant:craft_help", "action": "refuse", "target_id": "player:hero"}]
        result = self._evaluate(payload)
        self.assertIsInstance(result, RolePermission)
        self.assertEqual(result.status, PermissionStatus.DENIED)
        self.assertEqual(result.reasons, (PermissionReason.ACTIVE_GRANT,))


class RoleConditionInput(ContractEnvelope):
    proposal_id: str
    profile: PolicyVersion
    status: PermissionStatus
    reasons: tuple[PermissionReason, ...]


def accept_role_condition_input(permission: RolePermission, expected_policy: PolicyVersion, expected_timeline: str):
    if permission.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="roles.condition",
            retryable=False,
            source_ids=(permission.record_id,),
            public_message="Role permission timeline is no longer current.",
        )
    if permission.profile != expected_policy:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="roles.condition",
            retryable=False,
            source_ids=(permission.record_id,),
            public_message="Role permission profile does not match conditioner input.",
        )
    return RoleConditionInput(
        schema_version=permission.schema_version,
        record_id="role-condition-input:001",
        trace_id=permission.trace_id,
        causation_id=permission.record_id,
        game_id=permission.game_id,
        timeline_id=permission.timeline_id,
        npc_id=permission.npc_id,
        actor_id=permission.actor_id,
        target_id=permission.target_id,
        created_at=permission.created_at,
        source_ids=(permission.record_id,),
        policy_versions=permission.policy_versions,
        proposal_id=permission.proposal_id,
        profile=permission.profile,
        status=permission.status,
        reasons=permission.reasons,
    )


class RolesPermissionsHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "permissions-t01-valid.json").read_text())

    def _permission(self):
        result = evaluate(
            RoleProposal.model_validate(self.valid["proposal"]),
            RoleWorldView.model_validate(self.valid["world"]),
            RoleProfile.model_validate(self.valid["profile"]),
            record_id="role-permission:001",
        )
        self.assertIsInstance(result, RolePermission)
        return result

    def test_role_permission_satisfies_role_condition_handoff(self):
        permission = self._permission()
        handoff = accept_role_condition_input(permission, permission.profile, "timeline:main")
        self.assertIsInstance(handoff, RoleConditionInput)
        self.assertEqual(handoff.proposal_id, "proposal:craft_blaster")
        self.assertEqual(handoff.status, PermissionStatus.ALLOWED)
        with self.assertRaises(ValidationError):
            handoff.reasons = ()

    def test_role_condition_handoff_rejects_mismatched_policy_and_timeline(self):
        permission = self._permission()
        result = accept_role_condition_input(permission, PolicyVersion(policy_id="roles:permissions", version="v2"), "timeline:main")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        result = accept_role_condition_input(permission, permission.profile, "timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)

