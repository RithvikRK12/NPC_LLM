"""State merge contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode, PolicyVersion
from app.state.merge import (
    ChangeSource,
    CurrentState,
    Merge,
    MergeDecision,
    MergePolicy,
    MergedChanges,
    ProposedChange,
    ProposedChanges,
    StateDimension,
    merge,
)


FIXTURES = Path(__file__).parent / "fixtures" / "state"


class StateMergeContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "merge-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "merge-t01-rejected.json").read_text())

    def test_golden_round_trip_current_proposed_policy_and_merged(self):
        for model, key in (
            (CurrentState, "current"),
            (ProposedChanges, "proposed"),
            (MergePolicy, "policy"),
            (MergedChanges, "merged"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        proposed = ProposedChanges.model_validate(self.valid["proposed"])
        self.assertEqual(proposed.changes[0].source, ChangeSource.MEMORY_INFLUENCE)
        self.assertEqual(proposed.changes[0].dimension, StateDimension.TRUST)

    def test_rejected_fixture_has_unsupported_dimension_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            ProposedChanges.model_validate(self.rejected["proposed"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(rejection.stage, "state.merge")

    def test_missing_required_fields_and_invalid_values_are_rejected(self):
        for model, key, fields in (
            (CurrentState, "current", ("state_id", "revisions", "scalar_values", "known_relationship_subject_ids")),
            (ProposedChanges, "proposed", ("proposal_set_id", "changes", "source_ids")),
            (MergePolicy, "policy", ("policy", "source_precedence", "reject_duplicate_effects")),
            (MergedChanges, "merged", ("state_id", "proposal_set_id", "policy", "accepted")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        for value in ("0.2", True, float("nan"), float("inf"), -1.2, 1.2):
            payload = copy.deepcopy(self.valid["proposed"]["changes"][0])
            payload["delta"] = value
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ProposedChange.model_validate(payload)

    def test_subject_dimension_and_policy_precedence_invariants_are_strict(self):
        payload = copy.deepcopy(self.valid["proposed"]["changes"][0])
        payload["subject_id"] = None
        with self.assertRaises(ValidationError):
            ProposedChange.model_validate(payload)
        payload = copy.deepcopy(self.valid["proposed"]["changes"][2])
        payload["subject_id"] = "player:hero"
        with self.assertRaises(ValidationError):
            ProposedChange.model_validate(payload)
        policy = copy.deepcopy(self.valid["policy"])
        policy["source_precedence"] = ["memory_influence", "decision_proposal"]
        with self.assertRaises(ValidationError):
            MergePolicy.model_validate(policy)
        policy = copy.deepcopy(self.valid["policy"])
        policy["source_precedence"].append("decision_proposal")
        with self.assertRaises(ValidationError):
            MergePolicy.model_validate(policy)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        current = CurrentState.model_validate(self.valid["current"])
        proposed = ProposedChanges.model_validate(self.valid["proposed"])
        policy = MergePolicy.model_validate(self.valid["policy"])
        expected = MergedChanges.model_validate(self.valid["merged"])

        def fake(current: CurrentState, proposed: ProposedChanges, policy: MergePolicy):
            self.assertEqual(current.state_id, expected.state_id)
            self.assertEqual(policy.policy, expected.policy)
            return expected

        merge_fn: Merge = fake
        self.assertEqual(merge_fn(current, proposed, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["proposed"]["changes"][0]["delta"] = 0.9
        self.assertEqual(proposed.changes[0].delta, 0.2)
        with self.assertRaises(ValidationError):
            proposed.changes[0].delta = 0.1
        with self.assertRaises(TypeError):
            current.scalar_values[0] = current.scalar_values[0]

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.state.merge; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class StateMergeBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "merge-t01-valid.json").read_text())

    def _merge(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return merge(
            CurrentState.model_validate(data["current"]),
            ProposedChanges.model_validate(data["proposed"]),
            MergePolicy.model_validate(data["policy"]),
            record_id="merged-changes:001",
        )

    def test_valid_t01_fixture_produces_exact_merged_changes(self):
        result = self._merge()
        self.assertIsInstance(result, MergedChanges)
        self.assertEqual(result.model_dump(mode="json"), self.valid["merged"])

    def test_source_precedence_selects_one_change_per_target_dimension(self):
        result = self._merge()
        self.assertIsInstance(result, MergedChanges)
        self.assertEqual(tuple((change.dimension, change.subject_id) for change in result.accepted), (
            (StateDimension.TRUST, "player:hero"),
            (StateDimension.ATTENTION, None),
        ))
        self.assertEqual(result.accepted[0].source, ChangeSource.MEMORY_INFLUENCE)
        self.assertEqual(result.rejected[0].decision, MergeDecision.SUPERSEDED)

    def test_stable_effect_identity_breaks_same_precedence_ties_without_summing(self):
        payload = copy.deepcopy(self.valid)
        payload["proposed"]["changes"] = [
            {
                "effect_id": "effect:z_late",
                "dimension": "urgency",
                "delta": 0.7,
                "source": "decision_proposal",
                "source_id": "proposal:002",
                "subject_id": None,
            },
            {
                "effect_id": "effect:a_early",
                "dimension": "urgency",
                "delta": 0.2,
                "source": "decision_proposal",
                "source_id": "proposal:001",
                "subject_id": None,
            },
        ]
        result = self._merge(payload)
        self.assertIsInstance(result, MergedChanges)
        self.assertEqual(len(result.accepted), 1)
        self.assertEqual(result.accepted[0].effect_id, "effect:a_early")
        self.assertEqual(result.accepted[0].delta, 0.2)
        self.assertEqual(len(result.rejected), 1)
        self.assertEqual(result.rejected[0].effect_id, "effect:z_late")

    def test_verified_event_precedence_overrides_memory_and_proposal(self):
        payload = copy.deepcopy(self.valid)
        payload["proposed"]["changes"].append({
            "effect_id": "effect:verified_help",
            "dimension": "trust",
            "delta": -0.1,
            "source": "verified_event",
            "source_id": "event:refused_help",
            "subject_id": "player:hero",
        })
        result = self._merge(payload)
        self.assertIsInstance(result, MergedChanges)
        self.assertEqual(result.accepted[0].source, ChangeSource.VERIFIED_EVENT)
        self.assertEqual(result.accepted[0].effect_id, "effect:verified_help")
        self.assertEqual(tuple(change.effect_id for change in result.rejected), ("effect:memory_helped", "effect:proposal_help"))

    def test_real_merge_does_not_mutate_inputs(self):
        original = copy.deepcopy(self.valid)
        result = self._merge()
        self.assertEqual(self.valid, original)
        self.assertIsInstance(result, MergedChanges)
        with self.assertRaises(ValidationError):
            result.accepted[0].delta = 0.9


class StateMergeInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "merge-t01-valid.json").read_text())

    def _merge(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return merge(
            CurrentState.model_validate(data["current"]),
            ProposedChanges.model_validate(data["proposed"]),
            MergePolicy.model_validate(data["policy"]),
            record_id="merged-changes:001",
        )

    def test_duplicate_memory_influence_effect_is_rejected(self):
        payload = copy.deepcopy(self.valid)
        payload["proposed"]["changes"].append(copy.deepcopy(payload["proposed"]["changes"][0]))
        payload["proposed"]["changes"][-1]["delta"] = 0.1
        result = self._merge(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Proposed changes contain a duplicate effect identity.")

    def test_duplicate_proposal_effect_is_rejected_not_summed(self):
        payload = copy.deepcopy(self.valid)
        payload["proposed"]["changes"].append({
            "effect_id": "effect:proposal_attention",
            "dimension": "attention",
            "delta": 0.4,
            "source": "decision_proposal",
            "source_id": "proposal:retry",
            "subject_id": None,
        })
        result = self._merge(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Proposed changes contain a duplicate effect identity.")

    def test_unrecognized_relationship_subject_is_rejected(self):
        payload = copy.deepcopy(self.valid)
        payload["proposed"]["changes"][0]["subject_id"] = "player:unknown"
        result = self._merge(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Proposed change references an unknown relationship subject.")

    def test_conflict_precedence_keeps_single_winner_without_automatic_sum(self):
        result = self._merge()
        self.assertIsInstance(result, MergedChanges)
        trust_changes = [change for change in result.accepted + result.rejected if change.dimension == StateDimension.TRUST]
        self.assertEqual(len([change for change in trust_changes if change.decision == MergeDecision.ACCEPTED]), 1)
        self.assertEqual(sum(change.delta for change in result.accepted if change.dimension == StateDimension.TRUST), 0.2)
        self.assertEqual(result.rejected[0].delta, 0.1)

    def test_mismatched_timeline_and_policy_version_return_typed_errors(self):
        payload = copy.deepcopy(self.valid)
        payload["proposed"]["timeline_id"] = "timeline:old"
        result = self._merge(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Proposed changes are not for the current state timeline.")

        payload = copy.deepcopy(self.valid)
        payload["policy"]["policy"]["version"] = "v2"
        result = self._merge(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Merge policy version is not present in current state.")


class ExtractableMergedChanges(ContractEnvelope):
    state_id: str
    policy: PolicyVersion
    accepted: tuple[ProposedChange, ...]


def accept_state_extract_input(merged: MergedChanges, expected_policy: PolicyVersion, expected_timeline: str):
    if merged.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="state.extract",
            retryable=False,
            source_ids=(merged.record_id,),
            public_message="Merged changes timeline is no longer current.",
        )
    if merged.policy != expected_policy:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="state.extract",
            retryable=False,
            source_ids=(merged.record_id,),
            public_message="Merged changes policy does not match extractor input.",
        )
    return ExtractableMergedChanges(
        schema_version=merged.schema_version,
        record_id="state-extract-merge-input:001",
        trace_id=merged.trace_id,
        causation_id=merged.record_id,
        game_id=merged.game_id,
        timeline_id=merged.timeline_id,
        npc_id=merged.npc_id,
        actor_id=merged.actor_id,
        target_id=merged.target_id,
        created_at=merged.created_at,
        source_ids=(merged.record_id,),
        policy_versions=merged.policy_versions,
        state_id=merged.state_id,
        policy=merged.policy,
        accepted=tuple(
            ProposedChange(
                effect_id=change.effect_id,
                dimension=change.dimension,
                delta=change.delta,
                source=change.source,
                source_id=change.source_id,
                subject_id=change.subject_id,
            )
            for change in merged.accepted
        ),
    )


class StateMergeHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "merge-t01-valid.json").read_text())

    def _merged(self):
        result = merge(
            CurrentState.model_validate(self.valid["current"]),
            ProposedChanges.model_validate(self.valid["proposed"]),
            MergePolicy.model_validate(self.valid["policy"]),
            record_id="merged-changes:001",
        )
        self.assertIsInstance(result, MergedChanges)
        return result

    def test_merged_changes_satisfy_state_extract_handoff(self):
        merged = self._merged()
        handoff = accept_state_extract_input(merged, merged.policy, "timeline:main")
        self.assertIsInstance(handoff, ExtractableMergedChanges)
        self.assertEqual(handoff.state_id, "state:npc_craftsman")
        self.assertEqual(tuple(change.effect_id for change in handoff.accepted), ("effect:memory_helped", "effect:proposal_attention"))
        with self.assertRaises(ValidationError):
            handoff.accepted = ()

    def test_state_extract_handoff_rejects_mismatched_policy_and_timeline(self):
        merged = self._merged()
        result = accept_state_extract_input(merged, PolicyVersion(policy_id="state:merge", version="v2"), "timeline:main")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        result = accept_state_extract_input(merged, merged.policy, "timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)

