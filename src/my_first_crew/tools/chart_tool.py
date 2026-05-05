import json
import re
from pathlib import Path
from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[3]


OUTPUT_DIR = PROJECT_ROOT / "output"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower()).strip("_")
    return slug or "chart"


def create_bar_chart_from_rows(
    rows_json: str,
    x_column: str,
    y_column: str,
    title: str = "Biểu đồ dữ liệu",
) -> str:
    try:
        payload = json.loads(rows_json)
    except json.JSONDecodeError as error:
        return json.dumps({"ok": False, "error": f"JSON không hợp lệ: {error}"}, ensure_ascii=False, indent=2)

    rows = payload.get("rows", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        return json.dumps({"ok": False, "error": "Không có dữ liệu dạng list để vẽ biểu đồ."}, ensure_ascii=False, indent=2)

    labels: list[str] = []
    values: list[float] = []
    for row in rows:
        if not isinstance(row, dict) or x_column not in row or y_column not in row:
            continue
        labels.append("Không xác định" if row[x_column] is None else str(row[x_column]))
        try:
            values.append(float(row[y_column]))
        except (TypeError, ValueError):
            return json.dumps({"ok": False, "error": f"Cột {y_column} không phải số."}, ensure_ascii=False, indent=2)

    if not labels:
        return json.dumps({"ok": False, "error": "Không tìm thấy cột phù hợp trong dữ liệu."}, ensure_ascii=False, indent=2)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{_slugify(title)}.png"

    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars = ax.bar(labels, values, color="#0f766e")
    ax.set_title(title)
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    ax.bar_label(bars, labels=[f"{value:,.0f}" for value in values], padding=3)
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)

    return json.dumps(
        {
            "ok": True,
            "message": "Đã tạo biểu đồ cột.",
            "path": str(path),
            "relative_path": str(path.relative_to(PROJECT_ROOT)),
            "x_column": x_column,
            "y_column": y_column,
            "rows": rows,
        },
        ensure_ascii=False,
        indent=2,
    )

class BarChartInput(BaseModel):
    """Input schema for BarChartFromRowsTool."""

    rows_json: str = Field(..., description="JSON list hoặc object có field rows chứa dữ liệu.")
    x_column: str = Field(..., description="Tên cột dùng làm nhãn trục X.")
    y_column: str = Field(..., description="Tên cột số dùng làm giá trị trục Y.")
    title: str = Field("Biểu đồ dữ liệu", description="Tiêu đề biểu đồ.")


class BarChartFromRowsTool(BaseTool):
    name: str = "create_bar_chart"
    description: str = (
        "Tạo biểu đồ cột PNG từ dữ liệu JSON rows đã truy xuất. "
        "Dùng cho dữ liệu SQL Server hoặc dữ liệu bảng bất kỳ. Tool trả về JSON có path file thật."
    )
    args_schema: Type[BaseModel] = BarChartInput

    def _run(
        self,
        rows_json: str,
        x_column: str,
        y_column: str,
        title: str = "Biểu đồ dữ liệu",
    ) -> str:
        return create_bar_chart_from_rows(rows_json, x_column, y_column, title)
