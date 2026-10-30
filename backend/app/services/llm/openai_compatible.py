from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config.settings import get_settings
from app.services.llm.provider import LLMProvider
from app.services.semantic_routing import AcceptedInterpretation


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self) -> None:
        self._settings = get_settings()

    def generate(self, prompt: str, context: dict[str, Any]) -> str:
        if not self._settings.llm_base_url:
            raise RuntimeError("LLM base URL is not configured")

        if context.get('mode') == 'interpret':
            payload = {
                'model': self._settings.llm_model,
                'messages': [{'role': 'system', 'content': prompt},
                             {'role': 'user', 'content': context.get('player_input', '')}],
                'temperature': 0,
                'response_format': {'type': 'json_schema', 'json_schema': {
                    'name': 'chat_interpretation_v1', 'strict': True,
                    'schema': AcceptedInterpretation.json_schema(
                        facts=context.get('facts', []), capabilities=context.get('capabilities', []),
                        pending_question=context.get('pending_question'))}},
            }
            return self._post(payload)
        interpretation = context.get('accepted_interpretation') or {}
        concern_kinds = {c.get('kind') for c in interpretation.get('concerns', [])}
        social = 'social' in concern_kinds or concern_kinds == {'player_report'}
        recent = context.get('recent_dialogue', [])
        payload = {
            "model": self._settings.llm_model,
            "messages": [
                {"role": "system", "content": prompt},
                *recent,
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
        return self._post(payload)

    def _post(self, payload):
        headers = {"Authorization": f"Bearer {self._settings.llm_api_key}"} if self._settings.llm_api_key else {}
        with httpx.Client(timeout=httpx.Timeout(self._settings.llm_timeout_seconds, connect=5.0)) as client:
            response = client.post(f"{self._settings.llm_base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]
