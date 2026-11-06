"""Quest recovery contract, behaviour and handoff tests."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from pydantic import ValidationError

from app.contracts import ContractEnvelope, DomainError, ErrorCode, PolicyVersion
from app.domain.quest.recovery import (
    BlockedStep,
    CompletionEvidenceKind,
    OfferKind,
    OfferStatus,
    QuestBlocker,
    RecoveryOfferSet,
    RecoveryPolicy,
    RecoveryRoute,
    RecoveryWorldView,
    SelectRecoveryOffers,
    offers,
)


FIXTURES = Path(__file__).parent / "fixtures" / "quest"


class QuestRecoveryContractTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "recovery-t01-valid.json").read_text())
        self.rejected = json.loads((FIXTURES / "recovery-t01-rejected.json").read_text())

    def test_golden_round_trip_blocker_world_policy_and_offers(self):
        for model, key in (
            (QuestBlocker, "blocker"),
            (RecoveryWorldView, "world"),
            (RecoveryPolicy, "policy"),
            (RecoveryOfferSet, "offers"),
        ):
            with self.subTest(key=key):
                result = model.model_validate_json(json.dumps(self.valid[key]))
                self.assertEqual(result.model_dump(mode="json"), self.valid[key])
                self.assertEqual(model.model_validate_json(result.model_dump_json()), result)
        policy = RecoveryPolicy.model_validate(self.valid["policy"])
        self.assertEqual(policy.routes[0].kind, OfferKind.FAVOUR)
        self.assertEqual(policy.routes[0].blocked_step, BlockedStep.CRAFTING_ACCESS)

    def test_rejected_fixture_has_unsupported_route_kind_and_safe_error(self):
        with self.assertRaises(ValidationError) as caught:
            RecoveryPolicy.model_validate(self.rejected["policy"])
        self.assertEqual(caught.exception.errors()[0]["type"], "enum")
        rejection = DomainError.model_validate(self.rejected["error"])
        self.assertEqual(rejection.code, ErrorCode.INVALID_CONTRACT)
        self.assertEqual(rejection.stage, "domain.quest.recovery")

    def test_missing_required_fields_and_duplicates_are_rejected(self):
        for model, key, fields in (
            (QuestBlocker, "blocker", ("blocker_id", "quest_run_id", "blocked_step", "refusing_npc_id", "player_id")),
            (RecoveryWorldView, "world", ("available_item_ids", "source_ids")),
            (RecoveryPolicy, "policy", ("policy", "routes")),
            (RecoveryOfferSet, "offers", ("blocker_id", "policy", "offers")),
        ):
            for field in fields:
                payload = copy.deepcopy(self.valid[key])
                del payload[field]
                with self.subTest(key=key, field=field), self.assertRaises(ValidationError):
                    model.model_validate(payload)
        policy = copy.deepcopy(self.valid["policy"])
        policy["routes"].append(copy.deepcopy(policy["routes"][0]))
        with self.assertRaises(ValidationError):
            RecoveryPolicy.model_validate(policy)
        route = copy.deepcopy(self.valid["policy"]["routes"][1])
        route["costs"].append({"item_id": "item:fruits", "quantity": 2})
        with self.assertRaises(ValidationError):
            RecoveryRoute.model_validate(route)

    def test_fake_execution_and_immutability(self):
        original = copy.deepcopy(self.valid)
        blocker = QuestBlocker.model_validate(self.valid["blocker"])
        world = RecoveryWorldView.model_validate(self.valid["world"])
        policy = RecoveryPolicy.model_validate(self.valid["policy"])
        expected = RecoveryOfferSet.model_validate(self.valid["offers"])

        def fake(blocker: QuestBlocker, world: RecoveryWorldView, policy: RecoveryPolicy):
            self.assertEqual(blocker.blocker_id, expected.blocker_id)
            self.assertEqual(policy.policy, expected.policy)
            return expected

        selector: SelectRecoveryOffers = fake
        self.assertEqual(selector(blocker, world, policy), expected)
        self.assertEqual(self.valid, original)
        self.valid["blocker"]["blocked_step"] = "material_access"
        self.assertEqual(blocker.blocked_step, BlockedStep.CRAFTING_ACCESS)
        with self.assertRaises(ValidationError):
            blocker.blocked_step = BlockedStep.MATERIAL_ACCESS

    def test_module_import_has_no_infrastructure_dependency(self):
        script = "import sys; import app.domain.quest.recovery; assert not any(name.split('.')[0] in {'sqlalchemy', 'fastapi', 'httpx', 'godot', 'faiss', 'numpy'} for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class QuestRecoveryBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "recovery-t01-valid.json").read_text())

    def _offers(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return offers(
            QuestBlocker.model_validate(data["blocker"]),
            RecoveryWorldView.model_validate(data["world"]),
            RecoveryPolicy.model_validate(data["policy"]),
            record_id="recovery-offers:001",
        )

    def test_valid_fixture_produces_exact_offer_set(self):
        result = self._offers()
        self.assertIsInstance(result, RecoveryOfferSet)
        self.assertEqual(result.model_dump(mode="json"), self.valid["offers"])

    def test_same_npc_favour_and_trade_routes_are_selected(self):
        result = self._offers()
        self.assertIsInstance(result, RecoveryOfferSet)
        self.assertEqual(tuple(offer.kind for offer in result.offers), (OfferKind.FAVOUR, OfferKind.TRADE))
        self.assertTrue(all(offer.npc_id == "npc:craftsman" for offer in result.offers))
        self.assertEqual(result.offers[0].grant.source_offer_id, "offer:pulse_001:crafting_access:diagnostic_favour")

    def test_attainable_prerequisites_filter_unavailable_routes(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["available_item_ids"] = ["item:saw"]
        result = self._offers(payload)
        self.assertIsInstance(result, RecoveryOfferSet)
        self.assertEqual(tuple(offer.route_id for offer in result.offers), ("route:diagnostic_favour",))

    def test_verified_completion_marks_offer_completed_and_creates_grant(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["completion_evidence"] = [{
            "evidence_id": "event:diagnostic:001",
            "kind": "verified_event",
            "event_type": "event:diagnostic_complete",
            "actor_id": "player:hero",
            "target_id": "npc:craftsman",
        }]
        result = self._offers(payload)
        self.assertIsInstance(result, RecoveryOfferSet)
        self.assertEqual(result.offers[0].status, OfferStatus.COMPLETED)
        self.assertFalse(result.offers[0].grant.fulfilled)

    def test_world_and_policy_mismatch_return_typed_errors(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["timeline_id"] = "timeline:old"
        result = self._offers(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Recovery world evidence is mismatched.")

        payload = copy.deepcopy(self.valid)
        payload["policy"]["policy"]["version"] = "v2"
        result = self._offers(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.public_message, "Recovery policy version is not present in blocker.")


class QuestRecoveryInvariantTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "recovery-t01-valid.json").read_text())

    def _offers(self, payload=None):
        data = copy.deepcopy(payload or self.valid)
        return offers(
            QuestBlocker.model_validate(data["blocker"]),
            RecoveryWorldView.model_validate(data["world"]),
            RecoveryPolicy.model_validate(data["policy"]),
            record_id="recovery-offers:001",
        )

    def test_circular_or_wrong_npc_routes_are_not_viable(self):
        payload = copy.deepcopy(self.valid)
        for route in payload["policy"]["routes"]:
            route["required_available_item_ids"] = ["crafting_access"]
        payload["world"]["available_item_ids"] = ["crafting_access"]
        result = self._offers(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.NO_VIABLE_RECOVERY_ROUTE)

        payload = copy.deepcopy(self.valid)
        for route in payload["policy"]["routes"]:
            route["npc_id"] = "npc:broker"
        result = self._offers(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.NO_VIABLE_RECOVERY_ROUTE)

    def test_consumed_completed_expired_or_missing_resources_suppress_routes(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["consumed_offer_ids"] = [offer["offer_id"] for offer in self.valid["offers"]["offers"]]
        result = self._offers(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.NO_VIABLE_RECOVERY_ROUTE)

        payload = copy.deepcopy(self.valid)
        for route in payload["policy"]["routes"]:
            route["expires_at"] = "2026-10-12T09:00:00Z"
        result = self._offers(payload)
        self.assertIsInstance(result, DomainError)

        payload = copy.deepcopy(self.valid)
        payload["world"]["available_item_ids"] = []
        result = self._offers(payload)
        self.assertIsInstance(result, DomainError)

    def test_player_claim_completion_does_not_complete_offer(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["completion_evidence"] = [{
            "evidence_id": "claim:diagnostic",
            "kind": "player_claim",
            "event_type": "event:diagnostic_complete",
            "actor_id": "player:hero",
            "target_id": "npc:craftsman",
        }]
        result = self._offers(payload)
        self.assertIsInstance(result, RecoveryOfferSet)
        self.assertEqual(result.offers[0].status, OfferStatus.OFFERED)

    def test_repeated_completion_returns_no_new_viable_offer(self):
        payload = copy.deepcopy(self.valid)
        payload["world"]["completed_offer_ids"] = [offer["offer_id"] for offer in self.valid["offers"]["offers"]]
        result = self._offers(payload)
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.NO_VIABLE_RECOVERY_ROUTE)


class BowQuestRecoveryInput(ContractEnvelope):
    blocker_id: str
    grants: tuple[dict, ...]
    policy: PolicyVersion


def accept_bow_recovery_input(offer_set: RecoveryOfferSet, expected_policy: PolicyVersion, expected_timeline: str):
    if offer_set.timeline_id != expected_timeline:
        return DomainError(
            code=ErrorCode.OLD_TIMELINE,
            stage="domain.quest.bow",
            retryable=False,
            source_ids=(offer_set.record_id,),
            public_message="Recovery offers timeline is no longer current.",
        )
    if offer_set.policy != expected_policy:
        return DomainError(
            code=ErrorCode.INVALID_CONTRACT,
            stage="domain.quest.bow",
            retryable=False,
            source_ids=(offer_set.record_id,),
            public_message="Recovery offers policy does not match bow quest input.",
        )
    return BowQuestRecoveryInput(
        schema_version=offer_set.schema_version,
        record_id="bow-recovery-input:001",
        trace_id=offer_set.trace_id,
        causation_id=offer_set.record_id,
        game_id=offer_set.game_id,
        timeline_id=offer_set.timeline_id,
        npc_id=offer_set.npc_id,
        actor_id=offer_set.actor_id,
        target_id=offer_set.target_id,
        created_at=offer_set.created_at,
        source_ids=(offer_set.record_id,),
        policy_versions=offer_set.policy_versions,
        blocker_id=offer_set.blocker_id,
        grants=tuple(offer.grant.model_dump(mode="json") for offer in offer_set.offers),
        policy=offer_set.policy,
    )


class QuestRecoveryHandoffTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads((FIXTURES / "recovery-t01-valid.json").read_text())

    def _offer_set(self):
        result = offers(
            QuestBlocker.model_validate(self.valid["blocker"]),
            RecoveryWorldView.model_validate(self.valid["world"]),
            RecoveryPolicy.model_validate(self.valid["policy"]),
            record_id="recovery-offers:001",
        )
        self.assertIsInstance(result, RecoveryOfferSet)
        return result

    def test_offer_set_satisfies_bow_quest_recovery_handoff(self):
        offer_set = self._offer_set()
        handoff = accept_bow_recovery_input(offer_set, offer_set.policy, "timeline:main")
        self.assertIsInstance(handoff, BowQuestRecoveryInput)
        self.assertEqual(handoff.blocker_id, "blocker:crafting_refusal")
        self.assertEqual(len(handoff.grants), 2)
        with self.assertRaises(ValidationError):
            handoff.grants = ()

    def test_bow_quest_handoff_rejects_mismatched_policy_and_timeline(self):
        offer_set = self._offer_set()
        result = accept_bow_recovery_input(offer_set, PolicyVersion(policy_id="quest:recovery", version="v2"), "timeline:main")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.INVALID_CONTRACT)

        result = accept_bow_recovery_input(offer_set, offer_set.policy, "timeline:reset")
        self.assertIsInstance(result, DomainError)
        self.assertEqual(result.code, ErrorCode.OLD_TIMELINE)

