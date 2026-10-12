"""Pure dialogue event composition."""

from enum import Enum
from typing import Annotated, Protocol, TypeAlias

from pydantic import Field, model_validator

from app.contracts import ContractEnvelope, ContractValue, DialogueCondition, DialogueKind, DialogueTiming, DomainError, ErrorCode, Expression, Identifier, PolicyVersion


DialogueText = Annotated[str, Field(strict=True, min_length=1, max_length=300)]


class DialogueSourceKind(str, Enum):
    EXPRESSION = "expression"
    COMMITMENT = "commitment"
    VERIFIED_EVENT = "verified_event"


class VerifiedEventKind(str, Enum):
    QUEST_REWARD_GRANTED = "quest_reward_granted"
    ITEM_TRANSFERRED = "item_transferred"
    INTERACTION_FAILED = "interaction_failed"


class ApprovedDialogue(ContractEnvelope):
    source_id: Identifier
    kind: DialogueSourceKind
    expression: Expression
    approved_text: DialogueText | None = None
    verified_event_id: Identifier | None = None
    verified_event_kind: VerifiedEventKind | None = None
    event_fields: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def compatible_source(self):
        if self.kind == DialogueSourceKind.VERIFIED_EVENT:
            if self.verified_event_id is None or self.verified_event_kind is None:
                raise ValueError("verified event dialogue requires event identity and kind")
        elif self.verified_event_id is not None or self.verified_event_kind is not None:
            raise ValueError("only verified event dialogue carries verified event fields")
        if self.kind != DialogueSourceKind.VERIFIED_EVENT and self.approved_text is None:
            raise ValueError("expression and commitment dialogue require approved text")
        return self


class DialogueTemplate(ContractValue):
    event_kind: VerifiedEventKind
    template_id: Identifier
    text: DialogueText
    required_fields: tuple[Identifier, ...]

    @model_validator(mode="after")
    def unique_fields(self):
        if len(set(self.required_fields)) != len(self.required_fields):
            raise ValueError("required_fields must be unique")
        return self


class DialoguePolicy(ContractEnvelope):
    policy: PolicyVersion
    max_text_chars: int = Field(strict=True, ge=1, le=300)
    safe_ambiguous_success_text: DialogueText
    outcome_templates: tuple[DialogueTemplate, ...]

    @model_validator(mode="after")
    def unique_templates(self):
        if len({template.event_kind for template in self.outcome_templates}) != len(self.outcome_templates):
            raise ValueError("outcome_templates must contain one template per event kind")
        return self


class DialogueEvent(ContractEnvelope):
    display_id: Identifier
    source_id: Identifier
    text: DialogueText
    expression: Expression
    condition: DialogueCondition
    policy: PolicyVersion


DialogueComposeResult: TypeAlias = DialogueEvent | DomainError


class ComposeDialogue(Protocol):
    def __call__(self, source: ApprovedDialogue, policy: DialoguePolicy) -> DialogueComposeResult: ...


SUCCESS_TOKENS = ("complete", "completed", "done", "reward", "granted", "gave", "finished", "success")


def compose(
    source: ApprovedDialogue,
    policy: DialoguePolicy,
    *,
    record_id: Identifier,
    display_id: Identifier,
    created_at=None,
) -> DialogueComposeResult:
    evidence_error = _validate_evidence(source, policy)
    if evidence_error is not None:
        return evidence_error
    if source.kind == DialogueSourceKind.VERIFIED_EVENT:
        return _compose_outcome(source, policy, record_id, display_id, created_at)

    text = source.approved_text or policy.safe_ambiguous_success_text
    if _ambiguous_success_claim(text):
        text = policy.safe_ambiguous_success_text
    if len(text) > policy.max_text_chars:
        return _error(source, policy, ErrorCode.INVALID_CONTRACT, "Approved dialogue exceeds policy bounds.")
    kind = DialogueKind.EXPRESSION if source.kind == DialogueSourceKind.EXPRESSION else DialogueKind.COMMITMENT
    timing = DialogueTiming.ON_COMMAND_ACCEPTED if kind == DialogueKind.COMMITMENT else DialogueTiming.ON_COMMAND_ACCEPTED
    return _event(source, policy, record_id, display_id, text, kind, timing, source.expression, None, created_at)


def _compose_outcome(
    source: ApprovedDialogue,
    policy: DialoguePolicy,
    record_id: Identifier,
    display_id: Identifier,
    created_at,
) -> DialogueComposeResult:
    template = next((candidate for candidate in policy.outcome_templates if candidate.event_kind == source.verified_event_kind), None)
    if template is None:
        return _error(source, policy, ErrorCode.UNSUPPORTED_CAPABILITY, "No authored template exists for verified event kind.")
    missing = [field for field in template.required_fields if field not in source.event_fields]
    if missing:
        return _error(source, policy, ErrorCode.UNGROUNDED_REFERENCE, "Verified event is missing fields required by dialogue template.")
    try:
        text = template.text.format(**source.event_fields)
    except KeyError:
        return _error(source, policy, ErrorCode.UNGROUNDED_REFERENCE, "Verified event fields do not match dialogue template.")
    if len(text) > policy.max_text_chars:
        return _error(source, policy, ErrorCode.INVALID_CONTRACT, "Composed outcome dialogue exceeds policy bounds.")
    return _event(
        source,
        policy,
        record_id,
        display_id,
        text,
        DialogueKind.OUTCOME,
        DialogueTiming.ON_INTERACTION_SUCCESS,
        source.expression,
        source.verified_event_id,
        created_at,
    )


def _event(
    source: ApprovedDialogue,
    policy: DialoguePolicy,
    record_id: Identifier,
    display_id: Identifier,
    text: str,
    kind: DialogueKind,
    timing: DialogueTiming,
    expression: Expression,
    verified_outcome_id: Identifier | None,
    created_at,
) -> DialogueEvent:
    return DialogueEvent(
        schema_version=source.schema_version,
        record_id=record_id,
        trace_id=source.trace_id,
        causation_id=source.record_id,
        game_id=source.game_id,
        timeline_id=source.timeline_id,
        npc_id=source.npc_id,
        actor_id=source.actor_id,
        target_id=source.target_id,
        created_at=created_at or source.created_at,
        source_ids=(source.record_id, policy.record_id),
        policy_versions=(
            *tuple(version for version in source.policy_versions if version.policy_id != policy.policy.policy_id),
            policy.policy,
        ),
        display_id=display_id,
        source_id=source.source_id,
        text=text,
        expression=expression,
        condition=DialogueCondition(kind=kind, timing=timing, verified_outcome_id=verified_outcome_id),
        policy=policy.policy,
    )


def _validate_evidence(source: ApprovedDialogue, policy: DialoguePolicy) -> DomainError | None:
    if source.game_id != policy.game_id or source.timeline_id != policy.timeline_id or source.npc_id != policy.npc_id:
        return _error(source, policy, ErrorCode.INVALID_CONTRACT, "Dialogue policy evidence is mismatched.")
    policy_versions = {version.policy_id: version.version for version in source.policy_versions}
    if policy_versions.get(policy.policy.policy_id) != policy.policy.version:
        return _error(source, policy, ErrorCode.INVALID_CONTRACT, "Dialogue policy version is not present in source.")
    return None


def _ambiguous_success_claim(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in SUCCESS_TOKENS)


def _error(source: ApprovedDialogue, policy: DialoguePolicy, code: ErrorCode, message: str) -> DomainError:
    return DomainError(
        code=code,
        stage="dialogue.compose",
        retryable=False,
        source_ids=(source.record_id, policy.record_id),
        public_message=message,
    )

