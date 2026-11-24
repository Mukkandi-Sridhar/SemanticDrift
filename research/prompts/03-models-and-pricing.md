# Prompt 03: Current model lineup, exact API IDs and pricing (late 2026)

**Run in:** ChatGPT with **web search** (Deep Research is optional; this is a fact lookup).
**Then:** paste the full answer back. It will be saved to `research/02-design/models-chatgpt.md`.

**Why:** prompt 02 gave model names that couldn't be checked and prices in the wrong units ("per 1K"). We need exact facts with official links before spending any money.

---

## Copy everything below this line into ChatGPT

---

I'm running a tool-calling (function-calling) evaluation in late November 2026 and need **exact, current facts with official sources**. Rules:
- Use **only official provider pages** (pricing pages, model docs, API references) or the OpenRouter model pages. Give the **URL for every row**.
- Quote prices **per 1 million tokens (1M)**, never per 1K.
- If you can't confirm something from an official page, write **UNVERIFIED**. Don't guess or extrapolate model names.

### Part A: Model table
For each provider below, list the models that are **currently available via API and support native tool/function calling**:
OpenAI, Anthropic, Google (Gemini API), DeepSeek, Alibaba Qwen, Mistral, Meta Llama (via any official or major host), and any other open-weight family that is now commonly used for agent or tool-use evaluation.

Columns: Provider | Exact API model ID string | Release date | Open-weight? (Y/N) | Input $/1M | Output $/1M | Cached-input $/1M (if prompt caching exists) | Batch-API discount (if any) | Supports parallel tool calls? | Supports `tool_choice` "none"/"auto"/"required"? | Context window | Source URL

### Part B: OpenRouter
For the open-weight models, are they available on **OpenRouter** with tool-calling support? Give the OpenRouter model slug and price per 1M tokens, plus the URL. Also say whether OpenRouter's tool calling is reliable for these models (any known issues).

### Part C: Recommendation for my study
My study: one tool-selection call per request. Each call has about 3,000 input tokens (a catalog of ~40 tool JSON schemas, which is the same prefix every time, so caching helps) and about 100 output tokens. Per model: 3,600 calls (≈ 11M input tokens, ≈ 0.4M output tokens). Total budget is **about $100** across all models.

Recommend **7–8 models** that give a meaningful **ranking** comparison:
- 2 frontier closed models (different providers)
- 2–3 cheaper or smaller closed models
- 3 open-weight models of different sizes or families

For each recommended model, compute the **estimated cost** for 3,600 calls with and without prompt caching (show the arithmetic), and give the total. If the total goes over $100, suggest which model to run with fewer repeats (k=3 instead of 5).

### Part D: Practical notes
- Default temperature for each recommended model's API, and whether temperature can be set (some reasoning models don't allow it).
- Whether any recommended model is a "reasoning" model that adds hidden thinking tokens to the bill, and how to turn that off or limit it.
- Rate limits on a new or low-tier account that could slow a run of ~3,600 calls.
- Any free tiers or research credits currently offered.

### Output format
Use the Part A–D headings. Tables wherever possible. End with a **final list of the 7–8 models with their exact API ID strings**, ready to paste into a config file.
