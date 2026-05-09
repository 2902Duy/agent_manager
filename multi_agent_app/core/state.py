"""State schema shared across all agents in the graph."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Typed state flowing through every node in the LangGraph.

    Attributes
    ----------
    messages:
        Full conversation history (human + AI). Uses the ``operator.add``
        reducer so each node *appends* rather than overwrites.
    context:
        Raw data collected by worker agents (RAG chunks, DB rows, web
        snippets).  Keys are agent names; values are their output strings.
    proposed_action:
        SQL statement drafted by ``db_writer_agent`` that awaits human
        approval before execution.
    next_agent:
        Routing decision made by the supervisor.  One of the worker agent
        names, ``"final_agent"``, or ``"FINISH"``.
    human_approved:
        Flag set by the HITL interrupt handler.  ``True`` means the
        proposed SQL may be executed; ``False`` means it was rejected.
    iteration_count:
        Tracks how many supervisor→worker round-trips have occurred to
        prevent infinite loops.
    """

    messages: Annotated[list[BaseMessage], operator.add]
    context: dict[str, Any]
    proposed_action: str | None
    next_agent: (
        Literal[
            "rag_agent",
            "db_reader_agent",
            "db_writer_agent",
            "web_agent",
            "final_agent",
            "FINISH",
        ]
        | None
    )
    human_approved: bool | None
    iteration_count: int
