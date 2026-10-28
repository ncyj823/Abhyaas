"""Scorecard computation. Deterministic parts computed in code, not by LLM."""

from typing import Any, Callable, Dict, List, Set

from app.personas import HIDDEN_FACT_KEYS, Persona
from app.sessions import Session


def score_discovery(session: Session) -> int:
    """40 points: revealed facts / total facts."""
    return round(40 * session.discovery_ratio)


def score_intent_read(rep_guess: str, true_intent: str) -> int:
    """25 points: exact match = 25, adjacent = 10, wrong = 0."""
    rep_guess = rep_guess.upper().strip()
    true_intent = true_intent.upper().strip()
    if rep_guess == true_intent:
        return 25
    # Adjacent: HOT<->WARM or WARM<->COLD
    adjacent = {
        ("HOT", "WARM"), ("WARM", "HOT"),
        ("WARM", "COLD"), ("COLD", "WARM"),
    }
    if (rep_guess, true_intent) in adjacent:
        return 10
    return 0


def score_next_step(session: Session, llm_chat_json: Callable[..., Dict[str, Any]]) -> int:
    """15 points: LLM judges if rep proposed a concrete next step.

    Returns 0-15.
    """
    if not session.conversation:
        return 0

    transcript = _format_transcript(session.conversation)
    system = (
        "You are a sales coach evaluating whether the sales rep proposed a concrete next step "
        "at the end of the call. A concrete next step means a specific time, date, action, or "
        "follow-up that matches the customer's situation.\n\n"
        "Score from 0 to 15:\n"
        "- 15: Specific time/date for callback, demo, or delivery proposed\n"
        "- 10: General follow-up mentioned but no specific time\n"
        "- 5: Vague closing like 'I'll send details'\n"
        "- 0: No next step proposed or call just ended abruptly\n\n"
        "Reply with ONLY valid JSON: {\"score\": <number>, \"reason\": \"<short reason>\"}"
    )
    messages = [{"role": "user", "content": f"Transcript:\n{transcript}"}]

    try:
        result = llm_chat_json(system, messages)
        raw = result.get("score", 0)
        return max(0, min(15, int(raw)))
    except Exception:
        return 0


def score_natural_questioning(
    session: Session,
    llm_chat_json: Callable[..., Dict[str, Any]],
) -> int:
    """20 points: LLM judges how natural and skilled the questioning was.

    Returns 0-20. Retries once on failure.
    """
    if not session.conversation:
        return 0

    transcript = _format_transcript(session.conversation)
    system = (
        "You are a sales coach evaluating the quality of a sales rep's questioning technique.\n\n"
        "Score from 0 to 20:\n"
        "- 18-20: Excellent — open-ended questions, active listening, natural flow\n"
        "- 12-17: Good — mostly natural, some missed opportunities\n"
        "- 6-11: Average — formulaic or pushy questions\n"
        "- 0-5: Poor — interrogation style, no rapport building\n\n"
        "Reply with ONLY valid JSON: {\"score\": <number>, \"reason\": \"<short reason>\"}"
    )
    messages = [{"role": "user", "content": f"Transcript:\n{transcript}"}]

    for attempt in range(2):
        try:
            result = llm_chat_json(system, messages)
            raw = result.get("score", 0)
            return max(0, min(20, int(raw)))
        except Exception:
            if attempt == 0:
                continue
            return 0
    return 0


def generate_feedback(
    session: Session,
    llm_chat_json: Callable[..., Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate missed moments and strengths from the transcript."""
    if not session.conversation:
        return {"missed_moments": [], "strengths": []}

    transcript = _format_transcript(session.conversation)
    hidden_facts_desc = session.persona.hidden_facts.model_dump()

    system = (
        "You are a sales coach reviewing a practice call transcript.\n"
        "The customer had these hidden facts:\n"
        f"{hidden_facts_desc}\n\n"
        "Identify:\n"
        "1. 2-3 'missed moments': places where the rep could have uncovered a hidden fact "
        "or built better rapport. For each, give:\n"
        "   - rep_or_customer_quote: the actual quote from the transcript\n"
        "   - what_was_missed: what fact or opportunity was missed\n"
        "   - better_line: what the rep could have said instead\n\n"
        "2. 1-2 'strengths': things the rep did well.\n\n"
        "Reply with ONLY valid JSON:\n"
        "{\n"
        '  "missed_moments": [{\"rep_or_customer_quote\": "...", \"what_was_missed\": "...", \"better_line\": "..."}],\n'
        '  "strengths": ["..."]\n'
        "}"
    )
    messages = [{"role": "user", "content": f"Transcript:\n{transcript}"}]

    try:
        return llm_chat_json(system, messages)
    except Exception:
        return {"missed_moments": [], "strengths": []}


def build_scorecard(
    session: Session,
    rep_guess: str,
    llm_chat_json: Callable[..., Dict[str, Any]],
) -> Dict[str, Any]:
    """Build the full scorecard. Deterministic parts computed in code."""
    discovery = score_discovery(session)
    intent = score_intent_read(rep_guess, session.persona.true_intent)
    natural = score_natural_questioning(session, llm_chat_json)
    next_step = score_next_step(session, llm_chat_json)
    feedback = generate_feedback(session, llm_chat_json)

    total = discovery + intent + natural + next_step

    return {
        "total": total,
        "breakdown": {
            "discovery_coverage": {"score": discovery, "max": 40,
                                    "revealed": sorted(session.revealed_facts),
                                    "total_facts": session.total_facts},
            "intent_read": {"score": intent, "max": 25,
                            "rep_guess": rep_guess.upper(),
                            "true_intent": session.persona.true_intent},
            "natural_questioning": {"score": natural, "max": 20},
            "next_step": {"score": next_step, "max": 15},
        },
        "missed_moments": feedback.get("missed_moments", []),
        "strengths": feedback.get("strengths", []),
        "persona": {
            "name": session.persona.name,
            "business": session.persona.business,
            "true_intent": session.persona.true_intent,
            "hidden_facts": session.persona.hidden_facts.model_dump(),
        },
    }


def _format_transcript(conversation: List[Dict[str, str]]) -> str:
    """Format conversation into a readable transcript."""
    lines = []
    for msg in conversation:
        role = "Rep" if msg["role"] == "user" else "Customer"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)
