"""Deterministic backstop for modern technology outside the village setting.

This is a curated vocabulary, not a general semantic topic classifier. The prompt
also restricts knowledge to the world; extend this policy as the setting grows.
"""
import re
import unicodedata

from app.services.validation.models import LLMResponse, StateUpdate


_MODERN_TECH = re.compile(
    r"\b(?:a[.\s]?i|a[.\s]?w[.\s]?s|artificial intelligence|amazon web services|"
    r"machine learning|deep learning|neural networks?|large language models?|llms?|"
    r"chatgpt|openai|cloud computing|cloud services?|ec2|s3|azure|"
    r"computers?|software|programming|internet|websites?|smartphones?|"
    r"blockchain|cryptocurrency|kubernetes|docker)\b",
    re.IGNORECASE,
)


def outside_world(text: str) -> bool:
    return bool(_MODERN_TECH.search(unicodedata.normalize("NFKC", text)))


def unfamiliar_topic_response(role: str) -> LLMResponse:
    expertise = "tools, wood, and crafting" if role == "craftsman" else "the forest and gathering wood"
    return LLMResponse(
        intent="clarify", emotion="neutral",
        dialogue=f"I don't know about such things. My knowledge is of {expertise}. What would you like to know about those?",
        action="speak", reasoning="Topic is outside this NPC's knowledge of the village.",
        state_update=StateUpdate(),
    )
