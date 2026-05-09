"""Supervisor node – routes requests to the appropriate worker agent."""

from __future__ import annotations

import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from multi_agent_app.core.state import AgentState
from multi_agent_app.prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT

VALID_ROUTES = {
    "rag_agent",
    "db_reader_agent",
    "db_writer_agent",
    "web_agent",
    "final_agent",
    "FINISH",
}

MAX_ITERATIONS = 10


def supervisor_node(state: AgentState) -> dict:
    """Decide which agent to invoke next based on conversation state."""
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )

    iteration = state.get("iteration_count", 0)
    if iteration >= MAX_ITERATIONS:
        return {"next_agent": "final_agent", "iteration_count": iteration}

    context = state.get("context", {})
    context_summary = ""
    if context:
        parts = []
        for agent_name, data in context.items():
            parts.append(f"[{agent_name}]: {str(data)[:500]}")
        context_summary = "\n\nContext thu thập được:\n" + "\n".join(parts)

    conversation = state.get("messages", [])
    last_messages = conversation[-5:] if len(conversation) > 5 else conversation

    routing_input = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        *last_messages,
    ]
    if context_summary:
        routing_input.append(
            HumanMessage(content=f"Thông tin đã thu thập:{context_summary}")
        )

    response = llm.invoke(routing_input)
    decision = response.content.strip().lower().replace("`", "").replace("*", "")

    matched = None
    for route in VALID_ROUTES:
        if route in decision:
            matched = route
            break

    if matched is None:
        matched = "final_agent"

    return {"next_agent": matched, "iteration_count": iteration + 1}
