"""Final Agent – synthesises all collected context into a user-facing answer."""

from __future__ import annotations

import os

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from multi_agent_app.core.state import AgentState
from multi_agent_app.prompts.agent_prompts import FINAL_AGENT_PROMPT


def final_agent_node(state: AgentState) -> dict:
    """Produce a comprehensive answer from all agent contexts."""
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.5,
    )

    context = state.get("context", {})
    context_text = ""
    if context:
        parts = []
        for agent_name, data in context.items():
            parts.append(f"## {agent_name}\n{data}")
        context_text = "\n\n".join(parts)
    else:
        context_text = "Không có context từ các Agent khác."

    user_messages = [
        m for m in state.get("messages", []) if isinstance(m, HumanMessage)
    ]
    original_question = (
        user_messages[0].content if user_messages else "Không có câu hỏi."
    )

    messages = [
        SystemMessage(content=FINAL_AGENT_PROMPT),
        HumanMessage(
            content=(
                f"Câu hỏi gốc: {original_question}\n\n"
                f"Context thu thập:\n{context_text}"
            )
        ),
    ]

    response = llm.invoke(messages)
    output = response.content or "Không thể tổng hợp câu trả lời."

    return {
        "messages": [AIMessage(content=output)],
        "next_agent": "FINISH",
    }
