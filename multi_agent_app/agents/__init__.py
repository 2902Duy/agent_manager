"""Agent definitions for the multi-agent system."""

from multi_agent_app.agents.rag_agent import rag_agent_node
from multi_agent_app.agents.db_reader_agent import db_reader_agent_node
from multi_agent_app.agents.db_writer_agent import db_writer_agent_node
from multi_agent_app.agents.web_agent import web_agent_node
from multi_agent_app.agents.final_agent import final_agent_node

__all__ = [
    "rag_agent_node",
    "db_reader_agent_node",
    "db_writer_agent_node",
    "web_agent_node",
    "final_agent_node",
]
