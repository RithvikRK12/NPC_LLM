"""C03 fixture-only Python decoder; never schedules commands or grants authority.

The limited command shape exercises C01/C02 across languages. Production command
ownership remains application.commands. Successful decoding establishes syntax
and fixture linkage only; it does not verify approval, targets or outcomes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from app.contracts import (
    ContractEnvelope, ContractValue, DialogueCondition, EngineAction, Expression,
    Identifier, Position, Revision, RevisionSet, TimeWindow,
)

FixtureNumber = Annotated[float, Field(strict=True, ge=0, le=9007199254740991, allow_inf_nan=False)]
MOVEMENT = {EngineAction.MOVE_TO, EngineAction.APPROACH_TARGET, EngineAction.RETREAT_FROM_TARGET}
ENTITY_TARGET = {EngineAction.FACE_TARGET, EngineAction.APPROACH_TARGET, EngineAction.RETREAT_FROM_TARGET, EngineAction.INTERACT}


class FixtureParameters(ContractValue):
    expression: Expression
    max_speed: FixtureNumber | None
    arrival_distance: FixtureNumber | None


class FixtureCommand(ContractValue):
    approval_id: Identifier
    controller_revision: Revision
    kind: EngineAction
    target_id: Identifier | None
    position: Position | None
    parameters: FixtureParameters
    issued_at: datetime
    expires_at: datetime
    dialogue_condition: DialogueCondition | None

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
        if self.kind in ENTITY_TARGET and self.target_id is None:
            raise ValueError("fixture action requires an entity target")
        if (self.kind == EngineAction.MOVE_TO) != (self.position is not None):
            raise ValueError("fixture move_to requires a position; other kinds omit it")
        movement_values = (self.parameters.max_speed, self.parameters.arrival_distance)
        if self.kind in MOVEMENT:
            if any(value is None for value in movement_values):
                raise ValueError("fixture movement requires bounded movement parameters")
        elif any(value is not None for value in movement_values):
            raise ValueError("fixture nonmovement commands cannot carry movement parameters")
        return self


class CommandFixture(ContractValue):
    envelope: ContractEnvelope
    revisions: RevisionSet
    command: FixtureCommand

    @model_validator(mode="after")
    def consistent_links(self):
        if self.envelope.npc_id != self.revisions.npc_id:
            raise ValueError("fixture NPC revision scope mismatch")
        if self.revisions.approved_npc_state_revision is None:
            raise ValueError("fixture command requires approved state revision")
        if self.command.approval_id != self.envelope.causation_id:
            raise ValueError("fixture approval must be the envelope's causation")
        if self.command.target_id != self.envelope.target_id:
            raise ValueError("fixture target mismatch")
        if self.command.issued_at != self.envelope.created_at:
            raise ValueError("fixture issuance must match envelope creation")
        controllers = {entry.scope_id: entry.revision for entry in self.revisions.controller}
        if controllers.get(self.envelope.npc_id) != self.command.controller_revision:
            raise ValueError("fixture controller revision must match the NPC scope")
        return self


def _reject_constant(value):
    raise ValueError(f"nonstandard JSON constant: {value}")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def decode_fixture(payload: str) -> CommandFixture:
    return CommandFixture.model_validate(json.loads(payload, parse_constant=_reject_constant, object_pairs_hook=_unique_object))


def read_fixture(path: Path) -> CommandFixture:
    return decode_fixture(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    fixture_dir = Path(__file__).resolve().parents[2].parent / "contracts" / "fixtures" / "v1"
    failures = []
    for path in sorted(fixture_dir.glob("*.json")):
        try:
            read_fixture(path)
            valid = True
        except (ValueError, TypeError):
            valid = False
        expected = path.name.startswith("valid-")
        if valid != expected:
            failures.append(path.name)
        print(f"{'PASS' if valid == expected else 'FAIL'} {path.name}")
    if not list(fixture_dir.glob("*.json")):
        raise SystemExit("No shared fixtures found")
    raise SystemExit(1 if failures else 0)
