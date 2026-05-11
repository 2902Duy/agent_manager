"""Utility helpers for the multi-agent system."""

from __future__ import annotations

from typing import Any


def extract_text(content: Any) -> str:
    """Extract plain text from LLM response content.

    Gemini 3.x models with thinking enabled return content as a list of parts
    rather than a plain string. This helper normalises both cases.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                if "text" in part:
                    text_parts.append(part["text"])
        return "\n".join(text_parts)
    return str(content)
