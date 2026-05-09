"""FastAPI backend for Agent Manager – replaces Streamlit UI."""

import sys
from pathlib import Path

# Ensure the project src is importable
_project_root = Path(__file__).resolve().parents[1]
_src_dir = _project_root / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import agents, crew, outputs, tools, trace

app = FastAPI(title="Agent Manager API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(crew.router, prefix="/api/crew", tags=["crew"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(outputs.router, prefix="/api/outputs", tags=["outputs"])
app.include_router(trace.router, prefix="/api/trace", tags=["trace"])

# Serve output files
output_dir = _project_root / "output"
output_dir.mkdir(exist_ok=True)
app.mount("/api/files", StaticFiles(directory=str(output_dir)), name="output_files")


@app.get("/api/health")
def health():
    return {"status": "ok"}
