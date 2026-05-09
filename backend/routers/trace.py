"""Trace / audit endpoints – reads from in-memory sessions."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


def _get_sessions() -> dict[str, Any]:
    from backend.routers.crew import _sessions
    return _sessions


@router.get("")
def list_traces() -> list[dict]:
    sessions = _get_sessions()
    result = []
    for sid, session in sessions.items():
        monitor = session["monitor"]
        snap = monitor.snapshot()
        tool_calls = sum(1 for ev in snap["events"] if ev["kind"] == "tool")
        result.append({
            "session_id": sid,
            "status": snap["status"],
            "total_events": len(snap["events"]),
            "total_tool_calls": tool_calls,
            "total_duration_ms": 0,
        })
    return result


@router.get("/{session_id}")
def get_trace(session_id: str) -> dict:
    sessions = _get_sessions()
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    monitor = session["monitor"]
    snap = monitor.snapshot()
    tool_calls = sum(1 for ev in snap["events"] if ev["kind"] == "tool")
    return {
        "session_id": session_id,
        "summary": {
            "session_id": session_id,
            "status": snap["status"],
            "total_events": len(snap["events"]),
            "total_tool_calls": tool_calls,
            "total_duration_ms": 0,
        },
        "timeline": [
            {
                "id": str(i),
                "timestamp": ev.get("time", ""),
                "event_type": ev["kind"],
                "agent_name": "",
                "tool_name": "",
                "message": ev["message"],
                "duration_ms": 0,
                "data": {},
            }
            for i, ev in enumerate(snap["events"])
        ],
    }
