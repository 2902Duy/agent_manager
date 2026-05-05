from pathlib import Path
from typing import Iterable

import yaml
from crewai.skills.loader import activate_skill, load_skill_metadata
from crewai.skills.models import Skill


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "src" / "my_first_crew" / "config"
SKILLS_DIR = PROJECT_ROOT / "src" / "my_first_crew" / "skills"
TOOL_GROUPS_YAML = CONFIG_DIR / "tool_groups.yaml"
SKILLS_YAML = CONFIG_DIR / "skills.yaml"


DEFAULT_TOOL_GROUPS: dict[str, dict] = {
    "local-rag": {
        "description": "Đọc và truy xuất tài liệu nội bộ.",
        "risk_level": "low",
        "tools": ["rag_search"],
        "required_skills": ["rag-research"],
    },
    "sqlserver-readonly": {
        "description": "Đọc SQL Server thật bằng connection profile read-only.",
        "risk_level": "medium",
        "tools": ["sqlserver_test_connection", "sqlserver_schema", "sqlserver_query", "sqlserver_sample_rows"],
        "required_skills": ["sqlserver-operations", "sql-analysis"],
        "policies": ["readonly_only", "allowlisted_tables_only", "max_rows_500"],
    },
    "dataframe-analysis": {
        "description": "Phân tích dữ liệu bảng sau khi truy xuất.",
        "risk_level": "low",
        "tools": ["dataframe_profile"],
        "required_skills": ["data-quality-check", "business-metrics"],
    },
    "data-export": {
        "description": "Lưu dữ liệu đã truy xuất thành file thật trong output/.",
        "risk_level": "medium",
        "tools": ["save_rows_csv"],
        "required_skills": ["export-packaging"],
    },
    "charting": {
        "description": "Tạo biểu đồ từ dữ liệu.",
        "risk_level": "low",
        "tools": ["create_bar_chart"],
        "required_skills": ["chart-selection"],
    },
    "report-export": {
        "description": "Đóng gói kết quả thành báo cáo.",
        "risk_level": "medium",
        "tools": ["save_rows_csv", "export_markdown", "export_excel", "export_pdf"],
        "required_skills": ["report-writing", "export-packaging"],
    },
    "evaluation": {
        "description": "Review, kiểm định và đánh giá kết quả.",
        "risk_level": "low",
        "tools": [],
        "required_skills": ["result-review", "security-review"],
    },
}


DEFAULT_SKILLS: dict[str, dict] = {
    "agent-routing": {
        "description": "Chọn agent theo năng lực, tool group và risk level.",
        "allowed_tools": [],
    },
    "agent-design": {
        "description": "Đề xuất agent mới khi thiếu năng lực thật sự.",
        "allowed_tools": [],
    },
    "rag-research": {
        "description": "Truy xuất tài liệu nội bộ và trả lời có nguồn.",
        "allowed_tools": ["rag_search"],
    },
    "sql-analysis": {
        "description": "Viết và giải thích SQL read-only an toàn.",
        "allowed_tools": ["sqlserver_schema", "sqlserver_query"],
    },
    "sqlserver-operations": {
        "description": "Làm việc với SQL Server thật qua connection profile an toàn.",
        "allowed_tools": ["sqlserver_test_connection", "sqlserver_schema", "sqlserver_query", "sqlserver_sample_rows"],
    },
    "data-quality-check": {
        "description": "Kiểm tra dữ liệu thiếu, sai kiểu, bất thường và giới hạn phân tích.",
        "allowed_tools": ["dataframe_profile"],
    },
    "business-metrics": {
        "description": "Tính KPI, doanh thu, tăng trưởng và phân tích kinh doanh.",
        "allowed_tools": ["sqlserver_query", "dataframe_profile"],
    },
    "chart-selection": {
        "description": "Chọn biểu đồ phù hợp và yêu cầu tạo file output thật.",
        "allowed_tools": ["create_bar_chart", "chart_from_dataframe"],
    },
    "report-writing": {
        "description": "Viết câu trả lời và báo cáo ngắn gọn, có cấu trúc.",
        "allowed_tools": ["rag_search"],
    },
    "result-review": {
        "description": "Review kết quả cuối, kiểm tra dữ liệu thật và file output thật.",
        "allowed_tools": [],
    },
    "security-review": {
        "description": "Kiểm tra secret, query nguy hiểm và rủi ro dữ liệu.",
        "allowed_tools": [],
    },
    "export-packaging": {
        "description": "Đóng gói Markdown, Excel, PDF theo output thật.",
        "allowed_tools": ["save_rows_csv", "export_markdown", "export_excel", "export_pdf"],
    },
}


def normalize_capability_name(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _read_yaml(path: Path, fallback: dict[str, dict]) -> dict[str, dict]:
    if not path.exists():
        return fallback
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else fallback


def load_tool_groups() -> dict[str, dict]:
    return _read_yaml(TOOL_GROUPS_YAML, DEFAULT_TOOL_GROUPS)


def load_skill_configs() -> dict[str, dict]:
    return _read_yaml(SKILLS_YAML, DEFAULT_SKILLS)


def tools_for_groups(tool_groups: Iterable[str]) -> list[str]:
    groups = load_tool_groups()
    tools: list[str] = []
    for group_name in tool_groups:
        group = groups.get(normalize_capability_name(group_name), {})
        for tool_name in group.get("tools", []):
            if tool_name not in tools:
                tools.append(str(tool_name))
    return tools


def required_skills_for_groups(tool_groups: Iterable[str]) -> list[str]:
    groups = load_tool_groups()
    skills: list[str] = []
    for group_name in tool_groups:
        group = groups.get(normalize_capability_name(group_name), {})
        for skill_name in group.get("required_skills", []):
            normalized = normalize_capability_name(str(skill_name))
            if normalized not in skills:
                skills.append(normalized)
    return skills


def risk_for_groups(tool_groups: Iterable[str]) -> str:
    order = {"low": 1, "medium": 2, "high": 3, "blocked": 4}
    groups = load_tool_groups()
    risk = "low"
    for group_name in tool_groups:
        group = groups.get(normalize_capability_name(group_name), {})
        current = str(group.get("risk_level", "low"))
        if order.get(current, 1) > order.get(risk, 1):
            risk = current
    return risk


def load_agent_skills(skill_names: Iterable[str]) -> list[Skill]:
    loaded: list[Skill] = []
    for skill_name in skill_names:
        normalized = normalize_capability_name(skill_name)
        skill_dir = SKILLS_DIR / normalized
        if not (skill_dir / "SKILL.md").exists():
            continue
        loaded.append(activate_skill(load_skill_metadata(skill_dir)))
    return loaded
