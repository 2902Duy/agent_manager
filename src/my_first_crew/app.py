#!/usr/bin/env python
import threading
import time
import warnings

import streamlit as st

from my_first_crew.encoding_setup import force_utf8
from my_first_crew.crew import MyFirstCrew
from my_first_crew.dynamic_crew import DEFAULT_MODEL
from my_first_crew.execution_monitor import CrewExecutionMonitor
from my_first_crew.agent_registry import load_agent_blueprints
from crewai.events.event_bus import crewai_event_bus

force_utf8()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

st.set_page_config(
    page_title="Agent Manager",
    page_icon="🤖",
    layout="wide",
)

KIND_ICONS = {
    "crew": "🚀",
    "task": "📋",
    "agent": "🤖",
    "tool": "🔧",
    "delegation": "👥",
    "error": "❌",
}
KIND_COLORS = {
    "crew": "blue",
    "task": "orange",
    "agent": "violet",
    "tool": "green",
    "delegation": "cyan",
    "error": "red",
}


def run_crew_in_thread(user_task: str, model: str, monitor: CrewExecutionMonitor) -> None:
    try:
        monitor.setup_listeners(crewai_event_bus)
        MyFirstCrew().crew(user_task=user_task, model=model).kickoff()
    except Exception as e:
        monitor.status = "failed"
        monitor._record("error", f"Lỗi: {e}")
    finally:
        monitor.close()


def render_status_card(status: str) -> None:
    status_map = {
        "idle": ("⏸️", "gray"),
        "running": ("🔄", "orange"),
        "completed": ("✅", "green"),
        "failed": ("❌", "red"),
    }
    icon, color = status_map.get(status, ("❓", "gray"))
    st.markdown(
        f"<div style='padding:10px;border-radius:8px;background:{color}20;border:1px solid {color}40'>"
        f"<span style='font-size:24px'>{icon}</span> "
        f"<span style='font-weight:bold;color:{color}'>{status.upper()}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


st.title("🤖 Agent Manager")
st.caption("Multi-agent execution dashboard with real-time flow visualization")

col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("Trạng thái")
    status_placeholder = st.empty()
    agent_placeholder = st.empty()
    deleg_placeholder = st.empty()
    task_placeholder = st.empty()

with col1:
    st.subheader("Câu hỏi")
    user_task = st.text_area(
        "Nhập câu hỏi của bạn:",
        value="Giải thích RAG là gì và cách hoạt động?",
        height=80,
        label_visibility="collapsed",
    )

    model_options = {
        "Gemini 3.1 Flash Lite": "google/gemini-3.1-flash-lite",
        "Gemini 2.0 Flash Lite": "google/gemini-2.0-flash-lite",
        "Gemini 2.0 Flash (free)": "google/gemini-2.0-flash",
        "Ollama (local - llama3.1)": "ollama/llama3.1",
        "Groq (free)": "groq/llama-3.1-8b-instant",
    }
    selected_model_label = st.selectbox("Model:", list(model_options.keys()), index=0)
    model = model_options[selected_model_label]

    run_btn = st.button("▶️ Chạy", type="primary", use_container_width=True)

if "monitor" not in st.session_state:
    st.session_state.monitor = CrewExecutionMonitor()
    st.session_state.running = False
    st.session_state.blueprints = list(load_agent_blueprints())

st.divider()

col_left, col_right = st.columns([2, 1])

with col_right:
    st.subheader("👤 Danh sách Agent")
    bp_placeholder = st.empty()
    with bp_placeholder.container():
        for bp in st.session_state.blueprints:
            with st.expander(bp.role, expanded=False):
                st.caption(f"**Mục tiêu:** {bp.goal}")
                st.caption(f"**Tool groups:** {', '.join(bp.tool_groups) or 'none'}")
                st.caption(f"**Skills:** {', '.join(bp.skills) or 'none'}")

with col_left:
    st.subheader("📊 Luồng xử lý")
    log_container = st.container()
    log_placeholder = log_container.empty()


def render_events(events: list[dict]) -> None:
    lines = []
    for ev in reversed(events):
        icon = KIND_ICONS.get(ev["kind"], "•")
        color = KIND_COLORS.get(ev["kind"], "gray")
        msg = ev["message"]
        lines.append(
            f"<div style='padding:4px 8px;margin:2px 0;border-left:3px solid {color};"
            f"background:{color}08;border-radius:4px;font-size:14px'>"
            f"<span style='color:{color}'>{icon}</span> "
            f"<span style='color:#888;font-size:12px'>{ev.get('time','')}</span> "
            f"<span>{msg}</span>"
            f"</div>"
        )
    log_placeholder.markdown("\n".join(lines), unsafe_allow_html=True)


if run_btn and not st.session_state.running:
    if not user_task.strip():
        st.warning("Vui lòng nhập câu hỏi.")
    else:
        st.session_state.running = True
        st.session_state.monitor = CrewExecutionMonitor()
        st.session_state.monitor.status = "running"
        st.session_state.monitor._record("crew", "Crew bắt đầu chạy...")

        thread = threading.Thread(
            target=run_crew_in_thread,
            args=(user_task, model, st.session_state.monitor),
            daemon=True,
        )
        thread.start()

if st.session_state.running:
    with status_placeholder.container():
        render_status_card(st.session_state.monitor.status)

    snap = st.session_state.monitor.snapshot()
    agent_placeholder.markdown(
        f"<div style='padding:8px;border-radius:6px;background:#7c3aed15;border:1px solid #7c3aed30'>"
        f"🤖 **Agent:** {snap['current_agent'] or '—'}</div>",
        unsafe_allow_html=True,
    )
    deleg_placeholder.markdown(
        f"<div style='padding:8px;border-radius:6px;background:#06b6d415;border:1px solid #06b6d430'>"
        f"👥 **Được giao cho:** {snap['delegated_agent'] or '—'}</div>",
        unsafe_allow_html=True,
    )
    task_placeholder.markdown(
        f"<div style='padding:8px;border-radius:6px;background:#f59e0b15;border:1px solid #f59e0b30'>"
        f"📋 **Task:** {snap['current_task'][:100] or '—'}</div>",
        unsafe_allow_html=True,
    )
    render_events(snap["events"])

    if st.session_state.monitor.status in ("completed", "failed"):
        st.session_state.running = False

        if st.session_state.monitor.status == "completed":
            st.success("✅ Crew hoàn tất!")
            try:
                with open("answer.md", encoding="utf-8") as f:
                    st.markdown("### Kết quả:")
                    st.markdown(f.read())
            except FileNotFoundError:
                pass

        if st.button("🔄 Chạy lại", use_container_width=True):
            st.session_state.monitor = CrewExecutionMonitor()
            st.rerun()
    else:
        time.sleep(0.5)
        st.rerun()
else:
    with status_placeholder.container():
        render_status_card(st.session_state.monitor.status)
    snap = st.session_state.monitor.snapshot()
    render_events(snap["events"])
