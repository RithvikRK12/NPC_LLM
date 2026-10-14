from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config.settings import get_settings
from app.services.context.social import is_social_message, social_history
from app.services.llm.provider import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self) -> None:
        self._settings = get_settings()

    def generate(self, prompt: str, context: dict[str, Any]) -> str:
        if not self._settings.llm_base_url:
            raise RuntimeError("LLM base URL is not configured")

        social = is_social_message(context.get('player_input', ''))
        recent = context.get('recent_dialogue', [])
        payload = {
            "model": self._settings.llm_model,
            "messages": [
                {"role": "system", "content": prompt},
                *(social_history(recent) if social else recent),
                {"role": "user", "content": context.get("player_input", "")},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        if context.get('facts') and self._settings.llm_structured_output:
            # Decoder constraints improve shape, never replace server validation
            # or prove that a selected fact answers the player's question.
            payload['response_format'] = {
                'type': 'json_schema',
                'json_schema': {'name': 'village_reply', 'strict': True, 'schema': {
                    'type': 'object', 'additionalProperties': False,
                    'properties': {
                        'answer_kind': {'type': 'string', 'enum': ['chat'] if social else ['answer', 'clarify', 'chat']},
                        'fact_ids': {'type': 'array', 'maxItems': 0 if social else 2, 'items': {
                            'type': 'string', 'enum': [fact['id'] for fact in context['facts']]}},
                        'dialogue': {'type': 'string', 'maxLength': 600 if context.get('npc_role')=='craftsman' and re.search(r'\b(?:story|explain|tell me more)\b',context.get('player_input',''),re.I) else 240},
                    },
                    'required': ['answer_kind', 'fact_ids', 'dialogue'],
                }},
            }
        headers = {"Authorization": f"Bearer {self._settings.llm_api_key}"} if self._settings.llm_api_key else {}
        with httpx.Client(timeout=httpx.Timeout(self._settings.llm_timeout_seconds, connect=5.0)) as client:
            response = client.post(f"{self._settings.llm_base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]
