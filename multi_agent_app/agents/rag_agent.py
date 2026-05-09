"""RAG Agent – searches internal documents via vector store."""

from __future__ import annotations

import os

from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from multi_agent_app.core.state import AgentState
from multi_agent_app.prompts.agent_prompts import RAG_AGENT_PROMPT
from multi_agent_app.tools.rag_tools import get_rag_tools


def rag_agent_node(state: AgentState) -> dict:
    """Search internal documents and return summarised findings."""
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2,
    )
    llm_with_tools = llm.bind_tools(get_rag_tools())

    messages = [SystemMessage(content=RAG_AGENT_PROMPT)] + state["messages"][-5:]
    response = llm_with_tools.invoke(messages)

    tool_results = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            tool_fn = {t.name: t for t in get_rag_tools()}.get(tc["name"])
            if tool_fn:
                result = tool_fn.invoke(tc["args"])
                tool_results.append(str(result))

    if tool_results:
        summary_prompt = (
            "Tóm tắt ngắn gọn kết quả tìm kiếm sau:\n"
            + "\n".join(tool_results)
        )
        summary_response = llm.invoke(
            [SystemMessage(content=RAG_AGENT_PROMPT)]
            + [AIMessage(content=summary_prompt)]
        )
        output = summary_response.content
    else:
        output = response.content or "Không tìm thấy dữ liệu liên quan trong tài liệu nội bộ."

    context = dict(state.get("context", {}))
    context["rag_agent"] = output

    return {
        "messages": [AIMessage(content=f"[RAG Agent]: {output}")],
        "context": context,
    }
