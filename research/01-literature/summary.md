# Literature review: verified summary (Phase 0)

**Status:** verified against arXiv on 2026-11-23. Sources: ChatGPT Deep Research (prompt 01) plus direct arXiv searches.
Every paper listed here exists. Where a venue still needs checking, it's marked ⚠️.

---

## 1. Name: "semantic drift"

- The term is **already used** in NLP:
  - bootstrapped information extraction, where iterative extraction drifts away from the target concept (classic usage; Li et al., EDBT 2014 ⚠️ verify on DBLP);
  - long-form generation (Spataru et al., *Know When To Stop*, NAACL 2024, arXiv 2404.05411), which defines a "semantic drift score."
- **New collision:** *Robust Function Calling for LLM Agents Under Interface Drift* (arXiv 2610.23342) uses **"interface drift"** for tool descriptions and schemas that *change after deployment*.
- **Key observation:** "drift" implies change over time. Our phenomenon is a *static gap* between what the developer meant and what the model understands, so the word is somewhat misleading.

**Decision (pending prompt 02):** keep **SemanticDrift** as the project or repo name, but in the paper either (a) define the term precisely and contrast it with "interface drift," or (b) use a clearer paper-level term. Candidates to check: *tool-intent misalignment*, *description–intent gap*.

---

## 2. Related work by theme (verified)

### A. Tool-use and function-calling benchmarks
| Paper | Ref | Note |
|---|---|---|
| On the Tool Manipulation Capability of Open-source LLMs | Qiantong Xu et al., 2023, arXiv 2305.16504 | Early tool-manipulation benchmark |
| ToolLLM: Facilitating LLMs to Master 16000+ Real-world APIs | Yujia Qin et al., 2023, arXiv 2307.16789 | ToolBench (RapidAPI) and ToolEval |
| API-Bank | Minghao Li et al., EMNLP 2023, arXiv 2304.08244 | Dialogue-based API calling |
| Berkeley Function Calling Leaderboard (BFCL) | Shishir G. Patil et al., ICML 2025 ⚠️ | Standard function-calling leaderboard |
| τ-bench | Shunyu Yao et al., 2024, arXiv 2406.12045 | Introduces **pass^k = P(all k trials succeed)** |

### B. Tool selection
| Paper | Ref | Note |
|---|---|---|
| MetaTool Benchmark | Yue Huang et al., arXiv 2310.03128 | Whether to use a tool and which one; similar-choice subtasks |
| How Many Tools Should an LLM Agent See? | Vyzantinos Repantis et al., 2026, arXiv 2605.24660 | Shortlist size; Bits-over-Random metric |
| BiasBusters | Thierry Blankenstein et al., arXiv 2510.00307 | Small description perturbations shift selection; positional bias |
| Advertising to Agents | Haochuan Kevin Wang, arXiv 2605.23916 | Promotional wording raises a tool's pick rate by about 43 pp; order effects |

### C. Description quality and rewriting ⭐ closest area
| Paper | Ref | Note |
|---|---|---|
| EASYTOOL | Siyu Yuan et al., arXiv 2401.06201 | Condenses documentation into concise instructions |
| DRAFT (From Exploration to Mastery) | Changle Qu et al., arXiv 2410.08197 | Iterative self-refinement of documentation |
| Learning to Rewrite Tool Descriptions | Ruocheng Guo et al., 2026, arXiv 2602.20426 | Learned rewriting improves selection and execution |
| **MCP Tool Descriptions Are Smelly!** | Mohammed Mehedi Hasan et al., arXiv 2602.14878 | 856 tools; 97.1% contain a smell; 56% don't state their purpose clearly; augmentation gives a +5.85 pp median gain but regresses in 16.67% of cases |
| **From Docs to Descriptions: Smell-Aware Evaluation** | Peiran Wang et al., arXiv 2602.18914 | 18 smell categories, 10,831 servers, **controlled mutation study** on selection |
| **Which Metadata Matters for Tool Selection in MCP?** | Xiaofan Li et al., arXiv 2610.14334 | Changes one factor at a time (name, description, schema); schema has the largest effect |
| **Robust Function Calling Under Interface Drift** | Aniruddha Chattopadhyay et al., arXiv 2610.23342 | Post-deployment description and schema changes; distractor tools cause the most damage, while description edits alone do less |

### D. MCP benchmarks
| Paper | Ref |
|---|---|
| MCPToolBench++ | Shiqing Fan et al., arXiv 2508.07575 |
| LiveMCPBench | Guozhao Mo et al., arXiv 2508.01780 |
| HumanMCP (tool-retrieval queries) | Shubh Laddha et al., arXiv 2602.23367 |

### E. MCP and tool security (the adversarial counterpart)
| Paper | Ref |
|---|---|
| MCPTox | Zhiqiang Wang et al., arXiv 2508.14925 |
| Semantic Attacks on Tool-Augmented LLMs (Securing MCP) | Saeid Jamshidi et al., arXiv 2512.06556 |
| TRUSTDESC | Hengkai Ye et al., arXiv 2604.07536 |
| Don't believe everything you read (misleading descriptions) | Zhihao Li et al., arXiv 2602.03580 |
| Description-Code Inconsistency in MCP | Yutao Shi et al., arXiv 2606.04769 |
| The Surface You Test Is Not the Surface That Breaks | Syed Nazmus Sakib et al., arXiv 2605.30454 |

### F. Prompt-perturbation robustness
| Paper | Ref |
|---|---|
| Flip-Flop Consistency | Parsa Hejabi et al., arXiv 2510.14242 (ACL 2026 ⚠️) |

### G. Agent evaluation for deployment
| Paper | Ref |
|---|---|
| AssetOpsBench | Dhaval Patel et al., arXiv 2506.03828 |
| Evaluation and Benchmarking of LLM Agents: A Survey | Mahmoud Mohammadi et al., arXiv 2507.21504 |
| τ-bench (pass^k) | see A |

---

## 3. Novelty: honest reassessment ⚠️ important

ChatGPT claimed that *"no study has used controlled perturbations of tool descriptions."* **That is false.** In 2026 alone:
- Peiran Wang et al. (2602.18914) mutated descriptions by smell type and measured the effect on selection.
- Xiaofan Li et al. (2610.14334) intervened on one metadata factor at a time across 5 LLMs.
- Chattopadhyay et al. (2610.23342) studied description and schema changes as "interface drift."
- Hasan et al. (2602.14878) measured description smells against agent performance.
- BiasBusters and Advertising to Agents showed that wording shifts tool choice.

**So the plain "perturb descriptions and measure accuracy" study is no longer new.** A reviewer at this Bridge would likely know at least one of these papers.

### What still looks open (to be confirmed by prompt 02)

These angles fit the Bridge theme ("what benchmark evidence supports about deployment"):

1. **Do benchmark conclusions survive realistic description variation?** Measure whether model *rankings* and pass^k stay stable when the same tools are described in different, equally valid ways (meaning-preserving paraphrases vs. meaning-shifting edits). Sakib et al. did this for *adversarial injection surfaces*; nobody has done it for *benign* wording. This argues that a single tool-use score is weak deployment evidence.
2. **The failure-mode taxonomy as a diagnostic.** Prior work measures *whether* selection changes. Our taxonomy describes *how* it fails (over-generalization, over-specialization, contextual misalignment, parameter hallucination), mapping each description defect to a failure mode and its likely deployment cost.
3. **Over-generalization as a safety problem in industrial settings.** When *no* tool fits, do vague descriptions make agents call one anyway? In asset maintenance, that's a wrong action rather than a refusal. Use AssetOpsBench-style tools. This ties directly to Dhaval's domain.

**Recommendation (draft):** angle 1 as the core claim, angle 2 as the error analysis, and angle 3 as the industrial case study if time allows. To be finalized after prompt 02.

---

## 4. Methodology notes (verified or corrected)

- **pass^k** = probability that **all** k trials succeed (τ-bench). **pass@k** = at least one succeeds. Use pass^k for reliability.
- Control **tool position and order**: BiasBusters, Advertising to Agents and Which Metadata Matters all found strong position effects. Randomize or balance positions, or the results won't be valid.
- Change **one factor at a time** (as in 2610.14334).
- Report variance across repeated runs, and use a statistical test (for example, McNemar's test or a mixed-effects or conditional logistic regression).
- Manually check a sample of failures before assigning taxonomy labels.

## 5. Models

ChatGPT's suggestions (GPT-4o, Llama-3-70B, Mistral-7B) are **outdated for late 2026** and were not verified. Prompt 02 asks for the current lineup with sources.
