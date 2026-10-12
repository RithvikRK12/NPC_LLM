"""Small response-only fuzzy/FSEC adapter; never authorizes game effects."""
from datetime import datetime, timezone
import json
from pathlib import Path

from app.contracts import PolicyVersion
from app.domain.fuzzy.membership import MembershipInput, MembershipPolicy, Memberships, fuzzify
from app.services.validation.models import StateUpdate
from app.utils.math_utils import clamp

POLICY = json.loads(Path(__file__).with_name('behavior_policy.json').read_text())
DIMENSIONS = ('trust', 'fear', 'aggression', 'curiosity')


def tendencies(state, decision_id, scope):
    version = PolicyVersion(policy_id=POLICY['id'], version=POLICY['version'])
    envelope = dict(schema_version=1, trace_id=decision_id, causation_id=decision_id,
                    game_id='single-player', timeline_id=scope, npc_id='response',
                    created_at=datetime.now(timezone.utc), source_ids=(decision_id,),
                    policy_versions=(version,))
    candidate = MembershipInput(**envelope, record_id=decision_id + ':input',
                                candidate_state_id=decision_id,
                                dimensions=tuple(dict(dimension=k, value=float(state[k])) for k in DIMENSIONS))
    policy = MembershipPolicy(**envelope, record_id=decision_id + ':policy', policy=version,
                              dimensions=tuple(dict(dimension=k, labels=tuple(
                                  dict(label=label, shape=shape) for label, shape in POLICY['memberships'].items()
                              )) for k in DIMENSIONS))
    memberships = fuzzify(candidate, policy, record_id=decision_id + ':memberships')
    if not isinstance(memberships, Memberships):
        raise ValueError(memberships.public_message)
    degrees = {d.dimension: {v.label: v.degree for v in d.labels} for d in memberships.dimensions}
    strengths = {r['id']: min((degrees[d][label] for d, label in r['when']), default=1.0)
                 for r in POLICY['rules']}
    denominator = sum(strengths.values())  # baseline ensures nonzero coverage
    outputs = {name: clamp(sum(strengths[r['id']] * r['outputs'][name] for r in POLICY['rules']) / denominator)
               for name in ('cooperation', 'caution', 'expression')}
    return degrees, strengths, outputs


def select_behavior(npc, player, output, *, rejected, decision_id, scope):
    """Called only after role conditioning and final control validation.

    Item requests already carry independent ownership/role authorization.
    FSEC can narrow those permissions, never create or widen them.
    """
    state = {k: clamp(getattr(npc, k) + getattr(output.state_update, k)) for k in DIMENSIONS}
    degrees, strengths, values = tendencies(state, decision_id, scope)
    required = output.item in POLICY['required_items'] or output.intent == 'unavailable_item'
    request = output.intent == 'confirm_transfer' or output.action in {'give_item', 'receive_item'}
    available = (output.item in (npc.inventory or []) if output.action != 'receive_item'
                 else output.item in (player.inventory or []))
    supported_role = npc.role in {'craftsman', 'gatherer'}
    eligibility = {
        'answer': (not request and output.answer_kind != 'clarify', 'validated non-request response'),
        'clarify': (output.answer_kind == 'clarify' or (request and output.action == 'ask_question'), 'clarification already permitted'),
        'cooperate': (request and available and supported_role, 'authorized request with owned item and supported role'),
        'refuse': (request and available and supported_role and not required and output.action != 'receive_item'
                   and values['cooperation'] <= POLICY['refusal_cooperation_max'], 'optional owned outgoing item; low cooperation only'),
        'offer_recovery': (False, 'no authored recovery route'),
    }
    if rejected:
        eligibility = {k: (k == 'answer', 'rejected proposal: zero-effect fallback only') for k in eligibility}
    scores = {name: clamp(weights.get('bias', 0.0) + sum(weights.get(k, 0.0) * v for k, v in values.items()))
              for name, weights in POLICY['scores'].items() if eligibility[name][0]}
    selection = min(scores, key=lambda name: (-scores[name], name)) if scores else 'answer'
    mapped = output.model_copy(deep=True)
    if selection == 'refuse':
        mapped = mapped.model_copy(update=dict(intent='cancel_transfer', action='speak', item=None,
                    state_update=StateUpdate(), emotion='guarded',
                    dialogue=f"I'd rather keep my {output.item} for now. You can still ask me questions."))
    elif not rejected and (request or (output.answer_kind == 'chat' and output.intent == 'assist')):
        prefix = "Glad to help. " if values['expression'] >= POLICY['expression_threshold'] else "Let's be careful. "
        # Keep complete authoritative text; omit expression when space is tight.
        if len(prefix + mapped.dialogue) <= POLICY['max_dialogue_chars']:
            mapped.dialogue = prefix + mapped.dialogue
    trace = dict(policy={'id': POLICY['id'], 'version': POLICY['version']},
                 decision_id=decision_id, scope_revision=scope, candidate_state=state,
                 memberships=degrees, rule_strengths=strengths, outputs=values,
                 ordering=['role_conditioning', 'final_control_validation', 'fsec'],
                 eligibility={k: {'eligible': v[0], 'reason': v[1]} for k, v in eligibility.items()},
                 scores=scores, selection=selection, required_cooperation_protected=required,
                 mapping={'action': mapped.action, 'item': mapped.item, 'emotion': mapped.emotion,
                          'max_dialogue_chars': POLICY['max_dialogue_chars']})
    return mapped, trace
