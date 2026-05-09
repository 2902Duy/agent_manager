"""Agent CRUD endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from my_first_crew.agent_registry import (
    load_all_agent_blueprints,
    save_agent_blueprints,
)
from my_first_crew.models import AgentBlueprint

router = APIRouter()


class AgentResponse(BaseModel):
    name: str
    role: str
    goal: str
    backstory: str
    llm: str
    tool_groups: list[str]
    skills: list[str]
    tools_override: list[str]
    enabled: bool
    risk_level: str
    use_rag: bool
    use_sql: bool
    use_chart: bool


class AgentCreateUpdate(BaseModel):
    role: str
    goal: str
    backstory: str
    llm: str = ""
    tool_groups: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    tools_override: list[str] = Field(default_factory=list)
    enabled: bool = True
    risk_level: str = "low"
    use_rag: bool = False
    use_sql: bool = False
    use_chart: bool = False


def _bp_to_dict(bp: AgentBlueprint) -> dict:
    return AgentResponse(
        name=bp.name,
        role=bp.role,
        goal=bp.goal,
        backstory=bp.backstory,
        llm=bp.llm,
        tool_groups=bp.tool_groups,
        skills=bp.skills,
        tools_override=bp.tools_override,
        enabled=bp.enabled,
        risk_level=bp.risk_level,
        use_rag=bp.use_rag,
        use_sql=bp.use_sql,
        use_chart=bp.use_chart,
    ).model_dump()


@router.get("")
def list_agents() -> list[dict]:
    return [_bp_to_dict(bp) for bp in load_all_agent_blueprints()]


@router.get("/{name}")
def get_agent(name: str) -> dict:
    for bp in load_all_agent_blueprints():
        if bp.name == name:
            return _bp_to_dict(bp)
    raise HTTPException(404, f"Agent '{name}' not found")


@router.post("")
def create_agent(name: str, data: AgentCreateUpdate) -> dict:
    blueprints = list(load_all_agent_blueprints())
    if any(bp.name == name for bp in blueprints):
        raise HTTPException(409, f"Agent '{name}' already exists")
    bp = AgentBlueprint(name=name, **data.model_dump())
    blueprints.append(bp)
    save_agent_blueprints(blueprints)
    return _bp_to_dict(bp)


@router.put("/{name}")
def update_agent(name: str, data: AgentCreateUpdate) -> dict:
    blueprints = list(load_all_agent_blueprints())
    for i, bp in enumerate(blueprints):
        if bp.name == name:
            updated = AgentBlueprint(name=name, **data.model_dump())
            blueprints[i] = updated
            save_agent_blueprints(blueprints)
            return _bp_to_dict(updated)
    raise HTTPException(404, f"Agent '{name}' not found")


@router.delete("/{name}")
def delete_agent(name: str) -> dict:
    blueprints = list(load_all_agent_blueprints())
    new_list = [bp for bp in blueprints if bp.name != name]
    if len(new_list) == len(blueprints):
        raise HTTPException(404, f"Agent '{name}' not found")
    save_agent_blueprints(new_list)
    return {"deleted": name}


@router.patch("/{name}/toggle")
def toggle_agent(name: str) -> dict:
    blueprints = list(load_all_agent_blueprints())
    for i, bp in enumerate(blueprints):
        if bp.name == name:
            bp.enabled = not bp.enabled
            blueprints[i] = bp
            save_agent_blueprints(blueprints)
            return _bp_to_dict(bp)
    raise HTTPException(404, f"Agent '{name}' not found")
