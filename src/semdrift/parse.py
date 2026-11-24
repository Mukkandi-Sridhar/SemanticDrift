"""Normalize responses without executing anything; retain every call in raw_response."""

import json
from typing import Any


def _parse_arguments(arguments: Any) -> Any:
    if not isinstance(arguments, str):
        return arguments
    try:
        return json.loads(arguments)
    except (ValueError, TypeError):
        # Preserve malformed strings: validation fails, original remains available.
        return arguments


def parse(response: Any, provider: str) -> dict[str, Any]:
    if provider == "anthropic":
        calls = [c for c in (response.get("content") or []) if c.get("type") == "tool_use"]
        stop = response.get("stop_reason")
        name = calls[0].get("name") if calls else "NONE"
        arguments = calls[0].get("input") if calls else None
    else:
        choice = (response.get("choices") or [{}])[0]
        calls = (choice.get("message") or {}).get("tool_calls") or []
        stop = choice.get("finish_reason")
        function = calls[0].get("function", {}) if calls else {}
        name, arguments = function.get("name", "NONE"), function.get("arguments")
        arguments = _parse_arguments(arguments)
    if calls and (not isinstance(name, str) or not name or name == "NONE"):
        name = "<INVALID_TOOL_NAME>"
    return {
        "action": "tool" if calls else "text",
        "tool_name": name,
        "arguments": arguments,
        "n_tool_calls": len(calls),
        "raw_stop_reason": stop,
    }


def usage(response: Any, provider: str) -> dict[str, int]:
    token_usage = response.get("usage") or {}
    if provider == "anthropic":
        cached, write = (
            token_usage.get("cache_read_input_tokens", 0),
            token_usage.get("cache_creation_input_tokens", 0),
        )
        return {
            "input": token_usage.get("input_tokens", 0) + cached + write,
            "cached_input": cached,
            "cache_write": write,
            "output": token_usage.get("output_tokens", 0),
            "reasoning": 0,
        }
    return {
        "input": token_usage.get("prompt_tokens", 0),
        "cached_input": token_usage.get("prompt_tokens_details", {}).get(
            "cached_tokens", token_usage.get("prompt_cache_hit_tokens", 0)
        ),
        "cache_write": 0,
        "output": token_usage.get("completion_tokens", 0),
        "reasoning": token_usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0),
    }
