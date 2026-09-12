"""C02 closed vocabularies and immutable permission intersections.

Intent labels spell out design 3.3's categories; activity labels describe state,
expression labels describe tone, and engine actions are the exact design list.
These initial version-1 spellings are contract choices, not authored role policy.
Game operations such as trade/crafting are deliberately not engine commands.

Collections with set semantics are sorted tuples for stable cross-language JSON.
None means no additional restriction only in optional target ID sets/time bounds.
Empty allowed sets deny permission. Missing parameter bounds impose no additional
numeric restriction; they do NOT authorize parameters absent from an action's
own schema. Predicate/evidence references must be checked by owning modules.
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import field_validator, model_validator

from .core import ContractValue, FiniteCoordinate, Identifier


class Intent(str, Enum):
    HELP = "help"
    REQUEST_PURPOSE = "request_purpose"
    SET_BOUNDARY = "set_boundary"
    DECLINE = "decline"
    DEFER = "defer"
    SEEK_INFORMATION = "seek_information"
    CONVERSE = "converse"


class Activity(str, Enum):
    IDLE = "idle"
    CONVERSING = "conversing"
    MOVING = "moving"
    INTERACTING = "interacting"


class Expression(str, Enum):
    NEUTRAL = "neutral"
    CALM = "calm"
    CAUTIOUS = "cautious"
    REASSURING = "reassuring"
    FIRM = "firm"
    PRACTICAL = "practical"


class EngineAction(str, Enum):
    IDLE = "idle"
    SPEAK = "speak"
    FACE_TARGET = "face_target"
    MOVE_TO = "move_to"
    APPROACH_TARGET = "approach_target"
    RETREAT_FROM_TARGET = "retreat_from_target"
    INTERACT = "interact"
    PLAY_ANIMATION = "play_animation"


class ApplyWhen(str, Enum):
    APPROVAL = "approval"
    VERIFIED_OUTCOME = "verified_outcome"


class DialogueKind(str, Enum):
    EXPRESSION = "expression"
    COMMITMENT = "commitment"
    OUTCOME = "outcome"


class DialogueTiming(str, Enum):
    ON_COMMAND_ACCEPTED = "on_command_accepted"
    ON_ARRIVAL = "on_arrival"
    ON_INTERACTION_SUCCESS = "on_interaction_success"
    ON_FAILURE = "on_failure"


class DialogueCondition(ContractValue):
    """Structural display condition, not proof of outcome authority or eligibility.

    Outcome references must resolve to matching verified events and typed wording
    before display. Failure outcomes are legitimate; acceptance is not an outcome.
    Commitments begin after acceptance; cancellation handling belongs downstream.
    """

    kind: DialogueKind
    timing: DialogueTiming
    verified_outcome_id: Identifier | None = None

    @model_validator(mode="after")
    def compatible_timing(self) -> "DialogueCondition":
        if self.kind == DialogueKind.OUTCOME:
            if self.verified_outcome_id is None or self.timing == DialogueTiming.ON_COMMAND_ACCEPTED:
                raise ValueError("outcome requires a verified outcome reference and outcome timing")
        elif self.verified_outcome_id is not None:
            raise ValueError("only outcome conditions carry a verified outcome reference")
        if self.kind == DialogueKind.COMMITMENT and self.timing != DialogueTiming.ON_COMMAND_ACCEPTED:
            raise ValueError("commitment must use command acceptance timing")
        return self


class NumericInterval(ContractValue):
    """Closed interval; singleton bounds are valid and disjoint intersection is None."""

    minimum: FiniteCoordinate
    maximum: FiniteCoordinate

    @model_validator(mode="after")
    def ordered(self) -> "NumericInterval":
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self

    def intersection(self, other: "NumericInterval") -> "NumericInterval | None":
        low, high = max(self.minimum, other.minimum), min(self.maximum, other.maximum)
        return None if low > high else NumericInterval(minimum=low, maximum=high)


class TimeWindow(ContractValue):
    """UTC half-open validity window [not_before, expires_at); no default deadline."""

    not_before: datetime | None = None
    expires_at: datetime | None = None

    @field_validator("not_before", "expires_at", mode="before")
    @classmethod
    def timestamp_shape(cls, value: object) -> object:
        if value is not None and (not isinstance(value, (datetime, str)) or
                                  isinstance(value, str) and "T" not in value):
            raise ValueError("time bounds must be aware datetimes or ISO timestamps")
        return value

    @field_validator("not_before", "expires_at")
    @classmethod
    def utc_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            if value.utcoffset() is None:
                raise ValueError("time bounds must include a timezone")
            return value.astimezone(timezone.utc)
        return value

    @model_validator(mode="after")
    def ordered(self) -> "TimeWindow":
        if self.not_before is not None and self.expires_at is not None and self.not_before >= self.expires_at:
            raise ValueError("time window must be nonempty")
        return self

    def intersection(self, other: "TimeWindow") -> "TimeWindow | None":
        starts = [x for x in (self.not_before, other.not_before) if x is not None]
        ends = [x for x in (self.expires_at, other.expires_at) if x is not None]
        start, end = max(starts, default=None), min(ends, default=None)
        if start is not None and end is not None and start >= end:
            return None
        return TimeWindow(not_before=start, expires_at=end)


class TargetKind(str, Enum):
    NONE = "none"
    ENTITY = "entity"
    POSITION = "position"


class TargetPredicate(str, Enum):
    EXISTS = "exists"
    VISIBLE = "visible"
    REACHABLE = "reachable"
    IN_INTERACTION_RANGE = "in_interaction_range"


def _set_intersection(left, right):
    if left is None:
        return right
    if right is None:
        return left
    return tuple(sorted(set(left) & set(right)))


class TargetConstraint(ContractValue):
    """One target-kind alternative; all its predicates are mandatory (AND).

    Entity IDs restrict entity targets; area IDs restrict entity/position targets.
    Empty ID sets explicitly deny this alternative. Backend resolves references
    and reevaluates predicates using fresh authoritative spatial observations.
    """

    kind: TargetKind
    entity_ids: tuple[Identifier, ...] | None = None
    area_ids: tuple[Identifier, ...] | None = None
    predicates: tuple[TargetPredicate, ...] = ()

    @field_validator("entity_ids", "area_ids", "predicates")
    @classmethod
    def canonical_sets(cls, value):
        return None if value is None else tuple(sorted(set(value)))

    @model_validator(mode="after")
    def valid_target_fields(self) -> "TargetConstraint":
        if self.kind != TargetKind.ENTITY and self.entity_ids is not None:
            raise ValueError("entity IDs require an entity target")
        if self.kind == TargetKind.NONE and (self.area_ids is not None or self.predicates):
            raise ValueError("untargeted actions cannot carry target predicates or areas")
        return self

    @property
    def is_denied(self) -> bool:
        return self.entity_ids == () or self.area_ids == ()

    def intersection(self, other: "TargetConstraint") -> "TargetConstraint | None":
        if self.kind != other.kind:
            return None
        result = TargetConstraint(kind=self.kind,
                                  entity_ids=_set_intersection(self.entity_ids, other.entity_ids),
                                  area_ids=_set_intersection(self.area_ids, other.area_ids),
                                  predicates=tuple(set(self.predicates) | set(other.predicates)))
        return None if result.is_denied else result


class ParameterConstraint(ContractValue):
    """Parameter identifiers are owned/validated by each domain/action schema."""

    parameter: Identifier
    interval: NumericInterval


class ActionConstraint(ContractValue):
    """An allowed engine action and its OR alternatives for target kind."""

    action: EngineAction
    targets: tuple[TargetConstraint, ...]
    parameters: tuple[ParameterConstraint, ...] = ()

    @field_validator("targets")
    @classmethod
    def canonical_targets(cls, value):
        if len({x.kind for x in value}) != len(value):
            raise ValueError("one target constraint per target kind is required")
        return tuple(sorted((x for x in value if not x.is_denied), key=lambda x: x.kind))

    @field_validator("parameters")
    @classmethod
    def canonical_parameters(cls, value):
        if len({x.parameter for x in value}) != len(value):
            raise ValueError("parameter bounds must be unique")
        return tuple(sorted(value, key=lambda x: x.parameter))

    def intersection(self, other: "ActionConstraint") -> "ActionConstraint | None":
        if self.action != other.action:
            return None
        target_map = {x.kind: x for x in other.targets}
        targets = tuple(result for x in self.targets if x.kind in target_map
                        if (result := x.intersection(target_map[x.kind])) is not None)
        if not targets:
            return None
        parameters = {x.parameter: x for x in self.parameters}
        for candidate in other.parameters:
            if candidate.parameter in parameters:
                interval = parameters[candidate.parameter].interval.intersection(candidate.interval)
                if interval is None:
                    return None
                parameters[candidate.parameter] = ParameterConstraint(parameter=candidate.parameter, interval=interval)
            else:
                parameters[candidate.parameter] = candidate
        return ActionConstraint(action=self.action, targets=targets, parameters=tuple(parameters.values()))


class ConstraintSet(ContractValue):
    """Pure conjunctive permissions. Empty actions explicitly deny execution.

    No automatic fallback is inserted. Contradictory global permissions normalize
    to the unique deny-all value; contradictions for one action remove only that
    action. Owners evaluate evidence/predicates and action schemas before use.
    """

    intents: tuple[Intent, ...]
    activities: tuple[Activity, ...]
    expressions: tuple[Expression, ...]
    actions: tuple[ActionConstraint, ...]
    dialogue_timings: tuple[DialogueTiming, ...]
    time_window: TimeWindow = TimeWindow()
    mandatory_evidence: tuple[Identifier, ...] = ()

    @field_validator("intents", "activities", "expressions", "dialogue_timings", "mandatory_evidence")
    @classmethod
    def canonical_sets(cls, value):
        return tuple(sorted(set(value)))

    @field_validator("actions")
    @classmethod
    def canonical_actions(cls, value):
        if len({x.action for x in value}) != len(value):
            raise ValueError("action constraints must be unique")
        return tuple(sorted((x for x in value if x.targets), key=lambda x: x.action))

    @model_validator(mode="after")
    def normalize_denial(self) -> "ConstraintSet":
        # Denial is canonical for equality and algebra, with no executable action.
        if not all((self.intents, self.activities, self.expressions, self.actions)):
            for field in ("intents", "activities", "expressions", "actions", "dialogue_timings", "mandatory_evidence"):
                object.__setattr__(self, field, ())
            object.__setattr__(self, "time_window", TimeWindow())
        return self

    @classmethod
    def deny_all(cls) -> "ConstraintSet":
        return cls(intents=(), activities=(), expressions=(), actions=(), dialogue_timings=())

    @property
    def is_denied(self) -> bool:
        return not self.actions

    def intersection(self, other: "ConstraintSet") -> "ConstraintSet":
        window = self.time_window.intersection(other.time_window)
        if self.is_denied or other.is_denied or window is None:
            return self.deny_all()
        action_map = {x.action: x for x in other.actions}
        actions = tuple(result for x in self.actions if x.action in action_map
                        if (result := x.intersection(action_map[x.action])) is not None)
        return ConstraintSet(
            intents=_set_intersection(self.intents, other.intents),
            activities=_set_intersection(self.activities, other.activities),
            expressions=_set_intersection(self.expressions, other.expressions),
            actions=actions, dialogue_timings=_set_intersection(self.dialogue_timings, other.dialogue_timings),
            time_window=window, mandatory_evidence=tuple(set(self.mandatory_evidence) | set(other.mandatory_evidence)))

    def is_narrower_than(self, previous: "ConstraintSet") -> bool:
        """Includes equality and deny-all; does not evaluate referenced evidence."""
        return self.intersection(previous) == self
