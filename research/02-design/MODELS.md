# Model lineup: verified (2026-11-23)

Sources checked today: OpenAI developer pricing page (developers.openai.com/api/docs/pricing), DeepSeek API pricing page (api-docs.deepseek.com/quick_start/pricing), Anthropic model table (Claude API reference, cached 2026-11-03), and OpenRouter provider listings. **Re-check prices on the day of the run.**

## What ChatGPT got wrong (prompt 03)
| Claim | Verified |
|---|---|
| gpt-6.2-astra cached input $0.80 | **$0.40** |
| gpt-6.2-sol cached input $0.20 | **$0.10** |
| claude-fable-5-2 cache read $0.08 | **$0.20** |
| Claude "tool_choice not documented" | Wrong. `auto` and `none` are supported. Forced `any`/`tool` **returns a 400** on Opus 5.5, Sonnet 5.5 and Fable 5.2, so we use `auto` (which our design needs anyway) |
| "Anthropic default temperature ≈ 0" | Wrong. Current Claude models **reject** `temperature` (400), so the provider default is the only option. This matches our "provider default temperature" protocol |
| Mistral Large 4 / Medium 3.5 are "open-weight Y" | Unverified. Mistral Medium has historically been closed. **Its lineup had no confirmed open-weight model** |
| Omitted `claude-opus-5-5` ($4/$20) and `gpt-6.1-terra` ($1/$5) | Both exist and are better value than Fable 5.2 / Astra for our purposes |
| Second ChatGPT run: astra $24/$120, sol $6/$30, terra $0.50, luna $0.05 | **Contradicts the official page** checked the same day ($8/$40, $2/$10, $1/$5, $0.10/$0.50). Official values kept |
| Second run: "set OpenAI temperature to 0" | Not adopted. One policy for all models: provider default (Claude rejects temperature; pass^k needs natural variation) |
| Caching math ("$104 with caching") | Wrong. It didn't apply caching to frontier models, and it ignored the **Batch API (−50%)** |
| ✅ OpenAI and DeepSeek model IDs, DeepSeek prices, gpt-6-luna price | Correct |

## Verified prices (per 1M tokens, standard / short context)
| Model ID | Provider | Input | Cached input | Output | Batch | Notes |
|---|---|---|---|---|---|---|
| `gpt-6.2-astra` | OpenAI | $8.00 | $0.40 | $40.00 | 50% off | OpenAI's top model |
| `gpt-6.2-sol` | OpenAI | $2.00 | $0.10 | $10.00 | 50% off | |
| `gpt-6.1-terra` | OpenAI | $1.00 | $0.05 | $5.00 | 50% off | |
| `gpt-6-luna` | OpenAI | $0.10 | $0.01 | $0.50 | 50% off | small |
| `claude-fable-5-2` | Anthropic | $8.00 | $0.20 | $40.00 | 50% off | thinking always on |
| `claude-opus-5-5` | Anthropic | $4.00 | $0.20 | $20.00 | 50% off | thinking always on; effort default `medium` |
| `claude-sonnet-5-5` | Anthropic | $2.00 | $0.10 | $10.00 | 50% off | thinking can be turned off (`between_tools`) |
| `claude-haiku-5-5` | Anthropic | $0.10 | n/a | $0.50 | 50% off | prompts ≤100K tokens |
| `deepseek-flash` | DeepSeek | $0.15 off-peak / $0.30 peak | $0.003 / $0.006 | $0.60 / $1.20 | n/a | thinking on by default, can be disabled; **open-weight status not stated on the page** |
| `deepseek-v4-pro` | DeepSeek | $0.66 / $1.32 | $0.022 / $0.044 | $1.98 / $3.96 | n/a | same |

Open-weight candidates on OpenRouter (model pages checked 2026-11-23):
| Slug | Price per 1M (in / out) | `tools` + `tool_choice` | License on page |
|---|---|---|---|
| `qwen/qwen3.8-27b` | **varies by host**: $0.035–$0.99 in / $1.25–$3.20 out across ~23 providers | ✅ listed | not stated |
| `mistralai/mistral-small-2603` (Mistral Small 4) | $0.15 / $0.60 (Mistral-hosted) | ✅ listed | not stated |

⚠️ **Pin the host.** Different OpenRouter providers may serve different quantizations of the same open model, which would add noise to a stability study. Pin one provider (OpenRouter `provider.order` with `allow_fallbacks: false`) and log the provider for every response. License and open-weight status: confirm on the Hugging Face model card before calling the model "open-weight" in the paper.

## Recommended lineup (8 models)
| # | Model | Role | Why |
|---|---|---|---|
| 1 | `gpt-6.2-astra` | Frontier, OpenAI | Top of the ranking |
| 2 | `claude-opus-5-5` | Frontier, Anthropic | Half the price of Fable 5.2 |
| 3 | `gpt-6.2-sol` | Mid, OpenAI | |
| 4 | `claude-sonnet-5-5` | Mid, Anthropic | |
| 5 | `gpt-6-luna` | Small, OpenAI | |
| 6 | `claude-haiku-5-5` | Small, Anthropic | |
| 7 | `deepseek-flash` | Different lab, very cheap | |
| 8 | One OpenRouter open-weight model (`qwen/qwen3.8-27b` preferred) | Open-weight | Confirm the license and tool support before the run |

Eight models give 28 model pairs, enough for a meaningful Kendall's τ and pairwise flip rate.

## Settings policy (same for every model)
- `tool_choice: auto`, at most one tool call. Temperature is **not set** (provider default; required for Claude).
- **Reasoning:** each model at its **lowest available reasoning setting** (Claude Opus 5.5: effort `low`; Sonnet 5.5: thinking off via `between_tools`; Haiku 5.5: effort `low`; OpenAI: lowest reasoning effort the model allows; DeepSeek: non-thinking mode). Log the exact setting. *Rationale:* a fast, cheap first-action routing call, as in deployment.
- Use the **Batch API** for OpenAI and Anthropic (−50%, not latency-sensitive). Use the DeepSeek off-peak window.

## Budget estimate (k=5, 3,600 calls per model, ~3k input tokens with the catalog cached, ~300 output tokens for thinking models / ~100 otherwise)
| Model | Estimate (batch, cache hits) | Worst case (no cache hits, no batch) |
|---|---|---|
| gpt-6.2-astra | ~$25 | ~$130 |
| claude-opus-5-5 | ~$13 | ~$65 |
| gpt-6.2-sol | ~$6 | ~$33 |
| claude-sonnet-5-5 | ~$3 | ~$26 |
| gpt-6-luna | <$1 | ~$1.5 |
| claude-haiku-5-5 | ~$1 | ~$1.5 |
| deepseek-flash | <$1 | ~$3 |
| open-weight (OpenRouter) | ~$2–5 | ~$5 |
| **Total** | **≈ $50–55** | ≈ $265 |

**The gap between those columns is caching.** The **20-task pilot** measures real cache hits and output length. If Astra or Opus don't get cache hits in batch mode, run them at **k=3**, or drop Astra and keep `gpt-6.2-sol` as the OpenAI top model.

## Accounts needed (Sridhar)
- OpenAI API key (platform account with billing)
- Anthropic API key (Claude Console)
- DeepSeek API key
- OpenRouter key (for the open-weight model)

Keys go in a local `.env` file, which is git-ignored and never committed.

---

## ⚠️ Budget lineup adopted (2026-11-24) and used for the experiments
**Budget:** $20 in total = Sridhar's existing OpenAI credit ($10) + OpenRouter ($10). The 8-model lineup above is kept for reference but **not run**.

| Model (config key) | Route | Host pin / precision | $/1M in / cached / out | Lab |
|---|---|---|---|---|
| `gpt-6-luna` | OpenAI direct | — | 0.10 / 0.01 / 0.50 | OpenAI |
| `gpt-6.1-terra` | OpenAI direct | — | 1.00 / 0.05 / 5.00 | OpenAI |
| `anthropic/claude-haiku-5.5` | OpenRouter | `anthropic` (first-party) | 0.10 / 0.01 / 0.50 | Anthropic |
| `deepseek/deepseek-v4.1-flash-1017` | OpenRouter | `tenstorrent`, fp8 | 0.03 / 0.001 / 0.20 | DeepSeek |
| `qwen/qwen3.8-27b-fp8` (API id `qwen/qwen3.8-27b`) | OpenRouter | `chutes`, fp8 | 0.039 / 0.0039 / 1.25 | Alibaba (open-weight) |
| `mistralai/mistral-small-2603` | OpenRouter | `mistral` (first-party) | 0.15 / 0.015 / 0.60 | Mistral |
| `google/gemini-3.1-flash-lite` | OpenRouter | `google-ai-studio` (standard) | 0.25 / 0.025 / 1.50 | Google |

OpenRouter slugs, hosts, quantization, prices and tool support were read from OpenRouter's public API (`/api/v1/models`, `/models/<slug>/endpoints`) on 2026-11-24. Seven models from six labs give 21 model pairs for ranking analysis.

**Design changes:** k = 3 repeats (pass^3) instead of 5; the pilot uses k = 1 (840 trials); no batch API (OpenAI prefix caching instead). The equivalence judges are `gpt-6.1-terra` + `anthropic/claude-haiku-5.5`. Configs: `configs/budget_{pilot,full,judge}.toml`.

**Cost estimate (dry run, no cache, 150 output tokens):** pilot ≈ $1.40. Full run at k=3 ≈ $9.50 OpenAI + ≈ $10.30 OpenRouter → **over budget unless caching works.**
**Fallbacks, decided after the smoke test:** (1) drop `gpt-6.1-terra` (saves ≈ $8.60 of OpenAI); (2) move Gemini to the `flex` tier at half price (saves ≈ $2.20); (3) run k = 2 for the most expensive OpenRouter model.

**Paper framing:** "seven cost-efficient models commonly used for tool routing". **Limitation:** no frontier models.
