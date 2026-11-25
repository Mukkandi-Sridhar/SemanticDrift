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
