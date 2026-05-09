"""Tool registry endpoints."""

from fastapi import APIRouter

from my_first_crew.capability_registry import load_tool_groups

router = APIRouter()


TOOL_META = {
    "rag_search": {
        "name": "RAG Search",
        "group": "local-rag",
        "module": "my_first_crew.tools.rag_tool",
        "class": "RagSearchTool",
        "status": "implemented",
    },
    "sqlserver_test_connection": {
        "name": "SQL Server Test Connection",
        "group": "sqlserver-readonly",
        "module": "my_first_crew.tools.sqlserver_tool",
        "class": "SQLServerTestConnectionTool",
        "status": "implemented",
    },
    "sqlserver_schema": {
        "name": "SQL Server Schema",
        "group": "sqlserver-readonly",
        "module": "my_first_crew.tools.sqlserver_tool",
        "class": "SQLServerSchemaTool",
        "status": "implemented",
    },
    "sqlserver_query": {
        "name": "SQL Server Query",
        "group": "sqlserver-readonly",
        "module": "my_first_crew.tools.sqlserver_tool",
        "class": "SQLServerQueryTool",
        "status": "implemented",
    },
    "sqlserver_sample_rows": {
        "name": "SQL Server Sample Rows",
        "group": "sqlserver-readonly",
        "module": "my_first_crew.tools.sqlserver_tool",
        "class": "SQLServerSampleRowsTool",
        "status": "implemented",
    },
    "create_bar_chart": {
        "name": "Bar Chart Creator",
        "group": "charting",
        "module": "my_first_crew.tools.chart_tool",
        "class": "BarChartFromRowsTool",
        "status": "implemented",
    },
    "save_rows_csv": {
        "name": "Save Rows CSV",
        "group": "data-export",
        "module": "my_first_crew.tools.export_tool",
        "class": "SaveRowsCSVTool",
        "status": "implemented",
    },
}


@router.get("")
def list_tools() -> list[dict]:
    result = []
    for tool_id, meta in TOOL_META.items():
        result.append({"id": tool_id, **meta})
    return result


@router.get("/groups")
def list_tool_groups() -> dict:
    return load_tool_groups()
