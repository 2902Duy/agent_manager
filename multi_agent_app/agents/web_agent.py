"""Web Agent – searches the internet for information."""

from __future__ import annotations

import os

from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from multi_agent_app.core.state import AgentState
from multi_agent_app.prompts.agent_prompts import WEB_AGENT_PROMPT
from multi_agent_app.tools.web_tools import get_web_tools


def web_agent_node(state: AgentState) -> dict:
    """Search the web and return summarised findings."""
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,
    )
    tools = get_web_tools()
    llm_with_tools = llm.bind_tools(tools)

    messages = [SystemMessage(content=WEB_AGENT_PROMPT)] + state["messages"][-5:]
    response = llm_with_tools.invoke(messages)

    tool_results = []
    tool_map = {t.name: t for t in tools}
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            tool_fn = tool_map.get(tc["name"])
            if tool_fn:
                result = tool_fn.invoke(tc["args"])
                tool_results.append(str(result))

    if tool_results:
        summary_prompt = (
            "Tóm tắt ngắn gọn kết quả tìm kiếm web sau:\n"
            + "\n".join(tool_results)
        )
        summary_response = llm.invoke(
            [SystemMessage(content=WEB_AGENT_PROMPT)]
            + [AIMessage(content=summary_prompt)]
        )
        output = summary_response.content
    else:
        output = response.content or "Không thể tìm kiếm thông tin trên web."

    context = dict(state.get("context", {}))
    context["web_agent"] = output

    return {
        "messages": [AIMessage(content=f"[Web Agent]: {output}")],
        "context": context,
    }
