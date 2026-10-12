"""Bounded decision evidence; excludes prompts, raw prose, credentials and reasoning."""
from math import isfinite

from app.services.rule_engine.behavior import DIMENSIONS
from app.services.validation.items import ITEMS

TRACE_VERSION = 1


def proposal_summary(raw, permitted_fact_ids):
    """Unknown strings stay in the original conversation audit, never this trace."""
    raw = raw if isinstance(raw, dict) else {}
    ids = raw.get('fact_ids', [])
    ids = ids if isinstance(ids, list) else []
    known = set(permitted_fact_ids)
    selected = sorted({value for value in ids if isinstance(value, str) and value in known})[:2]
    deltas = raw.get('state_update', {})
    deltas = deltas if isinstance(deltas, dict) else {}
    safe_deltas = {key: value for key in DIMENSIONS if
                   isinstance(value := deltas.get(key), (int, float)) and not isinstance(value, bool)
                   and -1 <= value <= 1 and isfinite(value)}
    def choice(key, choices):
        value = raw.get(key)
        return value if isinstance(value, str) and value in choices else None
    return {'answer_kind': choice('answer_kind', {'chat', 'answer', 'clarify'}),
            'fact_ids': selected, 'unrecognized_fact_count': sum(
                not isinstance(value, str) or value not in known for value in ids),
            'action': choice('action', {'speak', 'idle', 'ask_question', 'share_memory',
                                       'give_item', 'receive_item', 'craft_axe', 'repair_tool',
                                       'request_materials', 'help_player'}),
            'item': choice('item', ITEMS), 'state_update': safe_deltas,
            'state_update_invalid': any(key not in safe_deltas for key in deltas),
            'unrecognized_field_count': len(set(raw) - {'answer_kind', 'fact_ids', 'intent', 'emotion',
                                               'dialogue', 'action', 'item', 'reasoning', 'state_update'})}


def build_decision_trace(*, context, raw_proposal, grounding, behavior, generation,
                         conversation, memory_classification, settings, timings):
    outcome = behavior['verified_outcome']
    safe_behavior = {key: behavior[key] for key in ('candidate_state', 'memberships', 'rule_strengths',
                     'outputs', 'ordering', 'eligibility', 'scores', 'selection')}
    mapping = behavior['mapping']
    safe_behavior['mapping'] = {key: mapping[key] for key in ('action', 'item', 'max_dialogue_chars')}
    # Legacy proposals allow free-form emotion labels; never export arbitrary prose.
    emotion = mapping.get('emotion')
    safe_behavior['mapping']['emotion'] = emotion if emotion in {
        'calm', 'friendly', 'guarded', 'neutral', 'angry', 'hostile', 'happy', 'sad', 'curious', 'afraid'
    } else None
    return {
        'schema_version': TRACE_VERSION,
        'decision_id': conversation.source_event_id,
        'recipient_id': conversation.npc_id,
        'game_scope': conversation.game_scope,
        'configuration': {'provider': grounding['provider'], 'model': settings.llm_model,
                          'structured_output': settings.llm_structured_output,
                          'temperature': .2 if grounding['provider'] == 'OpenAICompatibleProvider' else None,
                          'embedding_model': settings.embedding_model,
                          'embedding_revision': settings.embedding_revision,
                          'embedding_dimensions': settings.embedding_dimensions,
                          'behavior_policy': behavior['policy']},
        'generation': generation,
        'proposal': proposal_summary(raw_proposal, [f['id'] for f in context.facts]),
        'context': {'fact_sources': grounding['fact_sources'],
                    'retrieved_memory_provenance': grounding['retrieved_memory_provenance'],
                    'memory_retrieval': context.memory_retrieval,
                    'recent_dialogue_messages': len(context.recent_dialogue)},
        'validation': {'rejected': grounding['rejected'],
                       'reason': grounding['rejection_reason'],
                       'selected_fact_ids': grounding['selected_fact_ids']},
        'behavior': safe_behavior,
        'outcome': {'event_id': conversation.source_event_id, 'conversation_id': conversation.id,
                    'action': outcome['action'], 'transfer': outcome['transfer'],
                    'quest_before': outcome['quest_before'], 'quest_after': outcome['quest_after']},
        'memory_write': {key: memory_classification.get(key) for key in
                         ('important', 'stored', 'memory_id', 'source_event_id', 'epistemic_status', 'authority')},
        'timings_seconds': {key: round(value, 6) for key, value in timings.items()},
    }
