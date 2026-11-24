"""Usage.input includes cache hits/writes; output includes reasoning (no double billing)."""

from collections import defaultdict
from typing import Any


def charge(usage: dict[str, Any], prices: dict[str, Any], batch: bool = False) -> float:
    if prices.get("estimate_only"):
        raise ValueError(
            "Host-specific prices not verified; update prices before costing actual usage"
        )
    counts = {
        "input": usage["input"] - usage["cached_input"] - usage["cache_write"],
        "cached_input": usage["cached_input"],
        "cache_write": usage["cache_write"],
        "output": usage["output"],
    }
    if any(v < 0 for v in counts.values()):
        raise ValueError("Inconsistent usage counts")
    if any(counts[k] and prices[k] < 0 for k in counts):
        raise ValueError("Missing price for observed token category")
    return (
        sum(counts[k] * prices[k] for k in counts)
        / 1e6
        * (1 - prices["batch_discount"] if batch else 1)
    )


def estimate(
    config: dict[str, Any], estimates: list[dict[str, Any]], n_tasks: int
) -> dict[str, Any]:
    sums = defaultdict(float)
    for row in estimates:
        prices = config["model_settings"][row["model"]]["prices"]
        sums[row["model"]] += (
            row["input"] * prices["input"] + row["output"] * prices["output"]
        ) / 1e6
    scale = 140 * 5 / (n_tasks * config["k"])
    full = {
        model: total * scale * (1 - config["model_settings"][model]["prices"]["batch_discount"])
        for model, total in sums.items()
    }
    return {
        "label": (
            "estimate: request character count / 4; no cache hits; assumed "
            "output tokens; not measured usage"
        ),
        "assumed_output_tokens_per_trial": config.get("estimated_output_tokens", 300),
        "pilot_usd_by_model": dict(sums),
        "pilot_usd": sum(sums.values()),
        "full_140_tasks_k5_batch_usd_by_model": full,
        "full_140_tasks_k5_batch_usd": sum(full.values()),
        "limitations": (
            "OpenRouter uses host upper bounds; DeepSeek uses off-peak "
            "rates; cache-write prices absent in source; no cache assumptions."
        ),
    }


def report(records: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    if any(record.get("dry_run") for record in records):
        raise ValueError(
            "Fake usage is not measured cost; use results/dryrun/summary.json estimates"
        )
    if not records:
        raise ValueError("No measured usage records")
    if any(not record.get("raw_response", {}).get("usage") for record in records):
        raise ValueError("Missing provider usage; cannot report measured cost")
    totals = defaultdict(float)
    counts = defaultdict(int)
    for row in records:
        name = row["model"]
        totals[name] += charge(
            row["usage"], config["model_settings"][name]["prices"], row.get("batch", False)
        )
        counts[name] += 1
    return {
        "observed_usd_by_model": dict(totals),
        "observed_usd": sum(totals.values()),
        "full_projection_usd_by_model": {
            model: totals[model]
            / counts[model]
            * 140
            * 6
            * 5
            * (
                (1 - config["model_settings"][model]["prices"]["batch_discount"])
                if not any(record.get("batch") for record in records if record["model"] == model)
                else 1
            )
            for model in totals
        },
        "projection_assumption": (
            "Mean pilot usage and cache mix persist; full run "
            "OpenAI/Anthropic batch discount applied once."
        ),
    }
