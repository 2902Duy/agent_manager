from pathlib import Path
from typing import Iterable

import yaml

from my_first_crew.capability_registry import (
    normalize_capability_name,
    required_skills_for_groups,
    risk_for_groups,
    tools_for_groups,
)
from my_first_crew.models import AgentBlueprint, DEFAULT_MODEL


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTS_YAML = PROJECT_ROOT / "src" / "my_first_crew" / "config" / "agents.yaml"

LEGACY_TOOL_GROUPS_BY_AGENT_NAME = {
    "document_researcher": ["local-rag"],
    "sql_builder": ["sqlserver-readonly"],
    "database_retriever": ["sqlserver-readonly"],
}

DEFAULT_AGENT_BLUEPRINTS = [
    AgentBlueprint(
        name="document_researcher",
        role="Nhà nghiên cứu tài liệu",
        goal="Tìm và tóm tắt thông tin liên quan trong tài liệu nội bộ.",
        backstory="Bạn phụ trách truy xuất ngữ cảnh từ data.txt bằng RAG khi task cần kiến thức nội bộ.",
        tool_groups=["local-rag"],
        skills=["rag-research", "report-writing"],
        use_rag=True,
    ),
    AgentBlueprint(
        name="technical_writer",
        role="Người viết kỹ thuật",
        goal="Biến kết quả phân tích thành câu trả lời rõ ràng, có cấu trúc.",
        backstory="Bạn viết câu trả lời ngắn gọn, mạch lạc, và nêu rõ các giả định nếu có.",
        tool_groups=[],
        skills=["report-writing", "result-review"],
    ),
    AgentBlueprint(
        name="implementation_planner",
        role="Người lập kế hoạch triển khai",
        goal="Chia task thành các bước thực thi cụ thể và ưu tiên việc cần làm.",
        backstory="Bạn giỏi lập kế hoạch thực tế cho workflow agent và sản phẩm phần mềm.",
        tool_groups=[],
        skills=["agent-routing", "result-review"],
    ),
    AgentBlueprint(
        name="sql_builder",
        role="Chuyên viên tạo SQL",
        goal="Đọc schema mẫu, viết câu SQL SELECT phù hợp, và giải thích câu SQL đó.",
        backstory="Bạn chuyên chuyển câu hỏi kinh doanh thành SQL an toàn. Bạn luôn xem schema trước khi đề xuất truy vấn.",
        tool_groups=["sqlserver-readonly"],
        skills=["sql-analysis"],
        use_sql=True,
    ),
    AgentBlueprint(
        name="database_retriever",
        role="Chuyên viên truy xuất dữ liệu",
        goal="Chạy SQL Server read-only để lấy dữ liệu chính xác cho câu hỏi của user.",
        backstory=(
            "Bạn chịu trách nhiệm lấy dữ liệu thực tế từ SQL Server. "
            "Bạn chỉ dùng SELECT và luôn trả lại dữ liệu nguồn cho agent khác tổng hợp."
        ),
        tool_groups=["sqlserver-readonly"],
        skills=["sql-analysis", "data-quality-check"],
        use_sql=True,
    ),
    AgentBlueprint(
        name="data_answerer",
        role="Chuyên viên trả lời từ dữ liệu",
        goal="Dựa trên dữ liệu do agent truy xuất cung cấp để trả lời rõ ràng cho user.",
        backstory="Bạn không tự bịa số liệu. Bạn chỉ kết luận từ dữ liệu đã được truy xuất từ database hoặc tài liệu.",
        tool_groups=[],
        skills=["business-metrics", "report-writing", "result-review"],
    ),
]


def _list_config(config: dict, key: str) -> list[str]:
    value = config.get(key, [])
    if isinstance(value, str):
        return [normalize_capability_name(item) for item in value.replace(",", " ").split() if item.strip()]
    if isinstance(value, list):
        return [normalize_capability_name(str(item)) for item in value if str(item).strip()]
    return []


def _groups_from_legacy_tools(tools: list[str], name: str, config: dict) -> list[str]:
    groups = list(LEGACY_TOOL_GROUPS_BY_AGENT_NAME.get(name, []))
    if config.get("use_rag") or "rag_search" in tools:
        groups.append("local-rag")
    if config.get("use_sql") or "sql_schema" in tools or "sql_query" in tools:
        groups.append("sqlserver-readonly")
    if any(tool.startswith("sqlserver_") for tool in tools):
        groups.append("sqlserver-readonly")
    if config.get("use_chart") or "create_bar_chart" in tools:
        groups.append("charting")

    result: list[str] = []
    for group in groups:
        normalized = normalize_capability_name(group)
        if normalized not in result:
            result.append(normalized)
    return result


def _flags_from_tools(tools: list[str]) -> tuple[bool, bool, bool]:
    return (
        "rag_search" in tools,
        "sql_schema" in tools
        or "sql_query" in tools
        or "sqlserver_query" in tools,
        "create_bar_chart" in tools or "chart_from_dataframe" in tools,
    )


def _blueprint_from_yaml(name: str, config: dict) -> AgentBlueprint:
    tools = config.get("tools", [])
    if not isinstance(tools, list):
        tools = []
    tools = [str(tool) for tool in tools]
    tool_groups = _list_config(config, "tool_groups")
    if not tool_groups:
        tool_groups = _groups_from_legacy_tools(tools, name, config)

    tools_override = _list_config(config, "tools_override")
    effective_tools = [*tools_for_groups(tool_groups), *tools, *tools_override]
    use_rag, use_sql, use_chart = _flags_from_tools(effective_tools)

    skills = _list_config(config, "skills")
    for skill in required_skills_for_groups(tool_groups):
        if skill not in skills:
            skills.append(skill)

    return AgentBlueprint(
        name=name,
        role=str(config.get("role", "")).strip(),
        goal=str(config.get("goal", "")).strip(),
        backstory=str(config.get("backstory", "")).strip(),
        llm=str(config.get("llm", DEFAULT_MODEL)).strip() or DEFAULT_MODEL,
        tool_groups=tool_groups,
        skills=skills,
        tools_override=tools_override,
        enabled=bool(config.get("enabled", True)),
        risk_level=str(config.get("risk_level", risk_for_groups(tool_groups))),
        use_rag=use_rag,
        use_sql=use_sql,
        use_chart=use_chart,
    )


def load_all_agent_blueprints() -> list[AgentBlueprint]:
    """Load all agent blueprints including disabled ones."""
    if not AGENTS_YAML.exists():
        return list(DEFAULT_AGENT_BLUEPRINTS)

    data = yaml.safe_load(AGENTS_YAML.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return list(DEFAULT_AGENT_BLUEPRINTS)

    blueprints: list[AgentBlueprint] = []
    for name, config in data.items():
        if isinstance(config, dict):
            blueprints.append(_blueprint_from_yaml(str(name), config))
    return blueprints or list(DEFAULT_AGENT_BLUEPRINTS)


def load_agent_blueprints() -> list[AgentBlueprint]:
    """Load only enabled agent blueprints (for crew execution)."""
    return [bp for bp in load_all_agent_blueprints() if bp.enabled]


def _tools_for_blueprint(blueprint: AgentBlueprint) -> list[str]:
    tools = tools_for_groups(blueprint.tool_groups)
    tools.extend(tool for tool in blueprint.tools_override if tool not in tools)
    return tools


def _groups_for_blueprint(blueprint: AgentBlueprint) -> list[str]:
    if blueprint.tool_groups:
        return blueprint.tool_groups

    groups: list[str] = []
    if blueprint.use_rag:
        groups.append("local-rag")
    if blueprint.use_sql:
        groups.append("sqlserver-readonly")
    if blueprint.use_chart:
        groups.append("charting")
    return groups


def _skills_for_blueprint(blueprint: AgentBlueprint, tool_groups: list[str]) -> list[str]:
    skills = list(blueprint.skills)
    for skill in required_skills_for_groups(tool_groups):
        if skill not in skills:
            skills.append(skill)
    return skills


def save_agent_blueprints(blueprints: Iterable[AgentBlueprint], model: str = DEFAULT_MODEL) -> None:
    payload = {}
    used_names: set[str] = set()
    for blueprint in blueprints:
        name = blueprint.name
        if name in used_names:
            base = name
            index = 2
            while f"{base}_{index}" in used_names:
                index += 1
            name = f"{base}_{index}"
        used_names.add(name)

        tool_groups = _groups_for_blueprint(blueprint)
        skills = _skills_for_blueprint(blueprint, tool_groups)

        payload[name] = {
            "role": blueprint.role,
            "goal": blueprint.goal,
            "backstory": blueprint.backstory,
            "llm": blueprint.llm or model,
            "tool_groups": tool_groups,
            "skills": skills,
            "enabled": blueprint.enabled,
            "risk_level": blueprint.risk_level or risk_for_groups(tool_groups),
        }
        if blueprint.tools_override:
            payload[name]["tools_override"] = blueprint.tools_override

    AGENTS_YAML.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
