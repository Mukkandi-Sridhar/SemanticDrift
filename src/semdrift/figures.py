"""Draw the paper figures from the committed scores and analysis (no API calls).

Run: .venv/bin/python src/semdrift/figures.py
Reads  results/scores/main-A-all10-round1/metrics.csv and results/analysis/main/analysis.json
Writes figures/*.pdf (for the paper) and figures/*.png (for the README).
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures"
CATALOG_ORDER = ["V0", "V0R", "P1", "P2", "P3", "MG", "MS", "H3", "H1"]
CATALOG_LABELS = {
    "V0": "Original",
    "V0R": "Placebo",
    "P1": "Para. 1",
    "P2": "Para. 2",
    "P3": "Para. 3",
    "MG": "Vaguer",
    "MS": "Narrower",
    "H3": "Hist. (prev.)",
    "H1": "Hist. (earliest)",
}
FAMILY_COLOR = {  # Okabe-Ito, colour-blind safe
    "paraphrase": "#0072B2",
    "scope": "#E69F00",
    "history": "#009E73",
}
FAMILY = {
    "P1": "paraphrase",
    "P2": "paraphrase",
    "P3": "paraphrase",
    "MG": "scope",
    "MS": "scope",
    "H1": "history",
    "H3": "history",
}
SHORT = {
    "anthropic/claude-sonnet-5.5": "Claude Sonnet 5.5",
    "anthropic/claude-haiku-5.5": "Claude Haiku 5.5",
    "gpt-6.1-terra": "GPT-6.1 Terra",
    "gpt-6.2-sol": "GPT-6.2 Sol",
    "gpt-6-luna": "GPT-6 Luna",
    "google/gemini-4-argon-flex": "Gemini 4 Argon",
    "google/gemini-3.1-flash-lite": "Gemini 3.1 Flash-Lite",
    "deepseek/deepseek-v4.1-flash-1017": "DeepSeek V4.1 Flash",
    "qwen/qwen3.8-27b-fp8": "Qwen 3.8 27B",
    "mistralai/mistral-small-2603": "Mistral Small 4",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 9,
        "savefig.bbox": "tight",
        "savefig.dpi": 300,
    }
)


def save(fig, name: str) -> None:
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf", metadata={"CreationDate": None})  # reproducible bytes
    fig.savefig(OUT / f"{name}.png")
    plt.close(fig)


def load_accuracy() -> dict[str, dict[str, float]]:
    accuracy: dict[str, dict[str, float]] = defaultdict(dict)
    path = ROOT / "results/scores/main-A-all10-round1/metrics.csv"
    with path.open() as stream:
        for row in csv.DictReader(stream):
            accuracy[row["model"]][row["variant"]] = float(row["accuracy"])
    return accuracy


def ranking_figure(accuracy: dict[str, dict[str, float]]) -> None:
    """Rank of every model under each catalog (round 1, all ten models)."""
    ranks = {}
    for catalog in CATALOG_ORDER:
        ordered = sorted(accuracy, key=lambda m: (-accuracy[m][catalog], SHORT[m]))
        ranks[catalog] = {model: i + 1 for i, model in enumerate(ordered)}
    by_v0 = sorted(accuracy, key=lambda m: ranks["V0"][m])
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    xs = range(len(CATALOG_ORDER))
    palette = plt.get_cmap("tab10")
    for i, model in enumerate(by_v0):
        ys = [ranks[c][model] for c in CATALOG_ORDER]
        ax.plot(xs, ys, marker="o", markersize=3.5, linewidth=1.2, color=palette(i))
        ax.text(-0.15, ys[0], SHORT[model], ha="right", va="center", fontsize=7, color=palette(i))
    ax.axvspan(0.6, 1.4, color="0.92", zorder=0)  # placebo column
    ax.set_xticks(list(xs), [CATALOG_LABELS[c] for c in CATALOG_ORDER], rotation=30, ha="right")
    ax.set_yticks(range(1, len(by_v0) + 1), [])
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()
    right = ax.secondary_yaxis("right")
    right.set_yticks(range(1, len(by_v0) + 1))
    right.set_ylabel("Rank by accuracy (1 = best; ties broken by name)")
    ax.spines["left"].set_visible(False)
    ax.set_xlim(-0.2, len(CATALOG_ORDER) - 0.8)
    ax.set_title("Model ranking under each description catalog (round 1, 152 tasks)")
    save(fig, "fig1_rankings")


def excess_flip_figure(analysis: dict) -> None:
    """Decision changes beyond the placebo, per model and catalog, with 95% CIs."""
    rows = analysis["excess_flip_rates_all_tasks"]
    models = sorted({r["model"] for r in rows}, key=lambda m: SHORT[m])
    catalogs = [c for c in CATALOG_ORDER if c not in ("V0", "V0R")]
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    offsets = {c: (i - (len(catalogs) - 1) / 2) * 0.1 for i, c in enumerate(catalogs)}
    for row in rows:
        y = models.index(row["model"]) + offsets[row["variant"]]
        colour = FAMILY_COLOR[FAMILY[row["variant"]]]
        low, high = row["ci95"]
        ax.plot([low, high], [y, y], color=colour, linewidth=0.8, alpha=0.7)
        filled = low > 0
        ax.plot(
            row["excess_flip_rate"],
            y,
            marker="o",
            markersize=3.5,
            color=colour,
            markerfacecolor=colour if filled else "white",
        )
    ax.axvline(0, color="0.3", linewidth=0.8, linestyle="--")
    ax.set_yticks(range(len(models)), [SHORT[m] for m in models])
    ax.set_xlabel("Excess decision-change rate vs. placebo (filled: 95% CI above 0)")
    handles = [
        plt.Line2D([], [], color=c, marker="o", linestyle="", label=label)
        for label, c in (
            ("Paraphrases (P1-P3)", FAMILY_COLOR["paraphrase"]),
            ("Vaguer / narrower (MG, MS)", FAMILY_COLOR["scope"]),
            ("Real historical (H1, H3)", FAMILY_COLOR["history"]),
        )
    ]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=3,
        frameon=False,
        fontsize=7,
    )
    save(fig, "fig2_excess_flips")  # no title: the paper caption describes it


def harmful_write_figure(analysis: dict) -> None:
    """Share of 'should ask a human' tasks where the model chose a write tool."""
    rate: dict[str, dict[str, float]] = defaultdict(dict)
    for row in analysis["severity_profile"]:
        if row["task_type"] == "tempting":
            rate[row["model"]][row["variant"]] = row.get("harmful_write", 0.0)
    shown = ["V0", "MG", "H1"]
    models = sorted(rate, key=lambda m: -sum(rate[m].get(c, 0) for c in shown))
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    width = 0.26
    colours = {"V0": "0.35", "MG": FAMILY_COLOR["scope"], "H1": FAMILY_COLOR["history"]}
    for j, catalog in enumerate(shown):
        xs = [i + (j - 1) * width for i in range(len(models))]
        ax.bar(
            xs,
            [100 * rate[m].get(catalog, 0) for m in models],
            width,
            color=colours[catalog],
            label=CATALOG_LABELS[catalog],
        )
    ax.set_xticks(range(len(models)), [SHORT[m] for m in models], rotation=30, ha="right")
    ax.set_ylabel("Harmful writes (%)")
    ax.legend(frameon=False, fontsize=7)
    ax.set_title("Write actions on 24 tasks where the agent should ask a human first")
    save(fig, "fig3_harmful_writes")


def main() -> None:
    analysis = json.loads((ROOT / "results/analysis/main/analysis.json").read_text())
    ranking_figure(load_accuracy())
    excess_flip_figure(analysis)
    harmful_write_figure(analysis)
    print("wrote", sorted(p.name for p in OUT.glob("fig*")))


if __name__ == "__main__":
    main()
