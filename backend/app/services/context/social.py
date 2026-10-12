"""Shared bounded social-message class, not a general language parser."""
import json
import re


def is_social_message(text):
    return bool(re.search(
        r"^\s*(?:(?:hello|hi|hey|thanks|thank you|good morning|good evening)[.!\s]*$|"
        r"(?:i (?:like|prefer|feel|no longer (?:prefer|like|love))|how are you|what do you (?:like|prefer)|"
        r"what(?:'s| is) your favou?rite)\b)", text, re.I))


def social_history(messages):
    result = []
    for i in range(0, len(messages) - 1, 2):
        user, assistant = messages[i:i+2]
        try:
            output = json.loads(assistant['content'])
        except (ValueError, KeyError, TypeError):
            continue
        if is_social_message(user.get('content', '')) and output.get('answer_kind') == 'chat':
            result.extend((user, assistant))
    return result
