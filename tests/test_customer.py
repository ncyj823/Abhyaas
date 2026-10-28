"""Tests for customer reveal logic with mocked LLM."""

import pytest

from app.customer import build_system_prompt, process_turn, validate_revealed_facts
from app.personas import HIDDEN_FACT_KEYS, load_personas


class TestValidateRevealedFacts:
    """Test that only valid schema keys are accepted."""

    def test_valid_keys(self):
        result = validate_revealed_facts(["budget", "timeline"])
        assert result == {"budget", "timeline"}

    def test_invalid_keys_filtered(self):
        result = validate_revealed_facts(["budget", "nonsense", "alien_fact"])
        assert result == {"budget"}

    def test_empty_list(self):
        result = validate_revealed_facts([])
        assert result == set()

    def test_all_valid_keys(self):
        result = validate_revealed_facts(list(HIDDEN_FACT_KEYS))
        assert result == HIDDEN_FACT_KEYS


class TestProcessTurn:
    """Test process_turn with a mocked LLM."""

    def _mock_llm(self, reply: str, revealed: list[str]):
        """Create a mock LLM callable that returns a fixed response."""
        def mock_chat_json(system: str, messages: list) -> dict:
            return {"reply": reply, "revealed_facts": revealed}
        return mock_chat_json

    def test_basic_turn(self):
        persona = load_personas()[0]
        conversation = [{"role": "user", "content": "Tell me about your budget"}]
        revealed_so_far: set[str] = set()

        reply, newly_revealed = process_turn(
            persona=persona,
            conversation=conversation,
            revealed_so_far=revealed_so_far,
            llm_chat_json=self._mock_llm("Around 45k", ["budget"]),
        )

        assert reply == "Around 45k"
        assert "budget" in newly_revealed

    def test_no_double_reveal(self):
        """A fact already revealed should not be counted again."""
        persona = load_personas()[0]
        conversation = [{"role": "user", "content": "budget?"}]
        revealed_so_far = {"budget"}

        reply, newly_revealed = process_turn(
            persona=persona,
            conversation=conversation,
            revealed_so_far=revealed_so_far,
            llm_chat_json=self._mock_llm("I told you, 45k", ["budget"]),
        )

        assert reply == "I told you, 45k"
        assert "budget" not in newly_revealed
        assert len(newly_revealed) == 0

    def test_invalid_keys_in_response(self):
        """Invalid fact keys from LLM should be silently filtered."""
        persona = load_personas()[0]
        conversation = [{"role": "user", "content": "What do you do?"}]
        revealed_so_far: set[str] = set()

        reply, newly_revealed = process_turn(
            persona=persona,
            conversation=conversation,
            revealed_so_far=revealed_so_far,
            llm_chat_json=self._mock_llm("I make things", ["invalid_key", "timeline"]),
        )

        assert "invalid_key" not in newly_revealed
        assert "timeline" in newly_revealed

    def test_empty_reply_raises(self):
        """LLM returning empty reply should raise ValueError."""
        persona = load_personas()[0]
        conversation = [{"role": "user", "content": "hello"}]

        def bad_llm(system, messages):
            return {"reply": "", "revealed_facts": []}

        with pytest.raises(ValueError, match="empty reply"):
            process_turn(persona, conversation, set(), bad_llm)

    def test_multiple_facts_revealed(self):
        persona = load_personas()[0]
        conversation = [{"role": "user", "content": "Tell me everything"}]

        reply, newly_revealed = process_turn(
            persona=persona,
            conversation=conversation,
            revealed_so_far=set(),
            llm_chat_json=self._mock_llm(
                "OK here it is", ["budget", "timeline", "features"]
            ),
        )

        assert newly_revealed == {"budget", "timeline", "features"}

    def test_revealed_facts_not_list(self):
        """If LLM returns non-list for revealed_facts, treat as empty."""
        persona = load_personas()[0]
        conversation = [{"role": "user", "content": "hi"}]

        def bad_structure_llm(system, messages):
            return {"reply": "hello", "revealed_facts": "budget"}

        reply, newly_revealed = process_turn(
            persona, conversation, set(), bad_structure_llm
        )

        assert reply == "hello"
        assert len(newly_revealed) == 0


class TestSystemPrompt:
    """Test that the system prompt is well-formed."""

    def test_contains_persona_name(self):
        for p in load_personas():
            prompt = build_system_prompt(p)
            assert p.name in prompt

    def test_contains_hidden_facts(self):
        for p in load_personas():
            prompt = build_system_prompt(p)
            assert p.hidden_facts.budget in prompt
            assert p.hidden_facts.barrier in prompt

    def test_contains_json_format_instruction(self):
        for p in load_personas():
            prompt = build_system_prompt(p)
            assert "revealed_facts" in prompt
            assert "reply" in prompt

    def test_never_reveals_intent_label(self):
        """Prompt should tell persona not to say HOT/WARM/COLD directly."""
        for p in load_personas():
            prompt = build_system_prompt(p)
            assert "NEVER say" in prompt or "never say" in prompt.lower()
