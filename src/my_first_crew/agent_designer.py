import json
from typing import Iterable

from crewai import Agent

from my_first_crew.crew_builder import make_llm
from my_first_crew.models import AgentBlueprint, AgentDesignResult, DEFAULT_MODEL, agent_key, normalize_text


def _dedupe_suggestions(
    suggestions: Iterable[AgentBlueprint],
    blueprints: Iterable[AgentBlueprint],
) -> list[AgentBlueprint]:
    existing_names = {blueprint.name for blueprint in blueprints}
    existing_roles = {normalize_text(blueprint.role) for blueprint in blueprints}
    result: list[AgentBlueprint] = []
    for suggestion in suggestions:
        role_key = normalize_text(suggestion.role)
        if suggestion.name in existing_names or role_key in existing_roles:
            continue
        result.append(suggestion)
        existing_names.add(suggestion.name)
        existing_roles.add(role_key)
    return result


def _has_agent_with_tool(blueprints: Iterable[AgentBlueprint], tool_name: str) -> bool:
    if tool_name == "rag":
        return any(blueprint.use_rag for blueprint in blueprints)
    if tool_name == "sql":
        return any(blueprint.use_sql for blueprint in blueprints)
    if tool_name == "chart":
        return any(blueprint.use_chart for blueprint in blueprints)
    return False


def _filter_redundant_tool_suggestions(
    suggestions: Iterable[AgentBlueprint],
    blueprints: Iterable[AgentBlueprint],
) -> list[AgentBlueprint]:
    current_agents = list(blueprints)
    filtered: list[AgentBlueprint] = []

    for suggestion in suggestions:
        only_chart_gap = suggestion.use_chart and _has_agent_with_tool(current_agents, "chart")
        only_sql_gap = suggestion.use_sql and not suggestion.use_chart and _has_agent_with_tool(current_agents, "sql")
        only_rag_gap = suggestion.use_rag and not suggestion.use_sql and not suggestion.use_chart and _has_agent_with_tool(current_agents, "rag")

        if only_chart_gap or only_sql_gap or only_rag_gap:
            continue
        filtered.append(suggestion)

    return filtered


def _parse_design_result(raw: str) -> AgentDesignResult:
    try:
        return AgentDesignResult.model_validate_json(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return AgentDesignResult(needs_new_agents=False, reason="Không parse được JSON từ Agent Designer.")
        return AgentDesignResult.model_validate(json.loads(raw[start : end + 1]))


def task_needs_chart(user_task: str) -> bool:
    task_text = normalize_text(user_task)
    return any(
        keyword in task_text
        for keyword in (
            "bieu do",
            "ve bieu do",
            "chart",
            "do thi",
            "dashboard",
            "truc quan",
            "visual",
        )
    )


def suggest_missing_agents(
    user_task: str,
    blueprints: Iterable[AgentBlueprint],
    model: str = DEFAULT_MODEL,
    max_suggestions: int = 3,
) -> list[AgentBlueprint]:
    current_agents = list(blueprints)
    roster = "\n".join(
        f"- name={agent.name}; role={agent.role}; goal={agent.goal}; tools="
        f"{','.join(tool for tool, enabled in [('rag_search', agent.use_rag), ('sql_query/sql_schema', agent.use_sql), ('create_revenue_chart', agent.use_chart)] if enabled) or 'none'}"
        for agent in current_agents
    )
    capability_summary = (
        f"- Có RAG tool: {'có' if _has_agent_with_tool(current_agents, 'rag') else 'không'}\n"
        f"- Có SQL tool: {'có' if _has_agent_with_tool(current_agents, 'sql') else 'không'}\n"
        f"- Có Chart tool: {'có' if _has_agent_with_tool(current_agents, 'chart') else 'không'}"
    )

    designer = Agent(
        role="Agent Designer",
        goal="Phân tích task và chỉ đề xuất agent mới khi đội hình hiện tại thiếu năng lực thật sự.",
        backstory=(
            "Bạn là kiến trúc sư multi-agent thận trọng. Mặc định của bạn là tái sử dụng agent hiện có. "
            "Bạn chỉ đề xuất agent mới khi thiếu tool bắt buộc hoặc thiếu một chuyên môn khác biệt rõ ràng. "
            "Bạn không đề xuất agent mới chỉ vì task có từ khóa giống một mẫu đã biết."
        ),
        llm=make_llm(model=model, temperature=0),
        max_iter=1,
        max_retry_limit=1,
        verbose=False,
    )
    prompt = (
        "Task của user:\n"
        f"{user_task}\n\n"
        "Agent hiện có:\n"
        f"{roster}\n\n"
        "Tóm tắt năng lực hiện có:\n"
        f"{capability_summary}\n\n"
        "Tool có thể gắn cho agent mới:\n"
        "- use_rag=true nếu cần đọc data.txt bằng rag_search.\n"
        "- use_sql=true nếu cần đọc schema.sql hoặc truy vấn sample.db bằng sql_schema/sql_query.\n"
        "- use_chart=true nếu cần tạo file biểu đồ PNG bằng create_revenue_chart; nếu use_chart=true thì thường use_sql cũng nên true.\n\n"
        "Nguyên tắc ra quyết định:\n"
        "- Không tạo agent mới nếu agent hiện có đã có tool và vai trò đủ gần để xử lý task.\n"
        "- Không tạo agent mới chỉ vì task có từ khóa như biểu đồ, SQL, RAG, dashboard hoặc báo cáo.\n"
        "- Nếu task yêu cầu biểu đồ nhưng đã có agent có create_revenue_chart, trả về needs_new_agents=false.\n"
        "- Nếu task yêu cầu SQL nhưng đã có agent có sql_schema/sql_query, trả về needs_new_agents=false trừ khi cần chuyên môn khác biệt rõ ràng.\n"
        "- Chỉ đề xuất agent mới khi thiếu tool bắt buộc hoặc thiếu vai trò chuyên biệt chưa có, ví dụ: dự báo, xuất PDF/Excel, kiểm thử dữ liệu, tối ưu prompt.\n"
        "- Nếu cần đề xuất agent biểu đồ vì chưa có Chart tool, agent đó nên có use_chart=true và use_sql=true.\n\n"
        f"Hãy đề xuất tối đa {max_suggestions} agent mới nếu thật sự cần. "
        "Nếu agent hiện có đã đủ, trả về needs_new_agents=false. Trả về đúng JSON theo schema, không markdown."
    )

    try:
        output = designer.kickoff(prompt, response_format=AgentDesignResult)
        design = output.pydantic or _parse_design_result(output.raw)
    except Exception as error:
        return [
            AgentBlueprint(
                name="agent_designer_error",
                role="Lỗi đề xuất agent",
                goal="Không thể đề xuất agent mới.",
                backstory=f"Agent Designer lỗi: {error}",
            )
        ]

    if not design.needs_new_agents:
        return []

    suggestions = [
        AgentBlueprint(
            name=agent_key(agent.name or agent.role),
            role=agent.role,
            goal=agent.goal,
            backstory=agent.backstory,
            use_rag=agent.use_rag,
            use_sql=agent.use_sql or agent.use_chart,
            use_chart=agent.use_chart,
        )
        for agent in design.agents[:max_suggestions]
    ]
    suggestions = _filter_redundant_tool_suggestions(suggestions, current_agents)
    return _dedupe_suggestions(suggestions, current_agents)
