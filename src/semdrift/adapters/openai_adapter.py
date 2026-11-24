"""Build OpenAI tool-selection requests from frozen study catalogs."""

from typing import Any

from ..prompt import SYSTEM


def build(model: dict[str, Any], tools: list[dict[str, Any]], query: str) -> dict[str, Any]:
    from . import schema

    # VERIFY-ONLINE: Confirm Chat Completions and minimum reasoning_effort for each configured
    # OpenAI ID.
    body = {
        "model": model["api_id"],
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": query}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": schema(t["input_schema"]),
                },
            }
            for t in tools
        ],
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "reasoning_effort": model["reasoning_effort"],
        "max_completion_tokens": model.get("max_tokens", 1024),
    }
    return body
