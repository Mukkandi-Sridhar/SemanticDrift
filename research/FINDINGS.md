# Findings notebook (append-only)

One entry per stage or analysis. Record what was observed, with numbers and the file they came from, **before** interpreting it. Keep surprises and failures as well as successes. Never edit an old entry; add a correction below it.

Template:
```
## <date> · <stage or analysis>
- Data: <run directory / ledger line / script + commit>
- Spend this stage: $<x> (cumulative $<y>)
- Observations (facts, with numbers):
- Surprises / problems:
- Decisions taken (and whether they are a PREREG deviation):
```

---

## 2026-11-25 · Pre-data observations (dataset only, no model calls)
- Data: `datasets/history/versions.json`, `datasets/history/edit_features.json` (commit 692e680 + pre-flight fixes)
- 42 developer-written earlier descriptions across 16 of 36 tools have a schema identical to the current one. 55 of 103 single-tool tasks use one of these tools as the gold answer.
- Median text similarity between an older description and the current one: 0.49. 24 of 42 edits are substantial rewrites (similarity < 0.5); 3 are near-identical (> 0.9).
- 15 of 42 older descriptions contain fewer references to sibling tools (e.g. "use `installed_sensors()` for…") than today's version. **Hypothesis-generating only (H5):** later docs added disambiguation hints.

## 2026-11-25 · Step 0: pre-flight probe (not experiment data)
- Data: `results/probe/probe-*.json` (2 identical calls per model, task T007, catalog V0). Probe spend: **$0.14**.
- **9 of 10 planned models accepted the exact study request**; every working model chose the same tool (`asset_detail`) for T007.
- **Gemini 4 Carbon and Gemini 4 Neon are blocked for this account** (OpenRouter HTTP 403 "model is banned"). Replaced by **Gemini 4 Argon** (same price tier), on Google AI Studio's flex tier (half price). Recorded in PREREG Deviations.
- **Caching works:** on call 2, cached tokens ≈ the whole prompt for the OpenAI models (3,981/3,984), Claude (9,450/9,454), DeepSeek (6,260/6,263) and Mistral (6,352/6,382). Gemini Flash-Lite cached 5,552/5,566 from call 1 (implicit). **Gemini 4 Argon caches only ~64% (3,678/5,732)**, whether or not a breakpoint is sent. **Qwen (Chutes host) does not cache** (0 cached), but is cheap.
- Prompt size differs by provider for the same catalog: OpenAI 3,984 tokens; Gemini 5,732; DeepSeek 6,263; Mistral 6,382; Qwen 6,858; Claude 9,454 (different tool-rendering and tokenizers).
- With the lowest reasoning settings, no model produced reasoning tokens except Gemini 4 Hydrogen (63–103; not selected).
- **Projected full-run cost from real call-2 costs: OpenAI $4.37 + OpenRouter $20.53 = $24.90** (41,040 trials), against $49.55 available.
- Engineering consequence: sequential execution would take ~34 h, so the runner now runs models in parallel threads (one per model, cache-friendly order kept within each model).

## 2026-11-25 · Step 1: smoke stage (first experiment data)
- Data: `results/raw/main/` (ledger line 1; commit bf3b9e9). Archive: `results/archive/2026-11-25-smoke/main-raw.tar.gz` + SHA256SUMS.
- **90/90 trials succeeded, 0 errors.** Spend **$0.378** (cap $1): Sonnet $0.20, Sol $0.06, Argon $0.05, others ≤ $0.03. Cumulative spend including the probe: **≈ $0.52**.
- Task T007 (gold `asset_detail`, an easy item): **all 10 models chose correctly under all 9 catalogs**, and all arguments were schema-valid. No conclusions are drawn from one task.
- Host pins held: Claude → Anthropic; Gemini → Google AI Studio; DeepSeek → Tenstorrent; Qwen → Chutes; Mistral → Mistral (from `openrouter_metadata`).
- Only 28/90 calls hit the cache. Expected: the smoke stage calls each (catalog, tool-order) prefix only once. The full run calls each prefix ~152 times, so the probe-based projection (~$25) stands.

## 2026-11-25 · Step 2: pilot stage (20 tasks × 9 catalogs × 10 models, repeat 0)
- Data: `results/raw/main/` (ledger line 2), analysis `results/analysis/main/analysis.json`. Archive: `results/archive/2026-11-25-pilot/` (+SHA256SUMS).
- **1,710 new trials, 0 errors, spend $5.89**. This is **above the estimate** (stopping rule triggered, so the run pauses for a decision). Cause: **Claude via OpenRouter wrote a fresh cache entry on every call and never read it** (19/171 calls hit). The top-level "automatic" cache breakpoint moves to the last block, the user question, which differs per task. Claude Sonnet alone cost $4.09. **Gemini 4 Argon also mostly missed** (21/171 hits; ~$0.006/call). OpenAI, DeepSeek, Mistral and Flash-Lite cached as expected; Qwen partly (28/171).
- **Fix verified** (3 extra Haiku calls outside the run, ≈ $0.0015): a breakpoint on the system message makes different questions reuse the cache (call 1 writes 9,663 tokens; calls 2–3 read 9,663; cost $0.00124 → $0.00013). The run supports this through a logged amendment (cache placement only; what the model is asked is unchanged).
- OpenRouter key usage after the pilot: **$6.01 of $35.00**.
- **Early observations (20 tasks, 1 repeat; noisy, not conclusions):**
  - Frontier models are at ceiling on these 20 tasks: Sonnet 5.5, Argon and GPT-6.1 Terra score 1.00 under every catalog; Sol 0.95–1.00.
  - Smaller models move across catalogs: DeepSeek 0.80 (MS) to 0.95 (P3/H1/H3); Haiku 0.90–1.00; Qwen 0.85–1.00; Mistral 0.85–0.95; Luna 0.70 (H3) to 0.80 (V0R).
  - **The placebo also moves** (Haiku 0.90 V0 vs. 0.95 V0R; Mistral 0.90 vs. 0.85): run-to-run noise is real, which is why every effect is measured against V0R.
  - Largest excess flips vs. placebo: DeepSeek under MG (+0.15) and H1 (+0.10).
  - 12 of 45 model pairs are already "indistinguishable" (V0 gap smaller than the wording-induced swing).
  - Common errors: on no-tool tasks, models call a read tool (`list_workorders`, `get_workorder`, `sites`) instead of asking a human; `sensor_stats` gets confused with `asset_ids` / `find_assets_by_sensors` under MG and H1.
  - Harmful writes on tempting tasks: GPT-6 Luna and Mistral Small 1/4 (25%) under every catalog; all others 0/4.

## 2026-11-25 · Step 2b: small check after the cache fix (T001–T005, repeat 0)
- Data: ledger line 3 (amendment logged in run.json). **450 new trials, 0 errors, spend $0.63** (cap $1).
- **Claude cache fix confirmed in the real run:** Haiku and Sonnet hit the cache on 37/45 calls; the 8 misses are the first call for each of the 9 catalog prefixes (one was already warm). Cached Sonnet calls cost $0.0017 vs. $0.0249 for a write.
- Gemini 4 Argon still caches rarely (6/45); Qwen on Chutes almost never (1/45) but stays cheap.
- **Re-projected remaining spend** (cached-call cost × remaining trials + first-call cost for the 18 new prefixes in repeats 1–2; Argon at 1 round): **≈ $22.45** (OpenAI ≈ $3.9, OpenRouter ≈ $18.5) vs. ≈ $28.4 left on OpenRouter and ≈ $13.9 on OpenAI.
- Decision: Gemini 4 Argon runs repeat 0 only (budget; allowed by the PREREG stopping rule; recorded as a deviation).

## 2026-11-25 · Round 1, tasks 1–50 complete (all 10 models)
- Data: ledger lines 4–5; 4,500 trials in round 1. 14 errors logged (5 DeepSeek host `model_not_found`, 9 OpenAI network errors in one ~1-min window), all recovered: DeepSeek moved to DeepInfra fp8 (PREREG deviation), OpenAI trials re-sent. Superseded DeepSeek records kept in `superseded/`.
- Interim observations (50 tasks, 1 repeat, 4 tempting tasks; not conclusions):
  - Frontier models are stable across catalogs: Terra 0.98 everywhere; Sonnet 0.98–1.00; Sol 0.96–0.98; Argon 0.96–1.00.
  - Smaller models move: Mistral 0.84 (V0) → 0.90–0.92 (P1, P2, MG, MS, H1, H3); Qwen 0.88 (MG) to 1.00 (MS); Haiku 0.90–0.96.
  - Excess flip rate vs. placebo with a CI excluding 0: **Claude Haiku under P1, P3 and MS (+0.08 each)**. Mean excess flip across models is small (−0.002 to +0.018).
  - **Real historical drift (H1/H3) shows almost no excess flips so far (+0.004/+0.007).**
  - 14 of 36 model pairs (models complete at the time) are "indistinguishable" under wording changes.

## 2026-11-25 · Round 1, tasks 1–84 complete (slice T034–T073)
- Ledger line 6: 3,060 new trials, **0 errors**, $3.16. Cumulative ledger spend ≈ $12.60.
- Interim (84 tasks, 1 repeat; not conclusions):
  - Frontier stable: Terra 0.98–0.99, Sol 0.96–0.99, Sonnet 0.98–1.00, Argon 0.96–0.99.
  - Smaller models vary by catalog: **Mistral 0.88 (V0) vs. 0.95 (P1)**; **Qwen 0.90 (V0R/P1) to 0.98 (MS)**; Luna 0.88 (P1) vs. 0.93 (V0); DeepSeek 0.90 (MG) to 0.98 (H3).
  - Mean excess flip vs. placebo stays small (−0.002 to +0.017); only Haiku under P3 (+0.071) has a CI excluding 0.
  - Real historical drift: mean excess +0.006 (H1) / +0.002 (H3), still close to noise.
  - **20 of 45 model pairs indistinguishable** under wording changes (up from 14/36 at 50 tasks).

## 2026-11-25 · Interim: 8 models complete (all repeats; Argon k=1)
- Data: `results/raw/main/` at 35,450/38,304 trials; analysis restricted to the 8 complete models (30,096 trials). Claude Sonnet and Qwen still running. Spend for the combined run so far ≈ $9.
- **Placebo-adjusted wording effects are small but consistent and statistically clear:** for 7 of 8 models, at least one catalog has an excess flip rate vs. V0R whose 95% CI excludes 0. **This includes the real historical catalogs:** Haiku (H3 +0.024), Flash-Lite (H1 +0.029, H3 +0.020), Luna (H1 +0.026, H3 +0.033), Terra (H3 +0.013), Mistral (H1 +0.033). Mean excess flip by catalog: MS +0.026; P1/P3/H1 +0.013; H3 +0.011; P2 +0.009; MG +0.008. One negative case: DeepSeek P2 (−0.026), which has a high placebo flip rate (0.079).
- **Noise floors differ a lot by model:** placebo flip rate 0.004 (Terra) to 0.079 (DeepSeek).
- Accuracy is stable at the aggregate level (most models within ±1–2 pp across catalogs); Flash-Lite peaks under MS (0.831 vs. 0.807).
- **Safety (24 tempting tasks × 3 repeats):** harmful-write rate averaged over catalogs: **GPT-6 Luna 23%** (V0 18%, MG 25%), **Gemini Flash-Lite 10%**, **Mistral 9%** (MG 12.5%), Sol 4%, DeepSeek 2%, Haiku/Terra 0.2%, Argon 0%.
- Indistinguishable model pairs: 5 of 28 with the full data (fewer than the noisier early slices suggested).

## 2026-11-25 · Data collection complete (38,304 / 38,304 trials)
- Archive: `results/archive/2026-11-25-complete/` (raw run, logs, ledger, run.json, errors; SHA256SUMS). Errors over the whole run: 15 logged, all recovered (5 DeepSeek host, 9 network, 1 Sonnet rate limit); 0 trials missing.
- **Spend:** OpenRouter $29.93 (billed) + OpenAI ≈ $6.25 (priced from logged usage) = **≈ $36.18** of $49.55.
- Scores: `results/scores/main-A-all10-round1/` (10 models, round 1) and `results/scores/main-B-9models-k3/` (9 models, 3 rounds). Exploratory: `results/analysis/main/analysis.json`.

### Confirmatory (PREREG)
- **H1 / H2 (accuracy):** no V0-vs-variant McNemar comparison on majority decisions survives Holm correction, in either pass. **Benign rewording and real historical drift do not significantly change aggregate accuracy.**
- **H3 (rankings):** model rankings are not preserved. Round 1, 10 models: Kendall's τ vs. V0 is 0.79–0.93 for the 7 non-placebo catalogs vs. **0.965 for the placebo**, and **the top-ranked model changes under 6 of 7 non-placebo catalogs but not under the placebo**. 9 models × 3 rounds: τ 0.78 (H1, the lowest) to 0.94; the top model changes under 4 of 7 catalogs, not under the placebo.
- **Decision-level effects (placebo-adjusted):** 24 of 70 model × catalog excess-flip rates have a 95% CI above 0 (1 below). Mean excess flip: MS +0.022, P1 +0.012, H1 +0.011, P3 +0.011, H3 +0.008, MG +0.007, P2 +0.005. **On the 55 tasks whose tools were really edited, H1/H3 excess flips are clear for Mistral (+0.048 / +0.042), Luna (+0.042 / +0.024), Haiku (H3 +0.036) and Flash-Lite (H1 +0.024).**
- **H4 (safety):** harmful-write rates on 24 tempting tasks (see interim entry): GPT-6 Luna ≈ 23% (V0 18% → MG 25%), Flash-Lite ≈ 10%, Mistral ≈ 9% (MG 12.5%); frontier models ≈ 0–4%.

### Exploratory
- **Run-to-run noise differs by 25×:** placebo flip rate 0.004 (Terra) to 0.107 (Qwen) and 0.079 (DeepSeek). pass^3 under V0: Sonnet 0.987, Terra 0.980, Sol 0.961, Haiku 0.895, DeepSeek 0.862, Qwen 0.836, Mistral 0.822, Luna 0.809, Flash-Lite 0.803.
- Indistinguishable model pairs: 8 of 45.
- Position bias: Mistral's accuracy drops when the gold tool is listed last (0.902 vs. 0.985 when first); Argon, Sol and Terra show smaller last-position drops.
- Cost artifact: Sonnet's latency includes the client-side rate-limit wait (new-account cap of 20 rpm), so its latency isn't comparable.

## 2026-11-25 · Paraphrase-equivalence judge (with controls and historical edits)
- Data: `results/judge/judge_final/` (responses.jsonl, summary.json); config `configs/judge_final.toml`. Judges: GPT-6.2 Sol and Claude Sonnet 5.5; each changed tool judged in both directions (A→B, B→A) by both judges: 848 requests, 848 answered, 0 unparsed, **$1.28**.
- Rule: a tool counts as "equivalent" only if all 4 votes say EQUIVALENT.
- **Paraphrases (36 tools each):** strictly equivalent P1 19, P2 17, P3 15; clearly not equivalent P1 0, P2 1, P3 1; the rest mixed. **The judges disagree:** GPT-6.2 Sol says EQUIVALENT on 205/216 paraphrase votes (95%), Claude Sonnet 5.5 on 134/216 (62%), often noting the difference is minor ("although the two are close", "only on a small point"). Cohen's κ between judges over all 212 pairs: 0.44 (observed agreement 0.71).
- **Negative controls behave as expected:** narrower (MS) 34/36 not equivalent, 0 equivalent; vaguer (MG) 23/36 not equivalent, 3 equivalent, 10 mixed. The judges discriminate.
- **Real historical edits:** judged meaning-changing for 15/16 tools (H1) and 14/16 (H3); none were strictly equivalent. The AssetOpsBench developers' revisions changed content (e.g., added cross-references to sibling tools), not just wording.
- **Sensitivity check (single-tool tasks):** restricted to tasks whose gold tool's paraphrase is strictly equivalent (P1 57, P2 55, P3 46 tasks), mean excess flip vs. placebo is +0.003 / +0.002 / +0.007, and 2 of 30 model × catalog CIs exclude 0 (vs. +0.008 / +0.002 / +0.006 and 5 of 30 on all single-tool tasks).
- **Interpretation:** confirmed meaning-preserving rewording moves decisions by about run-to-run noise. The clearer effects come from description changes that alter content: the real historical revisions and the scope changes (MG/MS). The paper should frame results this way, and present ranking changes among near-tied models with that caveat.

## 2026-11-25 — Correction while drafting: paraphrases vs. history on the same tasks

- On the 55 tasks whose gold tool has a recovered history, the full paraphrase catalogs move
  decisions about as much as the historical catalogs: mean excess flip rate P1 0.012, P2 0.005,
  P3 0.010 against H1 0.013, H3 0.009 (all ten models). For Luna, P1 (+0.048) exceeds H1 (+0.042).
- So the earlier reading ("rewording ≈ noise, content changes matter") holds only for paraphrases
  that both judges accepted as equivalent. That subset is selected by the judges, and tools with
  smaller edits are probably more likely to pass, so it is not a clean contrast with history.
- Judge count for the historical edits is 29 of 32 unanimous not-equivalent (H1 15, H3 14); the
  other 3 are mixed. An earlier draft said 30.
- Accuracy range across catalogs (round 1): ≤ 0.026 for seven models; Qwen and Mistral 0.039,
  DeepSeek 0.053.
- Paper framing changed accordingly: specific decisions move under all kinds of edits for four
  smaller models; only judge-accepted paraphrases stay near noise; harmless edits are hard to
  recognise in advance.
- The judge sensitivity check (entry above) also needs a plainer reading: restricting to
  strictly equivalent paraphrases leaves the mean excess almost unchanged (+0.003/+0.002/+0.007
  vs. +0.008/+0.002/+0.006 on all single-tool tasks); the drop from 5 to 2 CIs above zero comes
  with fewer tasks per interval. Judge-detected meaning change does not explain the paraphrase
  effects.
