"""Pure state merge handoffs and precedence selection."""

from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DomainError, ErrorCode, Identifier, PolicyVersion, RevisionSet


StateValue = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=-1, le=1)]
RelativeDelta = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=-1, le=1)]


class StateDimension(str, Enum):
    EMOTION_VALENCE = "emotion_valence"
    ATTENTION = "attention"
    URGENCY = "urgency"
    TRUST = "trust"
    RELATIONSHIP = "relationship"


class ChangeSource(str, Enum):
    VERIFIED_EVENT = "verified_event"
    DECISION_PROPOSAL = "decision_proposal"
    MEMORY_INFLUENCE = "memory_influence"


class MergeDecision(str, Enum):
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"
    DUPLICATE_REJECTED = "duplicate_rejected"


class CurrentState(ContractEnvelope):
    state_id: Identifier
    revisions: RevisionSet
    scalar_values: tuple["StateScalar", ...]
    known_relationship_subject_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def unique_state_fields(self):
        scalar_keys = [(value.dimension, value.subject_id) for value in self.scalar_values]
        if len(set(scalar_keys)) != len(scalar_keys):
            raise ValueError("scalar_values must be unique per dimension and subject")
        if len(set(self.known_relationship_subject_ids)) != len(self.known_relationship_subject_ids):
            raise ValueError("known_relationship_subject_ids must be unique")
        return self


class StateScalar(ContractValue):
    dimension: StateDimension
    value: StateValue
    subject_id: Identifier | None = None

    @model_validator(mode="after")
    def subject_matches_dimension(self):
        if self.dimension in (StateDimension.TRUST, StateDimension.RELATIONSHIP):
            if self.subject_id is None:
                raise ValueError("relationship dimensions require subject_id")
        elif self.subject_id is not None:
            raise ValueError("non-relationship dimensions cannot carry subject_id")
        return self


class ProposedChange(ContractValue):
    effect_id: Identifier
    dimension: StateDimension
    delta: RelativeDelta
    source: ChangeSource
    source_id: Identifier
    subject_id: Identifier | None = None

    @model_validator(mode="after")
    def subject_matches_dimension(self):
        if self.dimension in (StateDimension.TRUST, StateDimension.RELATIONSHIP):
            if self.subject_id is None:
                raise ValueError("relationship changes require subject_id")
        elif self.subject_id is not None:
            raise ValueError("non-relationship changes cannot carry subject_id")
        return self


class ProposedChanges(ContractEnvelope):
    proposal_set_id: Identifier
    changes: tuple[ProposedChange, ...]


class MergePolicy(ContractEnvelope):
    policy: PolicyVersion
    source_precedence: tuple[ChangeSource, ...]
    reject_duplicate_effects: Annotated[bool, Field(strict=True)]

    @model_validator(mode="after")
    def unique_precedence(self):
        if len(set(self.source_precedence)) != len(self.source_precedence):
            raise ValueError("source_precedence must be unique")
        if set(self.source_precedence) != set(ChangeSource):
            raise ValueError("source_precedence must include every change source")
        return self


class MergedChange(ContractValue):
    effect_id: Identifier
    dimension: StateDimension
    delta: RelativeDelta
    source: ChangeSource
    source_id: Identifier
    decision: MergeDecision
    reason: Identifier
    subject_id: Identifier | None = None

    @model_validator(mode="after")
    def subject_matches_dimension(self):
        if self.dimension in (StateDimension.TRUST, StateDimension.RELATIONSHIP):
            if self.subject_id is None:
                raise ValueError("relationship changes require subject_id")
        elif self.subject_id is not None:
            raise ValueError("non-relationship changes cannot carry subject_id")
        return self


class MergedChanges(ContractEnvelope):
    state_id: Identifier
    proposal_set_id: Identifier
    policy: PolicyVersion
    accepted: tuple[MergedChange, ...]
    rejected: tuple[MergedChange, ...]

    @model_validator(mode="after")
    def unique_accepted_targets(self):
        targets = [(change.dimension, change.subject_id) for change in self.accepted]
        if len(set(targets)) != len(targets):
            raise ValueError("accepted changes must be unique per dimension and subject")
        return self


MergeResult: TypeAlias = MergedChanges | DomainError


class Merge(Protocol):
    def __call__(self, current: CurrentState, proposed: ProposedChanges, policy: MergePolicy) -> MergeResult: ...


def merge(
    current: CurrentState,
    proposed: ProposedChanges,
    policy: MergePolicy,
    *,
    record_id: Identifier,
    created_at=None,
) -> MergeResult:
    validation_error = _validate_inputs(current, proposed, policy)
    if validation_error is not None:
        return validation_error

    duplicate_error = _duplicate_effect_error(current, proposed, policy)
    if duplicate_error is not None:
        return duplicate_error

    precedence = {source: index for index, source in enumerate(policy.source_precedence)}
    grouped: dict[tuple[StateDimension, Identifier | None], list[ProposedChange]] = {}
    for change in proposed.changes:
        grouped.setdefault((change.dimension, change.subject_id), []).append(change)

    accepted: list[MergedChange] = []
    rejected: list[MergedChange] = []
    for changes in grouped.values():
        winner = min(changes, key=lambda change: (precedence[change.source], change.effect_id))
        for change in sorted(changes, key=lambda change: (precedence[change.source], change.effect_id)):
            if change == winner:
                accepted.append(_merged(change, MergeDecision.ACCEPTED, "state.merge:highest_precedence"))
            else:
                rejected.append(_merged(change, MergeDecision.SUPERSEDED, "state.merge:lower_precedence"))

    return MergedChanges(
        schema_version=current.schema_version,
        record_id=record_id,
        trace_id=current.trace_id,
        causation_id=proposed.record_id,
        game_id=current.game_id,
        timeline_id=current.timeline_id,
        npc_id=current.npc_id,
        actor_id=current.actor_id,
        target_id=current.target_id,
        created_at=created_at or proposed.created_at,
        source_ids=(current.record_id, proposed.record_id, policy.record_id),
        policy_versions=(
            *tuple(version for version in current.policy_versions if version.policy_id != policy.policy.policy_id),
            policy.policy,
        ),
        state_id=current.state_id,
        proposal_set_id=proposed.proposal_set_id,
        policy=policy.policy,
        accepted=tuple(accepted),
        rejected=tuple(rejected),
    )


def _validate_inputs(current: CurrentState, proposed: ProposedChanges, policy: MergePolicy) -> DomainError | None:
    if current.game_id != proposed.game_id or current.timeline_id != proposed.timeline_id:
        return _error(current, proposed, policy, ErrorCode.INVALID_CONTRACT, "Proposed changes are not for the current state timeline.")
    if current.game_id != policy.game_id or current.timeline_id != policy.timeline_id:
        return _error(current, proposed, policy, ErrorCode.INVALID_CONTRACT, "Merge policy is not for the current state timeline.")
    policy_versions = {version.policy_id: version.version for version in current.policy_versions}
    if policy_versions.get(policy.policy.policy_id) != policy.policy.version:
        return _error(current, proposed, policy, ErrorCode.INVALID_CONTRACT, "Merge policy version is not present in current state.")
    known_subjects = set(current.known_relationship_subject_ids)
    for change in proposed.changes:
        if change.subject_id is not None and change.subject_id not in known_subjects:
            return _error(current, proposed, policy, ErrorCode.INVALID_CONTRACT, "Proposed change references an unknown relationship subject.")
    return None


def _duplicate_effect_error(current: CurrentState, proposed: ProposedChanges, policy: MergePolicy) -> DomainError | None:
    if not policy.reject_duplicate_effects:
        return None
    seen: set[Identifier] = set()
    for change in proposed.changes:
        if change.effect_id in seen:
            return _error(current, proposed, policy, ErrorCode.INVALID_CONTRACT, "Proposed changes contain a duplicate effect identity.")
        seen.add(change.effect_id)
    return None


def _merged(change: ProposedChange, decision: MergeDecision, reason: Identifier) -> MergedChange:
    return MergedChange(
        effect_id=change.effect_id,
        dimension=change.dimension,
        delta=change.delta,
        source=change.source,
        source_id=change.source_id,
        subject_id=change.subject_id,
        decision=decision,
        reason=reason,
    )


def _error(current: CurrentState, proposed: ProposedChanges, policy: MergePolicy, code: ErrorCode, message: str) -> DomainError:
    return DomainError(
        code=code,
        stage="state.merge",
        retryable=False,
        source_ids=(current.record_id, proposed.record_id, policy.record_id),
        public_message=message,
    )

