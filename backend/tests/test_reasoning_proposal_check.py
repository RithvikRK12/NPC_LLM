"""T01 reasoning proposal-check contract and fake-boundary tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, ContractValue, DomainError, EngineAction, ErrorCode, Intent, PolicyVersion
from app.reasoning.proposal_check import (
    DecisionProposal,
    GroundingReference,
    GroundingScope,
    ProposalPolicy,
    RawProposal,
    RelativeStateDelta,
    Snapshot,
    StateField,
    ValidateProposal,
    validate,
)


FIXTURES = Path(__file__).parent / "fixtures" / "reasoning"


class ReasoningProposalCheckContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "proposal-check-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "proposal-check-t01-rejected.json").read_text())

    def test_golden_round_trip_raw_snapshot_policy_and_decision(self):
        for model, key in (
            (RawProposal, "raw_proposal"),
            (Snapshot, "snapshot"),
            (ProposalPolicy, "policy"),
            (DecisionProposal, "decision"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        raw = RawProposal.model_validate(self.valid["raw_proposal"])
        self.assertEqual(raw.intent, Intent.HELP)
        self.assertEqual(raw.action, EngineAction.SPEAK)

    def test_rejected_fixture_has_unsupported_variant_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            RawProposal.model_validate(self.rejected["raw_proposal"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.UNKNOWN_ENUM)
        self.assertEqual(rejection.stage, "reasoning.proposal_check")
        self.assertEqual(DomainError.model_validate_json(rejection.model_dump_json()), rejection)

    def test_missing_required_fields_are_rejected(self):
        for model, key, fields in (
            (RawProposal, "raw_proposal", ("snapshot_id", "intent", "action", "confidence", "grounding")),
            (Snapshot, "snapshot", ("snapshot_id", "fact_ids", "memory_ids", "source_ids")),
            (ProposalPolicy, "policy", ("policy", "allowed_intents", "allowed_actions", "allowed_state_fields")),
            (DecisionProposal, "decision", ("proposal_id", "snapshot_id", "policy", "intent", "action")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)

    def test_closed_variants_and_finite_numeric_values_are_strict(self):
        raw = copy.deepcopy(self.valid["raw_proposal"])
        for field, value in (
            ("intent", "teleport"),
            ("action", "spawn_reward"),
            ("activity", "sleeping"),
            ("expression", "angry"),
        ):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                RawProposal.model_validate(raw | {field: value})
        for value in ("0.8", True, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                RawProposal.model_validate(raw | {"confidence": value})
        with self.assertRaises(ValidationError):
            RelativeStateDelta.model_validate({"field": "trust", "delta": 2.0, "source_ref_id": "fact:visible_wood"})
        with self.assertRaises(ValidationError):
            GroundingReference.model_validate({"scope": "database", "ref_id": "fact:visible_wood"})
        with self.assertRaises(ValidationError):
            RelativeStateDelta.model_validate({"field": "absolute_health", "delta": 0.2, "source_ref_id": "fact:visible_wood"})

    def test_duplicate_references_and_policy_values_are_rejected(self):
        snapshot = copy.deepcopy(self.valid["snapshot"])
        snapshot["memory_ids"].append("memory:recent_request")
        with self.assertRaises(ValidationError):
            Snapshot.model_validate(snapshot)
        raw = copy.deepcopy(self.valid["raw_proposal"])
        raw["grounding"].append(copy.deepcopy(raw["grounding"][0]))
        with self.assertRaises(ValidationError):
            RawProposal.model_validate(raw)
        policy = copy.deepcopy(self.valid["policy"])
        policy["allowed_actions"].append("speak")
        with self.assertRaises(ValidationError):
            ProposalPolicy.model_validate(policy)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        raw = RawProposal.model_validate(self.valid["raw_proposal"])
        snapshot = Snapshot.model_validate(self.valid["snapshot"])
        policy = ProposalPolicy.model_validate(self.valid["policy"])
        expected = DecisionProposal.model_validate(self.valid["decision"])

        def fake(raw_proposal: RawProposal, snapshot: Snapshot, policy: ProposalPolicy):
            self.assertEqual(raw_proposal.snapshot_id, snapshot.snapshot_id)
            self.assertEqual(policy.policy, expected.policy)
            return expected

        validate: ValidateProposal = fake
        self.assertEqual(validate(raw, snapshot, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["raw_proposal"]["confidence"] = 0.1
        self.assertEqual(raw.confidence, 0.82)
        with self.assertRaises(ValidationError):
            raw.confidence = 0.1
        with self.assertRaises(TypeError):
            snapshot.fact_ids[0] = "fact:changed"

    def test_fake_rejection_uses_shared_error_value(self):
        rejection = DomainError.model_validate(self.rejected["error"])

        def fake(raw_proposal: RawProposal, snapshot: Snapshot, policy: ProposalPolicy):
            return rejection

        validate: ValidateProposal = fake
        result = validate(
            RawProposal.model_validate(self.valid["raw_proposal"]),
            Snapshot.model_validate(self.valid["snapshot"]),
            ProposalPolicy.model_validate(self.valid["policy"]),
        )
        self.assertIs(result, rejection)
        self.assertEqual(result.code, ErrorCode.UNKNOWN_ENUM)

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.reasoning.proposal_check; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class ReasoningProposalCheckBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "proposal-check-t01-valid.json").read_text())

    def _validate(self, payload=None, *, proposal_id="proposal:001"):
        data = copy.deepcopy(payload or self.valid)
        return validate(
            RawProposal.model_validate(data["raw_proposal"]),
            Snapshot.model_validate(data["snapshot"]),
            ProposalPolicy.model_validate(data["policy"]),
            proposal_id=proposal_id,
        )

    def test_valid_t01_fixture_produces_exact_decision_proposal(self):
        result = self._validate()
        self.assertIsInstance(result, DecisionProposal)
        self.assertEqual(result.model_dump(mode="json"), self.valid["decision"])

    def test_closed_vocabulary_accepts_each_policy_permitted_intent_and_action(self):
        for intent in ("request_purpose", "decline", "converse"):
            payload = copy.deepcopy(self.valid)
            payload["raw_proposal"]["intent"] = intent
            result = self._validate(payload, proposal_id=f"proposal:{intent}")
            self.assertIsInstance(result, DecisionProposal)
            self.assertEqual(result.intent.value, intent)
        for action in ("face_target", "idle"):
            payload = copy.deepcopy(self.valid)
            payload["raw_proposal"]["action"] = action
            result = self._validate(payload, proposal_id=f"proposal:{action}")
            self.assertIsInstance(result, DecisionProposal)
            self.assertEqual(result.action.value, action)

    def test_relative_state_fields_accept_policy_permitted_deltas_only(self):
        payload = copy.deepcopy(self.valid)
        payload["raw_proposal"]["state_deltas"] = [
            {"field": "attention", "delta": -0.2, "source_ref_id": "fact:bow_requires_materials"},
            {"field": "urgency", "delta": 0.4, "source_ref_id": "memory:recent_request"},
        ]
        result = self._validate(payload, proposal_id="proposal:relative-deltas")
        self.assertIsInstance(result, DecisionProposal)
        self.assertEqual(tuple(delta.field for delta in result.state_deltas), (StateField.ATTENTION, StateField.URGENCY))
        self.assertEqual(tuple(delta.delta for delta in result.state_deltas), (-0.2, 0.4))

    def test_exact_source_snapshot_identity_and_policy_version_are_required(self):
        payload = copy.deepcopy(self.valid)
        payload["raw_proposal"]["snapshot_id"] = "snapshot:other"
        result = self._validate(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Proposal does not reference the source snapshot.")

        payload = copy.deepcopy(self.valid)
        payload["policy"]["policy"]["version"] = "v2"
        result = self._validate(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Proposal policy version is not present in the snapshot.")

    def test_permitted_grounding_references_cover_each_snapshot_scope(self):
        payload = copy.deepcopy(self.valid)
        payload["raw_proposal"]["grounding"] = [
            {"scope": "fact", "ref_id": "fact:bow_requires_materials"},
            {"scope": "memory", "ref_id": "memory:recent_request"},
            {"scope": "observation", "ref_id": "observation:player_nearby"},
            {"scope": "constraint", "ref_id": "constraint:no_inventory_grant"},
        ]
        payload["raw_proposal"]["state_deltas"][0]["source_ref_id"] = "observation:player_nearby"
        result = self._validate(payload, proposal_id="proposal:all-grounding")
        self.assertIsInstance(result, DecisionProposal)
        self.assertEqual(tuple(reference.scope for reference in result.grounding), (
            GroundingScope.FACT,
            GroundingScope.MEMORY,
            GroundingScope.OBSERVATION,
            GroundingScope.CONSTRAINT,
        ))

    def test_policy_denial_returns_typed_error_without_repairing_proposal(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["allowed_actions"] = ["face_target"]
        result = self._validate(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNKNOWN_ENUM)
        self.assertEqual(result.public_message, "Proposal action is not allowed by policy.")


class ReasoningProposalCheckInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "proposal-check-t01-valid.json").read_text())

    def _validate(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return validate(
            RawProposal.model_validate(data["raw_proposal"]),
            Snapshot.model_validate(data["snapshot"]),
            ProposalPolicy.model_validate(data["policy"]),
            proposal_id="proposal:001",
        )

    def test_unknown_fact_and_memory_references_are_rejected_without_inventing_evidence(self):
        for scope, ref_id in (("fact", "fact:invented_reward"), ("memory", "memory:invented_promise")):
            payload = copy.deepcopy(self.valid)
            payload["raw_proposal"]["grounding"] = [{"scope": scope, "ref_id": ref_id}]
            payload["raw_proposal"]["state_deltas"] = []
            result = self._validate(payload)
            with self.subTest(scope=scope):
                self.assertIsInstance(result, DomainError)
                self.assertEqual(result.code, ErrorCode.UNGROUNDED_REFERENCE)
                self.assertEqual(result.public_message, "Proposal references evidence outside the snapshot.")
                self.assertNotIn(ref_id, payload["snapshot"]["fact_ids"])
                self.assertNotIn(ref_id, payload["snapshot"]["memory_ids"])

    def test_bad_source_scope_and_absolute_mutations_are_rejected_at_contract_boundary(self):
        raw = copy.deepcopy(self.valid["raw_proposal"])
        raw["grounding"] = [{"scope": "repository", "ref_id": "fact:bow_requires_materials"}]
        with self.assertRaises(ValidationError):
            RawProposal.model_validate(raw)

        raw = copy.deepcopy(self.valid["raw_proposal"])
        raw["state_deltas"] = [{"field": "trust", "absolute_value": 0.9, "source_ref_id": "memory:recent_request"}]
        with self.assertRaises(ValidationError):
            RawProposal.model_validate(raw)

    def test_unsupported_state_field_and_invalid_numeric_delta_are_rejected(self):
        raw = copy.deepcopy(self.valid["raw_proposal"])
        raw["state_deltas"] = [{"field": "inventory_count", "delta": 0.3, "source_ref_id": "memory:recent_request"}]
        with self.assertRaises(ValidationError):
            RawProposal.model_validate(raw)

        for value in ("0.2", True, float("nan"), float("inf"), -1.2, 1.2):
            raw = copy.deepcopy(self.valid["raw_proposal"])
            raw["state_deltas"] = [{"field": "trust", "delta": value, "source_ref_id": "memory:recent_request"}]
            with self.subTest(value=value), self.assertRaises(ValidationError):
                RawProposal.model_validate(raw)

    def test_state_delta_source_must_be_in_grounding_and_is_not_repaired(self):
        payload = copy.deepcopy(self.valid)
        payload["raw_proposal"]["state_deltas"] = [{"field": "trust", "delta": 0.2, "source_ref_id": "fact:missing"}]
        result = self._validate(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.UNGROUNDED_REFERENCE)
        self.assertEqual(result.public_message, "Proposal state delta lacks grounding evidence.")
        self.assertNotIn("fact:missing", payload["raw_proposal"]["grounding"])

    def test_disallowed_relative_field_returns_typed_error_without_summing_or_repair(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["allowed_state_fields"] = ["attention"]
        result = self._validate(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Proposal state delta is not allowed by policy.")


class ExtractedProposalInput(ContractEnvelope):
    proposal_id: str
    snapshot_id: str
    policy: PolicyVersion
    state_deltas: tuple[RelativeStateDelta, ...]


def accept_state_extraction_input(decision: DecisionProposal, expected_policy: PolicyVersion, expected_timeline: str):
    if decision.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="state.extract",
            retryable=False,
            source_ids=(decision.record_id,),
            public_message="Decision proposal timeline is no longer current.",
        )
    if decision.policy != expected_policy:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="state.extract",
            retryable=False,
            source_ids=(decision.record_id,),
            public_message="Decision proposal policy does not match extractor input.",
        )
    return ExtractedProposalInput(
        schema_version=decision.schema_version,
        record_id="state-extract-input:001",
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
        proposal_id=decision.proposal_id,
        snapshot_id=decision.snapshot_id,
        policy=decision.policy,
        state_deltas=decision.state_deltas,
    )


class ReasoningProposalCheckHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "proposal-check-t01-valid.json").read_text())

    def _decision(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        result = validate(
            RawProposal.model_validate(data["raw_proposal"]),
            Snapshot.model_validate(data["snapshot"]),
            ProposalPolicy.model_validate(data["policy"]),
            proposal_id="proposal:001",
        )
        self.assertIsInstance(result, DecisionProposal)
        return result

    def test_decision_proposal_satisfies_state_extraction_handoff(self):
        decision = self._decision()
        handoff = accept_state_extraction_input(decision, decision.policy, "timeline:main")
        self.assertIsInstance(handoff, ExtractedProposalInput)
        self.assertEqual(handoff.proposal_id, "proposal:001")
        self.assertEqual(handoff.snapshot_id, "snapshot:001")
        self.assertEqual(handoff.state_deltas, decision.state_deltas)
        with self.assertRaises(ValidationError):
            handoff.state_deltas = ()

    def test_state_extraction_handoff_rejects_mismatched_policy_and_timeline(self):
        decision = self._decision()
        result = accept_state_extraction_input(decision, PolicyVersion(policy_id="reasoning:proposal_check", version="v2"), "timeline:main")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        result = accept_state_extraction_input(decision, decision.policy, "timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)
