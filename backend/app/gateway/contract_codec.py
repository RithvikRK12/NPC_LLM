"""Pure contract codec for command transport payloads."""

import json
from datetime import datetime
from typing import Annotated, Any, Protocol, TypeAlias

from pydantic import Field, field_validator, model_validator

from app.contracts import (
    ContractEnvelope,
    ContractValue,
    DialogueCondition,
    DomainError,
    EngineAction,
    ErrorCode,
    FiniteCoordinate,
    Identifier,
    Position,
    Revision,
    TimeWindow,
)


ParameterValue = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=0, le=10000)]
COMMAND_SCHEMA_VERSION = 1
ENTITY_TARGET_ACTIONS = {
    EngineAction.FACE_TARGET,
    EngineAction.APPROACH_TARGET,
    EngineAction.RETREAT_FROM_TARGET,
    EngineAction.INTERACT,
}
POSITION_TARGET_ACTIONS = {EngineAction.MOVE_TO}
MOVEMENT_ACTIONS = {
    EngineAction.MOVE_TO,
    EngineAction.APPROACH_TARGET,
    EngineAction.RETREAT_FROM_TARGET,
}


class CommandParameters(ContractValue):
    max_speed: ParameterValue | None = None
    arrival_distance: ParameterValue | None = None
    animation_speed: ParameterValue | None = None

    @model_validator(mode="after")
    def known_parameter_values(self):
        return self


class GatewayCommand(ContractEnvelope):
    command_id: Identifier
    approval_id: Identifier
    controller_revision: Revision
    kind: EngineAction
    position: Position | None = None
    parameters: CommandParameters
    issued_at: datetime
    expires_at: datetime
    dialogue: tuple[DialogueCondition, ...] = ()

    @field_validator("issued_at", "expires_at", mode="before")
    @classmethod
    def timestamp_shape(cls, value):
        return TimeWindow.timestamp_shape(value)

    @field_validator("issued_at", "expires_at")
    @classmethod
    def utc_timestamp(cls, value):
        return TimeWindow.utc_timestamp(value)

    @model_validator(mode="after")
    def command_shape(self):
        TimeWindow(not_before=self.issued_at, expires_at=self.expires_at)
        if self.kind in ENTITY_TARGET_ACTIONS and self.target_id is None:
            raise ValueError("command action requires an entity target")
        if self.kind in POSITION_TARGET_ACTIONS and self.position is None:
            raise ValueError("move_to requires a position target")
        if self.kind not in POSITION_TARGET_ACTIONS and self.position is not None:
            raise ValueError("only move_to carries a position target")
        movement_values = (self.parameters.max_speed, self.parameters.arrival_distance)
        if self.kind in MOVEMENT_ACTIONS:
            if any(value is None for value in movement_values):
                raise ValueError("movement commands require bounded movement parameters")
        elif any(value is not None for value in movement_values):
            raise ValueError("nonmovement commands cannot carry movement parameters")
        return self


class GatewayDisplayRecord(ContractValue):
    display_id: Identifier
    text: Annotated[str, Field(strict=True, min_length=1, max_length=300)]
    condition: DialogueCondition


class GatewayOutcomeRecord(ContractValue):
    outcome_id: Identifier
    command_id: Identifier
    success: bool = Field(strict=True)
    occurred_at: datetime

    @field_validator("occurred_at", mode="before")
    @classmethod
    def timestamp_shape(cls, value):
        return TimeWindow.timestamp_shape(value)

    @field_validator("occurred_at")
    @classmethod
    def utc_timestamp(cls, value):
        return TimeWindow.utc_timestamp(value)


class CommandResult(ContractEnvelope):
    command: GatewayCommand
    displays: tuple[GatewayDisplayRecord, ...] = ()
    outcomes: tuple[GatewayOutcomeRecord, ...] = ()

    @model_validator(mode="after")
    def linked_records(self):
        if any(outcome.command_id != self.command.command_id for outcome in self.outcomes):
            raise ValueError("outcomes must reference the decoded command")
        return self


DecodeResult: TypeAlias = CommandResult | DomainError


class DecodeCommand(Protocol):
    def __call__(self, payload: str | dict[str, Any], *, current_timeline_id: Identifier) -> DecodeResult: ...


def decode_command(payload: str | dict[str, Any], *, current_timeline_id: Identifier) -> DecodeResult:
    try:
        data = _payload(payload)
        command_data = data["command"]
        if not isinstance(command_data, dict):
            return _error(ErrorCode.INVALID_CONTRACT, "Command payload failed contract validation.", ())
        if command_data.get("schema_version") != COMMAND_SCHEMA_VERSION:
            source = command_data.get("record_id")
            source_ids = (source,) if isinstance(source, str) and source else ()
            return _error(ErrorCode.INVALID_CONTRACT, "Command payload version is unsupported.", source_ids)
        command = GatewayCommand.model_validate(command_data)
        displays = tuple(GatewayDisplayRecord.model_validate(item) for item in data.get("displays", ()))
        outcomes = tuple(GatewayOutcomeRecord.model_validate(item) for item in data.get("outcomes", ()))
        result = CommandResult(
            schema_version=command.schema_version,
            record_id=data["record_id"],
            trace_id=command.trace_id,
            causation_id=command.record_id,
            game_id=command.game_id,
            timeline_id=command.timeline_id,
            npc_id=command.npc_id,
            actor_id=command.actor_id,
            target_id=command.target_id,
            created_at=command.created_at,
            source_ids=(command.record_id,),
            policy_versions=command.policy_versions,
            command=command,
            displays=displays,
            outcomes=outcomes,
        )
    except KeyError as exc:
        return _error(ErrorCode.INVALID_CONTRACT, f"Command payload is missing required field: {exc.args[0]}.", ())
    except (TypeError, ValueError) as exc:
        return _error(_code_for_exception(exc), "Command payload failed contract validation.", ())

    if result.timeline_id != current_timeline_id:
        return _error(ErrorCode.OLD_TIMELINE, "Command payload timeline is no longer current.", (result.command.record_id,))
    return result


def _payload(payload: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, str):
        parsed = json.loads(payload, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
    else:
        parsed = payload
    if not isinstance(parsed, dict):
        raise ValueError("payload must be an object")
    return parsed


def _reject_constant(value: str):
    raise ValueError(f"nonstandard JSON constant: {value}")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _code_for_exception(exc: Exception) -> ErrorCode:
    text = str(exc)
    if "finite" in text or "less than or equal" in text or "greater than or equal" in text:
        return ErrorCode.INVALID_CONTRACT
    if "enum" in text or "Input should be" in text:
        return ErrorCode.UNKNOWN_ENUM
    return ErrorCode.INVALID_CONTRACT


def _error(code: ErrorCode, message: str, source_ids: tuple[Identifier, ...]) -> DomainError:
    return DomainError(
        code=code,
        stage="gateway.contract_codec",
        retryable=False,
        source_ids=source_ids,
        public_message=message,
    )
