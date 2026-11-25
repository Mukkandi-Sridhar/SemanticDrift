# Analysis plan: confirmatory + exploratory (2026-11-25)

Confirmatory analyses are fixed in `PREREG.md` and reported first, exactly as registered. Everything in Part B is **exploratory**: it is labelled as such in the paper, never used to re-state a hypothesis, and reported whatever it shows. Every number in the paper must trace back to a script in `src/semdrift/analysis/` and the raw run data.

## Part A: Confirmatory (from PREREG §3–5)
| ID | Question | Output |
|---|---|---|
| A1 | Does benign rewording change accuracy beyond the placebo? | Table: accuracy by model × variant (95% CI); exact McNemar V0 vs. each variant (Holm-corrected) |
| A2 | Does real historical drift change decisions beyond the placebo, H1 more than H3? | Excess flip rate (V0→H1, V0→H3) minus (V0→V0R), per model and pooled, with bootstrap CIs; historical-subset (55 tasks) and all-task views |
| A3 | Do model rankings survive rewording? | Kendall's τ-b per variant; share of the 45 model pairs that swap; top-model change; **"indistinguishable pairs"** |
| A4 | Does vagueness cause harmful writes? | Harmful-write rate on 24 tempting tasks, V0 vs. MG, per model |
| A5 | (exploratory H5) Is older documentation worse? | Accuracy H1 vs. H3 vs. V0 |
| A6 | Variance decomposition | Share of variance from task / model / variant / repeat |

## Part B: Exploratory analyses (the "broad" analysis)

### B1. Where exactly do decisions move? (mechanism)
- **Confusion matrices** (gold tool → chosen tool) for each variant vs. V0; highlight new off-diagonal mass.
- **Tool-level attribution:** for each of the 16 historically edited tools, the change in selection rate of that tool, and of its near-miss siblings, between H1/H3 and V0. Which real edits mattered most?
- **Edit features vs. effect:** correlation between edit properties (text similarity, length ratio, added sibling references, Args/Returns added) and decision change. Example question: *do added "use X() instead" hints reduce confusion?*
- **Near-miss families:** latest_reading / history / sensor_stats; installed_sensors / measured_sensors; get_failure_modes / generate_failure_modes; get_workorder / list_workorders.

### B2. Consistency and noise
- Repeat-to-repeat agreement under V0 and under V0R (the noise floor), per model.
- pass^3 vs. accuracy gap per model: how much "unreliability" hides behind the averages.
- **Position bias:** selection rate vs. the gold tool's position in the shuffled list (3 permutations), per model.

### B3. Cross-model behaviour
- Agreement between models on each task (Fleiss' κ); tasks that every model gets wrong (benchmark item quality); tasks with the widest disagreement.
- Model "families" (same lab, size): do small and frontier models from the same lab drift the same way?
- Reasoning vs. no-reasoning models: is drift sensitivity smaller for the 3 models that must reason?

### B4. Deployment view (the Bridge's framing)
- **Severity profile** per model × variant (correct / unneeded_read / wrong_read / missed_action / harmful_write) and severity-weighted cost.
- **Abstention behaviour:** on no-tool tasks, the split between text reply (correct) and read/write calls, by subtype (easy / tempting / out-of-scope).
- **Cost and latency per correct decision** (billed cost from `usage.cost` / prices; latency percentiles), and the accuracy–cost frontier.
- **Parameter validity** of correct-tool calls; invented argument keys.
- **"What a single benchmark score would have told you":** for each model, the spread of accuracy across the 7 non-placebo catalogs vs. its V0 score.

### B5. Controls and robustness checks
- Lexical-overlap covariate (`datasets/tasks/lexical_overlap.csv`): does query–description word overlap explain any accuracy differences between V0 and P1–P3?
- Sensitivity analysis excluding truncated/refused responses (PREREG §6).
- Leave-one-model-out: are the ranking conclusions driven by one model?
- MS split by `ms_conflict`; MG split by near-miss vs. not.

### B6. Qualitative evidence
- 10–15 annotated examples (the request, the description change, the model's choice and its severity) for the paper and the talk. Chosen by a fixed rule (largest effects plus random picks), not cherry-picked.

## Figures planned for the paper (max 3) and talk
1. **Excess flip rate by condition** (P1–P3, MG, MS, H3, H1) with the placebo line, for each model.
2. **Ranking stability:** model accuracy under V0 vs. under each catalog (bump chart), with indistinguishable pairs marked.
3. **Severity profile on tempting tasks** (V0 vs. MG vs. H1).

## Data preservation (nothing is lost)
- Every trial: a full raw response, the parsed action, usage and billed cost, latency, host attribution, request hash and the compressed request body (`results/raw/main/`). Failures: `errors.jsonl`. Each stage: one line in `ledger.jsonl` (git commit, filters, spend, errors).
- After each stage: copy `results/raw/main/` to a dated archive with a SHA-256 list (`results/archive/<date>/`), and note it in `FINDINGS.md`.
- At submission: deposit the raw data, code and dataset on Zenodo (DOI); commit the processed tables and figures to git.
