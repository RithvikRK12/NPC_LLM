"""Gateway contract codec contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, EngineAction, ErrorCode
from app.gateway.contract_codec import (
    CommandResult,
    DecodeCommand,
    GatewayCommand,
    GatewayDisplayRecord,
    GatewayOutcomeRecord,
    decode_command,
)


FIXTURES = Path(__file__).parent / "fixtures" / "gateway"


class GatewayContractCodecContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "contract-codec-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "contract-codec-t01-rejected.json").read_text())

    def test_golden_round_trip_payload_records_and_result(self):
        payload = self.valid["payload"]
        for model, value in (
            (GatewayCommand, payload["command"]),
            (GatewayDisplayRecord, payload["displays"][0]),
            (GatewayOutcomeRecord, payload["outcomes"][0]),
            (CommandResult, self.valid["result"]),
        ):
            with self.subTest(model=model.__name__):
                result = model.model_validate_json(json.dumps(value))
                self.assertEqual(result.model_dump(mode="json"), value)
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        command = GatewayCommand.model_validate(payload["command"])
        self.assertEqual(command.kind, EngineAction.APPROACH_TARGET)

    def test_rejected_fixture_returns_unsupported_version_error(self):
        result = decode_command(self.rejected["payload"], current_timeline_id="timeline:main")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.model_dump(mode="json"), self.rejected["error"])

    def test_missing_required_fields_and_invalid_shapes_are_rejected(self):
        for model, value, fields in (
            (GatewayCommand, self.valid["payload"]["command"], ("command_id", "kind", "parameters", "issued_at", "expires_at", "source_ids")),
            (GatewayDisplayRecord, self.valid["payload"]["displays"][0], ("display_id", "text", "condition")),
            (GatewayOutcomeRecord, self.valid["payload"]["outcomes"][0], ("outcome_id", "command_id", "success", "occurred_at")),
            (CommandResult, self.valid["result"], ("command", "source_ids")),
        ):
            for field in fields:
                payload = copy.deepcopy(value)
                del payload[field]
                with self.subTest(model=model.__name__, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        command = copy.deepcopy(self.valid["payload"]["command"])
        command["target_id"] = None
        with self.assertRaises(ValidationError):
            GatewayCommand.model_validate(command)
        result = copy.deepcopy(self.valid["result"])
        result["outcomes"][0]["command_id"] = "command:other"
        with self.assertRaises(ValidationError):
            CommandResult.model_validate(result)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        expected = CommandResult.model_validate(self.valid["result"])

        def fake(payload, *, current_timeline_id: str):
            self.assertEqual(current_timeline_id, expected.timeline_id)
            return expected

        decoder: DecodeCommand = fake
        self.assertEqual(decoder(self.valid["payload"], current_timeline_id="timeline:main"), expected)
        self.assertEqual(self.valid, original)
        self.valid["payload"]["command"]["kind"] = "idle"
        self.assertEqual(expected.command.kind, EngineAction.APPROACH_TARGET)
        with self.assertRaises(ValidationError):
            expected.command.kind = EngineAction.IDLE

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.gateway.contract_codec; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class GatewayContractCodecBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "contract-codec-t01-valid.json").read_text())

    def _decode(self, payload=None, timeline="timeline:main"):
        return decode_command(copy.deepcopy(payload or self.valid["payload"]), current_timeline_id=timeline)

    def test_valid_fixture_decodes_exact_command_result_from_dict_and_json(self):
        for payload in (self.valid["payload"], json.dumps(self.valid["payload"])):
            with self.subTest(kind=type(payload).__name__):
                result = decode_command(payload, current_timeline_id="timeline:main")
                self.assertIsInstance(result, CommandResult)
                self.assertEqual(result.model_dump(mode="json"), self.valid["result"])

    def test_move_to_command_decodes_position_target(self):
        payload = copy.deepcopy(self.valid["payload"])
        payload["record_id"] = "command-result:move"
        payload["command"]["record_id"] = "gateway-command:move"
        payload["command"]["command_id"] = "command:move"
        payload["command"]["kind"] = "move_to"
        payload["command"]["target_id"] = None
        payload["command"]["position"] = {"x": 4.0, "y": 5.0, "area_id": "area:market", "spatial_revision": 12}
        payload["outcomes"][0]["command_id"] = "command:move"
        result = self._decode(payload)
        self.assertIsInstance(result, CommandResult)
        self.assertEqual(result.command.position.area_id, "area:market")
        self.assertIsNone(result.target_id)

    def test_display_and_outcome_records_are_decoded_without_applying_changes(self):
        result = self._decode()
        self.assertIsInstance(result, CommandResult)
        self.assertEqual(result.displays[0].display_id, "dialogue:commitment:001")
        self.assertEqual(result.outcomes[0].outcome_id, "outcome:arrival:001")
        self.assertTrue(result.outcomes[0].success)

    def test_old_timeline_returns_typed_error(self):
        result = self._decode(timeline="timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)
        self.assertEqual(result.public_message, "Command payload timeline is no longer current.")


class GatewayContractCodecInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "contract-codec-t01-valid.json").read_text())

    def _decode(self, payload=None):
        return decode_command(copy.deepcopy(payload or self.valid["payload"]), current_timeline_id="timeline:main")

    def test_unknown_action_missing_target_and_nonfinite_values_reject(self):
        payload = copy.deepcopy(self.valid["payload"])
        payload["command"]["kind"] = "teleport"
        result = self._decode(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNKNOWN_ENUM)

        payload = copy.deepcopy(self.valid["payload"])
        payload["command"]["target_id"] = None
        result = self._decode(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        payload = copy.deepcopy(self.valid["payload"])
        payload["command"]["parameters"]["max_speed"] = float("nan")
        result = self._decode(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

    def test_missing_parameter_and_extra_position_reject(self):
        payload = copy.deepcopy(self.valid["payload"])
        payload["command"]["parameters"]["arrival_distance"] = None
        result = self._decode(payload)
        self.assertIsInstance(result, DomainError)

        payload = copy.deepcopy(self.valid["payload"])
        payload["command"]["position"] = {"x": 1.0, "y": 1.0, "area_id": "area:market", "spatial_revision": 12}
        result = self._decode(payload)
        self.assertIsInstance(result, DomainError)

    def test_ids_and_backend_parameter_ranges_are_preserved(self):
        result = self._decode()
        self.assertIsInstance(result, CommandResult)
        self.assertEqual(result.command.command_id, "command:001")
        self.assertEqual(result.command.approval_id, "approval:001")
        self.assertEqual(result.command.parameters.max_speed, 120.0)
        self.assertEqual(result.command.parameters.arrival_distance, 24.0)


class ControllerLifecycleInput(ContractEnvelope):
    command_id: str
    kind: EngineAction
    controller_revision: int
    command_target_id: str | None


def accept_controller_lifecycle_input(result: CommandResult, expected_timeline: str):
    if result.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="controllers.lifecycle",
            retryable=False,
            source_ids=(result.record_id,),
            public_message="Decoded command timeline is no longer current.",
        )
    return ControllerLifecycleInput(
        schema_version=result.schema_version,
        record_id="controller-lifecycle-input:001",
        trace_id=result.trace_id,
        causation_id=result.record_id,
        game_id=result.game_id,
        timeline_id=result.timeline_id,
        npc_id=result.npc_id,
        actor_id=result.actor_id,
        target_id=result.target_id,
        created_at=result.created_at,
        source_ids=(result.record_id,),
        policy_versions=result.policy_versions,
        command_id=result.command.command_id,
        kind=result.command.kind,
        controller_revision=result.command.controller_revision,
        command_target_id=result.command.target_id,
    )


class GatewayContractCodecHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "contract-codec-t01-valid.json").read_text())

    def _result(self):
        result = decode_command(self.valid["payload"], current_timeline_id="timeline:main")
        self.assertIsInstance(result, CommandResult)
        return result

    def test_decoded_command_satisfies_controller_lifecycle_handoff(self):
        result = self._result()
        handoff = accept_controller_lifecycle_input(result, "timeline:main")
        self.assertIsInstance(handoff, ControllerLifecycleInput)
        self.assertEqual(handoff.command_id, "command:001")
        self.assertEqual(handoff.kind, EngineAction.APPROACH_TARGET)
        with self.assertRaises(ValidationError):
            handoff.command_id = "command:other"

    def test_controller_lifecycle_handoff_rejects_mismatched_timeline(self):
        result = self._result()
        handoff = accept_controller_lifecycle_input(result, "timeline:reset")
        self.assertIsInstance(handoff, DomainError)
        self.assertEqual(handoff.code, ErrorCode.OLD_TIMELINE)
