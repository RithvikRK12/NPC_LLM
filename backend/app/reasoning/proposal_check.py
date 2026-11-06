"""Pure decision proposal contract boundary and validation handoffs."""

from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import (
    Activity,
    ContractEnvelope,
    ContractValue,
    DomainError,
    EngineAction,
    ErrorCode,
    Expression,
    Identifier,
    Intent,
    PolicyVersion,
)


ProposalText = Annotated[str, Field(strict=True, min_length=1, max_length=1200)]
RationaleText = Annotated[str, Field(strict=True, min_length=1, max_length=500)]
Confidence = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=0, le=1)]
BoundedDelta = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=-1, le=1)]


class GroundingScope(str, Enum):
    FACT = "fact"
    MEMORY = "memory"
    OBSERVATION = "observation"
    CONSTRAINT = "constraint"


class StateField(str, Enum):
    EMOTION_VALENCE = "emotion_valence"
    TRUST = "trust"
    ATTENTION = "attention"
    URGENCY = "urgency"


class ProposalTarget(ContractValue):
    entity_id: Identifier | None = None
    position_id: Identifier | None = None

    @model_validator(mode="after")
    def exactly_one_target(self):
        if (self.entity_id is None) == (self.position_id is None):
            raise ValueError("proposal target requires exactly one entity_id or position_id")
        return self


class GroundingReference(ContractValue):
    scope: GroundingScope
    ref_id: Identifier


class RelativeStateDelta(ContractValue):
    field: StateField
    delta: BoundedDelta
    source_ref_id: Identifier


class RawProposal(ContractValue):
    snapshot_id: Identifier
    proposed_by: Identifier
    intent: Intent
    action: EngineAction
    activity: Activity
    expression: Expression
    target: ProposalTarget | None = None
    dialogue: ProposalText | None = None
    confidence: Confidence
    grounding: tuple[GroundingReference, ...] = Field(min_length=1)
    rationale: RationaleText
    state_deltas: tuple[RelativeStateDelta, ...] = ()

    @model_validator(mode="after")
    def unique_grounding_and_delta_sources(self):
        references = [(reference.scope, reference.ref_id) for reference in self.grounding]
        if len(set(references)) != len(references):
            raise ValueError("grounding references must be unique")
        delta_keys = [(delta.field, delta.source_ref_id) for delta in self.state_deltas]
        if len(set(delta_keys)) != len(delta_keys):
            raise ValueError("state deltas must be unique per field and source")
        return self


class Snapshot(ContractEnvelope):
    snapshot_id: Identifier
    fact_ids: tuple[Identifier, ...]
    memory_ids: tuple[Identifier, ...]
    observation_ids: tuple[Identifier, ...]
    constraint_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def unique_references(self):
        for field_name in ("fact_ids", "memory_ids", "observation_ids", "constraint_ids"):
            values = getattr(self, field_name)
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} must be unique")
        return self


class ProposalPolicy(ContractEnvelope):
    policy: PolicyVersion
    allowed_intents: tuple[Intent, ...]
    allowed_actions: tuple[EngineAction, ...]
    allowed_state_fields: tuple[StateField, ...]
    max_dialogue_chars: Annotated[int, Field(strict=True, ge=1, le=1200)]

    @model_validator(mode="after")
    def unique_allowed_values(self):
        for field_name in ("allowed_intents", "allowed_actions", "allowed_state_fields"):
            values = getattr(self, field_name)
            if len(set(values)) != len(values):
                raise ValueError(f"{field_name} must be unique")
        return self


class DecisionProposal(ContractEnvelope):
    proposal_id: Identifier
    snapshot_id: Identifier
    policy: PolicyVersion
    intent: Intent
    action: EngineAction
    activity: Activity
    expression: Expression
    target: ProposalTarget | None = None
    dialogue: ProposalText | None = None
    confidence: Confidence
    grounding: tuple[GroundingReference, ...] = Field(min_length=1)
    rationale: RationaleText
    state_deltas: tuple[RelativeStateDelta, ...] = ()

    @model_validator(mode="after")
    def unique_grounding_and_delta_sources(self):
        references = [(reference.scope, reference.ref_id) for reference in self.grounding]
        if len(set(references)) != len(references):
            raise ValueError("grounding references must be unique")
        delta_keys = [(delta.field, delta.source_ref_id) for delta in self.state_deltas]
        if len(set(delta_keys)) != len(delta_keys):
            raise ValueError("state deltas must be unique per field and source")
        return self


ProposalCheckResult: TypeAlias = DecisionProposal | DomainError


class ValidateProposal(Protocol):
    def __call__(
        self,
        raw_proposal: RawProposal,
        snapshot: Snapshot,
        policy: ProposalPolicy,
    ) -> ProposalCheckResult: ...


def validate(
    raw_proposal: RawProposal,
    snapshot: Snapshot,
    policy: ProposalPolicy,
    *,
    proposal_id: Identifier,
) -> ProposalCheckResult:
    lineage_error = _validate_lineage(raw_proposal, snapshot, policy)
    if lineage_error is not None:
        return lineage_error
    vocabulary_error = _validate_policy_vocabulary(raw_proposal, snapshot, policy)
    if vocabulary_error is not None:
        return vocabulary_error
    grounding_error = _validate_grounding(raw_proposal, snapshot, policy)
    if grounding_error is not None:
        return grounding_error

    return DecisionProposal(
        schema_version=snapshot.schema_version,
        record_id=_decision_record_id(proposal_id),
        trace_id=snapshot.trace_id,
        causation_id=snapshot.record_id,
        game_id=snapshot.game_id,
        timeline_id=snapshot.timeline_id,
        npc_id=snapshot.npc_id,
        actor_id=snapshot.actor_id,
        target_id=raw_proposal.target.entity_id if raw_proposal.target is not None else snapshot.target_id,
        created_at=snapshot.created_at,
        source_ids=(snapshot.record_id, policy.record_id),
        policy_versions=(
            *tuple(version for version in snapshot.policy_versions if version.policy_id != policy.policy.policy_id),
            policy.policy,
        ),
        proposal_id=proposal_id,
        snapshot_id=snapshot.snapshot_id,
        policy=policy.policy,
        intent=raw_proposal.intent,
        action=raw_proposal.action,
        activity=raw_proposal.activity,
        expression=raw_proposal.expression,
        target=raw_proposal.target,
        dialogue=raw_proposal.dialogue,
        confidence=raw_proposal.confidence,
        grounding=raw_proposal.grounding,
        rationale=raw_proposal.rationale,
        state_deltas=raw_proposal.state_deltas,
    )


def _validate_lineage(raw_proposal: RawProposal, snapshot: Snapshot, policy: ProposalPolicy) -> DomainError | None:
    if raw_proposal.snapshot_id != snapshot.snapshot_id:
        return _error(snapshot, policy, ErrorCode.INVALID_CONTRACT, "Proposal does not reference the source snapshot.")
    if snapshot.game_id != policy.game_id or snapshot.timeline_id != policy.timeline_id or snapshot.npc_id != policy.npc_id:
        return _error(snapshot, policy, ErrorCode.INVALID_CONTRACT, "Proposal policy evidence is mismatched.")
    policy_versions = {version.policy_id: version.version for version in snapshot.policy_versions}
    if policy_versions.get(policy.policy.policy_id) != policy.policy.version:
        return _error(snapshot, policy, ErrorCode.INVALID_CONTRACT, "Proposal policy version is not present in the snapshot.")
    return None


def _decision_record_id(proposal_id: Identifier) -> Identifier:
    _, _, suffix = proposal_id.partition(":")
    return f"decision-proposal-record:{suffix or proposal_id}"


def _validate_policy_vocabulary(raw_proposal: RawProposal, snapshot: Snapshot, policy: ProposalPolicy) -> DomainError | None:
    if raw_proposal.intent not in policy.allowed_intents:
        return _error(snapshot, policy, ErrorCode.UNKNOWN_ENUM, "Proposal intent is not allowed by policy.")
    if raw_proposal.action not in policy.allowed_actions:
        return _error(snapshot, policy, ErrorCode.UNKNOWN_ENUM, "Proposal action is not allowed by policy.")
    if raw_proposal.dialogue is not None and len(raw_proposal.dialogue) > policy.max_dialogue_chars:
        return _error(snapshot, policy, ErrorCode.INVALID_CONTRACT, "Proposal dialogue exceeds the policy budget.")
    for delta in raw_proposal.state_deltas:
        if delta.field not in policy.allowed_state_fields:
            return _error(snapshot, policy, ErrorCode.INVALID_CONTRACT, "Proposal state delta is not allowed by policy.")
    return None


def _validate_grounding(raw_proposal: RawProposal, snapshot: Snapshot, policy: ProposalPolicy) -> DomainError | None:
    allowed = {
        GroundingScope.FACT: set(snapshot.fact_ids),
        GroundingScope.MEMORY: set(snapshot.memory_ids),
        GroundingScope.OBSERVATION: set(snapshot.observation_ids),
        GroundingScope.CONSTRAINT: set(snapshot.constraint_ids),
    }
    proposal_refs = {reference.ref_id for reference in raw_proposal.grounding}
    for reference in raw_proposal.grounding:
        if reference.ref_id not in allowed[reference.scope]:
            return _error(snapshot, policy, ErrorCode.UNGROUNDED_REFERENCE, "Proposal references evidence outside the snapshot.")
    for delta in raw_proposal.state_deltas:
        if delta.source_ref_id not in proposal_refs:
            return _error(snapshot, policy, ErrorCode.UNGROUNDED_REFERENCE, "Proposal state delta lacks grounding evidence.")
    return None


def _error(snapshot: Snapshot, policy: ProposalPolicy, code: ErrorCode, message: str) -> DomainError:
    return DomainError(
        code=code,
        stage="reasoning.proposal_check",
        retryable=False,
        source_ids=(snapshot.record_id, policy.record_id),
        public_message=message,
    )
