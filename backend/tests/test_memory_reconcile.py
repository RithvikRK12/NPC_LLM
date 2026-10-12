"""Memory reconciliation contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode
from app.memory.reconcile import (
    EvidenceAuthority,
    EpistemicStatus,
    MemoryRecord,
    Reconcile,
    ReconciliationAction,
    ReconciliationPlan,
    ReconciliationPolicy,
    RelatedRecords,
    reconcile,
)


FIXTURES = Path(__file__).parent / "fixtures" / "memory"
CONTRACT_FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


class MemoryReconcileContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "reconcile-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "reconcile-t01-rejected.json").read_text())

    def test_golden_round_trip_new_related_policy_and_plan(self):
        for model, key in (
            (MemoryRecord, "new_record"),
            (RelatedRecords, "related"),
            (ReconciliationPolicy, "policy"),
            (ReconciliationPlan, "plan"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        record = MemoryRecord.model_validate(self.valid["new_record"])
        self.assertEqual(record.status, EpistemicStatus.FACT)
        self.assertEqual(record.authority, EvidenceAuthority.AUTHORITATIVE)

    def test_rejected_fixture_has_unsupported_status_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            MemoryRecord.model_validate(self.rejected["new_record"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(rejection.stage, "memory.reconcile")

    def test_missing_required_fields_and_invalid_values_are_rejected(self):
        for model, key, fields in (
            (MemoryRecord, "new_record", ("memory_id", "subject_id", "predicate", "status", "authority")),
            (RelatedRecords, "related", ("records", "source_ids")),
            (ReconciliationPolicy, "policy", ("policy", "authoritative_statuses", "allow_claim_consolidation")),
            (ReconciliationPlan, "plan", ("new_memory_id", "policy", "retain_memory_ids", "links")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        payload = copy.deepcopy(self.valid["new_record"])
        payload["confidence"] = 1.5
        with self.assertRaises(ValidationError):
            MemoryRecord.model_validate(payload)
        payload["confidence"] = "0.7"
        with self.assertRaises(ValidationError):
            MemoryRecord.model_validate(payload)
        payload = copy.deepcopy(self.valid["new_record"])
        payload["object_id"] = None
        payload["object_text"] = None
        with self.assertRaises(ValidationError):
            MemoryRecord.model_validate(payload)

    def test_duplicate_related_records_policy_statuses_and_retain_ids_are_rejected(self):
        payload = copy.deepcopy(self.valid["related"])
        payload["records"].append(copy.deepcopy(payload["records"][0]))
        with self.assertRaises(ValidationError):
            RelatedRecords.model_validate(payload)
        payload = copy.deepcopy(self.valid["policy"])
        payload["authoritative_statuses"].append("fact")
        with self.assertRaises(ValidationError):
            ReconciliationPolicy.model_validate(payload)
        payload = copy.deepcopy(self.valid["plan"])
        payload["retain_memory_ids"].append("memory:old_claim")
        with self.assertRaises(ValidationError):
            ReconciliationPlan.model_validate(payload)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        new_record = MemoryRecord.model_validate(self.valid["new_record"])
        related = RelatedRecords.model_validate(self.valid["related"])
        policy = ReconciliationPolicy.model_validate(self.valid["policy"])
        expected = ReconciliationPlan.model_validate(self.valid["plan"])

        def fake(new_record: MemoryRecord, related: RelatedRecords, policy: ReconciliationPolicy):
            self.assertEqual(new_record.memory_id, expected.new_memory_id)
            self.assertEqual(policy.policy, expected.policy)
            return expected

        reconcile_fn: Reconcile = fake
        self.assertEqual(reconcile_fn(new_record, related, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["new_record"]["confidence"] = 0.1
        self.assertEqual(new_record.confidence, 1.0)
        with self.assertRaises(ValidationError):
            new_record.confidence = 0.5
        with self.assertRaises(TypeError):
            related.records[0] = related.records[0]

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.memory.reconcile; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class MemoryReconcileBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "reconcile-t01-valid.json").read_text())

    def _reconcile(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return reconcile(
            MemoryRecord.model_validate(data["new_record"]),
            RelatedRecords.model_validate(data["related"]),
            ReconciliationPolicy.model_validate(data["policy"]),
            record_id="reconciliation-plan:001",
            created_at="2026-09-29T10:00:00Z",
        )

    def test_valid_fixture_produces_exact_authoritative_correction_plan(self):
        result = self._reconcile()
        self.assertIsInstance(result, ReconciliationPlan)
        self.assertEqual(result.model_dump(mode="json"), self.valid["plan"])

    def test_claim_consolidation_links_duplicate_evidence_without_deleting_history(self):
        payload = copy.deepcopy(self.valid)
        payload["new_record"]["status"] = "claim"
        payload["new_record"]["authority"] = "reported"
        payload["new_record"]["confidence"] = 0.5
        result = self._reconcile(payload)
        self.assertIsInstance(result, ReconciliationPlan)
        self.assertEqual(result.retain_memory_ids, ("memory:old_claim",))
        self.assertEqual(result.links[0].action, ReconciliationAction.LINK_CORRECTION)
        self.assertEqual(result.links[0].reason, "memory:duplicate_evidence")

    def test_retraction_marks_matching_record_without_silent_negation(self):
        payload = copy.deepcopy(self.valid)
        payload["new_record"]["status"] = "retraction"
        payload["new_record"]["authority"] = "authoritative"
        result = self._reconcile(payload)
        self.assertIsInstance(result, ReconciliationPlan)
        self.assertEqual(result.links[0].action, ReconciliationAction.MARK_RETRACTED)
        self.assertEqual(result.retain_memory_ids, ("memory:old_claim",))

    def test_conflicting_claims_are_retained_not_overwritten(self):
        payload = copy.deepcopy(self.valid)
        payload["new_record"]["status"] = "claim"
        payload["new_record"]["authority"] = "reported"
        payload["new_record"]["object_id"] = "item:stone"
        result = self._reconcile(payload)
        self.assertIsInstance(result, ReconciliationPlan)
        self.assertEqual(result.links[0].action, ReconciliationAction.KEEP_CONFLICT)
        self.assertEqual(result.links[0].reason, "memory:conflicting_evidence")
        self.assertEqual(result.retain_memory_ids, ("memory:old_claim",))

    def test_embedding_like_similarity_does_not_merge_different_predicates(self):
        payload = copy.deepcopy(self.valid)
        payload["related"]["records"][0]["predicate"] = "wants_item"
        payload["related"]["records"][0]["object_text"] = "wood"
        payload["related"]["records"][0]["object_id"] = None
        result = self._reconcile(payload)
        self.assertIsInstance(result, ReconciliationPlan)
        self.assertEqual(result.links, ())
        self.assertEqual(result.retain_memory_ids, ("memory:old_claim",))

    def test_invalid_evidence_returns_typed_rejections(self):
        cases = (
            (lambda payload: payload["related"].__setitem__("timeline_id", "timeline:old"), "Related memory evidence is mismatched."),
            (lambda payload: payload["policy"].__setitem__("timeline_id", "timeline:old"), "Reconciliation policy evidence is mismatched."),
            (lambda payload: payload["new_record"]["policy_versions"][0].__setitem__("version", "v0"), "Reconciliation policy evidence is mismatched."),
            (lambda payload: payload["new_record"].__setitem__("authority", "reported"), "Authoritative status requires authoritative evidence."),
        )
        for mutate, message in cases:
            payload = copy.deepcopy(self.valid)
            mutate(payload)
            with self.subTest(message=message):
                result = self._reconcile(payload)
                self.assertIsInstance(result, DomainError)
                self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
                self.assertEqual(result.public_message, message)


class MemoryReconcileHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "reconcile-t01-valid.json").read_text())
        self.c01_values = json.loads((CONTRACT_FIXTURES / "c01-values.json").read_text())

    def test_plan_satisfies_c01_envelope_handoff(self):
        result = reconcile(
            MemoryRecord.model_validate(self.valid["new_record"]),
            RelatedRecords.model_validate(self.valid["related"]),
            ReconciliationPolicy.model_validate(self.valid["policy"]),
            record_id="reconciliation-plan:001",
            created_at="2026-09-29T10:00:00Z",
        )
        self.assertIsInstance(result, ReconciliationPlan)
        payload = result.model_dump(mode="json")
        envelope = ContractEnvelope.model_validate({field: payload[field] for field in ContractEnvelope.model_fields})
        self.assertEqual(envelope.schema_version, self.c01_values["envelope"]["schema_version"])
        self.assertEqual(envelope.source_ids, ("memory-record:new", "related-records:001", "reconciliation-policy:001"))
        self.assertEqual(envelope.policy_versions[0].policy_id, "memory:reconcile")

    def test_next_handoff_can_consume_immutable_plan_identity(self):
        result = reconcile(
            MemoryRecord.model_validate(self.valid["new_record"]),
            RelatedRecords.model_validate(self.valid["related"]),
            ReconciliationPolicy.model_validate(self.valid["policy"]),
            record_id="reconciliation-plan:001",
            created_at="2026-09-29T10:00:00Z",
        )
        self.assertIsInstance(result, ReconciliationPlan)

        def fake_lifecycle_handoff(plan: ReconciliationPlan):
            self.assertEqual(plan.new_memory_id, "memory:new")
            self.assertEqual(plan.links[0].action, ReconciliationAction.SUPERSEDE)
            return plan.record_id

        self.assertEqual(fake_lifecycle_handoff(result), "reconciliation-plan:001")


if __name__ == "__main__":
    unittest.main()
