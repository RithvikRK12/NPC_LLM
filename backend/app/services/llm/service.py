from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import get_settings
from app.services.llm.mock import MockLLMProvider
from app.services.llm.openai_compatible import OpenAICompatibleProvider
from app.services.llm.provider import LLMProvider
from app.utils.json_utils import parse_strict_json
from app.services.semantic_routing import AcceptedInterpretation, InterpretationContext, interpretation_prompt


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

    def interpret(self, context: InterpretationContext) -> tuple[AcceptedInterpretation, float]:
        from time import monotonic
        started = monotonic()
        prompt = interpretation_prompt(context)
        provider_context = context.as_dict() | {'mode': 'interpret'}
        context.provider_calls += 1
        raw = self._provider.generate(prompt, provider_context)
        parsed = parse_strict_json(raw)
        try:
            value = AcceptedInterpretation.validate_for_context(parsed, context)
        except (ValueError, TypeError):
            # Repair exact offsets/schema noise locally; never call the model again
            # or change intent, targets, modality, capabilities, or fact choices.
            repaired = False
            if isinstance(parsed.get('concerns'), list):
                for concern in parsed['concerns']:
                    if not isinstance(concern, dict):
                        continue
                    evidence = concern.get('evidence')
                    if isinstance(evidence, str) and context.message.count(evidence) == 1:
                        start = context.message.index(evidence)
                        if concern.get('start') != start or concern.get('end') != start + len(evidence):
                            concern['start'], concern['end'] = start, start + len(evidence)
                            repaired = True
                    if concern.get('kind') in {'social', 'cancellation'} and concern.get('target') is not None:
                        concern['target'] = None; repaired = True
                    if concern.get('kind') != 'pending_answer' and concern.get('answer_type') is not None:
                        concern['answer_type'] = None; repaired = True
                    if concern.get('kind') != 'operation_request' and concern.get('operation') is not None:
                        concern['operation'] = None; repaired = True
                    if concern.get('kind') != 'operation_request' and concern.get('purpose') is not None:
                        concern['purpose'] = None; repaired = True
            if not repaired:
                raise
            context.span_repairs += 1
            value = AcceptedInterpretation.validate_for_context(parsed, context)
        return value, monotonic() - started
