"""Tests for deterministic scoring logic."""

import pytest

from app.personas import load_personas
from app.scoring import score_discovery, score_intent_read
from app.sessions import Session, create_session, clear_all_sessions


@pytest.fixture(autouse=True)
def cleanup_sessions():
    yield
    clear_all_sessions()


class TestScoreDiscovery:
    """Test the 40-point discovery score."""

    def test_no_facts_revealed(self):
        persona = load_personas()[0]
        session = create_session(persona)
        assert score_discovery(session) == 0

    def test_all_facts_revealed(self):
        persona = load_personas()[0]
        session = create_session(persona)
        session.revealed_facts = {"budget", "timeline", "products_count",
                                   "features", "decision_maker", "barrier"}
        assert score_discovery(session) == 40

    def test_half_facts_revealed(self):
        persona = load_personas()[0]
        session = create_session(persona)
        session.revealed_facts = {"budget", "timeline", "features"}
        # 3/6 = 0.5 => round(40 * 0.5) = 20
        assert score_discovery(session) == 20

    def test_one_fact_revealed(self):
        persona = load_personas()[0]
        session = create_session(persona)
        session.revealed_facts = {"budget"}
        # 1/6 => round(40 * 0.1667) = round(6.67) = 7
        assert score_discovery(session) == 7

    def test_deterministic(self):
        """Same facts always give same score."""
        persona = load_personas()[0]
        s1 = create_session(persona)
        s2 = create_session(persona)
        s1.revealed_facts = {"budget", "barrier"}
        s2.revealed_facts = {"budget", "barrier"}
        assert score_discovery(s1) == score_discovery(s2)


class TestScoreIntentRead:
    """Test the 25-point intent guess score."""

    def test_exact_match(self):
        assert score_intent_read("HOT", "HOT") == 25
        assert score_intent_read("WARM", "WARM") == 25
        assert score_intent_read("COLD", "COLD") == 25

    def test_case_insensitive(self):
        assert score_intent_read("hot", "HOT") == 25
        assert score_intent_read("Hot", "HOT") == 25

    def test_adjacent_hot_warm(self):
        assert score_intent_read("HOT", "WARM") == 10
        assert score_intent_read("WARM", "HOT") == 10

    def test_adjacent_warm_cold(self):
        assert score_intent_read("WARM", "COLD") == 10
        assert score_intent_read("COLD", "WARM") == 10

    def test_opposite_hot_cold(self):
        assert score_intent_read("HOT", "COLD") == 0
        assert score_intent_read("COLD", "HOT") == 0

    def test_deterministic(self):
        """Same inputs always give same score."""
        for _ in range(10):
            assert score_intent_read("WARM", "HOT") == 10


class TestScoreDeterminism:
    """Verify that the same transcript always yields the same deterministic scores."""

    def test_same_session_same_scores(self):
        persona = load_personas()[0]
        results = []
        for _ in range(5):
            session = create_session(persona)
            session.revealed_facts = {"budget", "timeline"}
            session.conversation = [
                {"role": "user", "content": "What's your budget?"},
                {"role": "assistant", "content": "Around 45k"},
                {"role": "user", "content": "When do you need it?"},
                {"role": "assistant", "content": "Within 2 weeks"},
            ]
            disc = score_discovery(session)
            intent = score_intent_read("HOT", persona.true_intent)
            results.append((disc, intent))

        # All results should be identical
        assert all(r == results[0] for r in results)
