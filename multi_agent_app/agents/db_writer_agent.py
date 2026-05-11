"""DB Writer Agent – proposes SQL write operations for human approval."""

from __future__ import annotations

import os

from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from multi_agent_app.core.state import AgentState
from multi_agent_app.core.utils import extract_text
from multi_agent_app.prompts.agent_prompts import DB_WRITER_AGENT_PROMPT
from multi_agent_app.tools.db_tools import execute_sql


def db_writer_agent_node(state: AgentState) -> dict:
    """Draft an SQL write statement and store it for human approval."""
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )

    messages = [SystemMessage(content=DB_WRITER_AGENT_PROMPT)] + state["messages"][-5:]

    context = state.get("context", {})
    if context:
        ctx_parts = [f"[{k}]: {str(v)[:500]}" for k, v in context.items()]
        from langchain_core.messages import HumanMessage

        messages.append(
            HumanMessage(content="Context:\n" + "\n".join(ctx_parts))
        )

    response = llm.invoke(messages)
    proposed_sql = extract_text(response.content)

    return {
        "messages": [
            AIMessage(
                content=f"[DB Writer Agent] Đề xuất SQL:\n{proposed_sql}"
            )
        ],
        "proposed_action": proposed_sql,
    }


def execute_approved_action(state: AgentState) -> dict:
    """Execute the proposed SQL after human approval."""
    proposed = state.get("proposed_action")
    approved = state.get("human_approved", False)

    if not approved or not proposed:
        return {
            "messages": [
                AIMessage(
                    content="[DB Writer Agent]: Hành động đã bị từ chối hoặc không có SQL để thực thi."
                )
            ],
            "proposed_action": None,
            "human_approved": None,
        }

    sql_lines = proposed.strip().split("\n")
    sql_statement = ""
    for line in sql_lines:
        stripped = line.strip()
        if stripped.upper().startswith(("INSERT", "UPDATE", "DELETE")):
            sql_statement = stripped
            break
    if not sql_statement:
        for line in sql_lines:
            stripped = line.strip()
            if stripped.endswith(";"):
                sql_statement = stripped
                break

    if not sql_statement:
        sql_statement = proposed.strip()

    result = execute_sql.invoke({"sql": sql_statement})

    context = dict(state.get("context", {}))
    context["db_writer_agent"] = result

    return {
        "messages": [
            AIMessage(content=f"[DB Writer Agent] Kết quả: {result}")
        ],
        "proposed_action": None,
        "human_approved": None,
        "context": context,
    }
