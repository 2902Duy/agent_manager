"""Crew execution endpoints."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from my_first_crew.agent_registry import load_agent_blueprints
from my_first_crew.crew_builder import build_managed_crew
from my_first_crew.execution_monitor import CrewExecutionMonitor
from my_first_crew.models import DEFAULT_MODEL

router = APIRouter()

# In-memory session store
_sessions: dict[str, dict[str, Any]] = {}
# Only one crew runs at a time to avoid global event bus cross-talk
_crew_lock = threading.Lock()


class RunRequest(BaseModel):
    task: str
    model: str = DEFAULT_MODEL
    auto_suggest_agents: bool = False
    data_source: str | None = None


class RunResponse(BaseModel):
    session_id: str
    status: str
    result: str | None = None
    error: str | None = None


class SessionInfo(BaseModel):
    session_id: str
    status: str
    task: str
    model: str
    started_at: str
    events_count: int


def _run_in_thread(session_id: str, task: str, model: str) -> None:
    from crewai.events.event_bus import crewai_event_bus

    monitor = _sessions[session_id]["monitor"]
    with _crew_lock:
        try:
            monitor.setup_listeners(crewai_event_bus)
            blueprints = load_agent_blueprints()
            crew = build_managed_crew(user_task=task, blueprints=blueprints, model=model)
            result = crew.kickoff()
            monitor.status = "completed"
            _sessions[session_id]["result"] = str(result)
        except Exception as exc:
            monitor.status = "failed"
            _sessions[session_id]["error"] = str(exc)
            monitor._record("error", f"Lỗi: {exc}")
        finally:
            monitor.close()


@router.post("/run")
def run_crew(req: RunRequest) -> RunResponse:
    session_id = str(uuid.uuid4())[:8]
    monitor = CrewExecutionMonitor()
    monitor.status = "running"
    monitor._record("crew", "Crew bắt đầu chạy...")

    _sessions[session_id] = {
        "monitor": monitor,
        "task": req.task,
        "model": req.model,
        "result": None,
        "error": None,
        "started_at": datetime.now().isoformat(),
    }

    thread = threading.Thread(
        target=_run_in_thread,
        args=(session_id, req.task, req.model),
        daemon=True,
    )
    thread.start()

    return RunResponse(session_id=session_id, status="running")


@router.get("/status/{session_id}")
def get_status(session_id: str) -> dict:
    session = _sessions.get(session_id)
    if not session:
        return {"session_id": session_id, "status": "not_found"}
    monitor: CrewExecutionMonitor = session["monitor"]
    snap = monitor.snapshot()
    return {
        "session_id": session_id,
        "status": snap["status"],
        "current_agent": snap["current_agent"],
        "current_task": snap["current_task"],
        "delegated_agent": snap["delegated_agent"],
        "events": snap["events"],
        "result": session.get("result"),
        "error": session.get("error"),
    }


@router.get("/sessions")
def list_sessions() -> list[dict]:
    result = []
    for sid, session in _sessions.items():
        monitor: CrewExecutionMonitor = session["monitor"]
        result.append({
            "session_id": sid,
            "status": monitor.status,
            "task": session["task"],
            "model": session["model"],
            "started_at": session["started_at"],
            "events_count": len(monitor.events),
        })
    return result
