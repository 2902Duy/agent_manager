import json
from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from my_first_crew.data_connections.sqlserver_connection import (
    connect,
    load_sqlserver_profile,
    redacted_profile,
)
from my_first_crew.security.query_validator import safe_identifier, validate_readonly_query


def test_sqlserver_connection() -> str:
    profile = load_sqlserver_profile()
    try:
        with connect(profile) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT DB_NAME() AS database_name")
            row = cursor.fetchone()
        return json.dumps(
            {"ok": True, "profile": redacted_profile(profile), "database_name": row[0] if row else ""},
            ensure_ascii=False,
            indent=2,
        )
    except Exception as error:
        return json.dumps(
            {"ok": False, "profile": redacted_profile(profile), "error": str(error)},
            ensure_ascii=False,
            indent=2,
        )


def sqlserver_schema(schema_name: str = "dbo") -> str:
    sql = """
    SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = ?
    ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
    """
    try:
        with connect() as connection:
            rows = connection.cursor().execute(sql, schema_name).fetchall()
    except Exception as error:
        return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False, indent=2)

    payload = [
        {
            "schema": row.TABLE_SCHEMA,
            "table": row.TABLE_NAME,
            "column": row.COLUMN_NAME,
            "type": row.DATA_TYPE,
            "nullable": row.IS_NULLABLE,
        }
        for row in rows
    ]
    return json.dumps({"ok": True, "columns": payload}, ensure_ascii=False, indent=2)


def sqlserver_query(sql: str) -> str:
    validation = validate_readonly_query(sql)
    if not validation.ok:
        return json.dumps({"ok": False, "error": validation.reason}, ensure_ascii=False, indent=2)

    profile = load_sqlserver_profile()
    try:
        with connect(profile) as connection:
            cursor = connection.cursor()
            cursor.execute(validation.sql)
            columns = [column[0] for column in cursor.description or []]
            rows = cursor.fetchmany(profile.max_rows)
    except Exception as error:
        return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False, indent=2)

    payload: list[dict[str, Any]] = [dict(zip(columns, row)) for row in rows]
    return json.dumps({"ok": True, "rows": payload, "max_rows": profile.max_rows}, ensure_ascii=False, indent=2, default=str)


def sqlserver_sample_rows(table_name: str, schema_name: str = "dbo", limit: int = 10) -> str:
    if not safe_identifier(table_name) or not safe_identifier(schema_name):
        return json.dumps({"ok": False, "error": "Tên schema/table không hợp lệ."}, ensure_ascii=False, indent=2)
    safe_limit = max(1, min(int(limit), 50))
    return sqlserver_query(f"SELECT TOP ({safe_limit}) * FROM [{schema_name}].[{table_name}]")


class SQLServerSchemaInput(BaseModel):
    schema_name: str = Field("dbo", description="Schema cần đọc, mặc định dbo.")


class SQLServerQueryInput(BaseModel):
    sql: str = Field(..., description="Câu SQL SELECT/WITH read-only.")


class SQLServerSampleRowsInput(BaseModel):
    table_name: str = Field(..., description="Tên bảng cần xem mẫu.")
    schema_name: str = Field("dbo", description="Schema của bảng.")
    limit: int = Field(10, description="Số dòng mẫu, tối đa 50.")


class SQLServerTestConnectionTool(BaseTool):
    name: str = "sqlserver_test_connection"
    description: str = "Kiểm tra kết nối SQL Server bằng biến môi trường, không hiển thị secret."

    def _run(self) -> str:
        return test_sqlserver_connection()


class SQLServerSchemaTool(BaseTool):
    name: str = "sqlserver_schema"
    description: str = "Đọc schema/column của SQL Server thật."
    args_schema: Type[BaseModel] = SQLServerSchemaInput

    def _run(self, schema_name: str = "dbo") -> str:
        return sqlserver_schema(schema_name)


class SQLServerQueryTool(BaseTool):
    name: str = "sqlserver_query"
    description: str = "Chạy SQL SELECT/WITH read-only trên SQL Server thật."
    args_schema: Type[BaseModel] = SQLServerQueryInput

    def _run(self, sql: str) -> str:
        return sqlserver_query(sql)


class SQLServerSampleRowsTool(BaseTool):
    name: str = "sqlserver_sample_rows"
    description: str = "Lấy vài dòng mẫu từ bảng SQL Server đã chọn."
    args_schema: Type[BaseModel] = SQLServerSampleRowsInput

    def _run(self, table_name: str, schema_name: str = "dbo", limit: int = 10) -> str:
        return sqlserver_sample_rows(table_name=table_name, schema_name=schema_name, limit=limit)
