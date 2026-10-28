"""Customer AI: builds the system prompt and processes each turn."""

from typing import Any, Callable, Dict, List, Set

from app.personas import HiddenFacts, Persona, HIDDEN_FACT_KEYS


def build_system_prompt(persona: Persona) -> str:
    """Build the LLM system prompt for playing this customer."""
    hf = persona.hidden_facts
    facts_block = (
        f"  budget: {hf.budget}\n"
        f"  timeline: {hf.timeline}\n"
        f"  products_count: {hf.products_count}\n"
        f"  features: {hf.features}\n"
        f"  decision_maker: {hf.decision_maker}\n"
        f"  barrier: {hf.barrier}"
    )
    phrases_block = "\n".join(f"  - \"{p}\"" for p in persona.indirect_phrases)

    script_rule = {
        "telugu": (
            "Write your reply in Telugu script (Unicode). "
            "Keep English brand names and product words in Latin script. "
            "Example: 'నేను candle supplier కోసం చూస్తున్నాను.'"
        ),
        "devanagari": (
            "Write your reply in Devanagari script (Unicode). "
            "Keep English brand names and product words in Latin script. "
            "Example: 'मुझे spare parts का supplier चाहिए।'"
        ),
        "latin": (
            "Write your reply in English using Latin script."
        ),
    }[persona.script]

    return f"""You are {persona.name}, a real customer who runs a {persona.business}.

PERSONALITY
- Language style: {persona.language_style}
- Temperament: {persona.temperament}
- You NEVER break character. You NEVER reveal that you are an AI.
- You speak in 1-2 SHORT sentences maximum per reply.

SCRIPT RULE
{script_rule}

YOUR HIDDEN FACTS (only reveal when the sales rep asks directly or naturally nearby):
{facts_block}

Your true buying intent is {persona.true_intent}, but you NEVER say "I am HOT/WARM/COLD".
Instead you express it indirectly through phrases like:
{phrases_block}

REVEAL RULES
- Only reveal a fact when the rep asks about it directly or gets naturally close to the topic.
- If the rep hasn't asked about a fact, be vague or deflect using your indirect phrases.
- You can hint at things using your indirect phrases, but never volunteer full details unprompted.

RESPONSE FORMAT — you MUST reply with valid JSON only, no other text:
{{
  "reply": "your in-character reply here",
  "revealed_facts": ["budget", "timeline"]
}}

The "revealed_facts" array must contain ONLY keys from this set: {sorted(HIDDEN_FACT_KEYS)}.
Include a key only if THIS reply meaningfully reveals that fact (not if it was revealed before).
If nothing new is revealed, use an empty array: [].
"""


def validate_revealed_facts(raw_keys: List[str]) -> Set[str]:
    """Filter revealed_facts to only valid schema keys."""
    return {k for k in raw_keys if k in HIDDEN_FACT_KEYS}


def process_turn(
    persona: Persona,
    conversation: List[Dict[str, str]],
    revealed_so_far: Set[str],
    llm_chat_json: Callable[..., Dict[str, Any]],
) -> tuple[str, Set[str]]:
    """Process one conversation turn.

    Args:
        persona: The customer persona.
        conversation: List of {"role": "user"/"assistant", "content": ...} messages.
        revealed_so_far: Set of fact keys revealed in previous turns.
        llm_chat_json: Callable that takes (system, messages) and returns parsed JSON dict.

    Returns:
        (reply_text, newly_revealed_keys)
    """
    system = build_system_prompt(persona)
    result = llm_chat_json(system, conversation)

    reply = result.get("reply", "")
    if not reply:
        raise ValueError("LLM returned empty reply")

    raw_revealed = result.get("revealed_facts", [])
    if not isinstance(raw_revealed, list):
        raw_revealed = []

    newly_revealed = validate_revealed_facts(raw_revealed) - revealed_so_far
    return reply, newly_revealed
