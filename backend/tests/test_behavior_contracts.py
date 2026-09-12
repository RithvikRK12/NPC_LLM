"""Focused C02 transport and no-privilege-expansion checks, no infrastructure."""
import itertools
import json
from pathlib import Path
import unittest

from pydantic import ValidationError

from app.contracts import (
    ActionConstraint, Activity, ApplyWhen, ConstraintSet, DialogueCondition,
    DialogueKind, DialogueTiming, EngineAction, Expression, Intent,
    NumericInterval, ParameterConstraint, TargetConstraint, TargetKind,
    TargetPredicate, TimeWindow,
)

FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


def interval(low=0.0, high=10.0):
    return NumericInterval(minimum=low, maximum=high)


def action(kind="approach_target", ids=None, predicates=(), bounds=()):
    return ActionConstraint(action=kind, targets=(TargetConstraint(kind="entity", entity_ids=ids, predicates=predicates),),
                            parameters=tuple(ParameterConstraint(parameter=name, interval=interval(low, high))
                                             for name, low, high in bounds))


def constraints(**changes):
    fields = dict(intents=tuple(Intent), activities=tuple(Activity), expressions=tuple(Expression),
                  actions=(action(),), dialogue_timings=tuple(DialogueTiming))
    fields.update(changes)
    return ConstraintSet(**fields)


class BehaviorContractTests(unittest.TestCase):
    def test_golden_fixtures_round_trip(self):
        for name, model in (("c02_constraints.json", ConstraintSet), ("c02_denied.json", ConstraintSet),
                            ("c02_failure_dialogue.json", DialogueCondition)):
            with self.subTest(name=name):
                payload = (FIXTURES / name).read_text()
                value = model.model_validate_json(payload)
                self.assertEqual(json.loads(payload), value.model_dump(mode="json"))
                self.assertEqual(value, model.model_validate_json(value.model_dump_json()))

    def test_vocabularies_are_separate_and_closed(self):
        for enum in (Intent, Activity, Expression, EngineAction, ApplyWhen, DialogueKind, DialogueTiming, TargetKind, TargetPredicate):
            for member in enum:
                self.assertEqual(enum(member.value), member)
            with self.assertRaises(ValueError):
                enum("invented_unknown")
        for value in ("trade", "craft_item", "help", "reassuring", 1):
            with self.assertRaises(ValidationError):
                action(kind=value)
        with self.assertRaises(ValidationError):
            constraints(intents=("speak",))
        with self.assertRaises(ValidationError):
            constraints(expressions=("move_to",))

    def test_numeric_interval_shape_and_touching_intersection(self):
        for low, high in ((2, 1), (float("nan"), 1), (0, float("inf")), (True, 1), ("0", 1)):
            with self.assertRaises(ValidationError):
                interval(low, high)
        self.assertEqual(interval(0, 1).intersection(interval(1, 2)), interval(1, 1))
        self.assertIsNone(interval(0, 1).intersection(interval(2, 3)))

    def test_time_shape_and_normalization(self):
        for fields in (dict(not_before="2026-09-12T12:00:00"), dict(expires_at=123),
                       dict(expires_at="123"), dict(not_before="2026-09-12T12:00:00Z", expires_at="2026-09-12T12:00:00Z"),
                       dict(not_before="2026-09-12T13:00:00Z", expires_at="2026-09-12T12:00:00Z")):
            with self.assertRaises(ValidationError):
                TimeWindow(**fields)
        self.assertEqual(TimeWindow(not_before="2026-09-12T13:00:00+01:00"),
                         TimeWindow(not_before="2026-09-12T12:00:00Z"))

    def test_time_intersection_never_extends_window(self):
        a = TimeWindow(not_before="2026-09-12T12:00:00Z", expires_at="2026-09-12T14:00:00Z")
        b = TimeWindow(not_before="2026-09-12T13:00:00Z", expires_at="2026-09-12T15:00:00Z")
        combined = a.intersection(b)
        self.assertEqual(combined.not_before, b.not_before)
        self.assertEqual(combined.expires_at, a.expires_at)
        self.assertEqual(a.intersection(TimeWindow()), a)
        self.assertIsNone(a.intersection(TimeWindow(not_before="2026-09-12T14:00:00Z")))
        self.assertTrue(constraints(time_window=a).intersection(
            constraints(time_window=TimeWindow(not_before="2026-09-12T14:00:00Z"))).is_denied)

    def test_target_intersection_is_conjunction(self):
        a = action(ids=("player-1", "player-2"), predicates=("visible",))
        b = action(ids=("player-2", "player-3"), predicates=("reachable",))
        target = a.intersection(b).targets[0]
        self.assertEqual(target.entity_ids, ("player-2",))
        self.assertEqual(target.predicates, (TargetPredicate.REACHABLE, TargetPredicate.VISIBLE))
        self.assertIsNone(a.intersection(action(ids=("player-3",))))

    def test_none_and_empty_target_restrictions_are_distinct(self):
        unrestricted = TargetConstraint(kind="entity", entity_ids=None)
        denied = TargetConstraint(kind="entity", entity_ids=())
        self.assertIsNone(unrestricted.model_dump(mode="json")["entity_ids"])
        self.assertEqual(denied.model_dump(mode="json")["entity_ids"], [])
        self.assertIsNone(unrestricted.intersection(denied))
        self.assertTrue(constraints(actions=(action(ids=()),)).is_denied)
        for value in (unrestricted, denied):
            self.assertEqual(value, TargetConstraint.model_validate_json(value.model_dump_json()))

    def test_area_constraints_and_target_alternatives(self):
        entity = TargetConstraint(kind="entity", area_ids=("square", "forest"))
        position = TargetConstraint(kind="position", area_ids=("square",))
        a = ActionConstraint(action="move_to", targets=(entity, position))
        b = ActionConstraint(action="move_to", targets=(TargetConstraint(kind="position", area_ids=("forest",)), entity))
        self.assertEqual(a.intersection(b).targets, (entity,))
        with self.assertRaises(ValidationError):
            TargetConstraint(kind="none", predicates=("visible",))
        with self.assertRaises(ValidationError):
            TargetConstraint(kind="position", entity_ids=("player-1",))

    def test_parameter_bounds_are_per_action_and_intersect(self):
        a = constraints(actions=(action(bounds=(("speed", 0, 10),)), action(kind="speak", bounds=(("volume", 0, 1),))))
        b = constraints(actions=(action(bounds=(("speed", 5, 20), ("arrival_distance", 1, 2))),
                                 action(kind="speak", bounds=(("volume", 2, 3),))))
        result = a.intersection(b)
        self.assertEqual(tuple(x.action for x in result.actions), (EngineAction.APPROACH_TARGET,))
        self.assertEqual(result.actions[0].parameters,
                         (ParameterConstraint(parameter="arrival_distance", interval=interval(1, 2)),
                          ParameterConstraint(parameter="speed", interval=interval(5, 10))))
        self.assertTrue(result.is_narrower_than(a))
        self.assertTrue(result.is_narrower_than(b))
        self.assertFalse(a.is_narrower_than(result))

    def test_mandatory_evidence_cannot_be_removed(self):
        a = constraints(mandatory_evidence=("source-a",))
        b = constraints(mandatory_evidence=("source-b",))
        result = a.intersection(b)
        self.assertEqual(result.mandatory_evidence, ("source-a", "source-b"))
        self.assertTrue(result.is_narrower_than(a))
        self.assertFalse(a.is_narrower_than(result))

    def test_empty_dialogue_permissions_allow_silent_actions(self):
        silent = constraints(dialogue_timings=())
        self.assertFalse(silent.is_denied)
        self.assertEqual(silent.intersection(constraints()), silent)
        self.assertFalse(constraints().is_narrower_than(silent))

    def test_empty_global_permissions_are_canonical_denial(self):
        denied = ConstraintSet.deny_all()
        for fields in (dict(intents=()), dict(activities=()), dict(expressions=()), dict(actions=())):
            value = constraints(**fields)
            self.assertEqual(value, denied)
            self.assertTrue(value.is_denied)
        self.assertEqual(constraints(intents=("help",)).intersection(constraints(intents=("decline",))), denied)
        self.assertTrue(denied.is_narrower_than(constraints()))
        self.assertFalse(constraints().is_narrower_than(denied))

    def test_algebra_over_varied_constraints(self):
        values = [constraints(), constraints(intents=("help",)), constraints(intents=("decline",)),
                  constraints(actions=(action(ids=("player-1",), predicates=("visible",), bounds=(("speed", 0, 2),)),)),
                  constraints(actions=(action(ids=("player-2",), bounds=(("speed", 3, 4),)),)),
                  constraints(mandatory_evidence=("event-1",)), constraints(dialogue_timings=()), ConstraintSet.deny_all()]
        for a in values:
            self.assertEqual(a.intersection(a), a)
        for a, b in itertools.product(values, repeat=2):
            self.assertEqual(a.intersection(b), b.intersection(a))
            self.assertTrue(a.intersection(b).is_narrower_than(a))
            self.assertTrue(a.intersection(b).is_narrower_than(b))
        for a, b, c in itertools.product(values, repeat=3):
            self.assertEqual(a.intersection(b).intersection(c), a.intersection(b.intersection(c)))

    def test_no_aliasing_and_nested_immutability(self):
        evidence = ["event-1"]
        value = constraints(mandatory_evidence=evidence)
        evidence.append("event-2")
        self.assertEqual(value.mandatory_evidence, ("event-1",))
        with self.assertRaises(ValidationError):
            value.actions = ()
        with self.assertRaises(ValidationError):
            value.actions[0].targets[0].entity_ids = ()
        with self.assertRaises(TypeError):
            value.mandatory_evidence[0] = "event-2"
        self.assertEqual(value, ConstraintSet.model_validate_json(value.model_dump_json()))

    def test_deterministic_serialization_and_duplicate_key_rejection(self):
        self.assertEqual(constraints(intents=tuple(reversed(tuple(Intent)))).model_dump_json(), constraints().model_dump_json())
        with self.assertRaises(ValidationError):
            constraints(actions=(action(), action()))
        with self.assertRaises(ValidationError):
            ActionConstraint(action="speak", targets=(TargetConstraint(kind="none"), TargetConstraint(kind="none")))
        with self.assertRaises(ValidationError):
            action(bounds=(("speed", 0, 1), ("speed", 0, 2)))
        with self.assertRaises(ValidationError):
            constraints(unrecognized=True)

    def test_dialogue_timing_valid_combinations_include_verified_failure(self):
        for timing in ("on_arrival", "on_interaction_success", "on_failure"):
            value = DialogueCondition(kind="outcome", timing=timing, verified_outcome_id="event-1")
            self.assertEqual(value, DialogueCondition.model_validate_json(value.model_dump_json()))
        DialogueCondition(kind="commitment", timing="on_command_accepted")
        DialogueCondition(kind="expression", timing="on_command_accepted")

    def test_dialogue_invalid_timing_combinations(self):
        for fields in (dict(kind="outcome", timing="on_arrival"),
                       dict(kind="outcome", timing="on_command_accepted", verified_outcome_id="event-1"),
                       dict(kind="commitment", timing="on_arrival"),
                       dict(kind="commitment", timing="on_failure"),
                       dict(kind="expression", timing="on_command_accepted", verified_outcome_id="event-1")):
            with self.assertRaises(ValidationError):
                DialogueCondition(**fields)


if __name__ == "__main__":
    unittest.main()
