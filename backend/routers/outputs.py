"""Output file management endpoints."""

import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"


@router.get("")
def list_outputs() -> list[dict]:
    OUTPUT_DIR.mkdir(exist_ok=True)
    files = []
    for entry in sorted(OUTPUT_DIR.iterdir()):
        if entry.is_file() and not entry.name.startswith("."):
            stat = entry.stat()
            ext = entry.suffix.lstrip(".").lower()
            files.append({
                "filename": entry.name,
                "size": stat.st_size,
                "type": ext,
                "modified": stat.st_mtime,
            })
    return files


@router.get("/{filename}")
def get_output(filename: str):
    filepath = OUTPUT_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        return {"error": "File not found"}
    return FileResponse(str(filepath))
