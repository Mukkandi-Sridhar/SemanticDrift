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


def _responses_calls(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Function calls in an OpenAI Responses API result, in output order."""
    return [item for item in response.get("output") or [] if item.get("type") == "function_call"]


def _responses_stop(response: dict[str, Any]) -> str | None:
    """`completed`, or the reason a response stopped early (e.g. `max_output_tokens`)."""
    details = response.get("incomplete_details") or {}
    return details.get("reason") or response.get("status")


def parse(response: Any, provider: str) -> dict[str, Any]:
    if provider == "openai":
        calls = _responses_calls(response)
        stop = _responses_stop(response)
        name = calls[0].get("name", "NONE") if calls else "NONE"
        arguments = _parse_arguments(calls[0].get("arguments")) if calls else None
    elif provider == "anthropic":
        calls = [c for c in (response.get("content") or []) if c.get("type") == "tool_use"]
        stop = response.get("stop_reason")
        name = calls[0].get("name") if calls else "NONE"
        arguments = calls[0].get("input") if calls else None
    else:
        choice = (response.get("choices") or [{}])[0]
        calls = (choice.get("message") or {}).get("tool_calls") or []
        stop = choice.get("finish_reason")
        function = (calls[0].get("function") or {}) if calls else {}
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


def usage(response: Any, provider: str) -> dict[str, Any]:
    """Token counts in one shape for every provider, plus the billed cost when reported.

    `cost` is OpenRouter's `usage.cost` (credits actually charged); other providers return None
    and cost is computed from the configured prices instead.
    """
    token_usage = response.get("usage") or {}
    if provider == "anthropic":
        cached = token_usage.get("cache_read_input_tokens") or 0
        write = token_usage.get("cache_creation_input_tokens") or 0
        return {
            "input": (token_usage.get("input_tokens") or 0) + cached + write,
            "cached_input": cached,
            "cache_write": write,
            "output": token_usage.get("output_tokens") or 0,
            "reasoning": 0,
            "cost": None,
        }
    if provider == "openai":
        input_details = token_usage.get("input_tokens_details") or {}
        output_details = token_usage.get("output_tokens_details") or {}
        return {
            "input": token_usage.get("input_tokens") or 0,
            "cached_input": input_details.get("cached_tokens") or 0,
            "cache_write": 0,
            "output": token_usage.get("output_tokens") or 0,
            "reasoning": output_details.get("reasoning_tokens") or 0,
            "cost": None,
        }
    prompt_details = token_usage.get("prompt_tokens_details") or {}
    completion_details = token_usage.get("completion_tokens_details") or {}
    return {
        "input": token_usage.get("prompt_tokens") or 0,
        "cached_input": prompt_details.get("cached_tokens")
        or token_usage.get("prompt_cache_hit_tokens")
        or 0,
        "cache_write": prompt_details.get("cache_write_tokens") or 0,
        "output": token_usage.get("completion_tokens") or 0,
        "reasoning": completion_details.get("reasoning_tokens") or 0,
        "cost": token_usage.get("cost"),
    }
