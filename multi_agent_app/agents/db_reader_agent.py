"""DB Reader Agent – reads data from database (SELECT only)."""

from __future__ import annotations

import os

from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from multi_agent_app.core.state import AgentState
from multi_agent_app.core.utils import extract_text
from multi_agent_app.prompts.agent_prompts import DB_READER_AGENT_PROMPT
from multi_agent_app.tools.db_tools import get_db_tools


def db_reader_agent_node(state: AgentState) -> dict:
    """Query the database and return results."""
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )
    tools = get_db_tools()
    llm_with_tools = llm.bind_tools(tools)

    messages = [SystemMessage(content=DB_READER_AGENT_PROMPT)] + state["messages"][-5:]
    response = llm_with_tools.invoke(messages)

    tool_results = []
    tool_map = {t.name: t for t in tools}
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            tool_fn = tool_map.get(tc["name"])
            if tool_fn:
                result = tool_fn.invoke(tc["args"])
                tool_results.append(f"[{tc['name']}]: {result}")

    if tool_results:
        output = "\n".join(tool_results)
    else:
        output = extract_text(response.content) or "Không thể truy vấn dữ liệu."

    context = dict(state.get("context", {}))
    context["db_reader_agent"] = output

    return {
        "messages": [AIMessage(content=f"[DB Reader Agent]: {output}")],
        "context": context,
    }
