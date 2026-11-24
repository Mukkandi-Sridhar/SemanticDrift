# Review of ChatGPT prompt 02 (checked 2026-11-23)

## ✅ What holds up
- **Angle choice is sound:** Angle 1 (stability under benign rewording) as the core, Angle 3 (no-tool over-generalization) as the secondary. This is confirmed by the Bridge page itself, whose listed topics include **"stability of results across runs and tasks"**, **"separating serious failures from tolerable ones"** and **"correction effort"**, plus an industrial-maintenance case built on AssetOpsBench.
- Paper numbers taken from abstracts (Peiran Wang +11.6 / +8.8 / 72%; Hasan +5.85 pp / 16.67%; Chattopadhyay 0.717→0.813, 0.580→0.805; Sakib 44.9% / 76.9%; Guo 29.23% / 60.89%) match the arXiv abstracts.
- The renaming suggestion is reasonable (decision below).

## ❌ What is wrong or unverified
| Claim | Problem |
|---|---|
| Prices "per 1K tokens" ($4/$20, $0.05/$0.25 …) | Units are almost certainly wrong. API prices are quoted **per 1M tokens**; $20 per 1K output tokens would be absurd. Its whole budget estimate is unreliable. |
| "gpt-6.2-sol", "gpt-6-luna", "DeepSeek V4-Flash" | **Unverified model names.** Confirm them on the official pricing pages (prompt 03). |
| Per-paper model lists (e.g., "GPT-4o-mini (1 model)", "GPT-5.4-mini, Claude Sonnet 4.6 …") | Not in the abstracts; unverified. Don't quote them without opening each PDF. |
| Venues "NGEN-AI", "NeurIPS workshop" | Unverified; cite as arXiv preprints. |
| "Faghih et al." mentioned without a citation | **Real and highly relevant:** Kazem Faghih et al., *Tool Preferences in Agentic LLMs are Unreliable*, arXiv **2505.18135**. Description edits gave >10× more usage; 17 models. Added to references. |
| "No paper tests meaning-preserving paraphrases" | Not contradicted by an arXiv search, but **don't claim "first" in the paper.** Say "to our knowledge, prior work studies promotional, adversarial or quality-degrading edits; we isolate meaning-preserving rewording." |
| Budget: 1,800 calls × 70 tokens | Wrong. Every call must include the **whole tool catalog** (~2–4k input tokens), not 50 tokens. |

## ⚠️ Design flaws I'm correcting

1. **Kendall's τ with only 3–4 models is almost meaningless.** With 4 models, a single swap moves τ from 1.0 to 0.67, so "τ < 0.9" can't be tested. **Fix:** evaluate **7–8 models** (mostly cheap ones) and also report how often the **top-ranked model changes**, plus pairwise flip rates (the same statistic as Sakib et al.).
2. **4–5 toy tools aren't realistic,** and reviewers will say so. **Fix:** use the **real AssetOpsBench MCP tool catalog** (verified in the repo: about 40 tools across the `iot`, `utilities`, `fmsr` and `wo` servers). It already contains natural near-miss pairs (`latest_reading` vs. `history` vs. `sensor_stats`; `installed_sensors` vs. `measured_sensors`; `get_failure_modes` vs. `generate_failure_modes`) and **read vs. write tools** (`generate_work_order`, `cancel_workorder` …), which lets us measure *unsafe* actions.
3. **30–40 tasks is too few** for per-condition McNemar tests at a 10 pp effect. **Fix:** about 120 tasks (about 95 single-tool tasks and about 25 no-tool / ask-the-human tasks).
4. **Temperature 0 plus pass^k conflict.** At temperature 0, repeats are near-identical, so pass^k carries little information. **Fix:** use each provider's default temperature with k=5, and treat run-to-run variance as part of the evidence.
5. **Paraphrase validity is the #1 reviewer attack** ("your paraphrase changed the meaning"). **Fix:** every paraphrase is (a) checked by Sridhar by hand and (b) checked by an LLM judge for two-way equivalence. Any that fail are regenerated, and the validation rate is reported.
6. **Order confound.** **Fix:** paired design, where repeat *r* uses the same random tool order across all description variants. Order effects then cancel out in the variant comparison.

## Naming decision
- Project and repo: **SemanticDrift** (unchanged).
- Paper concept: **"description–intent misalignment"**, defined explicitly and contrasted with "interface drift" (Chattopadhyay et al.), which concerns *post-deployment changes*.
- Working paper title (draft): *"Same Tools, Different Words: How Benign Rewording of Tool Descriptions Undermines Agent Benchmark Evidence."*
