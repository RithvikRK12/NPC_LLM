"""Memory classification contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode, PolicyVersion
from app.memory.classify import (
    ApprovedConversationOrEvent,
    ClassificationSourceKind,
    ClassifyMemory,
    ImportancePolicy,
    MemoryCategory,
    MemoryDecision,
    VerifiedEventType,
    classify,
)
from app.memory.reconcile import EpistemicStatus, EvidenceAuthority


FIXTURES = Path(__file__).parent / "fixtures" / "memory"


class MemoryClassifyContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "classify-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "classify-t01-rejected.json").read_text())

    def test_golden_round_trip_source_policy_and_decision(self):
        for model, key in (
            (ApprovedConversationOrEvent, "source"),
            (ImportancePolicy, "policy"),
            (MemoryDecision, "decision"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        source = ApprovedConversationOrEvent.model_validate(self.valid["source"])
        self.assertEqual(source.source_kind, ClassificationSourceKind.VERIFIED_EVENT)
        self.assertEqual(source.verified_event_type, VerifiedEventType.ITEM_TRANSFERRED)

    def test_rejected_fixture_has_unsupported_source_kind_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            ApprovedConversationOrEvent.model_validate(self.rejected["source"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.UNKNOWN_ENUM)
        self.assertEqual(rejection.stage, "memory.classify")

    def test_missing_required_fields_and_invalid_shapes_are_rejected(self):
        for model, key, fields in (
            (ApprovedConversationOrEvent, "source", ("source_kind", "grounded", "source_ids")),
            (ImportancePolicy, "policy", ("policy", "minimum_importance", "authoritative_event_importance", "exclude_greetings")),
            (MemoryDecision, "decision", ("category", "important", "importance", "reason", "summary", "status", "authority", "policy")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        source = copy.deepcopy(self.valid["source"])
        source["verified_event_type"] = None
        with self.assertRaises(ValidationError):
            ApprovedConversationOrEvent.model_validate(source)
        decision = copy.deepcopy(self.valid["decision"])
        decision["memory_id"] = None
        with self.assertRaises(ValidationError):
            MemoryDecision.model_validate(decision)
        decision = copy.deepcopy(self.valid["decision"])
        decision["authority"] = "reported"
        with self.assertRaises(ValidationError):
            MemoryDecision.model_validate(decision)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        source = ApprovedConversationOrEvent.model_validate(self.valid["source"])
        policy = ImportancePolicy.model_validate(self.valid["policy"])
        expected = MemoryDecision.model_validate(self.valid["decision"])

        def fake(source: ApprovedConversationOrEvent, policy: ImportancePolicy):
            self.assertEqual(source.record_id, expected.causation_id)
            self.assertEqual(policy.policy, expected.policy)
            return expected

        classifier: ClassifyMemory = fake
        self.assertEqual(classifier(source, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["source"]["object_id"] = "item:changed"
        self.assertEqual(source.object_id, "item:fruits")
        with self.assertRaises(ValidationError):
            source.object_id = "item:changed"

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.memory.classify; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class MemoryClassifyBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "classify-t01-valid.json").read_text())

    def _classify(self, payload=None, memory_id="memory:item-transfer-001"):
        data = copy.deepcopy(payload or self.valid)
        return classify(
            ApprovedConversationOrEvent.model_validate(data["source"]),
            ImportancePolicy.model_validate(data["policy"]),
            record_id="memory-decision:001",
            memory_id=memory_id,
        )

    def test_valid_fixture_produces_exact_verified_transfer_decision(self):
        result = self._classify()
        self.assertIsInstance(result, MemoryDecision)
        self.assertEqual(result.model_dump(mode="json"), self.valid["decision"])

    def test_player_commitment_is_retained_as_reported_claim_not_fact(self):
        payload = copy.deepcopy(self.valid)
        payload["source"]["source_kind"] = "approved_conversation"
        payload["source"]["player_text"] = "I promise I will bring the energy cell."
        payload["source"]["approved_dialogue"] = "I will remember you said that."
        payload["source"]["verified_event_type"] = None
        payload["source"]["subject_id"] = None
        payload["source"]["predicate"] = None
        payload["source"]["object_id"] = None
        payload["source"]["object_text"] = None
        payload["source"]["grounded"] = False
        result = self._classify(payload, "memory:commitment-001")
        self.assertIsInstance(result, MemoryDecision)
        self.assertEqual(result.category, MemoryCategory.COMMITMENT)
        self.assertEqual(result.status, EpistemicStatus.CLAIM)
        self.assertEqual(result.authority, EvidenceAuthority.REPORTED)
        self.assertEqual(result.predicate, "committed_to")
        self.assertTrue(result.important)

    def test_player_preference_and_personal_fact_are_reported_claims(self):
        for text, category, predicate, memory_id in (
            ("I prefer quiet routes through the market.", MemoryCategory.PREFERENCE, "prefers", "memory:preference-001"),
            ("My name is Rithvik.", MemoryCategory.PERSONAL_FACT, "stated_personal_fact", "memory:personal-001"),
        ):
            payload = copy.deepcopy(self.valid)
            payload["source"]["source_kind"] = "approved_conversation"
            payload["source"]["player_text"] = text
            payload["source"]["verified_event_type"] = None
            payload["source"]["subject_id"] = None
            payload["source"]["predicate"] = None
            payload["source"]["object_id"] = None
            payload["source"]["grounded"] = False
            with self.subTest(text=text):
                result = self._classify(payload, memory_id)
                self.assertIsInstance(result, MemoryDecision)
                self.assertEqual(result.category, category)
                self.assertEqual(result.predicate, predicate)
                self.assertEqual(result.status, EpistemicStatus.CLAIM)

    def test_verified_quest_events_qualify_independent_of_dialogue(self):
        for event_type, category, memory_id in (
            ("quest_progress", MemoryCategory.QUEST_PROGRESS, "memory:quest-progress-001"),
            ("quest_completed", MemoryCategory.QUEST_COMPLETION, "memory:quest-complete-001"),
        ):
            payload = copy.deepcopy(self.valid)
            payload["source"]["verified_event_type"] = event_type
            payload["source"]["approved_dialogue"] = "Whatever."
            payload["source"]["subject_id"] = "quest-run:pulse_001"
            payload["source"]["predicate"] = event_type
            payload["source"]["object_id"] = "quest:bow"
            with self.subTest(event_type=event_type):
                result = self._classify(payload, memory_id)
                self.assertIsInstance(result, MemoryDecision)
                self.assertEqual(result.category, category)
                self.assertEqual(result.status, EpistemicStatus.FACT)
                self.assertEqual(result.authority, EvidenceAuthority.AUTHORITATIVE)

    def test_policy_mismatch_returns_typed_error(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["timeline_id"] = "timeline:old"
        result = self._classify(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Memory classification policy evidence is mismatched.")

        payload = copy.deepcopy(self.valid)
        payload["policy"]["policy"]["version"] = "v2"
        result = self._classify(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Memory classification policy version is not present in source.")


class MemoryClassifyInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "classify-t01-valid.json").read_text())

    def _classify(self, payload=None, memory_id="memory:item-transfer-001"):
        data = copy.deepcopy(payload or self.valid)
        return classify(
            ApprovedConversationOrEvent.model_validate(data["source"]),
            ImportancePolicy.model_validate(data["policy"]),
            record_id="memory-decision:001",
            memory_id=memory_id,
        )

    def test_greetings_and_questions_are_not_durable(self):
        for text in ("hello", "Can you give me the axe?"):
            payload = copy.deepcopy(self.valid)
            payload["source"]["source_kind"] = "approved_conversation"
            payload["source"]["player_text"] = text
            payload["source"]["verified_event_type"] = None
            payload["source"]["subject_id"] = None
            payload["source"]["predicate"] = None
            payload["source"]["object_id"] = None
            payload["source"]["grounded"] = False
            with self.subTest(text=text):
                result = self._classify(payload, "memory:should-not-use")
                self.assertIsInstance(result, MemoryDecision)
                self.assertFalse(result.important)
                self.assertIsNone(result.memory_id)

    def test_rejected_output_and_provider_failure_are_excluded(self):
        for kind in ("rejected_output", "provider_failure"):
            payload = copy.deepcopy(self.valid)
            payload["source"]["source_kind"] = kind
            payload["source"]["verified_event_type"] = None
            payload["source"]["subject_id"] = None
            payload["source"]["predicate"] = None
            payload["source"]["object_id"] = None
            with self.subTest(kind=kind):
                result = self._classify(payload, "memory:should-not-use")
                self.assertIsInstance(result, MemoryDecision)
                self.assertEqual(result.category, MemoryCategory.EXCLUDED)
                self.assertFalse(result.important)
                self.assertEqual(result.importance, 0)

    def test_verified_transfer_retained_even_without_emotional_signal(self):
        payload = copy.deepcopy(self.valid)
        payload["source"]["approved_dialogue"] = "Fine."
        result = self._classify(payload)
        self.assertIsInstance(result, MemoryDecision)
        self.assertEqual(result.category, MemoryCategory.ITEM_TRANSFER)
        self.assertTrue(result.important)

    def test_player_claim_is_not_promoted_to_fact(self):
        payload = copy.deepcopy(self.valid)
        payload["source"]["source_kind"] = "approved_conversation"
        payload["source"]["player_text"] = "I will help with the repair."
        payload["source"]["verified_event_type"] = None
        payload["source"]["subject_id"] = None
        payload["source"]["predicate"] = None
        payload["source"]["object_id"] = None
        payload["source"]["grounded"] = False
        result = self._classify(payload, "memory:claim-001")
        self.assertIsInstance(result, MemoryDecision)
        self.assertEqual(result.status, EpistemicStatus.CLAIM)
        self.assertNotEqual(result.status, EpistemicStatus.FACT)
        self.assertEqual(result.authority, EvidenceAuthority.REPORTED)


class MemoryLifecycleInput(ContractEnvelope):
    memory_id: str
    category: MemoryCategory
    status: EpistemicStatus
    importance: float
    policy: PolicyVersion


def accept_memory_lifecycle_input(decision: MemoryDecision, expected_policy: PolicyVersion, expected_timeline: str):
    if decision.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="memory.lifecycle",
            retryable=False,
            source_ids=(decision.record_id,),
            public_message="Memory decision timeline is no longer current.",
        )
    if decision.policy != expected_policy:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="memory.lifecycle",
            retryable=False,
            source_ids=(decision.record_id,),
            public_message="Memory decision policy does not match lifecycle input.",
        )
    if not decision.important or decision.memory_id is None:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="memory.lifecycle",
            retryable=False,
            source_ids=(decision.record_id,),
            public_message="Only important memory decisions enter lifecycle.",
        )
    return MemoryLifecycleInput(
        schema_version=decision.schema_version,
        record_id="memory-lifecycle-input:001",
        trace_id=decision.trace_id,
        causation_id=decision.record_id,
        game_id=decision.game_id,
        timeline_id=decision.timeline_id,
        npc_id=decision.npc_id,
        actor_id=decision.actor_id,
        target_id=decision.target_id,
        created_at=decision.created_at,
        source_ids=(decision.record_id,),
        policy_versions=decision.policy_versions,
        memory_id=decision.memory_id,
        category=decision.category,
        status=decision.status,
        importance=decision.importance,
        policy=decision.policy,
    )


class MemoryClassifyHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "classify-t01-valid.json").read_text())

    def _decision(self):
        result = classify(
            ApprovedConversationOrEvent.model_validate(self.valid["source"]),
            ImportancePolicy.model_validate(self.valid["policy"]),
            record_id="memory-decision:001",
            memory_id="memory:item-transfer-001",
        )
        self.assertIsInstance(result, MemoryDecision)
        return result

    def test_memory_decision_satisfies_lifecycle_handoff(self):
        decision = self._decision()
        handoff = accept_memory_lifecycle_input(decision, decision.policy, "timeline:main")
        self.assertIsInstance(handoff, MemoryLifecycleInput)
        self.assertEqual(handoff.memory_id, "memory:item-transfer-001")
        self.assertEqual(handoff.status, EpistemicStatus.FACT)
        with self.assertRaises(ValidationError):
            handoff.memory_id = "memory:other"

    def test_lifecycle_handoff_rejects_mismatched_policy_and_timeline(self):
        decision = self._decision()
        result = accept_memory_lifecycle_input(decision, PolicyVersion(policy_id="memory:classify", version="v2"), "timeline:main")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        result = accept_memory_lifecycle_input(decision, decision.policy, "timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)
