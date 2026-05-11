"""Web search tools using Tavily API."""

from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import tool


@tool
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information using Tavily API.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        Search results as a formatted string.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return (
            "Error: TAVILY_API_KEY not set. "
            "Please set it in the .env file to enable web search."
        )

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=max_results)
        results = response.get("results", [])
        if not results:
            return "No web results found."
        formatted = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "N/A")
            url = r.get("url", "N/A")
            content = r.get("content", "N/A")[:300]
            formatted.append(f"[{i}] {title}\n    URL: {url}\n    {content}")
        return "\n\n".join(formatted)
    except ImportError:
        return (
            "Error: tavily-python is not installed. "
            "Run: pip install tavily-python"
        )
    except Exception as e:
        return f"Web search error: {e}"


def get_web_tools() -> list[Any]:
    """Return the list of web search tools."""
    return [search_web]
