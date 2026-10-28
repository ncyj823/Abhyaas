"""Tests for persona loading and schema validation."""

import pytest

from app.personas import (
    HiddenFacts,
    Persona,
    HIDDEN_FACT_KEYS,
    load_personas,
    get_persona_by_id,
    get_public_personas,
)


class TestPersonaSchema:
    """Test that all persona files load and pass validation."""

    def test_load_all_personas(self):
        personas = load_personas()
        assert len(personas) == 6, f"Expected 6 personas, got {len(personas)}"

    def test_all_have_required_fields(self):
        for p in load_personas():
            assert p.id, f"Missing id in persona"
            assert p.name, f"Missing name in {p.id}"
            assert p.business, f"Missing business in {p.id}"
            assert p.language_style, f"Missing language_style in {p.id}"
            assert p.speech_lang in ("te-IN", "hi-IN", "en-IN"), f"Bad speech_lang in {p.id}"
            assert p.script in ("latin", "telugu", "devanagari"), f"Bad script in {p.id}"
            assert p.temperament, f"Missing temperament in {p.id}"
            assert p.true_intent in ("HOT", "WARM", "COLD"), f"Bad true_intent in {p.id}"
            assert p.opening_line, f"Missing opening_line in {p.id}"

    def test_hidden_facts_all_keys(self):
        for p in load_personas():
            hf = p.hidden_facts
            for key in HIDDEN_FACT_KEYS:
                val = getattr(hf, key)
                assert val and len(val) > 5, (
                    f"Persona {p.id}: hidden_facts.{key} too short or empty: '{val}'"
                )

    def test_indirect_phrases_minimum(self):
        for p in load_personas():
            assert len(p.indirect_phrases) >= 3, (
                f"Persona {p.id}: needs at least 3 indirect_phrases, has {len(p.indirect_phrases)}"
            )

    def test_language_coverage(self):
        personas = load_personas()
        speech_langs = {p.speech_lang for p in personas}
        assert "te-IN" in speech_langs, "Missing Telugu persona"
        assert "hi-IN" in speech_langs, "Missing Hindi persona"
        assert "en-IN" in speech_langs, "Missing English persona"

    def test_intent_coverage(self):
        personas = load_personas()
        intents = {p.true_intent for p in personas}
        assert intents == {"HOT", "WARM", "COLD"}, f"Missing intents, got: {intents}"

    def test_script_matches_speech_lang(self):
        """Telugu personas use telugu script, Hindi use devanagari, English use latin."""
        for p in load_personas():
            if p.speech_lang == "te-IN":
                assert p.script == "telugu", f"{p.id}: te-IN should use telugu script"
            elif p.speech_lang == "hi-IN":
                assert p.script == "devanagari", f"{p.id}: hi-IN should use devanagari script"
            elif p.speech_lang == "en-IN":
                assert p.script == "latin", f"{p.id}: en-IN should use latin script"

    def test_unique_ids(self):
        personas = load_personas()
        ids = [p.id for p in personas]
        assert len(ids) == len(set(ids)), f"Duplicate persona ids: {ids}"


class TestPublicPersonas:
    """Test that public API strips hidden info."""

    def test_no_hidden_facts(self):
        for d in get_public_personas():
            assert "hidden_facts" not in d, f"hidden_facts leaked for {d['id']}"

    def test_no_true_intent(self):
        for d in get_public_personas():
            assert "true_intent" not in d, f"true_intent leaked for {d['id']}"

    def test_no_indirect_phrases(self):
        for d in get_public_personas():
            assert "indirect_phrases" not in d, f"indirect_phrases leaked for {d['id']}"

    def test_has_public_fields(self):
        for d in get_public_personas():
            assert "id" in d
            assert "name" in d
            assert "business" in d
            assert "opening_line" in d
            assert "speech_lang" in d


class TestGetPersonaById:
    def test_valid_id(self):
        personas = load_personas()
        p = get_persona_by_id(personas[0].id)
        assert p.id == personas[0].id

    def test_invalid_id(self):
        with pytest.raises(KeyError):
            get_persona_by_id("nonexistent_persona_xyz")


class TestInvalidPersonaSchema:
    """Test that bad data is rejected by pydantic."""

    def test_bad_speech_lang(self):
        with pytest.raises(Exception):
            Persona(
                id="bad", name="Bad", business="x", language_style="x",
                speech_lang="fr-FR", temperament="x", true_intent="HOT",
                opening_line="hi", script="latin",
                hidden_facts=HiddenFacts(
                    budget="x", timeline="x", products_count="x",
                    features="x", decision_maker="x", barrier="x"
                ),
                indirect_phrases=["a", "b", "c"],
            )

    def test_bad_intent(self):
        with pytest.raises(Exception):
            Persona(
                id="bad", name="Bad", business="x", language_style="x",
                speech_lang="en-IN", temperament="x", true_intent="MAYBE",
                opening_line="hi", script="latin",
                hidden_facts=HiddenFacts(
                    budget="x", timeline="x", products_count="x",
                    features="x", decision_maker="x", barrier="x"
                ),
                indirect_phrases=["a", "b", "c"],
            )

    def test_too_few_indirect_phrases(self):
        with pytest.raises(Exception):
            Persona(
                id="bad", name="Bad", business="x", language_style="x",
                speech_lang="en-IN", temperament="x", true_intent="HOT",
                opening_line="hi", script="latin",
                hidden_facts=HiddenFacts(
                    budget="x", timeline="x", products_count="x",
                    features="x", decision_maker="x", barrier="x"
                ),
                indirect_phrases=["a", "b"],
            )
