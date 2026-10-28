"""Persona loading and validation."""

import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator


PERSONAS_DIR = Path(__file__).parent / "data" / "personas"

HIDDEN_FACT_KEYS = frozenset(
    ["budget", "timeline", "products_count", "features", "decision_maker", "barrier"]
)


class HiddenFacts(BaseModel):
    budget: str
    timeline: str
    products_count: str
    features: str
    decision_maker: str
    barrier: str


class Persona(BaseModel):
    id: str
    name: str
    business: str
    language_style: str
    speech_lang: str = Field(..., pattern=r"^(te-IN|hi-IN|en-IN)$")
    temperament: str
    true_intent: str = Field(..., pattern=r"^(HOT|WARM|COLD)$")
    opening_line: str
    script: str = Field(..., pattern=r"^(latin|telugu|devanagari)$")
    hidden_facts: HiddenFacts
    indirect_phrases: List[str]

    @field_validator("language_style")
    @classmethod
    def style_must_be_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("language_style cannot be empty")
        return v

    @field_validator("indirect_phrases")
    @classmethod
    def at_least_three_phrases(cls, v: List[str]) -> List[str]:
        if len(v) < 3:
            raise ValueError("Need at least 3 indirect_phrases")
        return v


def load_personas() -> List[Persona]:
    """Load all persona JSON files from the data directory."""
    personas: List[Persona] = []
    for path in sorted(PERSONAS_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        personas.append(Persona(**data))
    return personas


def get_public_personas() -> List[Dict[str, Any]]:
    """Return persona dicts without hidden_facts or true_intent."""
    result: List[Dict[str, Any]] = []
    for p in load_personas():
        d = p.model_dump()
        d.pop("hidden_facts", None)
        d.pop("true_intent", None)
        d.pop("indirect_phrases", None)
        result.append(d)
    return result


def get_persona_by_id(persona_id: str) -> Persona:
    """Look up a single persona by id. Raises KeyError if missing."""
    for p in load_personas():
        if p.id == persona_id:
            return p
    raise KeyError(f"Persona '{persona_id}' not found")
