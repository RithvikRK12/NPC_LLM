"""Dialogue composition contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DialogueKind, DialogueTiming, DomainError, ErrorCode, Expression, PolicyVersion
from app.dialogue.compose import (
    ApprovedDialogue,
    ComposeDialogue,
    DialogueEvent,
    DialoguePolicy,
    DialogueSourceKind,
    VerifiedEventKind,
    compose,
)


FIXTURES = Path(__file__).parent / "fixtures" / "dialogue"


class DialogueComposeContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "compose-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "compose-t01-rejected.json").read_text())

    def test_golden_round_trip_source_policy_and_event(self):
        for model, key in (
            (ApprovedDialogue, "source"),
            (DialoguePolicy, "policy"),
            (DialogueEvent, "event"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        source = ApprovedDialogue.model_validate(self.valid["source"])
        self.assertEqual(source.kind, DialogueSourceKind.VERIFIED_EVENT)
        self.assertEqual(source.verified_event_kind, VerifiedEventKind.QUEST_REWARD_GRANTED)

    def test_rejected_fixture_has_unsupported_kind_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            ApprovedDialogue.model_validate(self.rejected["source"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.UNKNOWN_ENUM)
        self.assertEqual(rejection.stage, "dialogue.compose")

    def test_missing_required_fields_and_invalid_shapes_are_rejected(self):
        for model, key, fields in (
            (ApprovedDialogue, "source", ("source_id", "kind", "expression", "source_ids")),
            (DialoguePolicy, "policy", ("policy", "max_text_chars", "safe_ambiguous_success_text", "outcome_templates")),
            (DialogueEvent, "event", ("display_id", "source_id", "text", "condition", "policy")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        source = copy.deepcopy(self.valid["source"])
        source["verified_event_id"] = None
        with self.assertRaises(ValidationError):
            ApprovedDialogue.model_validate(source)
        event = copy.deepcopy(self.valid["event"])
        event["condition"]["verified_outcome_id"] = None
        with self.assertRaises(ValidationError):
            DialogueEvent.model_validate(event)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        source = ApprovedDialogue.model_validate(self.valid["source"])
        policy = DialoguePolicy.model_validate(self.valid["policy"])
        expected = DialogueEvent.model_validate(self.valid["event"])

        def fake(source: ApprovedDialogue, policy: DialoguePolicy):
            self.assertEqual(source.source_id, expected.source_id)
            self.assertEqual(policy.policy, expected.policy)
            return expected

        composer: ComposeDialogue = fake
        self.assertEqual(composer(source, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["source"]["event_fields"]["item_name"] = "Changed"
        self.assertEqual(source.event_fields["item_name"], "Pulse Blaster")
        with self.assertRaises(ValidationError):
            source.kind = DialogueSourceKind.EXPRESSION

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.dialogue.compose; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class DialogueComposeBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "compose-t01-valid.json").read_text())

    def _compose(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return compose(
            ApprovedDialogue.model_validate(data["source"]),
            DialoguePolicy.model_validate(data["policy"]),
            record_id="dialogue-event:001",
            display_id="dialogue:001",
        )

    def test_valid_fixture_composes_exact_outcome_event(self):
        result = self._compose()
        self.assertIsInstance(result, DialogueEvent)
        self.assertEqual(result.model_dump(mode="json"), self.valid["event"])

    def test_expression_wording_is_preserved_when_bounded(self):
        payload = copy.deepcopy(self.valid)
        payload["source"]["kind"] = "expression"
        payload["source"]["approved_text"] = "The grid is unstable, but I can guide you."
        payload["source"]["verified_event_id"] = None
        payload["source"]["verified_event_kind"] = None
        payload["source"]["event_fields"] = {}
        result = self._compose(payload)
        self.assertIsInstance(result, DialogueEvent)
        self.assertEqual(result.text, "The grid is unstable, but I can guide you.")
        self.assertEqual(result.condition.kind, DialogueKind.EXPRESSION)

    def test_commitment_wording_uses_commitment_timing(self):
        payload = copy.deepcopy(self.valid)
        payload["source"]["kind"] = "commitment"
        payload["source"]["approved_text"] = "I will hold the bench until you return."
        payload["source"]["verified_event_id"] = None
        payload["source"]["verified_event_kind"] = None
        payload["source"]["event_fields"] = {}
        result = self._compose(payload)
        self.assertIsInstance(result, DialogueEvent)
        self.assertEqual(result.condition.kind, DialogueKind.COMMITMENT)
        self.assertEqual(result.condition.timing, DialogueTiming.ON_COMMAND_ACCEPTED)

    def test_item_transfer_uses_transfer_template_not_reward_template(self):
        payload = copy.deepcopy(self.valid)
        payload["source"]["source_id"] = "event:water_transfer"
        payload["source"]["verified_event_id"] = "event:water_transfer"
        payload["source"]["verified_event_kind"] = "item_transferred"
        payload["source"]["event_fields"] = {"item_name": "Water"}
        result = self._compose(payload)
        self.assertIsInstance(result, DialogueEvent)
        self.assertEqual(result.text, "Transfer confirmed: Water.")
        self.assertNotIn("Pulse Blaster online", result.text)

    def test_policy_mismatch_returns_typed_error(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["timeline_id"] = "timeline:old"
        result = self._compose(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Dialogue policy evidence is mismatched.")

        payload = copy.deepcopy(self.valid)
        payload["policy"]["policy"]["version"] = "v2"
        result = self._compose(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Dialogue policy version is not present in source.")


class DialogueComposeInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "compose-t01-valid.json").read_text())

    def _compose(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return compose(
            ApprovedDialogue.model_validate(data["source"]),
            DialoguePolicy.model_validate(data["policy"]),
            record_id="dialogue-event:001",
            display_id="dialogue:001",
        )

    def test_unverified_outcome_reference_is_rejected_by_contract(self):
        payload = copy.deepcopy(self.valid["source"])
        payload["kind"] = "verified_event"
        payload["verified_event_id"] = None
        with self.assertRaises(ValidationError):
            ApprovedDialogue.model_validate(payload)

    def test_missing_template_fields_reject_outcome(self):
        payload = copy.deepcopy(self.valid)
        payload["source"]["event_fields"] = {}
        result = self._compose(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNGROUNDED_REFERENCE)

    def test_unsupported_verified_event_kind_rejected(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["outcome_templates"] = [payload["policy"]["outcome_templates"][1]]
        result = self._compose(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNSUPPORTED_CAPABILITY)

    def test_ambiguous_generated_success_claim_uses_safe_line(self):
        payload = copy.deepcopy(self.valid)
        payload["source"]["kind"] = "expression"
        payload["source"]["approved_text"] = "Done, I gave you the reward."
        payload["source"]["verified_event_id"] = None
        payload["source"]["verified_event_kind"] = None
        payload["source"]["event_fields"] = {}
        result = self._compose(payload)
        self.assertIsInstance(result, DialogueEvent)
        self.assertEqual(result.text, payload["policy"]["safe_ambiguous_success_text"])


class DialogueTimingInput(ContractEnvelope):
    display_id: str
    condition_kind: DialogueKind
    verified_outcome_id: str | None
    policy: PolicyVersion


def accept_dialogue_timing_input(event: DialogueEvent, expected_policy: PolicyVersion, expected_timeline: str):
    if event.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="dialogue.timing",
            retryable=False,
            source_ids=(event.record_id,),
            public_message="Dialogue event timeline is no longer current.",
        )
    if event.policy != expected_policy:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="dialogue.timing",
            retryable=False,
            source_ids=(event.record_id,),
            public_message="Dialogue event policy does not match timing input.",
        )
    return DialogueTimingInput(
        schema_version=event.schema_version,
        record_id="dialogue-timing-input:001",
        trace_id=event.trace_id,
        causation_id=event.record_id,
        game_id=event.game_id,
        timeline_id=event.timeline_id,
        npc_id=event.npc_id,
        actor_id=event.actor_id,
        target_id=event.target_id,
        created_at=event.created_at,
        source_ids=(event.record_id,),
        policy_versions=event.policy_versions,
        display_id=event.display_id,
        condition_kind=event.condition.kind,
        verified_outcome_id=event.condition.verified_outcome_id,
        policy=event.policy,
    )


class DialogueComposeHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "compose-t01-valid.json").read_text())

    def _event(self):
        result = compose(
            ApprovedDialogue.model_validate(self.valid["source"]),
            DialoguePolicy.model_validate(self.valid["policy"]),
            record_id="dialogue-event:001",
            display_id="dialogue:001",
        )
        self.assertIsInstance(result, DialogueEvent)
        return result

    def test_dialogue_event_satisfies_dialogue_timing_handoff(self):
        event = self._event()
        handoff = accept_dialogue_timing_input(event, event.policy, "timeline:main")
        self.assertIsInstance(handoff, DialogueTimingInput)
        self.assertEqual(handoff.display_id, "dialogue:001")
        self.assertEqual(handoff.verified_outcome_id, "event:quest_reward_001")
        with self.assertRaises(ValidationError):
            handoff.display_id = "dialogue:other"

    def test_dialogue_timing_handoff_rejects_mismatched_policy_and_timeline(self):
        event = self._event()
        result = accept_dialogue_timing_input(event, PolicyVersion(policy_id="dialogue:compose", version="v2"), "timeline:main")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        result = accept_dialogue_timing_input(event, event.policy, "timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)

