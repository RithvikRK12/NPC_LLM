from __future__ import annotations

import json
from typing import Any

import httpx

from app.config.settings import get_settings
from app.services.llm.provider import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self) -> None:
        self._settings = get_settings()

    def generate(self, prompt: str, context: dict[str, Any]) -> str:
        if not self._settings.llm_base_url:
            raise RuntimeError("LLM base URL is not configured")

        payload = {
            "model": self._settings.llm_model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(context, ensure_ascii=True)},
            ],
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {self._settings.llm_api_key}"} if self._settings.llm_api_key else {}
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{self._settings.llm_base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]