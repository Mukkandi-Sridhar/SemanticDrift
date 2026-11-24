"""Adapt study requests for DeepSeek and pinned OpenRouter providers."""

from typing import Any

from .openai_adapter import build as openai_build


def build(model: dict[str, Any], tools: list[dict[str, Any]], query: str) -> dict[str, Any]:
    body = openai_build({**model, "reasoning_effort": "none"}, tools, query)
    body.pop("reasoning_effort")
    body["max_tokens"] = body.pop("max_completion_tokens")
    if model["provider"] == "deepseek":
        # VERIFY-ONLINE: Confirm DeepSeek flash non-thinking switch and parallel_tool_calls support.
        body["thinking"] = {"type": "disabled"}
    else:
        # VERIFY-ONLINE: Confirm pinned host tool support and response provider attribution on
        # OpenRouter.
        body["provider"] = {"order": [model["provider_pin"]], "allow_fallbacks": False}
        if model.get("quantizations"):
            # VERIFY-ONLINE: OpenRouter provider.quantizations filter (pins the precision served).
            body["provider"]["quantizations"] = list(model["quantizations"])
        if model.get("reasoning_effort"):
            # VERIFY-ONLINE: OpenRouter unified reasoning parameter; lowest effort for routing
            # calls.
            body["reasoning"] = {"effort": model["reasoning_effort"]}
        _add_cache_hint(body, model.get("cache"))
    return body


def _add_cache_hint(body: dict[str, Any], mode: str | None) -> None:
    """Ask OpenRouter to cache the shared tools+system prefix (~97% of every request).

    "top_level": automatic caching, supported for Anthropic-hosted models.
    "explicit": a breakpoint on the system message, which follows the tool list in the
    rendered prompt, so the whole tool catalog sits inside the cached prefix.
    VERIFY-ONLINE: confirm via usage.prompt_tokens_details.cached_tokens in the smoke test.
    """
    if mode == "top_level":
        body["cache_control"] = {"type": "ephemeral"}
    elif mode == "explicit":
        system = body["messages"][0]
        system["content"] = [
            {"type": "text", "text": system["content"], "cache_control": {"type": "ephemeral"}}
        ]
    elif mode is not None:
        raise ValueError(f"Unknown cache mode: {mode}")
