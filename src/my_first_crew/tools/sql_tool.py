import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_FILE = PROJECT_ROOT / "sample.db"
SCHEMA_FILE = PROJECT_ROOT / "schema.sql"


def initialize_sample_db() -> None:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    with sqlite3.connect(DB_FILE) as connection:
        connection.executescript(schema)


def _connect() -> sqlite3.Connection:
    if not DB_FILE.exists():
        initialize_sample_db()
    connection = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _is_safe_select(sql: str) -> bool:
    compact = re.sub(r"\s+", " ", sql.strip().rstrip(";")).lower()
    blocked = ("insert ", "update ", "delete ", "drop ", "alter ", "create ", "replace ", "attach ", "pragma ")
    return compact.startswith("select ") and not any(token in compact for token in blocked)


def run_read_only_query(sql: str) -> str:
    if not _is_safe_select(sql):
        return "Chỉ cho phép truy vấn SELECT read-only trên sample.db."

    try:
        with _connect() as connection:
            rows = connection.execute(sql).fetchmany(50)
    except sqlite3.Error as error:
        return f"Lỗi SQL: {error}"

    payload: list[dict[str, Any]] = [dict(row) for row in rows]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def describe_schema() -> str:
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    create_blocks = re.findall(
        r"CREATE\s+TABLE\s+[\s\S]*?\);",
        schema,
        flags=re.IGNORECASE,
    )
    if not create_blocks:
        return "Không đọc được cấu trúc bảng từ schema.sql."

    return (
        "-- Schema mô tả cấu trúc bảng trong sample.db.\n"
        "-- Output này chỉ dùng để đọc cấu trúc, không chứa script khởi tạo hoặc dữ liệu seed.\n\n"
        + "\n\n".join(create_blocks)
    )


class SqlQueryInput(BaseModel):
    """Input schema for SqlQueryTool."""

    sql: str = Field(..., description="Câu SQL SELECT read-only để truy vấn sample.db.")


class SqlSchemaInput(BaseModel):
    """Input schema for SqlSchemaTool."""

    request: str = Field("schema", description="Yêu cầu mô tả schema SQL.")


class SqlQueryTool(BaseTool):
    name: str = "sql_query"
    description: str = (
        "Chạy câu SQL SELECT read-only trên sample.db và trả về tối đa 50 dòng dạng JSON."
    )
    args_schema: Type[BaseModel] = SqlQueryInput

    def _run(self, sql: str) -> str:
        return run_read_only_query(sql)


class SqlSchemaTool(BaseTool):
    name: str = "sql_schema"
    description: str = (
        "Đọc cấu trúc bảng read-only của sample.db. "
        "Tool chỉ trả cấu trúc CREATE TABLE đã lọc, không trả script khởi tạo hoặc dữ liệu seed."
    )
    args_schema: Type[BaseModel] = SqlSchemaInput

    def _run(self, request: str = "schema") -> str:
        return describe_schema()
