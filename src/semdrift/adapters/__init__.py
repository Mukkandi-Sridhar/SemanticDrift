"""Tool-selection robustness experiments for the SemanticDrift study."""

from typing import Any


def build(model: dict[str, Any], tools: list[dict[str, Any]], query: str) -> dict[str, Any]:
    from . import anthropic_adapter, openai_adapter, openai_compat_adapter

    adapter = {
        "openai": openai_adapter,
        "anthropic": anthropic_adapter,
        "deepseek": openai_compat_adapter,
        "openrouter": openai_compat_adapter,
    }[model["provider"]]
    return adapter.build(model, tools, query)


def schema(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: schema(v) for k, v in value.items() if k != "x_source_annotation"}
    if isinstance(value, list):
        return [schema(v) for v in value]
    return value
