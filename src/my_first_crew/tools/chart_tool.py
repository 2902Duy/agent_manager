import json
import re
from pathlib import Path
from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from my_first_crew.tools.sql_tool import PROJECT_ROOT, run_read_only_query


OUTPUT_DIR = PROJECT_ROOT / "output"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower()).strip("_")
    return slug or "chart"


def create_revenue_chart(title: str = "Doanh thu theo khách hàng") -> str:
    sql = """
    SELECT c.name AS customer, SUM(oi.quantity * oi.unit_price) AS revenue
    FROM customers c
    JOIN orders o ON o.customer_id = c.id
    JOIN order_items oi ON oi.order_id = o.id
    WHERE o.status = 'paid'
    GROUP BY c.id, c.name
    ORDER BY revenue DESC
    """
    raw = run_read_only_query(sql)
    try:
        rows: list[dict[str, Any]] = json.loads(raw)
    except json.JSONDecodeError:
        return raw

    if not rows:
        return json.dumps(
            {
                "ok": False,
                "message": "Không có dữ liệu để vẽ biểu đồ.",
                "path": "",
                "relative_path": "",
                "data": [],
            },
            ensure_ascii=False,
            indent=2,
        )

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{_slugify(title)}.png"

    labels = [str(row["customer"]) for row in rows]
    values = [float(row["revenue"]) for row in rows]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(labels, values, color="#2563eb")
    ax.set_title(title)
    ax.set_xlabel("Khách hàng")
    ax.set_ylabel("Doanh thu đã thanh toán")
    ax.bar_label(bars, labels=[f"{value:,.0f}" for value in values], padding=3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)

    return json.dumps(
        {
            "ok": True,
            "message": "Đã tạo biểu đồ doanh thu.",
            "path": str(path),
            "relative_path": str(path.relative_to(PROJECT_ROOT)),
            "data": rows,
        },
        ensure_ascii=False,
        indent=2,
    )


class RevenueChartInput(BaseModel):
    """Input schema for RevenueChartTool."""

    title: str = Field("Doanh thu theo khách hàng", description="Tiêu đề biểu đồ doanh thu.")


class RevenueChartTool(BaseTool):
    name: str = "create_revenue_chart"
    description: str = (
        "Tạo biểu đồ PNG doanh thu đã thanh toán theo khách hàng từ sample.db. "
        "Dùng khi user yêu cầu vẽ biểu đồ doanh thu hoặc phân tích dữ liệu bán hàng. "
        "Tool trả về JSON có field path là đường dẫn file PNG thật; luôn dùng nguyên văn field path trong câu trả lời."
    )
    args_schema: Type[BaseModel] = RevenueChartInput

    def _run(self, title: str = "Doanh thu theo khách hàng") -> str:
        return create_revenue_chart(title)
