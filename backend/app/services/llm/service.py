from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import get_settings
from app.services.llm.mock import MockLLMProvider
from app.services.llm.openai_compatible import OpenAICompatibleProvider
from app.services.llm.provider import LLMProvider
from app.utils.json_utils import parse_strict_json


@dataclass(slots=True)
class GenerationResult:
    raw_text: str
    raw_json: dict


class LLMService:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        settings = get_settings()
        if provider is not None:
            self._provider = provider
        elif settings.llm_base_url:
            self._provider = OpenAICompatibleProvider()
        else:
            self._provider = MockLLMProvider()

    def generate(self, prompt: str, context: dict) -> GenerationResult:
        raw_text = self._provider.generate(prompt, context)
        raw_json = parse_strict_json(raw_text)
        return GenerationResult(raw_text=raw_text, raw_json=raw_json)