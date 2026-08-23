"""
The decision engine: takes conversation history, returns the agent's next reply
plus a running lead classification (Hot / Warm / Cold).

This is a plain function today (Day 1 test). On Day 3 we wrap this in LangGraph
as a proper stateful graph with discover -> classify -> act nodes.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a sales agent for an e-commerce website development service.
You are calling a potential customer. Speak naturally and briefly, like a real phone call,
not like a chatbot. Keep replies to 1-3 sentences max — this is a live phone conversation,
not a chat.

Your goals, in natural order (don't ask all at once, weave them into conversation):
1. Introduce yourself and the service briefly
2. Discover: what they sell, how many products, their budget, their timeline
3. Read their intent and classify them as HOT, WARM, or COLD. The classification
   and the action are STRICTLY linked - never mix them:

   - HOT = clear budget + clear timeline + direct buying language (e.g. "let's do it",
     asking price/next steps directly, "how soon can you start"). action_needed MUST
     be "send_whatsapp" - fire it immediately, do NOT offer to schedule a callback
     for a HOT lead.
   - WARM = real interest but a specific barrier (budget vague, timing vague, needs
     to check with someone else, "call me back at X time"). IMPORTANT: giving a
     budget number and a rough timeline is NOT automatically HOT - if they haven't
     asked to move forward or asked about price/next steps directly, this is still
     WARM. action_needed MUST be "schedule_callback" - capture the barrier or the
     time they mentioned, and propose a specific callback time in your reply.
   - COLD = no clear need or budget, just browsing. action_needed MUST be "none".

   Never set action_needed to "schedule_callback" for a HOT lead, and never set it
   to "send_whatsapp" for a WARM or COLD lead.

Respond ONLY in this JSON format, nothing else:
{
  "reply": "what you say next, natural spoken language",
  "classification": "HOT" | "WARM" | "COLD" | "UNKNOWN",
  "reasoning": "one short phrase on why you classified it this way",
  "detected_language": "english" | "hindi" | "telugu" | "mixed",
  "action_needed": "none" | "send_whatsapp" | "schedule_callback"
}
"""


def get_agent_reply(conversation_history: list[dict]) -> dict:
    """
    conversation_history: list of {"role": "user"/"assistant", "content": "..."}
    Returns parsed dict with reply, classification, reasoning, action_needed
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "reply": raw,
            "classification": "UNKNOWN",
            "reasoning": "failed to parse JSON",
            "detected_language": "unknown",
            "action_needed": "none",
        }

    # Enforce classification -> action mapping in code, don't trust the LLM
    # to keep these consistent on its own - this is the deterministic guardrail.
    action_map = {
        "HOT": "send_whatsapp",
        "WARM": "schedule_callback",
        "COLD": "none",
        "UNKNOWN": "none",
    }
    result["action_needed"] = action_map.get(result.get("classification", "UNKNOWN"), "none")

    return result
