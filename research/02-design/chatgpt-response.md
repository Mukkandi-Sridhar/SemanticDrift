# Prompt 02: ChatGPT raw response (2026-11-23)

> Saved as received (lightly reformatted into tables). **Not citable as-is.** Model names, prices, per-paper model lists and venues are unverified, and several are wrong. See `review.md`.

---

## Task 1: Summary of related papers

| Paper | Research question | Manipulation | Models | Dataset | Metrics | Key results | Stated limitations | Open gap for SemanticDrift |
|---|---|---|---|---|---|---|---|---|
| From Docs to Descriptions: Smell-Aware Evaluation of MCP Server Descriptions (Peiran Wang et al., 2026, arXiv:2602.18914) | Which description quality dimensions ("smells") exist in MCP tool schemas, and how do they affect LLM tool selection? | Mutated MCP tool descriptions on each of 4 dimensions (Functionality, Accuracy, InfoCompleteness, Conciseness); clean vs. perturbed. | GPT-4o-mini (1 model) | 10,831 MCP servers (analysis); controlled tests: 10 servers × 100 queries, and 10 groups of 5 equivalent servers × 100 queries | Tool-selection probability | Functionality +11.6%, Accuracy +8.8% when clean; standard-compliant description chosen 72% vs. a 20% baseline (+260%). Info +5.9%, Conciseness +1.5%. | Static descriptions only; single proprietary LLM; isolated dimension perturbations. Future work: richer context, automated repair. | No benign paraphrases or context shifts; no "no-tool" tasks or hallucinated parameters. |
| Model Context Protocol (MCP) Tool Descriptions Are Smelly! (Mohammed M. Hasan et al., 2026, arXiv:2602.14878) | How prevalent are smells, and does augmenting descriptions improve task success? | Identified missing components in 856 tools / 103 servers; augmented descriptions via an LLM pipeline. | GPT-4.1, Qwen3-48B, GLM-4.5, Qwen3-80B (4) | MCP-Universe tasks (6 domains; 119 tasks) | Success rate, Average Evaluator score, steps | Median +5.85 pp success (p=0.02), +15.12% AE (p<0.01), +67% steps; 54.2% improved, 16.7% regressed. GPT-4.1 Finance 40.0%→57.5%. | Expensive LLM scoring; augmentation can hallucinate; gains not universal; no long multi-turn. | Enrichment, not paraphrasing; no failure categories or no-tool cases. |
| Which Metadata Matters for LLM Tool Selection in MCP? (Xiaofan Li et al., 2026, arXiv:2610.14334) | Which metadata (server name, tool name, description, schema) most influences tool choice? | Pairwise interventions changing exactly one metadata field. | GPT-5.4-mini, Claude Sonnet 4.6, Gemini 3.5 Flash, DeepSeek V4 Pro, Qwen3.7-Plus (5) | 5 tool-selection tasks, balanced candidate lists | Selection probability (conditional logistic regression) | Schema changes largest effect; parameter-explaining descriptions increase selection; name effects small and inconsistent. | Single-step only; few tasks; no multi-turn or ambiguous wording. | No over-generalization or context-dependent interpretation; no surface paraphrasing. |
| Robust Function Calling for LLM Agents Under Interface Drift (Chattopadhyay et al., 2026, "NGEN-AI", arXiv:2610.23342) | How robust are agents to interface changes; can SchemaShield recover? | Edited schemas and descriptions; added or removed distractor tools. | Qwen3.5-9B "(and presumably others)" | DICE-300, BFCL-200 | Accuracy | 0.717 / 0.580 under drift → 0.813 / 0.805 with repair; recovered 19/22 and 33/45; distractors cause most errors. | Post-deployment changes; single model; random/masked edits. | Not the static intent–interpretation gap; no error-mode classification. |
| BiasBusters (Blankenstein et al., 2025, arXiv:2510.00307) | How biased is tool selection; can it be mitigated? | Clusters of equivalent tools; metadata perturbations; filter + uniform sampling. | "7 LLMs (unspecified, likely GPT-4, Claude, etc.)" | "10 clusters × 5 APIs" | Bias (total variation), success, mitigation | Systematic fixations; description changes shift choices; query–description alignment drives choice. | Synthetic queries; English RapidAPI only. | No misinterpretation types; fairness focus. |
| Advertising to Agents (Haochuan K. Wang, 2026, arXiv:2605.23916) | Do promotional phrases bias selection? | Praise, structured vs. prose limits, order, "Sponsored" label, system warning. | 2 OpenAI models + 5 exploratory | "Not explicitly stated" | Pick rate | Stacked praise +43 pp; first position +72 pp; structured fields help; Sponsored label dampens. | Preliminary; small. | Persuasive language, not neutral paraphrase. |
| The Surface You Test Is Not the Surface That Breaks (Sakib et al., 2026, "NeurIPS workshop", arXiv:2605.30454) | Does injection robustness depend on the attacked surface? | Same payload in tool output vs. tool description. | 13 LLMs, AgentDojo 4 suites | 4 suites | Ranking stability; attack success | 44.9% of model pairs flip order; 76.9% riskier-surface prediction; defenses miss the description surface. | Adversarial only. | No benign rewording. |
| Learning to Rewrite Tool Descriptions (Ruocheng Guo et al., 2026, arXiv:2602.20426) | Can one model rewrite descriptions for better agent performance? | Trace-Free+ curriculum. | "GPT-4.1, Claude Sonnet 4.5, Gemini 3-pro" | Synthetic + StableToolBench | Accuracy, query-level success | −29.23% degradation, +60.89% success at 150+ tools. | Synthetic data; no human verification. | No failure categorization. |
| AssetOpsBench (Patel et al., 2025, arXiv:2506.03828) | How to evaluate agents on industrial maintenance? | 4 agents, 141 queries, 460 scenarios. | Framework | IoT, FMSR, TSFM, WO | 3 metrics | 250+ users, 500+ agents. | Framework paper. | No description-quality analysis. |

**Other benign-rewording papers:** "We found no additional work explicitly testing meaning-preserving paraphrases of tool descriptions."

## Task 2: Candidate angles

| Angle | Novelty | Bridge fit | Feasibility | Reviewer risk |
|---|---|---|---|---|
| 1. Ranking stability under paraphrases | Medium (Sakib = adversarial surfaces; BiasBusters and Faghih et al. = promotional/adversarial wording) | High | Medium-High | Medium; differentiate by the deployment-evidence framing and benign paraphrases |
| 2. Diagnostic taxonomy | Low-Medium | Medium | Low (manual analysis) | High |
| 3. No-tool over-generalization | High | High | High | Low |

**Recommended:** Angle 1 as primary, Angle 3 as secondary.
- RQ1: Do meaning-preserving paraphrases significantly change tool-selection accuracy or model rankings? H1: ≥10% accuracy degradation; Kendall's τ < 0.9.
- RQ2: Benign paraphrases vs. meaning-shifting edits. H2: meaning-shifting edits cause larger drops.
- RQ3: Do vague descriptions cause tool calls on no-tool tasks? H3: higher false-action rate; agents seldom abstain.

## Task 3: Naming
Recommends replacing "semantic drift" in the paper with **"semantic misalignment"** or **"description–intent misalignment"**; the project name stays SemanticDrift.

## Task 4: Experiment design (as proposed)
- 4–5 tools (getSensorReading, averageSensorValue, reportMaintenanceIssue, fetchWorkOrderStatus, plus optional distractors).
- Variants: clean; 2–3 paraphrases; over-generalized; over-specialized. Worked examples for getSensorReading and reportMaintenanceIssue.
- 30–40 tasks, including no-tool tasks.
- Randomized tool order; temperature 0; k=5 repeats; distractors.
- Metrics: accuracy, pass^k (all k succeed), flip rate, Kendall's τ, false-action rate, parameter validity.
- Statistics: McNemar, bootstrap CIs, optional mixed-effects logistic regression; "30–50 tasks" for a 10 pp effect.
- Budget: ~1,800 calls, "~$7–10."
- Threats: leakage, position bias, small task set, stochasticity, English only.

## Task 5: Models (as claimed)
- "gpt-6.2-sol / gpt-6.1-sol", "$4.00 per 1K input, $20.00 per 1K output"
- "gpt-6-luna", "$0.05/$0.25 per 1K"
- "Claude Sonnet 5.5", "~$2.00/$10.00 per 1K"
- "DeepSeek V4-Flash", "$0.14/$0.28 per 1K"
- Alternative: "Gemini 3.5 Flash-Lite $0.30/$2.50"

## Task 6: Outline
Intro (0.5 p) · Related Work (0.5 p) · Problem Formulation (0.5 p) · Experimental Setup (1.0 p) · Results (1.0–1.2 p; Fig. 1 variants example, Fig. 2 accuracy bars, Table 1 flip rate and Kendall's τ, no-tool false-action bars) · Discussion (0.5 p) · Conclusion (0.3 p).

## Final 5 bullets
1. Focus on Angle 1. 2. Include no-tool cases (Angle 3). 3. Rename to "semantic misalignment." 4. 3–4 models × ~40 tasks × 2–3 variants × 5 runs. 5. Formal metrics; McNemar; ~30–40 tasks for 10 pp.
