"""Safe capability descriptors projected from injected authoritative views.

This module owns no command registry or permission rules. The game service that
owns each rule supplies the audited view; this layer only copies its supported
surface into detached conversation contracts and drops server-private evidence.
"""
from collections.abc import Callable, Iterable
from typing import Protocol

from .contracts import CapabilityDescriptor, Precondition, TargetReference


class AuthoritativeCapabilityView(Protocol):
    """Detached rule-owner result; private evidence is intentionally not read."""

    command_id: str
    parameter_schema: object
    allowed_target_references: tuple[TargetReference, ...]
    available: bool
    safe_unavailable_reason: str | None
    relevant_preconditions: tuple[Precondition, ...]
    supported_speech_acts: tuple[str, ...]


CapabilityViewReader = Callable[[str, int], Iterable[AuthoritativeCapabilityView]]


def build_descriptors(
    views: Iterable[AuthoritativeCapabilityView],
) -> tuple[CapabilityDescriptor, ...]:
    """Project authoritative command views without creating capabilities.

    Duplicate command IDs are ambiguous and fail closed. Server-private
    preconditions are authorization evidence, so they are omitted. Unavailable
    reasons must already be safe public explanations supplied by the rule owner.
    """
    descriptors: list[CapabilityDescriptor] = []
    seen: set[str] = set()
    for view in views:
        command_id = view.command_id
        if command_id in seen:
            raise ValueError('authoritative capability views contain duplicate commands')
        seen.add(command_id)
        preconditions = tuple(
            sorted(
                (item for item in view.relevant_preconditions
                 if item.source.visibility != 'server_private'),
                key=lambda item: item.precondition_id,
            )
        )
        targets = tuple(sorted(view.allowed_target_references, key=lambda item: item.reference_id))
        speech_acts = tuple(sorted(view.supported_speech_acts))
        descriptors.append(CapabilityDescriptor(
            command_id=command_id,
            parameter_schema=view.parameter_schema,
            allowed_target_references=targets,
            available=view.available,
            safe_unavailable_reason=view.safe_unavailable_reason,
            relevant_preconditions=preconditions,
            supported_speech_acts=speech_acts,
        ))
    return tuple(sorted(descriptors, key=lambda item: item.command_id))


class CapabilityReader:
    """Read authoritative views through an injected rule-owner boundary."""

    def __init__(self, read_views: CapabilityViewReader):
        if not callable(read_views):
            raise TypeError('read_views must be callable')
        self._read_views = read_views

    def read(self, scope: str, npc_id: int) -> tuple[CapabilityDescriptor, ...]:
        return build_descriptors(self._read_views(scope, npc_id))
