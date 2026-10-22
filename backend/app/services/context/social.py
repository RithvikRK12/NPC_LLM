"""Shared bounded social-message class, not a general language parser."""
import json
import re


def is_social_message(text):
    # Whole-message day/well-being exchanges must use the same social route
    # for prompting, constrained decoding, history and validation.
    day_exchange = (
        r"\s*(?:how (?:has|was|is|did) your day(?: been| going| go| so far| today)*|"
        r"how['’]s your day(?: been| going| so far| today)*|"
        r"my day (?:has been|was|is) [^.!?]+[.!?]\s*what about you)\s*[.!?]*\s*"
    )
    if (not re.search(r"\b(?:inventory|materials|delivered|requirements|how many|give me|quest|finish my|repair my)\b", text, re.I)
            and re.fullmatch(day_exchange, text, re.I)):
        return True
    # Character reflection is distinct from requests for authoritative quantities or effects.
    if not re.search(r"\b(?:inventory|materials|delivered|requirements|how many|give me|quest|finish my|repair my)\b", text, re.I):
        if re.search(r"^\s*(?:what makes|what do you (?:think|believe|hope|dream|care)|do you ever|how do you (?:cope|spend)|why do you|what(?: is|\x27s) it like|any hobbies)\b",text,re.I):
            return True
        if re.search(r"\b(?:tell me a story|tell me about yourself|village life|living here|enjoy|interests?|lonely|loneliness|patience|uncertain|miss|scared|afraid|ever get home|not working|careful work|repairing useful|what do you do for fun)\b", text, re.I):
            return True
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
