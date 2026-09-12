"""C01 golden transport and rejection tests; no application runtime needed."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode, Position, RevisionSet


FIXTURE = Path(__file__).parent / "fixtures" / "contracts" / "c01-values.json"


class ContractValueTests(unittest.TestCase):
    def setUp(self):
        self.values = json.loads(FIXTURE.read_text())

    def test_golden_round_trips(self):
        pairs = [(ContractEnvelope, self.values["envelope"]),
                 (Position, self.values["position"]),
                 (RevisionSet, self.values["revisions"]),
                 (DomainError, self.values["error_fields"])]
        for model, payload in pairs:
            with self.subTest(model=model.__name__):
                value = model.model_validate_json(json.dumps(payload))
                self.assertEqual(value.model_dump(mode="json"), payload)
                self.assertEqual(model.model_validate_json(value.model_dump_json()), value)
                self.assertEqual(model.model_validate(payload), value)

    def test_reject_unknown_or_coerced_versions(self):
        for version in (0, 2, "1", 1.0, True, None):
            with self.subTest(version=version), self.assertRaises(ValidationError):
                ContractEnvelope.model_validate(self.values["envelope"] | {"schema_version": version})

    def test_reject_invalid_ids(self):
        for field in ("record_id", "trace_id", "causation_id", "game_id", "timeline_id", "npc_id", "actor_id", "target_id"):
            for value in ("", " name", "display name", "x\n", "../file", "é", 12, True):
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    ContractEnvelope.model_validate(self.values["envelope"] | {field: value})
        for overrides in ({"source_ids": ["bad source"]}, {"policy_versions": [{"policy_id": "bad id", "version": "v1"}]}, {"policy_versions": [{"policy_id": "role:gatherer", "version": 1}]}):
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError):
                ContractEnvelope.model_validate(self.values["envelope"] | overrides)

    def test_reject_missing_or_inconsistent_provenance(self):
        for field in self.values["envelope"]:
            if field in ("actor_id", "target_id"):
                continue
            payload = self.values["envelope"].copy()
            del payload[field]
            with self.subTest(missing=field), self.assertRaises(ValidationError):
                ContractEnvelope.model_validate(payload)
        for overrides in ({"source_ids": []}, {"source_ids": ["unrelated"]},
                          {"source_ids": ["interaction:001", "interaction:001"]},
                          {"policy_versions": self.values["envelope"]["policy_versions"] * 2}):
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError):
                ContractEnvelope.model_validate(self.values["envelope"] | overrides)

    def test_utc_normalization_and_invalid_timestamps(self):
        payload = self.values["envelope"] | {"created_at": "2026-09-12T15:30:00+05:30"}
        self.assertEqual(ContractEnvelope.model_validate(payload).model_dump(mode="json")["created_at"], "2026-09-12T10:00:00Z")
        for value in ("2026-09-12T10:00:00", "2026-09-12", 12345678, "12345678", True):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ContractEnvelope.model_validate(payload | {"created_at": value})

    def test_position_rejects_nonfinite_and_coerced_coordinates(self):
        for field in ("x", "y"):
            for value in (float("nan"), float("inf"), -float("inf"), "1.2", True):
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    Position.model_validate(self.values["position"] | {field: value})
        for field, value in (("area_id", "bad area"), ("spatial_revision", -1), ("spatial_revision", True), ("spatial_revision", "4")):
            with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                Position.model_validate(self.values["position"] | {field: value})

    def test_revisions_keep_base_and_approved_separate(self):
        revisions = RevisionSet.model_validate(self.values["revisions"])
        self.assertEqual(revisions.base_npc_state_revision, 7)
        self.assertEqual(revisions.approved_npc_state_revision, 8)
        pending = RevisionSet(npc_id="npc:gatherer", base_npc_state_revision=7)
        self.assertIsNone(pending.approved_npc_state_revision)
        self.assertEqual(pending.quest, ())
        self.assertEqual(pending.inventory, ())
        unchanged = RevisionSet(npc_id="npc:gatherer", base_npc_state_revision=7, approved_npc_state_revision=7)
        self.assertEqual(unchanged.approved_npc_state_revision, 7)

    def test_reject_invalid_revisions_and_duplicate_scopes(self):
        for field in ("base_npc_state_revision", "approved_npc_state_revision"):
            for value in (-1, True, "7", 7.5):
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    RevisionSet.model_validate(self.values["revisions"] | {field: value})
        with self.assertRaises(ValidationError):
            RevisionSet.model_validate(self.values["revisions"] | {"approved_npc_state_revision": 6})
        for category in ("quest", "inventory", "relationship", "policy", "controller"):
            for refs in ([{"scope_id": "scope", "revision": True}], [{"scope_id": "bad scope", "revision": 1}], self.values["revisions"][category] * 2):
                with self.subTest(category=category, refs=refs), self.assertRaises(ValidationError):
                    RevisionSet.model_validate(self.values["revisions"] | {category: refs})

    def test_deep_immutability_and_input_isolation(self):
        envelope = ContractEnvelope.model_validate(self.values["envelope"])
        revisions = RevisionSet.model_validate(self.values["revisions"])
        self.values["envelope"]["source_ids"].append("injected")
        self.values["envelope"]["policy_versions"][0]["version"] = "changed"
        self.values["revisions"]["quest"][0]["revision"] = 100
        self.assertNotIn("injected", envelope.source_ids)
        self.assertEqual(envelope.policy_versions[0].version, "v1")
        self.assertEqual(revisions.quest[0].revision, 2)
        for value, field, replacement in ((envelope, "npc_id", "changed"), (envelope.policy_versions[0], "version", "v2"), (revisions.quest[0], "revision", 9)):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                setattr(value, field, replacement)
        with self.assertRaises(TypeError):
            envelope.source_ids[0] = "changed"
        with self.assertRaises(TypeError):
            revisions.quest[0] = revisions.quest[0]

    def test_error_is_typed_value_with_no_exception_payload(self):
        payload = self.values["error_fields"]
        value = DomainError.model_validate(payload)
        self.assertIs(value.code, ErrorCode.STALE_REVISION)
        self.assertNotIsInstance(value, Exception)
        for overrides in ({"code": "UNKNOWN_FAILURE"}, {"retryable": "true"}, {"retryable": 1}, {"public_message": " "}, {"exception": "private detail"}, {"stage": ""}, {"source_ids": ["bad source"]}):
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError):
                DomainError.model_validate(payload | overrides)

    def test_unapplied_policy_and_missing_input_error_need_no_fabricated_lineage(self):
        envelope = ContractEnvelope.model_validate(self.values["envelope"] | {"policy_versions": []})
        self.assertEqual(envelope.policy_versions, ())
        error = DomainError(code="INVALID_CONTRACT", stage="gateway", retryable=False, source_ids=[], public_message="Required provenance is missing.")
        self.assertEqual(error.source_ids, ())
        payload = self.values["error_fields"].copy()
        del payload["source_ids"]
        with self.assertRaises(ValidationError):
            DomainError.model_validate(payload)

    def test_unknown_fields_rejected_on_all_records(self):
        for model, key in ((ContractEnvelope, "envelope"), (Position, "position"), (RevisionSet, "revisions")):
            with self.subTest(model=model.__name__), self.assertRaises(ValidationError):
                model.model_validate(self.values[key] | {"unknown_field": 1})

    def test_import_does_not_load_infrastructure(self):
        result = subprocess.run([sys.executable, "-c", "import sys; import app.contracts; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot'} for name in sys.modules)"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
