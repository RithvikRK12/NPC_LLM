"""T01 perception normalization contract and fake-boundary tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode
from app.perception.normalize import (
    EvidenceStatus,
    NormalizationPolicy,
    NormalizedSignal,
    NormalizedSignals,
    Normalize,
    ObservationSignal,
    ObservedSignals,
    SignalVisibility,
    normalize,
)


FIXTURES = Path(__file__).parent / "fixtures" / "perception"
CONTRACT_FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


class PerceptionNormalizeContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "normalize-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "normalize-t01-rejected.json").read_text())

    def test_golden_round_trip_observed_policy_and_normalized(self):
        for model, key in (
            (ObservedSignals, "observed"),
            (NormalizationPolicy, "policy"),
            (NormalizedSignals, "normalized"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        observed = ObservedSignals.model_validate(self.valid["observed"])
        self.assertEqual(observed.signals[0].status, EvidenceStatus.CLAIM)
        self.assertEqual(observed.signals[1].position.area_id, "area:village")

    def test_rejected_fixture_has_unsupported_variant_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            ObservedSignals.model_validate(self.rejected["observed"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(rejection.stage, "perception.normalize")
        self.assertEqual(DomainError.model_validate_json(rejection.model_dump_json()), rejection)

    def test_missing_required_fields_are_rejected(self):
        for model, key, fields in (
            (ObservedSignals, "observed", ("observation_id", "signals", "source_ids")),
            (NormalizationPolicy, "policy", ("policy", "canonical_units")),
            (NormalizedSignals, "normalized", ("observation_id", "policy", "signals")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)

    def test_signal_status_visibility_timestamps_and_units_are_strict(self):
        signal = copy.deepcopy(self.valid["observed"]["signals"][0])
        for field, value in (
            ("status", "rumor"),
            ("visibility", "omniscient"),
            ("observed_at", "2026-09-29"),
            ("source_id", "bad id"),
        ):
            payload = signal | {field: value}
            with self.subTest(field=field), self.assertRaises(ValidationError):
                ObservationSignal.model_validate(payload)
        for value in ("0.5", True, float("nan"), float("inf")):
            payload = signal | {"value": value, "unit": "score", "text": None}
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ObservationSignal.model_validate(payload)
        with self.assertRaises(ValidationError):
            ObservationSignal.model_validate(signal | {"value": 1.0, "unit": None})
        with self.assertRaises(ValidationError):
            ObservationSignal.model_validate(signal | {"text": None, "value": None, "unit": None, "position": None})

    def test_duplicate_normalized_sources_and_policy_units_are_rejected(self):
        payload = copy.deepcopy(self.valid["normalized"]["signals"][0])
        payload["source_ids"].append(payload["source_ids"][0])
        with self.assertRaises(ValidationError):
            NormalizedSignal.model_validate(payload)
        policy = copy.deepcopy(self.valid["policy"])
        policy["canonical_units"].append("score")
        with self.assertRaises(ValidationError):
            NormalizationPolicy.model_validate(policy)

    def test_fixture_decoding_and_fake_execution_do_not_mutate_inputs(self):
        original = copy.deepcopy(self.valid)
        observed = ObservedSignals.model_validate(self.valid["observed"])
        policy = NormalizationPolicy.model_validate(self.valid["policy"])
        expected = NormalizedSignals.model_validate(self.valid["normalized"])

        def fake(observed: ObservedSignals, policy: NormalizationPolicy):
            self.assertEqual(observed.observation_id, expected.observation_id)
            self.assertEqual(policy.policy, expected.policy)
            return expected

        normalize: Normalize = fake
        self.assertEqual(normalize(observed, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["observed"]["signals"][0]["text"] = "changed"
        self.valid["policy"]["canonical_units"][0] = "changed"
        self.assertEqual(observed.signals[0].text, "I saw wood near the workshop.")
        self.assertEqual(policy.canonical_units[0], "score")
        with self.assertRaises(ValidationError):
            observed.signals[0].text = "changed"
        with self.assertRaises(TypeError):
            policy.canonical_units[0] = "changed"

    def test_fake_rejection_uses_shared_error_value(self):
        rejection = DomainError.model_validate(self.rejected["error"])

        def fake(observed: ObservedSignals, policy: NormalizationPolicy):
            return rejection

        normalize: Normalize = fake
        result = normalize(
            ObservedSignals.model_validate(self.valid["observed"]),
            NormalizationPolicy.model_validate(self.valid["policy"]),
        )
        self.assertIs(result, rejection)
        self.assertFalse(result.retryable)

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.perception.normalize; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class PerceptionNormalizeBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "normalize-t01-valid.json").read_text())

    def _normalize(self, payload=None, *, record_id="normalized-signals:001", created_at="2026-09-29T10:00:00Z"):
        data = copy.deepcopy(payload or self.valid)
        return normalize(
            ObservedSignals.model_validate(data["observed"]),
            NormalizationPolicy.model_validate(data["policy"]),
            record_id=record_id,
            created_at=created_at,
        )

    def test_valid_t01_fixture_normalizes_exact_output(self):
        result = self._normalize()
        self.assertIsInstance(result, NormalizedSignals)
        expected = copy.deepcopy(self.valid["normalized"])
        expected["signals"] = [
            {
                "source_ids": [signal["source_id"]],
                "kind": signal["kind"],
                "status": signal["status"],
                "visibility": signal["visibility"],
                "observed_at": signal["observed_at"],
                "subject_id": signal.get("subject_id"),
                "target_id": signal.get("target_id"),
                "position": signal.get("position"),
                "value": signal.get("value"),
                "unit": signal.get("unit"),
                "text": signal.get("text"),
            }
            for signal in self.valid["observed"]["signals"]
        ]
        self.assertEqual(result.model_dump(mode="json"), expected)

    def test_primary_behaviour_preserves_fact_claim_and_interpretation_status(self):
        result = self._normalize()
        self.assertIsInstance(result, NormalizedSignals)
        statuses = tuple(signal.status for signal in result.signals)
        self.assertEqual(statuses, (EvidenceStatus.CLAIM, EvidenceStatus.FACT, EvidenceStatus.INTERPRETATION))
        self.assertEqual(result.signals[0].text, "I saw wood near the workshop.")
        self.assertEqual(result.signals[1].position.area_id, "area:village")
        self.assertEqual(result.signals[2].unit, "score")
        self.assertEqual(result.signals[2].value, 0.75)

    def test_primary_behaviour_normalizes_timestamps_to_utc_and_preserves_identity(self):
        payload = copy.deepcopy(self.valid)
        payload["observed"]["signals"][0]["observed_at"] = "2026-09-29T15:30:00+05:30"
        result = self._normalize(payload)
        self.assertIsInstance(result, NormalizedSignals)
        self.assertEqual(result.signals[0].observed_at.isoformat().replace("+00:00", "Z"), "2026-09-29T10:00:00Z")
        self.assertEqual(result.observation_id, "observation:001")
        self.assertEqual(result.policy.policy_id, "perception:normalize")
        self.assertEqual(result.source_ids, ("observed-signals:001", "normalization-policy:001"))

    def test_private_visibility_is_preserved(self):
        payload = copy.deepcopy(self.valid)
        payload["observed"]["signals"][0]["visibility"] = "private"
        result = self._normalize(payload)
        self.assertIsInstance(result, NormalizedSignals)
        self.assertEqual(result.signals[0].visibility, SignalVisibility.PRIVATE)

    def test_real_normalizer_does_not_mutate_inputs(self):
        original = copy.deepcopy(self.valid)
        result = self._normalize()
        self.assertEqual(self.valid, original)
        self.assertIsInstance(result, NormalizedSignals)
        with self.assertRaises(ValidationError):
            result.signals[0].text = "changed"


class PerceptionNormalizeInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "normalize-t01-valid.json").read_text())

    def _normalize(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return normalize(
            ObservedSignals.model_validate(data["observed"]),
            NormalizationPolicy.model_validate(data["policy"]),
            record_id="normalized-signals:001",
            created_at="2026-09-29T10:00:00Z",
        )

    def test_duplicate_identical_observations_are_deduplicated_by_source_identity(self):
        payload = copy.deepcopy(self.valid)
        payload["observed"]["signals"].append(copy.deepcopy(payload["observed"]["signals"][0]))
        result = self._normalize(payload)
        self.assertIsInstance(result, NormalizedSignals)
        self.assertEqual(len(result.signals), 3)
        self.assertEqual(result.signals[0].source_ids, ("signal:dialogue:001",))

    def test_duplicate_conflicting_observations_return_typed_rejection(self):
        payload = copy.deepcopy(self.valid)
        duplicate = copy.deepcopy(payload["observed"]["signals"][0])
        duplicate["text"] = "Changed claim."
        payload["observed"]["signals"].append(duplicate)
        result = self._normalize(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Duplicate source observations conflict.")
        self.assertEqual(result.source_ids, ("observed-signals:001", "normalization-policy:001"))

    def test_noncanonical_unit_returns_typed_rejection(self):
        payload = copy.deepcopy(self.valid)
        payload["observed"]["signals"][2]["unit"] = "raw_score"
        result = self._normalize(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(result.public_message, "Observed signal unit is not canonical.")

    def test_invalid_references_and_nonfinite_positions_reject_at_boundary(self):
        for mutate in (
            lambda payload: payload["observed"]["signals"][0].__setitem__("source_id", "bad source"),
            lambda payload: payload["observed"]["signals"][1]["position"].__setitem__("x", float("nan")),
        ):
            payload = copy.deepcopy(self.valid)
            mutate(payload)
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ObservedSignals.model_validate(payload["observed"])

    def test_mismatched_policy_timeline_or_version_returns_typed_rejection(self):
        for mutate in (
            lambda payload: payload["policy"].__setitem__("timeline_id", "timeline:old"),
            lambda payload: payload["observed"]["policy_versions"][0].__setitem__("version", "v0"),
        ):
            payload = copy.deepcopy(self.valid)
            mutate(payload)
            with self.subTest(payload=payload):
                result = self._normalize(payload)
                self.assertIsInstance(result, DomainError)
                self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)
                self.assertEqual(result.public_message, "Normalization policy evidence is mismatched.")


class PerceptionNormalizeHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "normalize-t01-valid.json").read_text())
        self.c01_values = json.loads((CONTRACT_FIXTURES / "c01-values.json").read_text())

    def test_normalized_result_satisfies_c01_envelope_handoff(self):
        result = normalize(
            ObservedSignals.model_validate(self.valid["observed"]),
            NormalizationPolicy.model_validate(self.valid["policy"]),
            record_id="normalized-signals:001",
            created_at="2026-09-29T10:00:00Z",
        )
        self.assertIsInstance(result, NormalizedSignals)
        payload = result.model_dump(mode="json")
        envelope = ContractEnvelope.model_validate({field: payload[field] for field in ContractEnvelope.model_fields})
        self.assertEqual(envelope.schema_version, self.c01_values["envelope"]["schema_version"])
        self.assertEqual(envelope.causation_id, "observed-signals:001")
        self.assertEqual(envelope.source_ids, ("observed-signals:001", "normalization-policy:001"))
        self.assertEqual(envelope.policy_versions[0].policy_id, "perception:normalize")
        self.assertEqual(envelope.policy_versions[0].version, "v1")

    def test_next_handoff_can_consume_immutable_normalized_identity(self):
        result = normalize(
            ObservedSignals.model_validate(self.valid["observed"]),
            NormalizationPolicy.model_validate(self.valid["policy"]),
            record_id="normalized-signals:001",
            created_at="2026-09-29T10:00:00Z",
        )
        self.assertIsInstance(result, NormalizedSignals)

        def fake_relevance_handoff(signals: NormalizedSignals):
            self.assertEqual(signals.observation_id, "observation:001")
            self.assertEqual(signals.policy.policy_id, "perception:normalize")
            self.assertEqual(tuple(signal.source_ids[0] for signal in signals.signals), (
                "signal:dialogue:001",
                "signal:entity:001",
                "signal:memory:001",
            ))
            return signals.record_id

        self.assertEqual(fake_relevance_handoff(result), "normalized-signals:001")


if __name__ == "__main__":
    unittest.main()
