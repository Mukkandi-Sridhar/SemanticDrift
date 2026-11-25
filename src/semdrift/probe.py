"""Pre-flight probe: two identical real calls per model before any experiment stage.

The first call checks that the provider accepts the exact request the experiment will send
(model id, tool format, reasoning setting, host pin). The second, identical call shows whether
the shared tool-list prefix is served from cache, which decides the real cost of the study.
Results go to results/probe/ and never enter an experiment run.
"""

import json
import time
from datetime import datetime, timezone
from typing import Any

from .cost import charge
from .data import load
from .parse import parse, usage
from .runner import plan, request, write_json
from .transport import RealTransport, sanitize

PROBE_TASK = "T007"
PROBE_VARIANT = "V0"
CALLS_PER_MODEL = 2


def _probe_model(config, dataset, trial, orders, transport) -> list[dict[str, Any]]:
    model = config["model_settings"][trial["model"]]
    body = request(config, dataset, trial, orders)
    results = []
    for attempt in range(CALLS_PER_MODEL):
        start = time.monotonic()
        try:
            raw = transport.send(model, body)
        except (RuntimeError, ValueError) as exc:
            results.append({"model": trial["model"], "call": attempt + 1, "error": str(exc)})
            break
        counts = usage(raw, model["provider"])
        parsed = parse(raw, model["provider"])
        try:
            cost = charge(counts, model["prices"])
        except ValueError as exc:
            cost = f"unpriced: {exc}"
        results.append(
            {
                "model": trial["model"],
                "call": attempt + 1,
                "latency_s": round(time.monotonic() - start, 2),
                "action": parsed["action"],
                "tool_name": parsed["tool_name"],
                "stop": parsed["raw_stop_reason"],
                "usage": counts,
                "cost_usd": cost,
                "served_by": raw.get("provider") or raw.get("openrouter_metadata"),
                "model_returned": raw.get("model"),
                "raw": sanitize(raw),
            }
        )
    return results


def run_probe(config: dict[str, Any], models: list[str] | None = None) -> dict[str, Any]:
    dataset = load(config["root"])
    trials, orders = plan({**config, "k": 1}, dataset)
    chosen = models or config["models"]
    results = []
    transport = RealTransport()
    for name in chosen:
        trial = next(
            t
            for t in trials
            if t["model"] == name and t["task_id"] == PROBE_TASK and t["variant"] == PROBE_VARIANT
        )
        results.extend(_probe_model(config, dataset, trial, orders, transport))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = config["root"] / "results/probe" / f"probe-{stamp}.json"
    write_json(path, results)
    summary = [
        {k: row.get(k) for k in ("model", "call", "error", "action", "tool_name", "stop",
                                 "cost_usd", "latency_s")}
        | ({"cached": row["usage"]["cached_input"], "input": row["usage"]["input"],
            "output": row["usage"]["output"], "reasoning": row["usage"]["reasoning"]}
           if "usage" in row else {})
        for row in results
    ]
    return {"saved": str(path), "calls": len(results), "results": summary}
