"""Build Anthropic tool-selection requests with explicit cache boundaries."""

from typing import Any

from ..prompt import SYSTEM


def build(model: dict[str, Any], tools: list[dict[str, Any]], query: str) -> dict[str, Any]:
    from . import schema

    body = {
        "model": model["api_id"],
        "system": SYSTEM,
        "messages": [{"role": "user", "content": query}],
        "max_tokens": 1024,
    }
    if tools:
        body["tools"] = [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": schema(t["input_schema"]),
            }
            for t in tools
        ]
        body["tools"][-1]["cache_control"] = {"type": "ephemeral"}
        body["tool_choice"] = {"type": "auto", "disable_parallel_tool_use": True}
    # VERIFY-ONLINE: Confirm low effort, between_tools thinking, and last-tool cache support for the
    # configured Claude IDs.
    if model.get("thinking"):
        body["thinking"] = {"type": model["thinking"]}
    if model.get("effort"):
        body["output_config"] = {"effort": model["effort"]}
    return body
