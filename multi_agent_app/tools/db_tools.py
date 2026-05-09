"""Database tools using SQLAlchemy for reading and writing."""

from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_engine: Engine | None = None


def _get_engine() -> Engine:
    """Return a singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///multi_agent_app/db/sample.db")
        _engine = create_engine(db_url, echo=False)
    return _engine


@tool
def get_schema(table_name: str | None = None) -> str:
    """Get database schema information.

    Args:
        table_name: Specific table name, or None to list all tables.

    Returns:
        Schema description as a string.
    """
    engine = _get_engine()
    with engine.connect() as conn:
        if table_name:
            if engine.dialect.name == "sqlite":
                result = conn.execute(
                    text(f"PRAGMA table_info('{table_name}')")
                )
                rows = result.fetchall()
                if not rows:
                    return f"Table '{table_name}' not found."
                cols = [
                    f"  {r[1]} {r[2]}{'  PRIMARY KEY' if r[5] else ''}"
                    for r in rows
                ]
                return f"Table: {table_name}\n" + "\n".join(cols)
            else:
                result = conn.execute(
                    text(
                        "SELECT column_name, data_type "
                        "FROM information_schema.columns "
                        "WHERE table_name = :tbl"
                    ),
                    {"tbl": table_name},
                )
                rows = result.fetchall()
                if not rows:
                    return f"Table '{table_name}' not found."
                cols = [f"  {r[0]} {r[1]}" for r in rows]
                return f"Table: {table_name}\n" + "\n".join(cols)
        else:
            if engine.dialect.name == "sqlite":
                result = conn.execute(
                    text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' ORDER BY name"
                    )
                )
            else:
                result = conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                )
            tables = [r[0] for r in result.fetchall()]
            return "Tables: " + ", ".join(tables) if tables else "No tables found."


@tool
def query_database(sql: str) -> str:
    """Execute a read-only SQL SELECT query and return results.

    Args:
        sql: A SELECT SQL statement.

    Returns:
        Query results as a formatted string.
    """
    normalized = sql.strip().upper()
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE"]
    for keyword in forbidden:
        if normalized.startswith(keyword):
            return f"Error: '{keyword}' statements are not allowed. Use SELECT only."

    engine = _get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())
            if not rows:
                return "Query returned 0 rows."
            header = " | ".join(columns)
            separator = "-+-".join("-" * len(c) for c in columns)
            body = "\n".join(" | ".join(str(v) for v in row) for row in rows[:50])
            truncation = (
                f"\n... ({len(rows)} total rows, showing first 50)"
                if len(rows) > 50
                else f"\n({len(rows)} rows)"
            )
            return f"{header}\n{separator}\n{body}{truncation}"
    except Exception as e:
        return f"SQL Error: {e}"


@tool
def execute_sql(sql: str) -> str:
    """Execute an INSERT/UPDATE SQL statement (after human approval).

    Args:
        sql: An INSERT or UPDATE SQL statement.

    Returns:
        Execution result or error message.
    """
    normalized = sql.strip().upper()
    dangerous = ["DROP", "TRUNCATE", "ALTER"]
    for keyword in dangerous:
        if keyword in normalized:
            return f"Error: '{keyword}' operations are forbidden."

    engine = _get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            conn.commit()
            return f"Success: {result.rowcount} row(s) affected."
    except Exception as e:
        return f"SQL Error: {e}"


def get_db_tools() -> list[Any]:
    """Return the list of DB read tools."""
    return [get_schema, query_database]


def get_db_write_tools() -> list[Any]:
    """Return the list of DB write tools."""
    return [get_schema, execute_sql]
