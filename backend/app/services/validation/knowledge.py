"""Deterministic backstop for real-world technology outside the game setting.

This is a curated vocabulary, not a general semantic topic classifier. The prompt
also restricts knowledge to the world; extend this policy as the setting grows.
"""
import re
import unicodedata

from app.services.validation.models import LLMResponse, StateUpdate


_MODERN_TECH = re.compile(
    r"\b(?:a[.\s]?w[.\s]?s|amazon web services|"
    r"large language models?|llms?|chatgpt|openai|cloud computing|cloud services?|"
    r"ec2|s3|azure|websites?|smartphones?|blockchain|cryptocurrency|kubernetes|docker)\b",
    re.IGNORECASE,
)


def outside_world(text: str) -> bool:
    return bool(_MODERN_TECH.search(unicodedata.normalize("NFKC", text)))


def unfamiliar_topic_response(role: str) -> LLMResponse:
    expertise = "pulse hardware, neon coils, and bench assembly" if role == "craftsman" else "street intel, salvage routes, and circuit boards"
    return LLMResponse(
        intent="clarify", emotion="neutral",
        dialogue=f"I don't know about such things. My knowledge is of {expertise}. What would you like to know about those?",
        action="speak", reasoning="Topic is outside this NPC's knowledge of the JIT Cyber Grid.",
        state_update=StateUpdate(),
    )
