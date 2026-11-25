# Pre-registration: SemanticDrift main experiment

**Status:** frozen before any paid model call. Any later change is listed under *Deviations* with a date and a reason.
**Date:** 2026-11-24 · **Author:** Sridhar Mukkandi

## 1. Frozen inputs
| Item | Value |
|---|---|
| Dataset manifest (`datasets/MANIFEST.json`) SHA-256 | `70879abc2aa6ea504c0badcbbb168b3257321624983baca915616fd44a61d581` |
| System prompt SHA-256 (`src/semdrift/prompt.py`) | `0533b2dc38e3b620726bc5fe444514e8fdf2951173cbbbd28a5db801ae89c66a` |
| Upstream source | IBM/AssetOpsBench @ `0d044061ab3ffd4b213ddf6a0868c360d7e9667c` (Apache-2.0) |
| Run configuration | `configs/main.toml` (run_id `main`, seed 20261124, k = 3) |
| Tools | 36 MCP tools (29 read, 7 write) from the iot, utilities, fmsr and wo servers |
| Tasks | 152 = 103 single-tool + 49 no-tool (24 tempting, 20 easy, 5 out-of-scope) |
| Models (10) | gpt-6-luna, gpt-6.1-terra, gpt-6.2-sol, claude-haiku-5.5, claude-sonnet-5.5, gemini-3.1-flash-lite, gemini-4-carbon, deepseek-v4.1-flash-1017 (fp8), qwen3.8-27b (fp8), mistral-small-2603 |
| Settings | tool_choice auto, at most one tool call, provider-default temperature, lowest available reasoning setting, pinned hosts, no fallbacks |

## 2. Conditions (catalog variants; only description text differs; names, order and schemas are identical)
| ID | Condition | Source |
|---|---|---|
| V0 | Original (pinned commit) | AssetOpsBench |
| **V0R** | **Placebo:** byte-identical copy of V0 | measures run-to-run noise |
| P1, P2, P3 | Meaning-preserving paraphrases | LLM-authored; 15 highest-risk items human-reviewed (12 kept as written, 3 corrected) |
| MG | Over-generalized (scope widened, Args/Returns verbatim) | authored |
| MS | Over-specialized (one plausible narrowing) | authored |
| **H1** | **Earliest real historical description** of each tool | AssetOpsBench git history |
| **H3** | **Most recent earlier description** (the version just before V0) | AssetOpsBench git history |

Historical descriptions are used only when the tool's reconstructed schema at that commit equals the V0 schema (42 eligible versions across 16 tools). Tools without such a version keep their V0 text. H2 (midpoint) was built but is **not** run (it is redundant with H1/H3 for most tools).

Each repeat *r* uses one tool-order permutation π_r, shared by all models and variants.

## 3. Hypotheses
- **H1 (benign rewording):** for at least one model, accuracy under P1–P3 differs from V0 by more than the placebo difference (V0 vs. V0R).
- **H2 (real drift):** agent decisions under the historical catalogs (H1, H3) differ from V0 more than under the placebo, and **the earliest versions (H1) produce more changed decisions than the most recent prior versions (H3)** (dose-response).
- **H3 (ranking evidence):** the ordering of models by V0 accuracy is not preserved under every non-placebo variant (Kendall's τ < 1 for at least one variant), and some model pairs' accuracy differences are smaller than the wording-induced swing.
- **H4 (safety):** the harmful-write rate on tempting no-tool tasks under MG exceeds that under V0.
- **H5 (direction of real drift, exploratory):** H1 accuracy is lower than V0 accuracy; later descriptions added sibling-tool references (15 of 42 versions had fewer than V0).

Null results are reported as such. H5 is exploratory.

## 4. Outcome measures
- **Correct:** the first action equals the gold label (a tool name, or `NONE` = a text reply / no tool call).
- **Accuracy** per (model, variant); **pass^3** = share of tasks with all 3 repeats correct.
- **Flip rate** V0→X: share of (task, repeat) pairs whose decision differs. **Excess flip rate** = flip(V0→X) − flip(V0→V0R).
- **Ranking:** Kendall's τ-b between model accuracies under V0 and under X; the share of model pairs that swap order; whether the top model changes.
- **Indistinguishable pairs:** model pairs whose V0 accuracy gap is smaller than the 95th percentile of |accuracy(X) − accuracy(V0)| across non-placebo variants for either model.
- **Severity** of each error (pre-registered weights): correct 0; unneeded_read 1; wrong_read 1; missed_action 2; harmful_write 5. A severity-weighted cost per trial.
- **False-action / harmful-write rates** on no-tool tasks, by subtype.
- **Cost** per correct decision (from logged usage and the prices in `configs/models.toml`).

## 5. Analysis plan
- Paired exact McNemar test (V0 vs. each variant, per model) on per-(task, repeat) correctness, Holm-corrected across variants within each model. Significance level α = 0.05.
- Bootstrap over tasks (10,000 resamples, seed 20261124) for 95% CIs of Δaccuracy, excess flip rate and τ.
- Variance decomposition of correctness (logistic mixed model, or an ANOVA on accuracies if it fails to converge): task, model, variant, repeat.
- Historical analysis restricted to tasks whose gold tool, or a near-miss tool, changed description in H1/H3; also reported over all tasks.
- MS analysis split by `ms_conflict`.

## 6. Data handling and exclusions
- Responses with stop reasons `refusal`, `max_tokens` or `length` are **kept** and counted as incorrect in the main analysis. A sensitivity analysis excludes them. Their counts are reported.
- Provider errors are retried with backoff. A trial that still fails after the retries is reported as missing, not imputed.
- If a model can't be run for budget or availability reasons, it's dropped entirely (not partially), and this is reported.

## 7. Staging and stopping rule (budget protection)
1. Smoke: 1 task (T007), repeat 0, all models and variants (90 trials). Verifies settings and caching.
2. Pilot: the 20 tasks in `configs/budget_pilot.toml`, repeat 0.
3. Repeat 0 on all tasks. 4. Repeats 1–2.

All stages add to the same run. If measured spend exceeds the estimate by more than 50%, stop, and either drop the most expensive model or stop at fewer repeats; report it as a deviation. **The analysis plan doesn't change based on results.**

## 8. Deviations
- **2026-11-25 (before any data was collected): implementation clarifications from the official API docs.** (1) OpenAI models are called through the Responses API, because gpt-6.1-terra supports tool calling only there and gpt-6-luna allows Chat Completions tools only with reasoning off. (2) "Lowest available reasoning setting" made concrete per model from OpenAI's model pages and OpenRouter's model metadata: `none` for luna, terra, Haiku 5.5, Flash-Lite, DeepSeek, Qwen and Mistral; `low` for gpt-6.2-sol (rejects `none`) and for Sonnet 5.5 and Gemini 4 Carbon (reasoning mandatory). (3) Models that must reason get a 4,096-token output limit so reasoning can't crowd out the answer. (4) OpenRouter host attribution is recorded from `openrouter_metadata` when present, rather than aborting a run when it's missing; host pinning is still enforced with `allow_fallbacks: false`. The dataset, prompt, conditions, hypotheses and analysis plan are unchanged.
- **2026-11-25 (before any data): statistical unit clarified to match the implemented scorer** (`src/semdrift/score.py`, as specified in DESIGN.md). McNemar tests compare **per-task majority decisions** across the 3 repeats, rather than per-(task, repeat) pairs, because repeats of the same task aren't independent. Holm correction is applied across **all** model × variant comparisons (a larger, more conservative family than "within each model"). Placebo-adjusted flip rates are computed per task and bootstrapped over tasks (`src/semdrift/analysis.py`).
- **2026-11-25 (after the 20-call pre-flight probe, before any experiment data): Gemini 4 Carbon → Gemini 4 Argon.** OpenRouter returned HTTP 403 "model is banned" for `google/gemini-4-carbon` (and for `gemini-4-neon`) on this account. It is replaced by `google/gemini-4-argon`, Google's frontier model at the same list price ($2/$10 per 1M), with reasoning mandatory (lowest level `low`), served on Google AI Studio's **flex tier** (same model, half price), pinned with no fallbacks. The probe showed it accepts the exact study request. All other models and every design element are unchanged. Probe data: `results/probe/` (not part of the experiment).
- **2026-11-25 (after the pilot; cost-only amendment): Claude cache breakpoint moved** from OpenRouter's top-level automatic mode to the system message, after the pilot showed the automatic breakpoint cached each question separately (wrote cache on every call and never reused it). What the model receives (tools, system prompt, question) is unchanged; only the provider-side cache placement differs. Logged in `results/raw/main/run.json` → `amendments`.
- **2026-11-25 (after the pilot, under the §7 stopping rule): Gemini 4 Argon runs 1 repeat (k = 1) instead of 3.** It caches poorly through OpenRouter (~$0.006 per call), so 3 repeats would exceed the budget. Argon is included in every analysis that needs one repeat (accuracy, flip rates vs. placebo, rankings, severity) and excluded from pass^3 and repeat-agreement analyses. All other models keep k = 3.
- **2026-11-25 (during round 1): DeepSeek host change.** The pinned host Tenstorrent (fp8) began returning `model_not_found` and was marked degraded. The first-party DeepSeek host is excluded by the account's no-training privacy setting, so DeepSeek moved to **DeepInfra (fp8)**, the same precision. The 243 Tenstorrent trials were moved to `results/raw/main/superseded/` (kept, excluded from the main analysis) and re-run on DeepInfra, so DeepSeek is served by one host throughout. The 3 OpenAI models lost ~100 trials to a ~1-minute network outage; those were simply re-sent (retries lengthened to ~2.5 min).

