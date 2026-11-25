"""Build OpenAI Responses API requests.

OpenAI's model pages state that gpt-6.1-terra supports tool calling only through the Responses
API, and that gpt-6-luna supports Chat Completions function calling only with reasoning off, so
every OpenAI model in the study uses the Responses API.
"""

from typing import Any

from ..prompt import SYSTEM

DEFAULT_MAX_OUTPUT_TOKENS = 1024


def build(model: dict[str, Any], tools: list[dict[str, Any]], query: str) -> dict[str, Any]:
    from . import schema

    return {
        "model": model["api_id"],
        "input": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": query},
        ],
        "tools": [
            {
                "type": "function",
                "name": tool["name"],
                "description": tool["description"],
                "parameters": schema(tool["input_schema"]),
                "strict": False,  # schemas are reproduced as-is; validity is scored afterwards
            }
            for tool in tools
        ],
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "reasoning": {"effort": model["reasoning_effort"]},
        "max_output_tokens": model.get("max_tokens", DEFAULT_MAX_OUTPUT_TOKENS),
        "store": False,  # do not retain study prompts on the provider side
    }
