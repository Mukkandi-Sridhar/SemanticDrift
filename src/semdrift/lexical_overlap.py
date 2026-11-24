"""Compute the frozen token-overlap covariate for each task and catalog."""

import argparse
import csv
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any

CLI_DESCRIPTION = """Deterministic lexical covariate, using standard-library Python only.

Each non-stopword query token occurrence counts once in the denominator. The
numerator counts occurrences whose casefolded token occurs anywhere in the gold
description. Tokens are Unicode alphanumeric/underscore runs; punctuation splits
words. No stemming, synonyms, or per-variant stopwords. NONE has no gold tool:
its CSV overlap is blank and it is excluded from all reported means.
Run from repo root: python3 -I src/semdrift/lexical_overlap.py
"""


FILES = {
    "V0": "v0_original.json",
    "P1": "p1_paraphrase.json",
    "P2": "p2_paraphrase.json",
    "P3": "p3_paraphrase.json",
    "MG": "mg_overgeneral.json",
    "MS": "ms_overspecial.json",
}
# Frozen generic function-word list, identical for every task and variant.
STOPWORDS = frozenset(
    """a an the and or but if then than as at by for from in into of
on onto to with without about across against all any each every both either
neither this that these those it its their our your my me us i we you they he she
is are was were be been being am do does did doing have has had having can could
may might must shall should will would not no so such only very also just what
which who whom whose when where why how there here out up down over under per
through during before after between until since same other more most some s t""".split()
)


def tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"\w+", text.casefold()) if token not in STOPWORDS]


def compute(root: Path) -> tuple[list[dict[str, Any]], dict[str, float]]:
    catalogs = _load_descriptions(root)
    tasks = [
        json.loads(line) for line in (root / "datasets/tasks/tasks.jsonl").read_text().splitlines()
    ]
    rows = []
    for task in tasks:
        query = tokens(task["query"])
        for variant in FILES:
            overlap = None
            if task["gold"] != "NONE":
                vocabulary = set(tokens(catalogs[variant][task["gold"]]))
                overlap = sum(w in vocabulary for w in query) / len(query) if query else 0.0
            rows.append({"task_id": task["id"], "variant": variant, "overlap": overlap})
    means = {variant: _mean_overlap(rows, variant) for variant in FILES}
    return rows, means


def main() -> None:
    parser = argparse.ArgumentParser(description=CLI_DESCRIPTION)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    rows, means = compute(args.root)
    path = args.root / "datasets/tasks/lexical_overlap.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["task_id", "variant", "overlap"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {**row, "overlap": "" if row["overlap"] is None else f"{row['overlap']:.12f}"}
            )
    for variant, value in means.items():
        print(f"{variant}: {value:.6f}")
    spread = max(means[variant] for variant in ("V0", "P1", "P2", "P3")) - min(
        means[variant] for variant in ("V0", "P1", "P2", "P3")
    )
    print(f"V0/P1/P2/P3 max-minus-min: {spread:.6f}")


def _load_descriptions(root: Path) -> dict[str, dict[str, str]]:
    catalogs = {}
    for variant, filename in FILES.items():
        tools = json.loads((root / "datasets/tools" / filename).read_text())
        catalogs[variant] = {tool["name"]: tool["description"] for tool in tools}
    return catalogs


def _mean_overlap(rows: list[dict[str, Any]], variant: str) -> float:
    return mean(
        row["overlap"] for row in rows if row["variant"] == variant and row["overlap"] is not None
    )


if __name__ == "__main__":
    main()
