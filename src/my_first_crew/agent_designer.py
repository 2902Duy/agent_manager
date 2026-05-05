import json
from typing import Iterable

from crewai import Agent

from my_first_crew.capability_registry import (
    load_agent_skills,
    normalize_capability_name,
    required_skills_for_groups,
)
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
        return any(blueprint.use_rag or "local-rag" in blueprint.tool_groups for blueprint in blueprints)
    if tool_name == "sql":
        return any(
            blueprint.use_sql
            or "sqlserver-readonly" in blueprint.tool_groups
            for blueprint in blueprints
        )
    if tool_name == "chart":
        return any(blueprint.use_chart or "charting" in blueprint.tool_groups for blueprint in blueprints)
    return False


def _default_groups_for_flags(agent: AgentBlueprint) -> list[str]:
    groups: list[str] = []
    if agent.use_rag:
        groups.append("local-rag")
    if agent.use_sql:
        groups.append("sqlserver-readonly")
    if agent.use_chart:
        groups.append("charting")
    return groups


def _normalize_groups(values: Iterable[str]) -> list[str]:
    groups: list[str] = []
    for value in values:
        normalized = normalize_capability_name(value)
        if normalized and normalized not in groups:
            groups.append(normalized)
    return groups


def _normalize_skills(values: Iterable[str], tool_groups: Iterable[str]) -> list[str]:
    skills: list[str] = []
    for value in values:
        normalized = normalize_capability_name(value)
        if normalized and normalized not in skills:
            skills.append(normalized)
    for skill in required_skills_for_groups(tool_groups):
        if skill not in skills:
            skills.append(skill)
    return skills


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
        f"- name={agent.name}; role={agent.role}; goal={agent.goal}; "
        f"tool_groups={','.join(agent.tool_groups) or 'none'}; skills={','.join(agent.skills) or 'none'}"
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
        skills=load_agent_skills(["agent-design", "security-review"]) or None,
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
        "- local-rag: đọc data.txt bằng rag_search.\n"
        "- sqlserver-readonly: đọc SQL Server thật bằng connection profile read-only.\n"
        "- dataframe-analysis: phân tích dữ liệu bảng sau khi truy xuất.\n"
        "- charting: tạo file biểu đồ PNG.\n"
        "- report-export: xuất Markdown/Excel/PDF.\n\n"
        "Skill có thể gắn cho agent mới: rag-research, sql-analysis, sqlserver-operations, "
        "data-quality-check, business-metrics, chart-selection, report-writing, result-review, security-review.\n\n"
        "Nguyên tắc ra quyết định:\n"
        "- Không tạo agent mới nếu agent hiện có đã có tool và vai trò đủ gần để xử lý task.\n"
        "- Không tạo agent mới chỉ vì task có từ khóa như biểu đồ, SQL, RAG, dashboard hoặc báo cáo.\n"
        "- Nếu task yêu cầu biểu đồ nhưng đã có agent có charting hoặc create_bar_chart, trả về needs_new_agents=false.\n"
        "- Nếu task yêu cầu SQL thật nhưng đã có agent có sqlserver-readonly, trả về needs_new_agents=false trừ khi cần chuyên môn khác biệt rõ ràng.\n"
        "- Chỉ đề xuất agent mới khi thiếu tool bắt buộc hoặc thiếu vai trò chuyên biệt chưa có, ví dụ: dự báo, xuất PDF/Excel, kiểm thử dữ liệu, tối ưu prompt.\n"
        "- Nếu cần đề xuất agent biểu đồ cho dữ liệu thật, agent đó nên có tool_groups=[sqlserver-readonly, dataframe-analysis, charting] và skills=[sqlserver-operations, sql-analysis, business-metrics, chart-selection].\n"
        "- Ưu tiên trả về tool_groups và skills ngắn gọn; các field use_rag/use_sql/use_chart chỉ để tương thích cũ.\n\n"
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
        (lambda groups, agent: AgentBlueprint(
            name=agent_key(agent.name or agent.role),
            role=agent.role,
            goal=agent.goal,
            backstory=agent.backstory,
            tool_groups=groups,
            skills=_normalize_skills(agent.skills, groups),
            use_rag=agent.use_rag,
            use_sql=agent.use_sql or agent.use_chart,
            use_chart=agent.use_chart,
        ))(_normalize_groups(agent.tool_groups) or _default_groups_for_flags(agent), agent)
        for agent in design.agents[:max_suggestions]
    ]
    suggestions = _filter_redundant_tool_suggestions(suggestions, current_agents)
    return _dedupe_suggestions(suggestions, current_agents)
