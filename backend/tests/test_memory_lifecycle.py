"""Memory lifecycle contract, behaviour and handoff tests."""

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode, PolicyVersion
from app.memory.lifecycle import (
    CategoryRetentionRule,
    LifecycleAction,
    LifecycleMutation,
    LifecyclePlan,
    MemoryLifecycleState,
    MemoryRecordSet,
    MemoryRecordView,
    RetentionPolicy,
    ReviewMemoryLifecycle,
    review,
)


FIXTURES = Path(__file__).parent / "fixtures" / "memory"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class MemoryLifecycleContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "lifecycle-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "lifecycle-t01-rejected.json").read_text())

    def test_golden_round_trip_records_policy_and_plan(self):
        for model, key in (
            (MemoryRecordSet, "records"),
            (RetentionPolicy, "policy"),
            (LifecyclePlan, "plan"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        records = MemoryRecordSet.model_validate(self.valid["records"])
        self.assertEqual(records.records[0].lifecycle, MemoryLifecycleState.ACTIVE)

    def test_rejected_fixture_has_unsupported_lifecycle_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            MemoryRecordSet.model_validate(self.rejected["records"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.UNKNOWN_ENUM)
        self.assertEqual(rejection.stage, "memory.lifecycle")

    def test_missing_required_fields_and_invalid_shapes_are_rejected(self):
        for model, key, fields in (
            (MemoryRecordSet, "records", ("records", "source_ids")),
            (RetentionPolicy, "policy", ("policy", "allow_deletion", "protect_authoritative_provenance")),
            (LifecyclePlan, "plan", ("reviewed_at", "policy", "mutations")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        record = copy.deepcopy(self.valid["records"]["records"][0])
        record["salience"] = 1.5
        with self.assertRaises(ValidationError):
            MemoryRecordView.model_validate(record)
        rule = {"category": "routine", "retrieval_ttl_hours": 72, "archive_after_hours": 24}
        with self.assertRaises(ValidationError):
            CategoryRetentionRule.model_validate(rule)
        plan = copy.deepcopy(self.valid["plan"])
        plan["mutations"].append(copy.deepcopy(plan["mutations"][0]))
        with self.assertRaises(ValidationError):
            LifecyclePlan.model_validate(plan)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        records = MemoryRecordSet.model_validate(self.valid["records"])
        policy = RetentionPolicy.model_validate(self.valid["policy"])
        expected = LifecyclePlan.model_validate(self.valid["plan"])
        now = parse_time(self.valid["now"])

        def fake(records: MemoryRecordSet, now: datetime, policy: RetentionPolicy):
            self.assertEqual(records.record_id, expected.causation_id)
            self.assertEqual(policy.policy, expected.policy)
            return expected

        reviewer: ReviewMemoryLifecycle = fake
        self.assertEqual(reviewer(records, now, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["records"]["records"][0]["salience"] = 0.1
        self.assertEqual(records.records[0].salience, 0.8)
        with self.assertRaises(ValidationError):
            records.records[0].salience = 0.1

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.memory.lifecycle; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class MemoryLifecycleBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "lifecycle-t01-valid.json").read_text())

    def _review(self, payload=None, now=None):
        data = copy.deepcopy(payload or self.valid)
        return review(
            MemoryRecordSet.model_validate(data["records"]),
            now or parse_time(data["now"]),
            RetentionPolicy.model_validate(data["policy"]),
            record_id="lifecycle-plan:001",
        )

    def test_valid_fixture_produces_exact_lifecycle_plan(self):
        result = self._review()
        self.assertIsInstance(result, LifecyclePlan)
        self.assertEqual(result.model_dump(mode="json"), self.valid["plan"])

    def test_temporary_expiry_is_separate_from_archive_or_deletion(self):
        result = self._review()
        self.assertIsInstance(result, LifecyclePlan)
        mutation = result.mutations[0]
        self.assertEqual(mutation.action, LifecycleAction.EXPIRE_FOR_RETRIEVAL)
        self.assertEqual(mutation.to_lifecycle, MemoryLifecycleState.RETRIEVAL_EXPIRED)
        self.assertNotEqual(mutation.to_lifecycle, MemoryLifecycleState.ARCHIVED)
        self.assertNotEqual(mutation.action, LifecycleAction.DELETE)

    def test_archive_exclusion_happens_without_deletion(self):
        payload = copy.deepcopy(self.valid)
        payload["records"]["records"] = [copy.deepcopy(self.valid["records"]["records"][0])]
        payload["records"]["records"][0]["occurred_at"] = "2026-10-08T10:00:00Z"
        payload["records"]["records"][0]["created_at"] = "2026-10-08T10:00:00Z"
        result = self._review(payload)
        self.assertIsInstance(result, LifecyclePlan)
        self.assertEqual(result.mutations[0].action, LifecycleAction.ARCHIVE)
        self.assertEqual(result.mutations[0].to_lifecycle, MemoryLifecycleState.ARCHIVED)

    def test_policy_mismatch_returns_typed_error(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["timeline_id"] = "timeline:old"
        result = self._review(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Lifecycle policy evidence is mismatched.")

        payload = copy.deepcopy(self.valid)
        payload["policy"]["policy"]["version"] = "v2"
        result = self._review(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Lifecycle policy version is not present in records.")


class MemoryLifecycleInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "lifecycle-t01-valid.json").read_text())

    def _review(self, payload=None, now=None):
        data = copy.deepcopy(payload or self.valid)
        return review(
            MemoryRecordSet.model_validate(data["records"]),
            now or parse_time(data["now"]),
            RetentionPolicy.model_validate(data["policy"]),
            record_id="lifecycle-plan:001",
        )

    def test_salience_decay_does_not_delete_or_change_lifecycle(self):
        result = self._review()
        self.assertIsInstance(result, LifecyclePlan)
        mutation = result.mutations[1]
        self.assertEqual(mutation.action, LifecycleAction.DECAY_SALIENCE)
        self.assertEqual(mutation.from_lifecycle, mutation.to_lifecycle)
        self.assertLess(mutation.to_salience, mutation.from_salience)

    def test_protected_provenance_is_not_deleted(self):
        result = self._review()
        self.assertIsInstance(result, LifecyclePlan)
        mutation = result.mutations[2]
        self.assertEqual(mutation.action, LifecycleAction.PROTECT)
        self.assertEqual(mutation.to_lifecycle, MemoryLifecycleState.ARCHIVED)
        self.assertNotEqual(mutation.to_lifecycle, MemoryLifecycleState.DELETED)

    def test_no_deletion_when_retention_is_unspecified(self):
        payload = copy.deepcopy(self.valid)
        payload["records"]["records"] = [copy.deepcopy(self.valid["records"]["records"][1])]
        payload["records"]["records"][0]["occurred_at"] = "2026-01-01T10:00:00Z"
        result = self._review(payload)
        self.assertIsInstance(result, LifecyclePlan)
        self.assertEqual(result.mutations[0].action, LifecycleAction.DECAY_SALIENCE)
        self.assertNotEqual(result.mutations[0].to_lifecycle, MemoryLifecycleState.DELETED)

    def test_deletion_requires_explicit_policy_and_unprotected_record(self):
        payload = copy.deepcopy(self.valid)
        payload["policy"]["allow_deletion"] = True
        payload["records"]["records"] = [copy.deepcopy(self.valid["records"]["records"][0])]
        payload["records"]["records"][0]["occurred_at"] = "2026-09-01T10:00:00Z"
        for rule in payload["policy"]["rules"]:
            if rule["category"] == "routine":
                rule["delete_after_hours"] = 720
        result = self._review(payload)
        self.assertIsInstance(result, LifecyclePlan)
        self.assertEqual(result.mutations[0].action, LifecycleAction.DELETE)
        self.assertEqual(result.mutations[0].to_lifecycle, MemoryLifecycleState.DELETED)

    def test_naive_review_time_is_rejected(self):
        result = self._review(now=datetime(2026, 10, 12, 10, 0, 0))
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Lifecycle review time must include a timezone.")


class MemoryRetrieveInput(ContractEnvelope):
    visible_memory_ids: tuple[str, ...]
    archived_memory_ids: tuple[str, ...]
    policy: PolicyVersion


def accept_memory_retrieve_input(plan: LifecyclePlan, expected_policy: PolicyVersion, expected_timeline: str):
    if plan.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="memory.retrieve",
            retryable=False,
            source_ids=(plan.record_id,),
            public_message="Lifecycle plan timeline is no longer current.",
        )
    if plan.policy != expected_policy:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="memory.retrieve",
            retryable=False,
            source_ids=(plan.record_id,),
            public_message="Lifecycle plan policy does not match retrieval input.",
        )
    visible = tuple(
        mutation.memory_id for mutation in plan.mutations
        if mutation.to_lifecycle not in {MemoryLifecycleState.RETRIEVAL_EXPIRED, MemoryLifecycleState.ARCHIVED, MemoryLifecycleState.DELETED}
    )
    archived = tuple(mutation.memory_id for mutation in plan.mutations if mutation.to_lifecycle == MemoryLifecycleState.ARCHIVED)
    return MemoryRetrieveInput(
        schema_version=plan.schema_version,
        record_id="memory-retrieve-input:001",
        trace_id=plan.trace_id,
        causation_id=plan.record_id,
        game_id=plan.game_id,
        timeline_id=plan.timeline_id,
        npc_id=plan.npc_id,
        actor_id=plan.actor_id,
        target_id=plan.target_id,
        created_at=plan.created_at,
        source_ids=(plan.record_id,),
        policy_versions=plan.policy_versions,
        visible_memory_ids=visible,
        archived_memory_ids=archived,
        policy=plan.policy,
    )


class MemoryLifecycleHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "lifecycle-t01-valid.json").read_text())

    def _plan(self):
        result = review(
            MemoryRecordSet.model_validate(self.valid["records"]),
            parse_time(self.valid["now"]),
            RetentionPolicy.model_validate(self.valid["policy"]),
            record_id="lifecycle-plan:001",
        )
        self.assertIsInstance(result, LifecyclePlan)
        return result

    def test_lifecycle_plan_satisfies_memory_retrieve_handoff(self):
        plan = self._plan()
        handoff = accept_memory_retrieve_input(plan, plan.policy, "timeline:main")
        self.assertIsInstance(handoff, MemoryRetrieveInput)
        self.assertEqual(handoff.visible_memory_ids, ("memory:quiet-route",))
        self.assertEqual(handoff.archived_memory_ids, ("memory:old-transfer",))
        with self.assertRaises(ValidationError):
            handoff.visible_memory_ids = ()

    def test_memory_retrieve_handoff_rejects_mismatched_policy_and_timeline(self):
        plan = self._plan()
        result = accept_memory_retrieve_input(plan, PolicyVersion(policy_id="memory:lifecycle", version="v2"), "timeline:main")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        result = accept_memory_retrieve_input(plan, plan.policy, "timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)
