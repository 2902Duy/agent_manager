from dataclasses import dataclass, field
import unicodedata

from pydantic import BaseModel, Field


import os

DEFAULT_MODEL = os.getenv("MODEL", "google/gemini-2.0-flash")


@dataclass
class AgentBlueprint:
    name: str
    role: str
    goal: str
    backstory: str
    llm: str = DEFAULT_MODEL
    tool_groups: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    tools_override: list[str] = field(default_factory=list)
    enabled: bool = True
    risk_level: str = "low"
    use_rag: bool = False
    use_sql: bool = False
    use_chart: bool = False


class DesignedAgent(BaseModel):
    name: str = Field(..., description="Tên kỹ thuật snake_case, ví dụ: dashboard_designer")
    role: str = Field(..., description="Vai trò agent bằng tiếng Việt")
    goal: str = Field(..., description="Mục tiêu cụ thể của agent")
    backstory: str = Field(..., description="Bối cảnh/năng lực của agent")
    tool_groups: list[str] = Field(default_factory=list, description="Nhóm tool đề xuất, ví dụ: sqlserver-readonly, charting")
    skills: list[str] = Field(default_factory=list, description="Skill đề xuất, ví dụ: sql-analysis, chart-selection")
    use_rag: bool = Field(False, description="Có cần dùng rag_search đọc data.txt không")
    use_sql: bool = Field(False, description="Có cần dùng tool SQL read-only không")
    use_chart: bool = Field(False, description="Có cần dùng chart tool tạo biểu đồ không")


class AgentDesignResult(BaseModel):
    needs_new_agents: bool
    reason: str
    agents: list[DesignedAgent] = Field(default_factory=list)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def agent_key(value: str) -> str:
    normalized = normalize_text(value)
    normalized = "".join(char if char.isalnum() else "_" for char in normalized)
    normalized = "_".join(part for part in normalized.split("_") if part)
    return normalized or "custom_agent"
