from typing import Iterable

from crewai import Agent, Crew, LLM, Process, Task

from my_first_crew.encoding_setup import force_utf8
from my_first_crew.models import AgentBlueprint, DEFAULT_MODEL, normalize_text
from my_first_crew.tools.chart_tool import RevenueChartTool
from my_first_crew.tools.rag_tool import RagSearchTool
from my_first_crew.tools.sql_tool import SqlQueryTool, SqlSchemaTool


force_utf8()


def make_llm(model: str = DEFAULT_MODEL, temperature: float = 0.2) -> LLM:
    return LLM(model=model, temperature=temperature, timeout=120, max_tokens=1200)


def recommend_agent(user_task: str, blueprints: Iterable[AgentBlueprint]) -> AgentBlueprint:
    task_text = normalize_text(user_task)
    candidates = list(blueprints)
    if not candidates:
        raise ValueError("Không có agent nào để router lựa chọn.")

    rag_keywords = ("data.txt", "tai lieu", "rag", "ollama", "langgraph", "crewai")
    sql_keywords = (
        "sql",
        "database",
        "sqlite",
        "sample.db",
        "schema",
        "bang",
        "du lieu",
        "truy van",
        "doanh thu",
        "don hang",
        "khach hang",
        "ban hang",
    )
    chart_keywords = ("bieu do", "ve bieu do", "chart", "visual", "do thi", "dashboard")
    planning_keywords = ("plan", "ke hoach", "workflow", "setup", "quy trinh", "trien khai")
    writing_keywords = ("viet", "tom tat", "bao cao", "tra loi", "giai thich")

    def score(blueprint: AgentBlueprint) -> int:
        haystack = normalize_text(f"{blueprint.role} {blueprint.goal} {blueprint.backstory}")
        value = 0
        if blueprint.use_rag and any(keyword in task_text for keyword in rag_keywords):
            value += 5
        if blueprint.use_sql and any(keyword in task_text for keyword in sql_keywords):
            value += 6
        if blueprint.use_chart and any(keyword in task_text for keyword in chart_keywords):
            value += 8
        if any(keyword in task_text for keyword in planning_keywords) and any(
            keyword in haystack for keyword in ("lap ke hoach", "ke hoach", "workflow", "trien khai")
        ):
            value += 4
        if any(keyword in task_text for keyword in writing_keywords) and any(
            keyword in haystack for keyword in ("viet", "ky thuat", "bao cao", "cau tra loi")
        ):
            value += 3
        value += sum(1 for word in task_text.split() if len(word) > 3 and word in haystack)
        return value

    return max(candidates, key=score)


def build_agents(blueprints: Iterable[AgentBlueprint], llm: LLM) -> list[Agent]:
    agents: list[Agent] = []
    for blueprint in blueprints:
        tools = [RagSearchTool()] if blueprint.use_rag else []
        if blueprint.use_sql:
            tools.extend([SqlSchemaTool(), SqlQueryTool()])
        if blueprint.use_chart:
            tools.append(RevenueChartTool())
        agents.append(
            Agent(
                role=blueprint.role,
                goal=blueprint.goal,
                backstory=blueprint.backstory,
                tools=tools,
                llm=llm,
                allow_delegation=False,
                max_iter=2,
                max_retry_limit=1,
                verbose=True,
            )
        )
    return agents


def build_managed_crew(
    user_task: str,
    blueprints: Iterable[AgentBlueprint],
    model: str = DEFAULT_MODEL,
    verbose: bool = True,
) -> Crew:
    llm = make_llm(model=model)
    worker_blueprints = list(blueprints)
    workers = build_agents(worker_blueprints, llm)
    recommended = recommend_agent(user_task, worker_blueprints)
    roster = "\n".join(
        f"- {item.role}: mục tiêu={item.goal}; RAG tool={'có' if item.use_rag else 'không'}; SQL tool={'có' if item.use_sql else 'không'}; Chart tool={'có' if item.use_chart else 'không'}"
        for item in worker_blueprints
    )

    manager = Agent(
        role="Agent quản lý",
        goal="Nhận task của user, chọn agent phù hợp nhất, giao việc, tổng hợp kết quả, và yêu cầu làm lại nếu kết quả chưa đạt.",
        backstory=(
            "Bạn là agent điều phối tổng. Bạn hiểu năng lực của từng agent, "
            "không tự làm hết việc nếu có agent phù hợp hơn, và luôn tạo kết quả cuối cùng có thể review được."
        ),
        llm=llm,
        allow_delegation=True,
        max_iter=3,
        max_retry_limit=1,
        verbose=verbose,
    )

    reviewer = Agent(
        role="Agent duyệt kết quả",
        goal="Review kết quả cuối cùng trước khi trả về cho user.",
        backstory=(
            "Bạn đại diện cho agent gốc để kiểm tra: đã đúng task chưa, agent được chọn có phù hợp không, "
            "kết quả có thiếu thông tin quan trọng không, và cần sửa gì trước khi gửi user."
        ),
        llm=llm,
        allow_delegation=False,
        max_iter=2,
        max_retry_limit=1,
        verbose=verbose,
    )

    execution_task = Task(
        description=(
            "Task của user:\n"
            f"{user_task}\n\n"
            "Danh sách agent có sẵn:\n"
            f"{roster}\n\n"
            "Router gợi ý trước khi chạy:\n"
            f"Nếu không có lý do mạnh để đổi, hãy giao cho agent: {recommended.role}\n\n"
            "Quy trình bắt buộc:\n"
            "1. Đọc danh sách agent và chọn agent phù hợp nhất.\n"
            "2. Nếu task cần tài liệu nội bộ, giao cho agent có RAG tool.\n"
            "3. Nếu task cần dữ liệu bảng, SQL, doanh thu, đơn hàng hoặc khách hàng, giao cho agent có SQL tool.\n"
            "4. Khi cần dữ liệu DB, ưu tiên quy trình: agent tạo SQL hoặc xem schema -> agent truy xuất dữ liệu -> agent trả lời từ dữ liệu.\n"
            "5. Nếu task yêu cầu vẽ biểu đồ, phải giao cho agent có Chart tool và yêu cầu tạo file PNG thật.\n"
            "6. Nếu dùng create_revenue_chart, bắt buộc copy nguyên văn đường dẫn file tool trả về; không tự đặt tên file.\n"
            "7. Giao việc rõ ràng cho agent đã chọn.\n"
            "8. Tổng hợp kết quả thành bản trả lời nháp, kèm tên agent đã xử lý và lý do chọn agent."
        ),
        expected_output=(
            "Bản trả lời nháp bằng tiếng Việt gồm: agent đã chọn, lý do chọn, kết quả thực hiện, "
            "các điểm còn thiếu nếu có. Nếu có file output, phải ghi đúng đường dẫn file."
        ),
    )

    review_task = Task(
        description=(
            "Review kết quả của execution_task trước khi trả về user. "
            "Nếu kết quả chưa bám sát task, hãy chỉ rõ cần sửa. "
            "Nếu đạt, viết câu trả lời cuối cùng ngắn gọn và có cấu trúc. "
            "Nếu có file output, phải giữ nguyên đường dẫn file thật từ tool."
        ),
        expected_output="Final answer bằng tiếng Việt gồm 3 phần: Kết quả, Review của manager, Bước tiếp theo nếu cần.",
        agent=reviewer,
        context=[execution_task],
        output_file="answer.md",
    )

    return Crew(
        agents=[*workers, reviewer],
        tasks=[execution_task, review_task],
        process=Process.hierarchical,
        manager_agent=manager,
        verbose=verbose,
    )


def kickoff_managed_task(
    user_task: str,
    blueprints: Iterable[AgentBlueprint],
    model: str = DEFAULT_MODEL,
    verbose: bool = True,
):
    return build_managed_crew(
        user_task=user_task,
        blueprints=blueprints,
        model=model,
        verbose=verbose,
    ).kickoff()
