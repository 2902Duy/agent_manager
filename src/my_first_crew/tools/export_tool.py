import csv
import json
import re
from pathlib import Path
from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from my_first_crew.output_manager import OUTPUT_DIR, PROJECT_ROOT


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower()).strip("_")
    return slug or "output"


def save_rows_csv(rows_json: str, filename: str = "data_export.csv") -> str:
    try:
        payload = json.loads(rows_json)
    except json.JSONDecodeError as error:
        return json.dumps({"ok": False, "error": f"JSON không hợp lệ: {error}"}, ensure_ascii=False, indent=2)

    rows = payload.get("rows", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        return json.dumps({"ok": False, "error": "Không có dữ liệu rows để lưu CSV."}, ensure_ascii=False, indent=2)
    if not all(isinstance(row, dict) for row in rows):
        return json.dumps({"ok": False, "error": "Rows phải là list object/dict."}, ensure_ascii=False, indent=2)

    OUTPUT_DIR.mkdir(exist_ok=True)
    safe_name = _slugify(Path(filename).stem) + ".csv"
    path = OUTPUT_DIR / safe_name

    columns: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in columns:
                columns.append(str(key))

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return json.dumps(
        {
            "ok": True,
            "message": "Đã lưu CSV.",
            "path": str(path),
            "relative_path": str(path.relative_to(PROJECT_ROOT)),
            "rows": len(rows),
            "columns": columns,
        },
        ensure_ascii=False,
        indent=2,
    )


class SaveRowsCSVInput(BaseModel):
    """Input schema for SaveRowsCSVTool."""

    rows_json: str = Field(..., description="JSON list hoặc object có field rows chứa dữ liệu cần lưu.")
    filename: str = Field("data_export.csv", description="Tên file CSV trong thư mục output.")


class SaveRowsCSVTool(BaseTool):
    name: str = "save_rows_csv"
    description: str = (
        "Lưu dữ liệu JSON rows thành file CSV thật trong thư mục output/. "
        "Dùng sau sqlserver_query khi user yêu cầu lưu hoặc xuất dữ liệu."
    )
    args_schema: Type[BaseModel] = SaveRowsCSVInput

    def _run(self, rows_json: str, filename: str = "data_export.csv") -> str:
        return save_rows_csv(rows_json, filename)
