import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from my_first_crew.encoding_setup import force_utf8

force_utf8()

import streamlit as st
from dotenv import load_dotenv

from my_first_crew.dynamic_crew import (
    DEFAULT_MODEL,
    AgentBlueprint,
    kickoff_managed_task,
    load_agent_blueprints,
    recommend_agent,
    save_agent_blueprints,
    suggest_missing_agents,
    task_needs_chart,
)
from my_first_crew.execution_monitor import CrewExecutionMonitor
from my_first_crew.output_manager import OUTPUT_DIR, list_generated_images
from my_first_crew.tools.chart_tool import create_revenue_chart
from my_first_crew.tools.rag_tool import query_db
from my_first_crew.tools.sql_tool import describe_schema, run_read_only_query


MODEL_OPTIONS = [
    "gemini/gemini-3.1-flash-lite-preview",
    "gemini/gemini-3-flash-preview",
    "gemini/gemini-2.5-flash",
    "gemini/gemini-flash-lite-latest",
    "gemini/gemini-2.0-flash-lite",
    "gemini/gemini-1.5-flash",
    "gemini/gemini-2.0-flash",
    "gemini/gemma-3-1b-it",
    "gemini/gemma-3-4b-it",
    "gemini/gemma-3-12b-it",
    "gemini/gemma-3-27b-it",
    "ollama/llama3.1",
    "custom",
]

load_dotenv()


def _init_state() -> None:
    defaults = {
        "agent_suggestions": [],
        "last_trace": None,
        "last_result_raw": "",
        "last_tasks_output": [],
        "last_added_agents": [],
        "last_generated_images": [],
        "last_router_agent": "",
        "task_text": "Phân tích dữ liệu bán hàng rồi vẽ biểu đồ doanh thu",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _uses_google_api(model: str) -> bool:
    return model.startswith("gemini/")


def _is_quota_error(error: Exception) -> bool:
    message = str(error)
    return "429" in message or "RESOURCE_EXHAUSTED" in message or "quota" in message.lower()


def _is_encoding_error(error: Exception) -> bool:
    message = str(error)
    return "codec can't encode" in message or "ordinal not in range" in message


def _show_run_error(error: Exception, model: str) -> None:
    if _is_quota_error(error):
        st.error("Google Gemini API đang hết quota hoặc project/key hiện tại không có quota cho model này.")
        st.info(
            "Cách xử lý: đổi sang model nhẹ hơn, dùng API key/project khác đã bật billing, "
            "hoặc chọn ollama/llama3.1 để chạy local."
        )
        with st.expander("Chi tiết lỗi quota"):
            st.code(str(error))
        return

    if _is_encoding_error(error):
        st.error("Lỗi encoding tiếng Việt trên Windows khi gọi model.")
        st.info(
            "Hãy restart Streamlit với UTF-8: "
            "$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; uv run streamlit run src/my_first_crew/app.py"
        )
        with st.expander("Chi tiết lỗi encoding"):
            st.code(str(error))
        return

    st.error(f"Workflow bị lỗi khi gọi model {model}.")
    with st.expander("Chi tiết lỗi"):
        st.code(str(error))


def _agent_table(agents: list[AgentBlueprint]) -> list[dict]:
    return [
        {
            "name": agent.name,
            "role": agent.role,
            "goal": agent.goal,
            "rag": agent.use_rag,
            "sql": agent.use_sql,
            "chart": agent.use_chart,
        }
        for agent in agents
    ]


def _render_monitor(snapshot: dict | None) -> None:
    if not snapshot:
        st.caption("Chưa có trace. Hãy chạy workflow trước.")
        return

    status = snapshot.get("status") or "idle"
    current_agent = snapshot.get("current_agent") or "Đang chờ"
    current_task = snapshot.get("current_task") or "Chưa có task đang chạy"
    delegated_agent = snapshot.get("delegated_agent") or "Chưa xác định"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Trạng thái", status)
    col2.metric("Agent đang chạy", current_agent)
    col3.metric("Task hiện tại", current_task[:42])
    col4.metric("Đã giao cho", delegated_agent)

    events = snapshot.get("events", [])
    if not events:
        st.caption("Chưa có event nào.")
        return

    rows = []
    for item in reversed(events[-40:]):
        detail_parts = []
        for key in ("task", "agent", "args", "output", "error"):
            value = item.get(key)
            if value:
                detail_parts.append(f"{key}: {value}")
        rows.append(
            {
                "time": item.get("time", ""),
                "type": item.get("kind", ""),
                "event": item.get("message", ""),
                "detail": " | ".join(detail_parts),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_generated_images() -> None:
    images = list_generated_images()
    if not images:
        st.caption(f"Chưa có file PNG nào trong {OUTPUT_DIR}.")
        return

    for image_path in images:
        st.image(str(image_path), caption=str(image_path), use_container_width=True)


def _render_image_paths(image_paths: list[str]) -> None:
    existing_paths = [Path(path) for path in image_paths if Path(path).exists()]
    if not existing_paths:
        return

    st.markdown("### Ảnh vừa tạo")
    for image_path in existing_paths:
        st.image(str(image_path), caption=str(image_path), use_container_width=True)


def _require_api_key(model: str) -> bool:
    if _uses_google_api(model) and not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        st.error("Cần GOOGLE_API_KEY hoặc GEMINI_API_KEY để gọi Google Gemini API.")
        return False
    return True


def _analyze_agents(task: str, agents: list[AgentBlueprint], model: str) -> list[AgentBlueprint]:
    if not _require_api_key(model):
        return []
    with st.spinner("Agent Designer đang phân tích task và đề xuất agent mới..."):
        suggestions = suggest_missing_agents(task, agents, model=model)
    st.session_state.agent_suggestions = suggestions
    return suggestions


def _run_workflow(task: str, agents: list[AgentBlueprint], model: str, live_updates: bool) -> None:
    if not _require_api_key(model):
        return

    suggestions = _analyze_agents(task, agents, model)
    if task_needs_chart(task) and not any(agent.use_chart for agent in [*agents, *suggestions]):
        st.warning(
            "Task yêu cầu biểu đồ nhưng Agent Designer chưa tạo agent có Chart tool. "
            "Workflow chưa chạy để tránh trả lời thiếu file biểu đồ."
        )
        return

    if suggestions:
        agents = [*agents, *suggestions]
        st.session_state.last_added_agents = [agent.role for agent in suggestions]
        st.success("Agent Designer đã thêm tạm thời: " + ", ".join(st.session_state.last_added_agents))
    else:
        st.session_state.last_added_agents = []
        st.info("Agent Designer không thấy cần thêm agent mới. Workflow dùng đội hình hiện có.")

    recommended = recommend_agent(task, agents)
    st.session_state.last_router_agent = recommended.role
    st.info(f"Router dự kiến giao task cho: {recommended.role}")

    monitor = CrewExecutionMonitor(initial_delegated_agent=recommended.role)
    progress_box = st.empty()
    images_before = {str(path) for path in list_generated_images(limit=100)}
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                kickoff_managed_task,
                user_task=task,
                blueprints=agents,
                model=model,
                verbose=False,
            )

            if live_updates:
                while not future.done():
                    with progress_box.container():
                        st.subheader("Đang chạy")
                        _render_monitor(monitor.snapshot())
                    time.sleep(2)
            else:
                with progress_box.container():
                    st.subheader("Đang chạy")
                    st.markdown(f"**Agent dự kiến nhận task:** `{recommended.role}`")
                    st.caption("Trace sẽ hiển thị sau khi workflow hoàn tất.")
                while not future.done():
                    time.sleep(2)

            result = future.result()
    except Exception as error:
        _show_run_error(error, model)
        return
    finally:
        st.session_state.last_trace = monitor.snapshot()
        monitor.close()

    st.session_state.last_result_raw = result.raw
    st.session_state.last_tasks_output = [task_output.raw for task_output in getattr(result, "tasks_output", [])]

    images_after = [path for path in list_generated_images(limit=100) if str(path) not in images_before]
    if task_needs_chart(task) and not images_after:
        create_revenue_chart("Doanh thu theo khách hàng")
        images_after = [path for path in list_generated_images(limit=100) if str(path) not in images_before]
    st.session_state.last_generated_images = [str(path) for path in images_after[:5]]

    with progress_box.container():
        st.subheader("Trace thực thi")
        _render_monitor(st.session_state.last_trace)
        _render_image_paths(st.session_state.last_generated_images)


def _sidebar() -> tuple[str, bool]:
    st.sidebar.header("Cấu hình")
    selected_model = st.sidebar.selectbox("Model", MODEL_OPTIONS, index=0)
    if selected_model == "custom":
        model = st.sidebar.text_input("Model tùy chỉnh", value=DEFAULT_MODEL).strip() or DEFAULT_MODEL
    else:
        model = selected_model

    api_key = st.sidebar.text_input("GOOGLE_API_KEY / GEMINI_API_KEY", type="password")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key

    live_updates = st.sidebar.checkbox(
        "Cập nhật tiến trình trực tiếp",
        value=False,
        help="Bật nếu muốn xem trace khi đang chạy. Tắt mặc định để giao diện ổn định hơn.",
    )
    return model, live_updates


def _run_tab(model: str, live_updates: bool, agents: list[AgentBlueprint]) -> None:
    st.subheader("Chạy task")
    task = st.text_area("Task", key="task_text", height=140)

    col1, col2, col3 = st.columns([1, 1, 2])
    if col1.button("Phân tích đội hình"):
        suggestions = _analyze_agents(task, agents, model)
        if suggestions:
            st.success("Agent đề xuất: " + ", ".join(agent.role for agent in suggestions))
        else:
            st.info("Không cần thêm agent mới.")

    if col2.button("Chạy workflow", type="primary"):
        _run_workflow(task, agents, model, live_updates)

    if st.session_state.agent_suggestions:
        st.markdown("**Agent Designer đề xuất**")
        st.dataframe(_agent_table(st.session_state.agent_suggestions), use_container_width=True, hide_index=True)

    if st.session_state.last_result_raw:
        st.subheader("Kết quả mới nhất")
        st.markdown(st.session_state.last_result_raw)
        _render_image_paths(st.session_state.last_generated_images)


def _agents_tab(model: str, agents: list[AgentBlueprint]) -> None:
    st.subheader("Quản lý agent")
    st.caption("Danh sách này được load từ src/my_first_crew/config/agents.yaml")
    st.dataframe(_agent_table(agents), use_container_width=True, hide_index=True)

    suggestions: list[AgentBlueprint] = st.session_state.agent_suggestions
    st.markdown("### Agent được đề xuất")
    if suggestions:
        st.dataframe(_agent_table(suggestions), use_container_width=True, hide_index=True)
        col1, col2 = st.columns(2)
        if col1.button("Lưu agent đề xuất vào agents.yaml"):
            current = load_agent_blueprints()
            existing = {agent.name for agent in current}
            merged = [*current, *[agent for agent in suggestions if agent.name not in existing]]
            save_agent_blueprints(merged, model=model)
            st.session_state.agent_suggestions = []
            st.success("Đã lưu agent đề xuất vào agents.yaml.")
            st.rerun()
        if col2.button("Xóa đề xuất hiện tại"):
            st.session_state.agent_suggestions = []
            st.rerun()
    else:
        st.caption("Chưa có agent đề xuất.")


def _tools_tab() -> None:
    st.subheader("Tool")
    st.dataframe(
        [
            {"tool": "rag_search", "mô tả": "Tìm nội dung liên quan trong data.txt"},
            {"tool": "sql_schema", "mô tả": "Đọc cấu trúc bảng đã lọc an toàn"},
            {"tool": "sql_query", "mô tả": "Chạy SELECT read-only trên sample.db"},
            {"tool": "create_revenue_chart", "mô tả": "Tạo biểu đồ PNG doanh thu"},
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Test nhanh tool")
    tool_choice = st.selectbox("Chọn tool", ["rag_search", "sql_schema", "sql_query", "create_revenue_chart"])
    if tool_choice == "rag_search":
        query = st.text_input("Câu hỏi", value="CrewAI là gì?")
        if st.button("Test rag_search"):
            st.code(query_db(query), language="text")
    elif tool_choice == "sql_schema":
        if st.button("Test sql_schema"):
            st.code(describe_schema(), language="sql")
    elif tool_choice == "sql_query":
        sql = st.text_area(
            "SQL SELECT",
            value=(
                "SELECT c.name, SUM(oi.quantity * oi.unit_price) AS revenue\n"
                "FROM customers c\n"
                "JOIN orders o ON o.customer_id = c.id\n"
                "JOIN order_items oi ON oi.order_id = o.id\n"
                "WHERE o.status = 'paid'\n"
                "GROUP BY c.id, c.name\n"
                "ORDER BY revenue DESC"
            ),
            height=160,
        )
        if st.button("Test sql_query"):
            st.code(run_read_only_query(sql), language="json")
    else:
        title = st.text_input("Tiêu đề biểu đồ", value="Doanh thu theo khách hàng")
        if st.button("Test create_revenue_chart"):
            st.code(create_revenue_chart(title), language="text")


def _outputs_tab() -> None:
    st.subheader("Kết quả")
    if st.session_state.last_result_raw:
        st.markdown(st.session_state.last_result_raw)
    else:
        st.caption("Chưa có kết quả workflow trong phiên này.")

    st.markdown("### Ảnh đã tạo")
    _render_image_paths(st.session_state.last_generated_images)
    _render_generated_images()


def _trace_tab() -> None:
    st.subheader("Trace")
    _render_monitor(st.session_state.last_trace)

    if st.session_state.last_tasks_output:
        st.markdown("### Output từng task")
        for index, output in enumerate(st.session_state.last_tasks_output, start=1):
            with st.expander(f"Task {index}", expanded=False):
                st.write(output)


def main() -> None:
    st.set_page_config(page_title="CrewAI Agent Workspace", layout="wide")
    _init_state()
    st.title("CrewAI Agent Workspace")
    st.caption("Thiết kế agent, chạy workflow, dùng tool và xem output trong một giao diện.")

    model, live_updates = _sidebar()
    agents = load_agent_blueprints()

    tab_run, tab_agents, tab_tools, tab_outputs, tab_trace = st.tabs(
        ["Chạy task", "Quản lý agent", "Tool", "Kết quả", "Trace"]
    )

    with tab_run:
        _run_tab(model, live_updates, agents)
    with tab_agents:
        _agents_tab(model, agents)
    with tab_tools:
        _tools_tab()
    with tab_outputs:
        _outputs_tab()
    with tab_trace:
        _trace_tab()


if __name__ == "__main__":
    main()
