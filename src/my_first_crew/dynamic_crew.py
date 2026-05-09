"""Compatibility facade for the standardized modules.

New code should import from:
- my_first_crew.models
- my_first_crew.agent_registry
- my_first_crew.agent_designer
- my_first_crew.crew_builder
- my_first_crew.output_manager
"""

from my_first_crew.agent_designer import suggest_missing_agents, task_needs_chart
from my_first_crew.agent_registry import (
    AGENTS_YAML,
    DEFAULT_AGENT_BLUEPRINTS,
    load_agent_blueprints,
    load_all_agent_blueprints,
    save_agent_blueprints,
)
from my_first_crew.crew_builder import (
    build_agents,
    build_managed_crew,
    kickoff_managed_task,
    make_llm,
    recommend_agent,
)
from my_first_crew.models import AgentBlueprint, AgentDesignResult, DEFAULT_MODEL, DesignedAgent


__all__ = [
    "AGENTS_YAML",
    "AgentBlueprint",
    "AgentDesignResult",
    "DEFAULT_AGENT_BLUEPRINTS",
    "DEFAULT_MODEL",
    "DesignedAgent",
    "build_agents",
    "build_managed_crew",
    "kickoff_managed_task",
    "load_agent_blueprints",
    "load_all_agent_blueprints",
    "make_llm",
    "recommend_agent",
    "save_agent_blueprints",
    "suggest_missing_agents",
    "task_needs_chart",
]
