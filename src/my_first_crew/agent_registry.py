from pathlib import Path
from typing import Iterable

import yaml

from my_first_crew.models import AgentBlueprint, DEFAULT_MODEL


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTS_YAML = PROJECT_ROOT / "src" / "my_first_crew" / "config" / "agents.yaml"

TOOL_FLAG_BY_AGENT_NAME = {
    "document_researcher": {"use_rag": True},
    "sql_builder": {"use_sql": True},
    "database_retriever": {"use_sql": True},
}

DEFAULT_AGENT_BLUEPRINTS = [
    AgentBlueprint(
        name="document_researcher",
        role="Nhà nghiên cứu tài liệu",
        goal="Tìm và tóm tắt thông tin liên quan trong tài liệu nội bộ.",
        backstory="Bạn phụ trách truy xuất ngữ cảnh từ data.txt bằng RAG khi task cần kiến thức nội bộ.",
        use_rag=True,
    ),
    AgentBlueprint(
        name="technical_writer",
        role="Người viết kỹ thuật",
        goal="Biến kết quả phân tích thành câu trả lời rõ ràng, có cấu trúc.",
        backstory="Bạn viết câu trả lời ngắn gọn, mạch lạc, và nêu rõ các giả định nếu có.",
    ),
    AgentBlueprint(
        name="implementation_planner",
        role="Người lập kế hoạch triển khai",
        goal="Chia task thành các bước thực thi cụ thể và ưu tiên việc cần làm.",
        backstory="Bạn giỏi lập kế hoạch thực tế cho workflow agent và sản phẩm phần mềm.",
    ),
    AgentBlueprint(
        name="sql_builder",
        role="Chuyên viên tạo SQL",
        goal="Đọc schema mẫu, viết câu SQL SELECT phù hợp, và giải thích câu SQL đó.",
        backstory="Bạn chuyên chuyển câu hỏi kinh doanh thành SQL an toàn. Bạn luôn xem schema trước khi đề xuất truy vấn.",
        use_sql=True,
    ),
    AgentBlueprint(
        name="database_retriever",
        role="Chuyên viên truy xuất dữ liệu",
        goal="Chạy SQL read-only trên sample.db để lấy dữ liệu chính xác cho câu hỏi của user.",
        backstory=(
            "Bạn chịu trách nhiệm lấy dữ liệu thực tế từ SQLite database mẫu. "
            "Bạn chỉ dùng SELECT và luôn trả lại dữ liệu nguồn cho agent khác tổng hợp."
        ),
        use_sql=True,
    ),
    AgentBlueprint(
        name="data_answerer",
        role="Chuyên viên trả lời từ dữ liệu",
        goal="Dựa trên dữ liệu do agent truy xuất cung cấp để trả lời rõ ràng cho user.",
        backstory="Bạn không tự bịa số liệu. Bạn chỉ kết luận từ dữ liệu đã được truy xuất từ database hoặc tài liệu.",
    ),
]


def _blueprint_from_yaml(name: str, config: dict) -> AgentBlueprint:
    flags = TOOL_FLAG_BY_AGENT_NAME.get(name, {})
    tools = config.get("tools", [])
    if not isinstance(tools, list):
        tools = []
    return AgentBlueprint(
        name=name,
        role=str(config.get("role", "")).strip(),
        goal=str(config.get("goal", "")).strip(),
        backstory=str(config.get("backstory", "")).strip(),
        use_rag=bool(config.get("use_rag", flags.get("use_rag", False)) or "rag_search" in tools),
        use_sql=bool(
            config.get("use_sql", flags.get("use_sql", False))
            or "sql_schema" in tools
            or "sql_query" in tools
        ),
        use_chart=bool(config.get("use_chart", flags.get("use_chart", False)) or "create_revenue_chart" in tools),
    )


def load_agent_blueprints() -> list[AgentBlueprint]:
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


def _tools_for_blueprint(blueprint: AgentBlueprint) -> list[str]:
    tools: list[str] = []
    if blueprint.use_rag:
        tools.append("rag_search")
    if blueprint.use_sql:
        tools.extend(["sql_schema", "sql_query"])
    if blueprint.use_chart:
        tools.append("create_revenue_chart")
    return tools


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

        payload[name] = {
            "role": blueprint.role,
            "goal": blueprint.goal,
            "backstory": blueprint.backstory,
            "llm": model,
            "tools": _tools_for_blueprint(blueprint),
        }

    AGENTS_YAML.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
