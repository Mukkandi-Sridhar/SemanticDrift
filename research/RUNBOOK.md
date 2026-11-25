# Runbook: spending the credits safely (2026-11-25)

**Credit available:** OpenRouter $35.00 · OpenAI $14.55 (≈ $49.55).
**Expected total:** ≈ $35–40 if caching works and reasoning stays short. The main uncertainty is reasoning tokens for the 3 models that must reason (gpt-6.2-sol, Claude Sonnet 5.5, Gemini 4 Carbon).
**Rule:** each step starts only after the previous one is checked, and Sridhar says go.

All commands run from the project folder. Keys are read from `.env` (git-ignored).

## Step 0: Probe (20 calls, ≈ $0.05)
```bash
PYTHONPATH=src python3 -m semdrift.cli probe --config configs/main.toml
```
Two identical calls per model (task T007, original catalog). Saved to `results/probe/`; **not** part of the experiment.

**Pass criteria per model:**
| Check | Pass |
|---|---|
| No error | HTTP 200; the request shape is accepted (model id, tools, reasoning level, host pin) |
| Sensible action | A tool call or a text reply; no `max_tokens`/`length`/`max_output_tokens` stop |
| **Caching** | **Call 2 shows `cached` ≈ the tool-list size (thousands of tokens)** |
| Reasoning size | `reasoning` tokens recorded; for mandatory-reasoning models, note the count (it drives cost) |
| Host | OpenRouter `served_by` shows the pinned host, or is empty (the pin is enforced by `allow_fallbacks: false`) |

**If a model fails:** fix its settings (e.g., gpt-6.2-sol at `minimal` vs. `low`, or a provider slug) and re-probe *only that model* with `--models <key>`. Any setting change is recorded under PREREG → Deviations *before* the smoke step.

**Cost projection:** multiply each model's call-2 cost by 4,104 (its trials in the full run). If the projected total is over $45, decide *before* step 1: drop Gemini 4 Carbon or Sonnet, or run frontier models at k = 2.

## Step 1: Smoke (90 trials, ≈ $0.10–0.50)
```bash
PYTHONPATH=src python3 -m semdrift.cli run --config configs/main.toml --tasks T007 --repeats 0 --max-spend 1
```
Check that the records are complete and the costs match the probe.

## Step 2: Pilot (20 tasks × repeat 0 = 1,800 trials, ≈ $2–9)
```bash
PYTHONPATH=src python3 -m semdrift.cli run --config configs/main.toml --repeats 0 \
  --tasks T007,T011,T017,T040,T043,T051,T054,T061,T064,T080,T099,T114,T115,T122,T127,T128,T132,T134,T137,T140 \
  --max-spend 10
```
Check the spend against the projection (stopping rule: more than 50% over → stop and decide).

## Step 3: Repeat 0, all tasks (13,680 trials, ≈ $12)
```bash
PYTHONPATH=src python3 -m semdrift.cli run --config configs/main.toml --repeats 0 --max-spend 20
```
A first complete analysis is possible after this step.

## Step 4: Repeats 1–2 (27,360 trials, ≈ $23)
```bash
PYTHONPATH=src python3 -m semdrift.cli run --config configs/main.toml --repeats 1,2 --max-spend 30
```

## Step 5: Paraphrase judge (≈ $0.50)
Run with `judge-run --config configs/judge_final.toml --max-spend 4`. Judges: GPT-6.2 Sol + Claude Sonnet 5.5; P1–P3 checked, MG/MS as negative controls, H1/H3 classified: 212 changed tools × 2 directions × 2 judges = 848 requests ($1.28).

## Safety facts (verified 2026-11-25)
- OpenAI uses the **Responses API** (gpt-6.1-terra requires it for tools; gpt-6-luna only allows Chat Completions tools with reasoning off). `store: false`.
- **Lowest reasoning per model:** luna/terra `none`; gpt-6.2-sol `low` ("none" is rejected; whether `minimal` works is untested); Sonnet 5.5 and Gemini 4 Carbon `low` (reasoning mandatory); Haiku 5.5, Flash-Lite, DeepSeek, Qwen and Mistral `none`. Without these settings, Qwen would default to `xhigh` and DeepSeek to `high`, which would multiply the cost.
- OpenRouter bills exactly what it reports in `usage.cost`; the harness records it per call.
- OpenRouter pins: `provider.order` + `allow_fallbacks: false` (+ `quantizations: ["fp8"]` for DeepSeek and Qwen). `session_id` keeps requests on one host for cache hits.
- The OpenRouter key's credit limit is the hard cap. OpenAI auto-reload stays OFF.

## Recording (nothing is lost)
- Each trial → `results/raw/main/<model>.jsonl` (full raw response, parsed action, usage + billed cost, latency, host, request hash). Each request body → `results/raw/main/requests/<sha256>.json.gz`.
- Each failure → `results/raw/main/errors.jsonl`. After 3 consecutive failures, a model is paused for that stage; its trials stay pending and resume on re-run.
- Each stage → one line in `results/raw/main/ledger.jsonl` (git commit, filters, spend by model, errors, budget stop).
- `--max-spend` caps every stage. Re-running a stage only sends the missing trials (resumable).
- After each stage: archive the run folder with checksums and add an entry to `research/FINDINGS.md`.

## Analysis (after any stage; works on partial data)
```bash
PYTHONPATH=src python3 -m semdrift.cli analyze --config configs/main.toml
```
Writes `results/analysis/main/analysis.json`: accuracy by model × catalog, placebo-adjusted flip rates (all tasks and the 55 historically affected tasks, with bootstrap CIs), indistinguishable model pairs, per-tool attribution of the real IBM edits, top confusions, position bias, severity profiles, repeat agreement, and billed cost/latency per correct decision. The confirmatory scores (`score`) run once a stage is complete.
