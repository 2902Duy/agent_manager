from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Any, Callable

from crewai.events import (
    AgentExecutionCompletedEvent,
    AgentExecutionErrorEvent,
    AgentExecutionStartedEvent,
    BaseEventListener,
    CrewKickoffCompletedEvent,
    CrewKickoffFailedEvent,
    CrewKickoffStartedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskStartedEvent,
    ToolUsageFinishedEvent,
    ToolUsageStartedEvent,
)
from crewai.events.event_bus import crewai_event_bus


def _shorten(value: Any, limit: int = 220) -> str:
    text = str(value or "").replace("\n", " ").strip()
    return text if len(text) <= limit else f"{text[:limit]}..."


def _agent_role(agent: Any) -> str:
    return str(getattr(agent, "role", "") or "Agent chưa xác định").strip()


def _task_title(task: Any) -> str:
    name = getattr(task, "name", None)
    description = getattr(task, "description", None)
    return _shorten(name or description or "Task chưa đặt tên", 180)


def _format_tool_args(tool_args: Any) -> str:
    if isinstance(tool_args, dict):
        parts = []
        for key in ("coworker", "task", "query", "context"):
            if key in tool_args:
                parts.append(f"{key}: {_shorten(tool_args[key], 120)}")
        if parts:
            return "; ".join(parts)
    return _shorten(tool_args)


def _delegated_agent(tool_args: Any) -> str | None:
    if isinstance(tool_args, dict):
        coworker = tool_args.get("coworker")
        return str(coworker).strip() if coworker else None
    text = str(tool_args or "")
    if "coworker" in text.lower():
        return _shorten(text, 120)
    return None


class CrewExecutionMonitor(BaseEventListener):
    """Collects CrewAI execution events for UI display."""

    def __init__(self, initial_delegated_agent: str = "") -> None:
        self._lock = Lock()
        self._handlers: list[tuple[type[Any], Callable[..., Any]]] = []
        self.events: list[dict[str, str]] = []
        self.current_agent = ""
        self.current_task = ""
        self.delegated_agent = initial_delegated_agent
        self.status = "idle"
        super().__init__()

    def _record(self, kind: str, message: str, **fields: str) -> None:
        with self._lock:
            self.events.append(
                {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "kind": kind,
                    "message": message,
                    **fields,
                }
            )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "status": self.status,
                "current_agent": self.current_agent,
                "current_task": self.current_task,
                "delegated_agent": self.delegated_agent,
                "events": list(self.events),
            }

    def close(self) -> None:
        for event_type, handler in self._handlers:
            crewai_event_bus.off(event_type, handler)
        self._handlers.clear()

    def setup_listeners(self, event_bus) -> None:
        def listen(event_type):
            def decorator(handler):
                event_bus.on(event_type)(handler)
                self._handlers.append((event_type, handler))
                return handler

            return decorator

        @listen(CrewKickoffStartedEvent)
        def on_crew_started(source, event):
            self.status = "running"
            self._record("crew", "Crew bắt đầu chạy")

        @listen(CrewKickoffCompletedEvent)
        def on_crew_completed(source, event):
            self.status = "completed"
            self.current_agent = ""
            self.current_task = ""
            self._record("crew", "Crew đã hoàn tất")

        @listen(CrewKickoffFailedEvent)
        def on_crew_failed(source, event):
            self.status = "failed"
            self._record("error", f"Crew lỗi: {_shorten(getattr(event, 'error', ''))}")

        @listen(TaskStartedEvent)
        def on_task_started(source, event):
            task_name = _task_title(getattr(event, "task", None))
            self.current_task = task_name
            self._record("task", f"Task bắt đầu: {task_name}")

        @listen(TaskCompletedEvent)
        def on_task_completed(source, event):
            task_name = _task_title(getattr(event, "task", None))
            self._record("task", f"Task hoàn tất: {task_name}")

        @listen(TaskFailedEvent)
        def on_task_failed(source, event):
            task_name = _task_title(getattr(event, "task", None))
            self._record("error", f"Task lỗi: {task_name}", error=_shorten(getattr(event, "error", "")))

        @listen(AgentExecutionStartedEvent)
        def on_agent_started(source, event):
            role = _agent_role(getattr(event, "agent", None))
            task_name = _task_title(getattr(event, "task", None))
            self.current_agent = role
            self.current_task = task_name
            self._record("agent", f"Agent đang chạy: {role}", task=task_name)

        @listen(AgentExecutionCompletedEvent)
        def on_agent_completed(source, event):
            role = _agent_role(getattr(event, "agent", None))
            self._record("agent", f"Agent hoàn tất: {role}", output=_shorten(getattr(event, "output", "")))

        @listen(AgentExecutionErrorEvent)
        def on_agent_error(source, event):
            role = _agent_role(getattr(event, "agent", None))
            self._record("error", f"Agent lỗi: {role}", error=_shorten(getattr(event, "error", "")))

        @listen(ToolUsageStartedEvent)
        def on_tool_started(source, event):
            tool_name = str(getattr(event, "tool_name", "tool"))
            tool_args = getattr(event, "tool_args", "")
            delegated = _delegated_agent(tool_args)
            if delegated:
                self.delegated_agent = delegated
                self._record("delegation", f"Manager giao việc cho: {delegated}")
            self._record(
                "tool",
                f"Tool bắt đầu: {tool_name}",
                agent=str(getattr(event, "agent_role", "") or ""),
                args=_format_tool_args(tool_args),
            )

        @listen(ToolUsageFinishedEvent)
        def on_tool_finished(source, event):
            tool_name = str(getattr(event, "tool_name", "tool"))
            self._record("tool", f"Tool hoàn tất: {tool_name}", output=_shorten(getattr(event, "output", "")))
