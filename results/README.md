# Results

Processed outputs of the main run (`configs/main.toml`, 38,304 decisions, 2026-11-25). Raw
responses, request bodies, logs and the run ledger are too large for git (about 240 MB); they
are archived with SHA-256 checksums and will be published on Zenodo.

## `scores/`

Confirmatory scores from `src/semdrift/score.py`, in two passes, because Gemini 4 Argon ran one
repeat and the other nine models ran three:

| Folder | Models | Repeats | Use |
|---|---|---|---|
| `main-A-all10-round1/` | all 10 | repeat 0 | rankings and comparisons that include every model |
| `main-B-9models-k3/` | 9 (no Argon) | 3 | pass^3, majority decisions, repeat-based statistics |

Each folder has:

- `metrics.csv`: one row per model × catalog. `accuracy`; `pass^k` (all k repeats correct);
  `false_action_rate` on no-tool tasks (also by subtype); `unsafe_write_rate`;
  `parameter_validity`; accuracy split by `ms_conflict`; the share of each severity tier
  (`severity_correct`, `severity_unneeded_read`, `severity_wrong_read`,
  `severity_missed_action`, `severity_harmful_write`) and `severity_weighted_cost`.
- `comparisons.csv`: each catalog vs. the original, per model. `delta_accuracy`, `flip_rate`,
  exact McNemar counts and p-values (raw and Holm-corrected), with bootstrap 95% CIs.
- `rankings.csv`: per catalog, Kendall's τ-b against the original ranking (with bootstrap CI),
  whether the top model changed, and the share of model pairs that swap order.
- `summary.json`: all of the above, plus the statistical settings.

## `analysis/main/analysis.json`

Exploratory analysis from `src/semdrift/analysis.py`: accuracy by model and catalog;
decision-change rates against the placebo (V0R), with task-bootstrap CIs, for all tasks and for
the 55 tasks whose gold tool was edited in the git history; indistinguishable model pairs;
per-tool effects of the historical edits; the most common confusions; position bias; severity
profiles by task type; repeat agreement; and billed cost and latency per model.

Latency for Claude Sonnet 5.5 includes time spent waiting for its 20-requests-per-minute
account limit, so it isn't comparable with the other models.

## `judge/judge_final/`

LLM judgements of whether each rewritten description means the same as the original
(`configs/judge_final.toml`; judges GPT-6.2 Sol and Claude Sonnet 5.5, both directions).
`responses.jsonl` has every answer with its reason; `summary.json` gives, per catalog and tool,
`equivalent` (all four votes), `not_equivalent`, or `mixed`, plus the agreement between judges.
The vaguer and narrower catalogs are negative controls; the historical catalogs show which real
AssetOpsBench edits changed meaning.

## Reproducing

```bash
PYTHONPATH=src python3 -m semdrift.cli score   --config configs/main.toml   # needs the raw run
PYTHONPATH=src python3 -m semdrift.cli analyze --config configs/main.toml
python3 src/semdrift/figures.py                                            # from these files only
PYTHONPATH=src python3 -m semdrift.cli judge-run --config configs/judge_final.toml --max-spend 4
```
