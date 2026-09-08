from __future__ import annotations

import json
from typing import Any


def strip_code_fences(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def parse_strict_json(raw_text: str) -> dict[str, Any]:
    text = strip_code_fences(raw_text)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("LLM output must be a JSON object")
    return parsed


def dumps_pretty(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True)