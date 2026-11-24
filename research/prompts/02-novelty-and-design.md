# Prompt 02: Close-competitor analysis, sharpened research question and experiment design

**Run in:** ChatGPT, **Deep Research** mode (web search must be on, because it has to read the papers below).
**Then:** paste the full answer back to Claude. It will be saved to `research/02-design/chatgpt-response.md`.

**Why this prompt:** prompt 01 missed the closest prior work and claimed a novelty that isn't true. This prompt makes ChatGPT read those papers directly and design an experiment that is actually new.

---

## Copy everything below this line into ChatGPT

---

You are a rigorous research advisor helping me design a 2–4 page workshop paper due December 1, 2026. Be critical and honest. Strict rules:
- **Read the actual papers** (arXiv abstract, plus method and results sections where possible) before making any claim about them.
- **Never invent papers, arXiv IDs, numbers or model names.** Write "UNVERIFIED" next to anything you couldn't confirm from a source.
- Separate **facts from sources** and **your recommendations** clearly.

### Context

**My project:** "SemanticDrift," about how LLM agents misinterpret natural-language tool descriptions (for example, Model Context Protocol (MCP) tool schemas), leading to wrong tool selection or misuse. My draft taxonomy of failure modes:
1. Over-generalization: a tool gets used for tasks it wasn't meant for.
2. Over-specialization: a valid tool isn't used for a task it applies to.
3. Contextual misalignment: the interpretation of a tool shifts with the conversation context.
4. Parameter hallucination: the model invents parameters that aren't in the schema.

**Venue:** AAAI-27 Bridge "From Agent Benchmarks to Deployment Evidence" (https://bench-to-evidence.github.io/). It examines what benchmark evidence does and doesn't support about agent **reliability, safety and the human correction effort** needed in deployment, including an industrial-maintenance case using IBM's AssetOpsBench (arXiv 2506.03828).

**Problem:** I found these recent papers, which already do controlled perturbations of tool descriptions. My original "perturb descriptions and measure accuracy" idea is therefore **not new**:

1. arXiv 2602.18914: *From Docs to Descriptions: Smell-Aware Evaluation of MCP Server Descriptions* (Peiran Wang et al.)
2. arXiv 2602.14878: *Model Context Protocol (MCP) Tool Descriptions Are Smelly!* (Hasan et al.)
3. arXiv 2610.14334: *Which Metadata Matters for LLM Tool Selection in MCP? Evidence from Controlled Factor-Level Interventions* (Xiaofan Li et al.)
4. arXiv 2610.23342: *Robust Function Calling for LLM Agents Under Interface Drift* (Chattopadhyay et al.)
5. arXiv 2510.00307: *BiasBusters: Uncovering and Mitigating Tool Selection Bias in LLMs* (Blankenstein et al.)
6. arXiv 2605.23916: *Advertising to Agents: Measuring Description-Framing Bias in LLM Tool Selection* (Wang)
7. arXiv 2605.30454: *The Surface You Test Is Not the Surface That Breaks* (Sakib et al.)
8. arXiv 2602.20426: *Learning to Rewrite Tool Descriptions for Reliable LLM-Agent Tool Use* (Ruocheng Guo et al.)
9. arXiv 2506.03828: *AssetOpsBench* (Patel et al.)

### Task 1: Close-competitor table
For each of the 9 papers, give: the exact research question; what they perturb or manipulate; the models used (names and how many); dataset size; metrics; the main quantitative findings (with numbers); and stated limitations or future work. Then add **one row per paper on what it leaves open that I could address.**

Also search for **any other 2025–2026 paper** (arXiv, ACL, NeurIPS, ICLR, ICML or AAAI workshops) that studies how *benign, meaning-preserving rewordings* of tool descriptions affect tool selection, model rankings or reliability. List anything you find with its arXiv ID.

### Task 2: Evaluate three candidate angles
For each angle, judge: **(a) novelty** given the papers above (High/Medium/Low, with the specific overlapping paper); **(b) fit** with the Bridge theme; **(c) feasibility** for one person in about 5 days with a limited API budget (around $50–100); and **(d) the risk** of a reviewer saying "this was already done in X."

- **Angle 1, ranking stability as deployment evidence:** do tool-use benchmark conclusions (model rankings, accuracy, pass^k) stay stable when the *same* tools are described in different, equally valid ways? Compare meaning-preserving paraphrases with meaning-shifting edits. Claim: a single tool-use score is weak deployment evidence if it depends on description wording. (Paper 7 does this for adversarial injection surfaces, not benign wording.)
- **Angle 2, failure-mode taxonomy as a diagnostic:** instead of measuring *whether* selection changes, classify *how* it fails (my 4 failure modes), map each type of description defect to its failure mode, and estimate the human correction effort for each.
- **Angle 3, over-generalization when no tool fits:** in an industrial-maintenance setting (AssetOpsBench-style tools), when the correct action is "no tool applies / ask the human," do vague descriptions make agents call a tool anyway? That would be a wrong action in deployment rather than a safe refusal.

Then **recommend one primary angle** (optionally plus one secondary angle used as analysis) and write the **research question(s)** in one or two sentences each, plus **2–3 testable hypotheses**.

### Task 3: Naming
"Drift" implies change over time, and paper 4 already uses "interface drift" for post-deployment description changes. My phenomenon is a static gap between developer intent and model interpretation. Should the paper keep "semantic drift" (the project name can stay SemanticDrift), or use a different term? Suggest the best option and check that it isn't already used for this concept.

### Task 4: Concrete experiment design for the recommended angle
Give a design I can implement immediately:
- **Tools:** how many, which domains, and whether and how to adapt AssetOpsBench tools (describe what its tool and agent set looks like in the repo if you can verify it).
- **Description variants:** an exact list of variant types (for example, clean, meaning-preserving paraphrase ×N, and the specific meaning-shifting edits), with **one worked example of each** for a single tool. Use an industrial tool such as a sensor-reading or work-order tool as the example.
- **Tasks:** how many, how to write them, how to set gold labels, how to include "no tool fits" tasks, and how to avoid leaking the answer.
- **Controls:** tool position and order randomization, number of candidate tools shown, distractor tools, temperature, and number of repeats.
- **Metrics with formal definitions:** selection accuracy; pass^k (= P(all k trials succeed), NOT pass@k); flip rate between variants; ranking stability (for example, Kendall's τ between model rankings across variants); false-action rate on no-tool tasks; and parameter validity.
- **Statistics:** which tests to use (for example, McNemar's test, bootstrap confidence intervals, or mixed-effects or conditional logistic regression), and the minimum number of tasks and repeats needed to detect a roughly 10 percentage-point difference.
- **Budget:** estimate the total API calls and rough cost for your recommended setup.
- **Validity threats** and how to address each.

### Task 5: Models (late 2026)
Using sources dated **2026**, list the current frontier and strong open-weight models that support tool or function calling, with their exact API model names and approximate prices per million input and output tokens. Recommend **4 models** (a mix of closed frontier, cheaper closed and open-weight) for the study, with one sentence each on why. Don't recommend GPT-4o, Llama-3 or other models from 2024 or earlier unless you have a specific reason.

### Task 6: Paper outline
Give a 4-page outline (section names, target length for each, what each figure or table shows) for the recommended angle, framed for the Bridge audience: what the evidence does and doesn't support for deployment.

### Output format
- Use the headings Task 1 … Task 6.
- Use tables wherever possible.
- End with **"Final recommendation in 5 bullets."**
