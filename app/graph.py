"""
Day 3: wraps brain.py's logic into a proper LangGraph state machine.

Why this matters for Day 4: right now action_needed just gets printed.
Once we build real FastMCP tools (WhatsApp send, scheduler), they slot in
as the whatsapp_node and schedule_node below - no restructuring needed,
just swap the placeholder body for a real async tool call.

Graph shape (per turn, called once per conversation turn):

    agent_node (calls Groq, classifies, decides action)
         |
    route_action (conditional edge)
       /    |    \\
  whatsapp schedule  END
   node     node
      \\    /
       END
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from app.brain import get_agent_reply


class CallState(TypedDict):
    history: list[dict]          # full conversation so far
    reply: str                   # agent's latest reply text
    classification: str          # HOT / WARM / COLD / UNKNOWN
    reasoning: str
    detected_language: str
    action_needed: str           # none / send_whatsapp / schedule_callback
    action_taken: str            # what actually happened (filled by action nodes)


def agent_node(state: CallState) -> CallState:
    """Calls the brain (Groq) to get the next reply + classification."""
    result = get_agent_reply(state["history"])

    new_history = state["history"] + [{"role": "assistant", "content": result["reply"]}]

    return {
        **state,
        "history": new_history,
        "reply": result["reply"],
        "classification": result["classification"],
        "reasoning": result["reasoning"],
        "detected_language": result["detected_language"],
        "action_needed": result["action_needed"],
    }


def whatsapp_node(state: CallState) -> CallState:
    """
    Day 3 placeholder. Day 4 replaces this body with a real FastMCP tool
    call that sends WhatsApp via Twilio/WAPI, fired async so it doesn't
    block the live call.
    """
    print("  >>> [PLACEHOLDER] Would fire WhatsApp here with call context")
    return {**state, "action_taken": "whatsapp_sent_placeholder"}


def schedule_node(state: CallState) -> CallState:
    """
    Day 3 placeholder. Day 4 replaces this body with a real FastMCP tool
    call that parses the spoken time and books a callback.
    """
    print("  >>> [PLACEHOLDER] Would book callback here")
    return {**state, "action_taken": "callback_scheduled_placeholder"}


def route_action(state: CallState) -> Literal["whatsapp_node", "schedule_node", "__end__"]:
    """Conditional edge: decides which action node to visit, if any."""
    action = state["action_needed"]
    if action == "send_whatsapp":
        return "whatsapp_node"
    elif action == "schedule_callback":
        return "schedule_node"
    else:
        return "__end__"


def build_graph():
    graph = StateGraph(CallState)

    graph.add_node("agent_node", agent_node)
    graph.add_node("whatsapp_node", whatsapp_node)
    graph.add_node("schedule_node", schedule_node)

    graph.set_entry_point("agent_node")

    graph.add_conditional_edges(
        "agent_node",
        route_action,
        {
            "whatsapp_node": "whatsapp_node",
            "schedule_node": "schedule_node",
            "__end__": END,
        },
    )

    graph.add_edge("whatsapp_node", END)
    graph.add_edge("schedule_node", END)

    return graph.compile()


# Compiled once, reused across turns
call_graph = build_graph()


def run_turn(history: list[dict]) -> CallState:
    """
    Call this once per conversation turn. Pass the full history so far
    (including the user's latest message already appended), get back
    the updated state with the agent's reply and any action taken.
    """
    initial_state: CallState = {
        "history": history,
        "reply": "",
        "classification": "",
        "reasoning": "",
        "detected_language": "",
        "action_needed": "none",
        "action_taken": "",
    }
    return call_graph.invoke(initial_state)
