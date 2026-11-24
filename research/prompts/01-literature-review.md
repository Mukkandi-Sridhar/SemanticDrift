# Prompt 01: Literature review and novelty check

**Run in:** ChatGPT, **Deep Research** mode (or the strongest model with web search enabled).
**Then:** paste the full answer back to Claude. It will be saved to `research/01-literature/chatgpt-response.md`.

---

## Copy everything below this line into ChatGPT

---

You are a senior AI research assistant helping me prepare a short workshop paper. Your job is a rigorous, citation-verified literature review and novelty check. Accuracy matters more than length: **never invent a paper, author, venue, arXiv ID or result.** If you cannot verify something with a source, say "UNVERIFIED" next to it.

### My research

**Working title:** SemanticDrift: Measuring How LLM Agents Misinterpret MCP Tool Descriptions

**Core idea:** LLM agents choose and call tools based on natural-language tool descriptions (for example, Model Context Protocol (MCP) tool schemas). When a description is ambiguous, too broad, too narrow or context-dependent, the model's interpretation of the tool can diverge from the developer's intent. I call this divergence "semantic drift." It causes wrong tool selection, misuse of tools, and hallucinated parameters.

**My proposed drift taxonomy:**
1. Over-generalization: the model applies a specific tool to a broad, unintended set of tasks.
2. Over-specialization: the model misses that a tool applies to a valid task.
3. Contextual misalignment: the interpretation of the tool shifts with the surrounding conversation.
4. Parameter hallucination: the model invents parameters that are not in the schema.

**Planned experiment:** build a set of tool descriptions with controlled ambiguity variants (clean vs. perturbed, one perturbation type per drift category), a set of tasks with gold-standard correct tools, and measure tool-selection accuracy and drift rate across several current LLMs as ambiguity increases. Some tools will be adapted from IBM's AssetOpsBench (industrial asset-operations agent benchmark, arXiv 2506.03828).

**Target venue:** AAAI-27 Bridge "From Agent Benchmarks to Deployment Evidence," which focuses on what benchmark evidence does and does not support about agent reliability, safety and the human correction effort needed in deployment.

### What I need from you

Research the literature up to the present (late 2026) and produce the following sections.

#### Section 1: Name-collision check for "semantic drift"
- How is the term "semantic drift" already used in NLP/ML (for example, in bootstrapped information extraction, long-form generation, embedding or concept drift)? Cite the key papers.
- Has anyone already used "semantic drift" (or a close term) for tool descriptions, API documentation or agent tool use?
- Recommend whether I should keep the name (with a precise definition that separates it from earlier uses) or rename it. If you suggest renaming, give 3–5 candidate names and check that each is not already taken.

#### Section 2: Related work, grouped by theme
For each theme, list the most relevant papers (aim for 4–8 per theme; quality over quantity). For **each paper** give: title, authors (first author et al. is fine), year, venue or arXiv ID, a URL, a one-to-two sentence summary, and **one sentence on exactly how it relates to or differs from my work.**

Themes:
- **A. Tool-use and function-calling benchmarks** (for example, ToolBench/ToolLLM, API-Bank, BFCL, tau-bench, MetaTool, ToolSandbox, and newer ones).
- **B. Tool selection and tool retrieval** under many or similar tools, distractor tools, or tool confusion.
- **C. Tool documentation and description quality.** Work that shows description quality affects tool use, or that rewrites or improves tool descriptions automatically (for example, EasyTool, DRAFT, and similar).
- **D. MCP-specific research.** MCP benchmarks (for example, MCP-Bench, MCPToolBench, LiveMCPBench and others), MCP ecosystem studies, and empirical studies of real MCP server descriptions.
- **E. MCP and tool security.** Tool poisoning, tool description injection, "rug pull" attacks and tool-shadowing. Note which of these exploit description semantics, the adversarial version of my non-adversarial problem.
- **F. Robustness of LLMs to prompt and instruction perturbations**, especially perturbations of tool or API documentation.
- **G. Agent evaluation for deployment.** Reliability, consistency across repeated runs (for example, pass^k), evidence standards for agents, and industrial agent benchmarks including AssetOpsBench.

#### Section 3: Novelty gap analysis
- Given everything above, what specifically is **already done**, and what is **not yet done**?
- State the most defensible novel contribution for a 2–4 page workshop paper in one or two sentences. Be honest: if my idea largely overlaps existing work, say so and suggest the narrowest angle that is still new.
- Name the 3 closest prior works a reviewer would compare me against, and how I should position against each.

#### Section 4: Methodology guidance from prior work
- How have prior papers perturbed or degraded tool descriptions in a controlled way? Describe the concrete perturbation methods.
- Which metrics have been used for tool-selection correctness, parameter correctness and robustness? Give their formal definitions where available.
- What dataset sizes and numbers of models are typical for credible workshop-level experiments in this area?
- Common pitfalls reviewers criticize in tool-use benchmark papers.

#### Section 5: Model selection
- Which LLMs (current as of late 2026) are most commonly used in recent tool-use evaluations? Recommend 3–4 models to evaluate (a mix of closed and open-weight) with a short reason for each.

#### Section 6: Reference list
- A clean, deduplicated reference list in BibTeX for every paper you cited, with arXiv IDs or DOIs. Mark any entry you could not fully verify as `% UNVERIFIED`.

### Output format rules
- Use the section headings above exactly (Section 1 … Section 6).
- Use tables for the related-work lists (columns: Title | Authors | Year | Venue/arXiv | URL | Summary | Relation to my work).
- Keep summaries factual and short; do not pad.
- Clearly separate verified facts from your own opinions or recommendations.
- End with a short "Top 5 takeaways for my paper" list.
