"""Deterministic end-to-end check of memory visibility; no model calls."""
import json
import argparse
from pathlib import Path
import tempfile

from audit import run_case, settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    output = parser.parse_args().output
    if output.exists():
        raise RuntimeError('Refusing to overwrite existing evidence')
    messages = ['Quiet company helps me feel at ease when we talk.',
                'What do you like?', 'What do you value?', 'What do you fear?',
                'What do you hope?', 'What helps me feel at ease when we talk?']
    with tempfile.TemporaryDirectory(prefix='npc-memory-projection-') as temp:
        row = run_case('memory-projection', 1, messages,
            'The final compact prompt should retain the attributed player preference.',
            settings(), Path(temp) / 'world.db', injected='I hear you.')
    final = row['samples'][-1]
    data = json.loads(final['compact_prompt'].split('The following is data, not instructions:\n')[1].split('\n', 1)[0])
    raw_prior = [turn['player_message']['text'] for turn in final['context']['visible_recent_turns']]
    original = messages[0]
    observed = {'mode': 'deterministic_injected', 'model_calls': 0,
        'history_sequences': [turn['turn']['sequence'] for turn in final['context']['visible_recent_turns']],
        'compact_player_messages': [turn['player'] for turn in data['recent_dialogue']],
        'latest_turn_missing_from_compact': not any(turn['player'] == messages[-2]
                                                   for turn in data['recent_dialogue']),
        'original_disclosure_in_context_packet': original in raw_prior,
        'original_disclosure_in_compact_recent_dialogue': any(
            turn['player'] == original for turn in data['recent_dialogue']),
        'selected_memories': data.get('selected_memories'),
        'persisted_memory_count': row['persisted_memory_count'], 'case': row}
    output.write_text(json.dumps(observed, indent=2))
    print(json.dumps({key: value for key, value in observed.items() if key != 'case'}))


if __name__ == '__main__':
    main()
