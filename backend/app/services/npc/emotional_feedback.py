"""Bounded state policy driven by semantic player conduct, independent of prose."""
from app.services.validation.models import StateUpdate
from app.utils.math_utils import clamp

MAX_CHANGE = .4
REACTIONS = {
    'conciliatory': {'trust': .2, 'fear': -.1, 'aggression': -.2, 'curiosity': .1},
    'antagonistic': {'trust': -.3, 'aggression': .3, 'curiosity': -.1},
    'intimidating': {'trust': -.3, 'fear': .3, 'aggression': .2, 'curiosity': -.1},
    'engaging': {'curiosity': .2},
}


def emotional_feedback(interpretation: dict) -> StateUpdate:
    changes = {key: 0. for key in ('trust', 'fear', 'aggression', 'curiosity')}
    for concern in interpretation.get('concerns', []):
        if concern.get('kind') != 'social' or concern.get('modality') != 'direct':
            continue
        for key, value in REACTIONS.get(concern.get('social_effect'), {}).items():
            changes[key] += value
    return StateUpdate(**{key: clamp(value, -MAX_CHANGE, MAX_CHANGE) for key, value in changes.items()})
