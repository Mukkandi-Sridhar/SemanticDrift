# Enhanced plan: stronger findings per dollar (2026-11-24)

Goal: before spending any API credit, (1) close the weaknesses a reviewer would attack, (2) add analyses that produce a **headline finding** for the Bridge, and (3) engineer cost so every dollar buys evidence.

---

## 1. Honest review of the current pipeline

| # | Weakness | Why it matters | Fix (cost) |
|---|---|---|---|
| W1 | **No noise floor.** Models are stochastic, so some answers flip between two identical runs. Our "flip rate under paraphrase" means nothing unless it beats the flip rate under *no change at all*. | This is the first question a reviewer asks; without it the main claim is unprovable. | Add a **placebo variant `V0R`**: an identical copy of V0, run with the same tool order. Paraphrase effect = flips(V0→P) − flips(V0→V0R). (+1 variant) |
| W2 | **One rewriter.** All paraphrases were written by one LLM (Codex), and P2 is derived from P1. A result could be "Codex style", not "benign rewording". | Undermines generality; already a disclosed limitation. | Replace P2 with an **independent paraphrase set written by Claude**, with the same rules, validator and judge. Three paraphrase sets from 2 independent writers. ($0 API; ~1 hour) |
| W3 | **Pilot money is thrown away.** The pilot is a separate run. | Wastes ~10% of the budget. | Make the pilot the **first slice of the full run** (same run_id, trial IDs and permutations), so its trials count. ($0) |
| W4 | **Cache-unaware scheduling.** About 97% of every call is the same ~5,800-token tool list. Caches last ~5 minutes; the runner order doesn't keep them warm. | Without cache hits the cost is ~5–10× higher. | Run trials **grouped by (model, variant, permutation)**; send OpenRouter `session_id` per group (sticky routing); add `cache_control` where the provider requires it (Anthropic, Gemini, Qwen via OpenRouter). Measure hits in the smoke test. ($0) |
| W5 | **Errors are only right or wrong.** The Bridge asks to "separate serious failures from tolerable ones" and to measure "correction effort". | Misses the venue's central framing. | **Severity tiers** for every error: *benign* (wrong read tool, easy to retry), *wasted* (asked a human when a tool fitted), *harmful* (write tool when none or a read was correct). Report a severity-weighted score and a correction-effort proxy. ($0, analysis only) |
| W6 | **Few tempting tasks** (12) for the safety claim. | Wide confidence intervals on the unsafe-write rate. | Add 12 more tempting no-tool tasks (24 in total). (+~9% trials) |
| W7 | **Unverified API details** (`VERIFY-ONLINE`). | A silent setting bug would invalidate a model's data. | The smoke test confirms each setting from real responses, and logs the effective reasoning and cache settings. (<$1) |
| W8 | **No pre-registration.** | For an "evidence" venue, hypotheses fixed before data are much more credible. | Commit and tag the hypotheses, metrics, analysis plan and dataset hashes **before** the first paid call (`git tag prereg-v1`). ($0) |

**What's already strong** (verified): exact catalog extraction with provenance; paired permutations; leakage check; lexical-overlap control; human-reviewed paraphrases; ms_conflict labelling; correct pass^k, McNemar and Kendall's τ.

---

## 2. Headline findings the study is now designed to produce

1. **"Wording noise vs. model gap."** For each pair of models, is their accuracy difference larger than the swing caused by benign rewording (beyond the placebo noise floor)? Headline form: *"X of Y model pairs cannot be reliably ordered once tool descriptions are benignly reworded."* This speaks directly to "do benchmark results support deployment decisions?" A **variance decomposition** (task, model, wording, run-noise) gives the numbers.
2. **Ranking instability.** Kendall's τ and top-1 changes across P1–P3, compared against the placebo.
3. **Safety under vagueness.** The unsafe-write rate on tempting tasks: V0 vs. MG, with severity tiers. Industrial framing, using Dhaval's own catalog.
4. **Cost as evidence.** Logged cost per correct decision for each model. The Bridge lists cost as a deployment need. (Free from the logs.)
5. **Position bias** from the paired permutations. (Free side finding.)

---

## 3. Cost engineering (facts checked 2026-11-24)
- Prompt size measured from the dry-run bodies: **≈5,950 tokens per call**, of which ≈5,800 is the tool list (shared prefix).
- **OpenAI:** automatic prompt caching for prompts ≥1,024 tokens. Batch API −50%.
- **OpenRouter** (docs): Anthropic needs `cache_control` (top-level automatic mode supported), reads at 0.1×, 5-minute TTL. Gemini: docs contradict each other, so send `cache_control` anyway. DeepSeek: automatic. Qwen (Alibaba): explicit `cache_control`. Cache usage is reported in `usage.prompt_tokens_details.cached_tokens` / `cache_write_tokens`. `session_id` gives sticky routing (60-minute expiry).
- **OpenRouter Batch API:** "typically 50%" off, usually within 24 h. **Tool-calling support isn't documented**, and `provider.order` is rejected in batch (use `provider.only`). Use batch only if the smoke test proves it works with tools.
- **OpenRouter credit fee:** 5.5% (min $0.80); no markup on inference.

With warm caches, a call costs roughly **10–25% of the no-cache price**. That's what makes a bigger study affordable.

---

## 4. Budget tiers

Assumes ≈6k input + 150 output tokens per trial, 3,192 trials per model, cached input at 0.05–0.1× of list price; reasoning tokens could add 10–30%. Add a 5.5% OpenRouter top-up fee.
 (7 variants = V0, V0R, P1, P2′, P3, MG, MS; 152 tasks; k = 3)

| Tier | Models | Trials | Est. cost with caching | Without caching |
|---|---|---|---|---|
| **A: $20** | 7 cost-efficient models (luna, terra, haiku-5.5, deepseek-v4.1-flash, qwen3.8-27b, mistral-small-4, gemini-3.1-flash-lite) | ≈22k | **≈$7–9** | ≈$36 |
| **B: recommended, ≈$45–60** | Tier A + **3 frontier models**: `gpt-6.2-sol` (OpenAI), `anthropic/claude-sonnet-5.5`, `google/gemini-4-carbon` (OpenRouter) | ≈32k | **≈$27–35** | ≈$165 |
| **C: ≈$100+** | Tier B + `gpt-6.2-astra` and `claude-opus-5.5` (top tier) | ≈38k | ≈$65–80 | ≈$440 |

Tier B gives **10 models / 5 labs / 45 model pairs**, covering cheap and frontier models. That makes the claim "this affects even frontier models, not just small ones" testable, which is what makes the paper stand out.

**Spending order (no money wasted):**
1. **Smoke test** (<$1): every model, 1 task × 7 variants. Confirms settings, tool calls, cache hits and real token counts.
2. **Stage 1** = repeat 1 of the full run on the 20 pilot tasks. It counts toward the final data. Check cost per trial against the estimate.
3. **Stage 2** = repeat 1 on all tasks → a first complete analysis (go/no-go for the frontier models).
4. **Stage 3** = repeats 2–3. Stop at any point if spending runs ahead of the estimate.
5. **Judge** (all 108+ paraphrase pairs, two judges, both directions): about $1.

---

## 5. Future work (after submission)
- End-to-end runs in the AssetOpsBench environment (multi-step agents, real tool execution in its simulator) to measure correction effort directly.
- Offer the description-robustness suite to AssetOpsBench as reproducible scenarios.
- Extend beyond AssetOpsBench to other MCP catalogs to test whether the effects generalize.

## 6. Work needed before the smoke test (Codex prompt 09)
W1 placebo variant; W3 staged run; W4 cache-aware scheduling, `session_id` and `cache_control`; W5 severity tiers and correction-effort proxy; W6 +12 tempting tasks; W7 effective-settings logging; variance decomposition and "indistinguishable pairs" in scoring; Tier B model configs. **Claude** writes the independent P2′ paraphrase set (W2) and the pre-registration document (W8).
