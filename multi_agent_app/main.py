"""FastAPI entry point for the Multi-Agent system."""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from multi_agent_app.core.utils import extract_text

load_dotenv()

# ── Global state ────────────────────────────────────────────────────────
_graph = None
_checkpointer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the graph once at startup and tear down on shutdown."""
    global _graph, _checkpointer
    from multi_agent_app.core.graph import build_graph

    _graph, _checkpointer = build_graph()
    yield
    # Cleanup
    _checkpointer = None
    _graph = None


app = FastAPI(
    title="Multi-Agent API",
    description="LangGraph + Gemini multi-agent system with HITL support",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response schemas ──────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    thread_id: str
    response: str
    status: str
    proposed_action: str | None = None


class ApproveRequest(BaseModel):
    thread_id: str
    approved: bool


class IngestRequest(BaseModel):
    file_path: str
    file_type: str = "txt"


class IngestResponse(BaseModel):
    chunks_added: int
    file_path: str


# ── Endpoints ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message and get the multi-agent response."""
    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialised")

    thread_id = req.thread_id or str(uuid.uuid4())
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "messages": [HumanMessage(content=req.message)],
        "context": {},
        "proposed_action": None,
        "next_agent": None,
        "human_approved": None,
        "iteration_count": 0,
    }

    try:
        result = _graph.invoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    messages = result.get("messages", [])
    last_msg = extract_text(messages[-1].content) if messages else "No response."
    proposed = result.get("proposed_action")

    status = "awaiting_approval" if proposed else "completed"

    return ChatResponse(
        thread_id=thread_id,
        response=last_msg,
        status=status,
        proposed_action=proposed,
    )


@app.post("/approve", response_model=ChatResponse)
async def approve(req: ApproveRequest):
    """Approve or reject the proposed SQL action and resume the graph."""
    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialised")

    config: dict[str, Any] = {"configurable": {"thread_id": req.thread_id}}

    try:
        _graph.update_state(config, {"human_approved": req.approved})
        result = _graph.invoke(None, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    messages = result.get("messages", [])
    last_msg = extract_text(messages[-1].content) if messages else "No response."
    proposed = result.get("proposed_action")

    status = "awaiting_approval" if proposed else "completed"

    return ChatResponse(
        thread_id=req.thread_id,
        response=last_msg,
        status=status,
        proposed_action=proposed,
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(req: IngestRequest):
    """Ingest a document into the RAG vector store."""
    from multi_agent_app.tools.rag_tools import ingest_pdf, ingest_text_file

    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {req.file_path}")

    try:
        if req.file_type == "pdf":
            count = ingest_pdf(req.file_path)
        else:
            count = ingest_text_file(req.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return IngestResponse(chunks_added=count, file_path=req.file_path)


@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """Get the current state of a conversation thread."""
    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialised")

    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    try:
        state = _graph.get_state(config)
        values = state.values
        messages = [
            {"role": type(m).__name__, "content": m.content}
            for m in values.get("messages", [])
        ]
        return {
            "thread_id": thread_id,
            "messages": messages,
            "context": values.get("context", {}),
            "proposed_action": values.get("proposed_action"),
            "next_agent": values.get("next_agent"),
            "iteration_count": values.get("iteration_count", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── CLI runner ──────────────────────────────────────────────────────────
def run_cli():
    """Simple CLI loop for testing the multi-agent system."""
    from multi_agent_app.core.graph import build_graph

    graph, _ = build_graph()
    thread_id = str(uuid.uuid4())
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

    print("=" * 60)
    print("  Multi-Agent System (LangGraph + Gemini)")
    print("  Type 'quit' to exit, 'approve' / 'reject' for HITL")
    print("=" * 60)

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break

        if user_input.lower() == "approve":
            result = graph.invoke({"human_approved": True}, config=config)
        elif user_input.lower() == "reject":
            result = graph.invoke({"human_approved": False}, config=config)
        else:
            result = graph.invoke(
                {
                    "messages": [HumanMessage(content=user_input)],
                    "context": {},
                    "proposed_action": None,
                    "next_agent": None,
                    "human_approved": None,
                    "iteration_count": 0,
                },
                config=config,
            )

        messages = result.get("messages", [])
        if messages:
            print(f"\nAssistant: {messages[-1].content}")

        proposed = result.get("proposed_action")
        if proposed:
            print(f"\n⚠ Proposed SQL action:\n{proposed}")
            print("Type 'approve' or 'reject' to continue.")


if __name__ == "__main__":
    import sys

    if "--cli" in sys.argv:
        run_cli()
    else:
        import uvicorn

        uvicorn.run(
            "multi_agent_app.main:app",
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
            reload=True,
        )
