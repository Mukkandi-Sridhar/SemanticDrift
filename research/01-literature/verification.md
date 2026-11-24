# Citation verification: Prompt 01 (checked 2026-11-23 against the arXiv API)

Method: each arXiv ID from ChatGPT's answer was looked up on export.arxiv.org; wrong IDs were re-found by title search.

## Results

| Paper (as ChatGPT cited it) | ChatGPT's ID | Verdict | Correct reference |
|---|---|---|---|
| ToolBench / Tool manipulation (Xu) | 2305.16504 | ✅ ID correct · ❌ author "Rui Xu" wrong · ❌ summary mixes it up with ToolLLM | Qiantong Xu et al., 2023 |
| ToolLLM (Qin) | 2310.01090 | ❌ **FAKE ID** (that's a maths paper) · ❌ author "Hongyang" wrong | **2307.16789**, Yujia Qin et al., 2023 |
| API-Bank (Li) | 2310.05513 | ❌ **FAKE ID** (a speech paper) · ❌ author wrong | **2304.08244**, Minghao Li et al., EMNLP 2023 |
| BFCL (Patil) | none | ⚠️ ICML 2025 is plausible · ❌ first name "Utsav" wrong (Shishir G. Patil) · pages unverified | Patil et al., ICML 2025: check the proceedings before citing |
| MetaTool (Huang) | 2310.01762 | ❌ **FAKE ID** (a sampling paper) | **2310.03128**, Yue Huang et al. (ICLR 2024) |
| How Many Tools Should an LLM Agent See? | 2605.24660 | ✅ correct | Vyzantinos Repantis et al., 2026 |
| Tool-DE (Lu) | EmergentMind link | ❌ **not a citable source**; no arXiv match found | Drop it |
| EASYTOOL (Yuan) | 2401.07139 | ❌ **FAKE ID** (satellite video) · ❌ "AISTATS 2024" wrong | **2401.06201**, Siyu Yuan et al. |
| DRAFT (Qu) | 2410.08197 | ✅ ID correct (first posted 2024) | Changle Qu et al. (ICLR 2025) |
| Learning to Rewrite Tool Descriptions | 2602.20426 | ✅ ID correct · ❌ author "Xuchao Guo" wrong | Ruocheng Guo et al., 2026 |
| MCPToolBench++ | 2508.07575 | ✅ correct | Shiqing Fan et al., 2025 |
| LiveMCPBench | 2508.01780 | ✅ ID correct · ❌ author "Guo" wrong · ❌ "ICASSP" invented | Guozhao Mo et al., 2025 |
| MCPTox | 2508.14925 | ✅ ID correct · ❌ author "Xichen Wang" wrong | Zhiqiang Wang et al., 2025 |
| Jamshidi, Securing MCP | 2512.06556 | ✅ ID correct · ❌ **title wrong** · ❌ "JACM" invented | "Semantic Attacks on Tool-Augmented LLMs: Securing the Model Context Protocol Against Descriptor-Level Manipulation", Saeid Jamshidi et al., 2025 |
| TRUSTDESC (Ye) | 2601.05975 | ❌ **FAKE ID** (a finance paper) | **2604.07536**, Hengkai Ye et al., 2026 |
| Flip-Flop Consistency (Hejabi) | none (ACL 2026) | ⚠️ paper is real; ACL 2026 venue unverified | **2510.14242**, Parsa Hejabi et al. |
| τ-bench (Yao) | 2305.04218 | ❌ **FAKE ID** (a Mandelbrot paper) · ❌ "ICLR 2024" wrong · ❌ **pass^k definition backwards** | **2406.12045**, Shunyu Yao et al., 2024 |
| AssetOpsBench (Patel) | 2506.03828 | ✅ correct | Dhaval Patel et al., 2025 |
| LLM agent evaluation survey | 2507.21504 | ✅ ID correct · ❌ author "Jianwei Wang" wrong | Mahmoud Mohammadi et al., 2025 |
| Know When To Stop (Spataru) | none (NAACL 2024) | ✅ real | **2404.05411**, Ava Spataru et al., NAACL 2024 |
| Li et al., EDBT 2014 (semantic drift in IE) | none | ⚠️ unverified; not on arXiv | Check DBLP before citing |

**Score:** 7 of 21 IDs were fake or pointed to unrelated papers, and 9 author or venue errors were found. Nothing from ChatGPT goes into the paper without this check.

## Factual error that matters

**pass^k was defined backwards.** In τ-bench, **pass^k is the probability that *all* k independent trials succeed** (a consistency measure). "At least one of k succeeds" is pass@k. Using the wrong one in the paper would be an obvious error to reviewers.

## Major gap: ChatGPT missed the closest prior work

A direct arXiv search found several 2026 papers that do **exactly** the "controlled perturbation of tool descriptions" ChatGPT said nobody had done. See `summary.md` §3.

- 2602.18914, *From Docs to Descriptions: Smell-Aware Evaluation of MCP Server Descriptions* (Peiran Wang et al.): 18 smell categories, **controlled mutation study** on tool selection.
- 2602.14878, *MCP Tool Descriptions Are Smelly!* (Hasan et al.): 856 tools; 97.1% have at least one smell; augmenting descriptions gives a +5.85 pp median task-success improvement but regresses in 16.67% of cases.
- 2610.14334, *Which Metadata Matters for LLM Tool Selection in MCP?* (Xiaofan Li et al.): one-factor-at-a-time interventions on name, description and schema across 5 LLMs.
- 2610.23342, *Robust Function Calling for LLM Agents Under Interface Drift* (Chattopadhyay et al.): **uses the word "drift"** for post-deployment description and schema changes.
- 2605.23916, *Advertising to Agents: Measuring Description-Framing Bias in LLM Tool Selection* (Haochuan Kevin Wang).
- 2510.00307, *BiasBusters* (Blankenstein et al.): small description perturbations shift tool choice.
- 2602.03580, *Don't believe everything you read* (Zhihao Li et al.) and 2606.04769, *Description-Code Inconsistency* (Yutao Shi et al.): descriptions that don't match the code.
- 2605.30454, *The Surface You Test Is Not the Surface That Breaks* (Sakib et al.): model rankings flip depending on the injection surface (tool output vs. tool description).
