"""Analyses beyond the core scores (research/ANALYSIS_PLAN.md, A2-A6 and B1-B4).

Everything here is computed from the logged trial records, the frozen dataset and the run's
permutations. Placebo-adjusted results use V0R, an identical copy of V0: any decision change
between V0 and V0R is run-to-run noise, so it is the baseline every other effect must beat.
"""

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .data import load
from .score import correct, mean, severity

PLACEBO = "V0R"
BASELINE = "V0"
HISTORICAL = ("H1", "H3")
BOOTSTRAP_RESAMPLES = 2000
SEED = 20261124


def _index(records: list[dict[str, Any]]) -> dict[tuple[str, str, str, int], dict[str, Any]]:
    return {(r["model"], r["variant"], r["task_id"], r["repeat"]): r for r in records}


def _decision(record: dict[str, Any]) -> str:
    return record["tool_name"]


def _paired_flips(index, model: str, variant: str, tasks: list[str], repeats: list[int]):
    """Per task: share of repeats whose decision differs between V0 and `variant`."""
    per_task = {}
    for task_id in tasks:
        changes = [
            _decision(index[(model, BASELINE, task_id, r)])
            != _decision(index[(model, variant, task_id, r)])
            for r in repeats
            if (model, BASELINE, task_id, r) in index and (model, variant, task_id, r) in index
        ]
        if changes:
            per_task[task_id] = mean(changes)
    return per_task


def excess_flip_rates(records, tasks: list[str] | None = None, resamples=BOOTSTRAP_RESAMPLES):
    """Flip rate V0->X minus flip rate V0->V0R, per model, with a task-level bootstrap CI."""
    index = _index(records)
    models = sorted({r["model"] for r in records})
    variants = sorted({r["variant"] for r in records} - {BASELINE, PLACEBO})
    repeats = sorted({r["repeat"] for r in records})
    all_tasks = tasks or sorted({r["task_id"] for r in records})
    rng = random.Random(SEED)
    rows = []
    for model in models:
        placebo = _paired_flips(index, model, PLACEBO, all_tasks, repeats)
        for variant in variants:
            edited = _paired_flips(index, model, variant, all_tasks, repeats)
            shared = sorted(placebo.keys() & edited.keys())
            if not shared:
                continue
            diffs = [edited[t] - placebo[t] for t in shared]
            boot = sorted(
                mean(diffs[rng.randrange(len(diffs))] for _ in diffs) for _ in range(resamples)
            )
            rows.append(
                {
                    "model": model,
                    "variant": variant,
                    "n_tasks": len(shared),
                    "flip_rate": mean(edited[t] for t in shared),
                    "placebo_flip_rate": mean(placebo[t] for t in shared),
                    "excess_flip_rate": mean(diffs),
                    "ci95": [boot[int(0.025 * resamples)], boot[int(0.975 * resamples) - 1]],
                }
            )
    return rows


def accuracy_table(records) -> dict[tuple[str, str], float]:
    groups = defaultdict(list)
    for r in records:
        groups[(r["model"], r["variant"])].append(correct(r))
    return {key: mean(values) for key, values in groups.items()}


def indistinguishable_pairs(records) -> dict[str, Any]:
    """Model pairs whose V0 accuracy gap is smaller than either model's wording-induced swing.

    Swing = the 95th percentile of |acc(X) - acc(V0)| over non-placebo catalogs X.
    """
    acc = accuracy_table(records)
    models = sorted({m for m, _ in acc})
    variants = sorted({v for _, v in acc} - {BASELINE, PLACEBO})
    swing = {}
    for model in models:
        moves = sorted(
            abs(acc[(model, v)] - acc[(model, BASELINE)]) for v in variants if (model, v) in acc
        )
        swing[model] = moves[min(len(moves) - 1, int(0.95 * len(moves)))] if moves else 0.0
    pairs = []
    for i, a in enumerate(models):
        for b in models[i + 1 :]:
            gap = abs(acc[(a, BASELINE)] - acc[(b, BASELINE)])
            pairs.append(
                {
                    "pair": [a, b],
                    "v0_gap": gap,
                    "swing": max(swing[a], swing[b]),
                    "indistinguishable": gap < max(swing[a], swing[b]),
                }
            )
    return {
        "n_pairs": len(pairs),
        "n_indistinguishable": sum(p["indistinguishable"] for p in pairs),
        "swing_by_model": swing,
        "pairs": pairs,
    }


def historical_attribution(records, dataset) -> list[dict[str, Any]]:
    """For each tool whose description changed in H1/H3: how often it is chosen, by catalog."""
    v0 = {t["name"]: t["description"] for t in dataset["catalogs"][BASELINE]}
    rows = []
    for variant in HISTORICAL:
        if variant not in dataset["catalogs"]:
            continue
        changed = {
            t["name"] for t in dataset["catalogs"][variant] if t["description"] != v0[t["name"]]
        }
        for tool in sorted(changed):
            gold_rows = {
                cat: [r for r in records if r["variant"] == cat and r["gold"] == tool]
                for cat in (BASELINE, PLACEBO, variant)
            }
            chosen = {
                cat: mean(r["tool_name"] == tool for r in records if r["variant"] == cat)
                for cat in (BASELINE, variant)
            }
            rows.append(
                {
                    "variant": variant,
                    "tool": tool,
                    "accuracy_when_gold": {
                        cat: mean(map(correct, rows_)) for cat, rows_ in gold_rows.items()
                    },
                    "selection_rate_any_task": chosen,
                }
            )
    return rows


def confusions(records, top: int = 15) -> dict[str, list[dict[str, Any]]]:
    """Most frequent wrong (gold -> chosen) pairs per catalog."""
    out = {}
    for variant in sorted({r["variant"] for r in records}):
        counts = Counter(
            (r["gold"], r["tool_name"])
            for r in records
            if r["variant"] == variant and not correct(r)
        )
        out[variant] = [
            {"gold": g, "chosen": c, "count": n} for (g, c), n in counts.most_common(top)
        ]
    return out


def position_bias(records, permutations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Accuracy by the gold tool's position (thirds of the list) in that repeat's order."""
    order = {p["repeat"]: p["tool_order"] for p in permutations}
    buckets = defaultdict(list)
    for r in records:
        if r["gold"] == "NONE" or r["repeat"] not in order:
            continue
        tools = order[r["repeat"]]
        third = min(2, tools.index(r["gold"]) * 3 // len(tools))
        buckets[(r["model"], ("first", "middle", "last")[third])].append(correct(r))
    return [
        {"model": m, "gold_position": p, "n": len(v), "accuracy": mean(v)}
        for (m, p), v in sorted(buckets.items())
    ]


def severity_profile(records) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for r in records:
        groups[(r["model"], r["variant"], r.get("subtype") or "single_tool")].append(severity(r))
    return [
        {
            "model": m,
            "variant": v,
            "task_type": t,
            "n": len(values),
            **{tier: values.count(tier) / len(values) for tier in sorted(set(values))},
        }
        for (m, v, t), values in sorted(groups.items())
    ]


def repeat_agreement(records) -> list[dict[str, Any]]:
    """Share of (task, catalog) cells where all repeats made the same decision."""
    cells = defaultdict(list)
    for r in records:
        cells[(r["model"], r["variant"], r["task_id"])].append(_decision(r))
    by_model = defaultdict(list)
    for (model, variant, _), decisions in cells.items():
        if len(decisions) > 1:
            by_model[(model, variant)].append(len(set(decisions)) == 1)
    return [
        {"model": m, "variant": v, "all_repeats_agree": mean(x)}
        for (m, v), x in sorted(by_model.items())
    ]


def cost_per_correct(records) -> list[dict[str, Any]]:
    groups = defaultdict(lambda: {"cost": 0.0, "correct": 0, "n": 0, "latency": []})
    for r in records:
        g = groups[r["model"]]
        g["cost"] += (r.get("usage") or {}).get("cost") or 0.0
        g["correct"] += correct(r)
        g["n"] += 1
        if r.get("latency_ms") is not None:
            g["latency"].append(r["latency_ms"])
    rows = []
    for model, g in sorted(groups.items()):
        latency = sorted(g["latency"])
        rows.append(
            {
                "model": model,
                "trials": g["n"],
                "billed_cost_usd": g["cost"],
                "cost_per_correct_usd": g["cost"] / g["correct"] if g["correct"] else None,
                "latency_ms_p50": latency[len(latency) // 2] if latency else None,
                "latency_ms_p90": latency[int(0.9 * (len(latency) - 1))] if latency else None,
            }
        )
    return rows


def analyze(records: list[dict[str, Any]], root: Path, run_dir: Path) -> dict[str, Any]:
    dataset = load(root)
    permutations = json.loads((run_dir / "permutations.json").read_text())
    v0 = {t["name"]: t["description"] for t in dataset["catalogs"][BASELINE]}
    drifted = {
        t["name"]
        for cat in HISTORICAL
        if cat in dataset["catalogs"]
        for t in dataset["catalogs"][cat]
        if t["description"] != v0[t["name"]]
    }
    historical_tasks = sorted({t["id"] for t in dataset["tasks"] if t["gold"] in drifted})
    accuracy = accuracy_table(records)
    return {
        "n_records": len(records),
        "accuracy": [
            {"model": m, "variant": v, "accuracy": a} for (m, v), a in sorted(accuracy.items())
        ],
        "excess_flip_rates_all_tasks": excess_flip_rates(records),
        "excess_flip_rates_historical_tasks": excess_flip_rates(records, historical_tasks),
        "indistinguishable_pairs": indistinguishable_pairs(records),
        "historical_attribution": historical_attribution(records, dataset),
        "confusions": confusions(records),
        "position_bias": position_bias(records, permutations),
        "severity_profile": severity_profile(records),
        "repeat_agreement": repeat_agreement(records),
        "cost_per_correct": cost_per_correct(records),
        "notes": "Exploratory except where PREREG names the analysis; CIs are task bootstraps.",
    }
