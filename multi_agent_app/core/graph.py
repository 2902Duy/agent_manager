"""LangGraph definition – nodes, edges, conditional routing, and checkpointing."""

from __future__ import annotations

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from multi_agent_app.agents.db_reader_agent import db_reader_agent_node
from multi_agent_app.agents.db_writer_agent import (
    db_writer_agent_node,
    execute_approved_action,
)
from multi_agent_app.agents.final_agent import final_agent_node
from multi_agent_app.agents.rag_agent import rag_agent_node
from multi_agent_app.agents.web_agent import web_agent_node
from multi_agent_app.core.state import AgentState
from multi_agent_app.core.supervisor import supervisor_node


def _route_supervisor(state: AgentState) -> str:
    """Conditional edge: pick the next node based on supervisor decision."""
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "FINISH":
        return END
    return next_agent


def _route_after_human_review(state: AgentState) -> str:
    """After the HITL interrupt, decide whether to execute or reject."""
    if state.get("human_approved"):
        return "execute_approved_action"
    return "supervisor"


def build_graph(checkpoint_db: str = "multi_agent_app/db/sqlite_checkpoints.db"):
    """Construct and compile the LangGraph with SQLite checkpointing.

    Parameters
    ----------
    checkpoint_db:
        Path to the SQLite database used for LangGraph checkpointing
        (enables Human-in-the-Loop resume).

    Returns
    -------
    tuple[CompiledGraph, SqliteSaver]
        The compiled graph and the checkpointer (keep a reference to close it).
    """
    workflow = StateGraph(AgentState)

    # -- Nodes --
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("rag_agent", rag_agent_node)
    workflow.add_node("db_reader_agent", db_reader_agent_node)
    workflow.add_node("db_writer_agent", db_writer_agent_node)
    workflow.add_node("web_agent", web_agent_node)
    workflow.add_node("final_agent", final_agent_node)
    workflow.add_node("execute_approved_action", execute_approved_action)

    # -- Entry point --
    workflow.set_entry_point("supervisor")

    # -- Conditional edges from supervisor --
    workflow.add_conditional_edges(
        "supervisor",
        _route_supervisor,
        {
            "rag_agent": "rag_agent",
            "db_reader_agent": "db_reader_agent",
            "db_writer_agent": "db_writer_agent",
            "web_agent": "web_agent",
            "final_agent": "final_agent",
            END: END,
        },
    )

    # -- Worker agents always return to supervisor --
    workflow.add_edge("rag_agent", "supervisor")
    workflow.add_edge("db_reader_agent", "supervisor")
    workflow.add_edge("web_agent", "supervisor")

    # -- DB Writer: interrupt for human approval, then route --
    workflow.add_conditional_edges(
        "db_writer_agent",
        _route_after_human_review,
        {
            "execute_approved_action": "execute_approved_action",
            "supervisor": "supervisor",
        },
    )
    workflow.add_edge("execute_approved_action", "supervisor")

    # -- Final agent ends the graph --
    workflow.add_edge("final_agent", END)

    # -- Compile with checkpointer --
    checkpointer = SqliteSaver.from_conn_string(checkpoint_db)
    graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["db_writer_agent"],
    )

    return graph, checkpointer
