# Research Log

Chronological record of research decisions and results. Newest entries at the bottom.
Personal correspondence and planning notes are kept outside the repository.

---

## 2026-11-23: Research kickoff
- Repo audit: `datasets/`, `examples/`, `figures/` and `future-code/` are empty; README claims a pilot study that is not in the repo yet. **Must fix before submission.**
- README model list (GPT-4, Claude 3.5 Sonnet, Gemini 1.5 Pro) is outdated → replace with current models.
- Created `research/prompts/01-literature-review.md` → to be run in ChatGPT Deep Research.
- **Next:** paste the ChatGPT answer back → save to `research/01-literature/chatgpt-response.md` → verify citations → write `summary.md`.

## 2026-11-23: Phase 0 results (literature review)
- ChatGPT prompt 01 answer saved: `research/01-literature/chatgpt-response.md` (raw, **not citable**).
- Verified every arXiv ID → `research/01-literature/verification.md`. **7 of 21 IDs were fake** (e.g., ToolLLM, API-Bank, MetaTool, EASYTOOL, τ-bench, TRUSTDESC). ChatGPT also defined pass^k backwards.
- Direct arXiv search found the **closest prior work that ChatGPT missed**: smell-aware mutation study (2602.18914), MCP descriptions are smelly (2602.14878), factor-level metadata interventions (2610.14334), interface drift (2610.23342), BiasBusters, Advertising to Agents, Surface You Test.
- **Decision:** "perturb descriptions → measure accuracy" alone is NOT novel. Candidate angles: (1) ranking and reliability stability under benign wording as deployment evidence; (2) failure-mode taxonomy as a diagnostic; (3) over-generalization when no tool fits, in an industrial setting.
- **Naming risk:** "interface drift" is already used; "drift" implies change over time. Decide in Phase 1.
- Verified summary: `research/01-literature/summary.md`; clean BibTeX: `research/01-literature/references.bib`.
- **Next:** run `research/prompts/02-novelty-and-design.md` in ChatGPT Deep Research → paste back.

## 2026-11-23: Phase 1 (design)
- ChatGPT prompt 02 answer saved: `research/02-design/chatgpt-response.md`. Review: `research/02-design/review.md`.
- Angle confirmed: **stability of benchmark evidence under benign rewording** (primary) + **no-tool / unsafe-write actions** (secondary). The Bridge call explicitly lists "stability of results across runs and tasks" and "correction effort".
- ChatGPT errors: prices given "per 1K" (wrong units); unverifiable model names (gpt-6.2-sol, gpt-6-luna); budget ignored the tool-catalog tokens; design too small (4 tools, 30–40 tasks, 3–4 models makes Kendall's τ meaningless).
- Found missing close work: Faghih et al., *Tool Preferences in Agentic LLMs are Unreliable* (arXiv 2505.18135).
- Verified the AssetOpsBench repo: ~40 real MCP tools across the iot / utilities / fmsr / wo servers, including near-miss read tools and write tools → **use the real catalog verbatim** as V0.
- Naming: paper concept = **"description–intent misalignment"**; the repo stays SemanticDrift.
- **Locked design:** `research/02-design/DESIGN.md` (≈40 AOB tools, 6 catalog variants, ≈120 tasks incl. ≈25 no-tool, 7–8 models, k=5, paired orderings).
- **Next:** run prompt 03 (models and pricing) in ChatGPT. In parallel, Claude starts Phase 2: extract the AOB tool catalog and build the dataset.

## 2026-11-23: Models and budget (prompt 03)
- ChatGPT answer kept in `research/02-design/models-chatgpt.md` (not to be used).
- Verified against the official OpenAI and DeepSeek pricing pages and the Anthropic model table → `research/02-design/MODELS.md`.
- ChatGPT errors: wrong cached prices (Astra, Sol, Fable), "Claude has no tool_choice" (false), "Claude default temperature ≈ 0" (false; temperature is rejected), no confirmed open-weight model, broken caching math, Batch API ignored.
- **Lineup (8):** gpt-6.2-astra, claude-opus-5-5, gpt-6.2-sol, claude-sonnet-5-5, gpt-6-luna, claude-haiku-5-5, deepseek-flash, plus one OpenRouter open-weight model (qwen3.8-27b, pending license check).
- **Policy:** tool_choice auto; no temperature; lowest reasoning setting per model; Batch API for OpenAI and Anthropic.
- **Budget:** ≈ $50–55 with batch and caching; worst case ≈ $265 → the 20-task pilot decides k for the frontier models.
- **Needs from Sridhar:** API keys for OpenAI, Anthropic, DeepSeek and OpenRouter (in a git-ignored `.env`).
- **Next:** Phase 2, extract the AOB tool catalog verbatim and build the variants and tasks.
- Second ChatGPT run of prompt 03: same lineup, but OpenAI prices 3× the official page → rejected. OpenRouter check: qwen/qwen3.8-27b supports tools but is served by ~23 hosts at different prices → **pin one host** for reproducibility. Mistral Small 4 is the backup open model. Lineup unchanged.

## 2026-11-23: Phase 2 blocked at source checkout
- Read PLAN.md, LOG.md, the locked DESIGN.md, and MODELS.md before attempting extraction.
- Required shallow clone of IBM/AssetOpsBench into `/tmp/semdrift-aob-20261123` failed (exit 128): `Could not resolve host: github.com`. No upstream commit or catalog was obtained.
- Recorded the evidence, outstanding reviews, and resume requirements in `research/03-dataset/NOTES.md`. No dataset or passing validation is claimed; design unchanged.
- No model API calls, secrets, commits, or pushes. Resume once the upstream checkout is accessible.

## 2026-11-23: Phase 2 unblocked
- Codex attempt 1 was blocked: its sandbox has no network, so the AssetOpsBench clone failed (see `research/03-dataset/NOTES.md`). No data was fabricated, which is correct behavior.
- Claude cloned AssetOpsBench into `vendor/AssetOpsBench/` (git-ignored). Commit `0d044061ab3ffd4b213ddf6a0868c360d7e9667c` (2026-11-14), Apache-2.0 license.
- Found: iot, utilities and fmsr tools use decorators; the wo tools are registered centrally (15 default tools). Scenario utterances are in `src/scenarios/` and `benchmarks/scenario_suite/`.
- **Next:** run `research/prompts/05-codex-phase2-resume.md` in Codex.

## 2026-11-23: Phase 2 dataset built; semantic sign-off pending
- Verified local AssetOpsBench commit `0d044061ab3ffd4b213ddf6a0868c360d7e9667c`; extracted 36 tools (iot 12, utilities 6, fmsr 3, wo 15), 29 read and 7 write. Used the default WO wrapper registrations and static signature schemas; source/license/hash provenance is in `datasets/tools/SOURCE.md`.
- Created six catalogs and 216 rationale entries. P1–P3 pass word and character length bounds and four-word-overlap checks. P2 uses reordered authored clauses, not independent random seeds. MG/MS scope changes are documented for review.
- Created 127 tasks: 102 single-tool, 25 no-tool, including 15 write temptations. The seven-task excess over ≈95 single-tool requests preserves four-task coverage for 15 near-miss tools. Four tasks adapt traceable upstream scenarios; the other 123 are labeled authored.
- Offline validator passes all checks; V0 reproduces byte-for-byte and five source spot-checks are recorded. Mutation tests reject nine corruptions. Saved `research/03-dataset/validation_report.txt`, review notes and `datasets/MANIFEST.json` fingerprints.
- Sridhar's manual review and independent two-way LLM equivalence judging remain pending; no semantic pass rate or experiment readiness is claimed. NOTES.md lists 15 priority paraphrases and ambiguous candidates rejected/revised during author label review.
- No network or model API calls, dependency installs, secrets, commits or pushes. Vendor checkout unchanged; pre-existing `.gitignore` changes left untouched. Only LOG.md and 03-dataset/ were modified within research/.

## 2026-11-23: Claude review of the Codex Phase 2 dataset
- Verified: 36 tools extracted exactly (5 spot-checked against source docstrings), re-extraction is byte-identical, provenance and license are complete, validator shows 0 structural failures.
- **Problems found** (`research/03-dataset/REVIEW-claude.md`): MG is truncation (median 19% of original length); MS is a template suffix ("Only for site MAIN" on 26/36 tools, while 70/127 tasks use MAIN); paraphrases drop the Args/Returns formatting; at least one paraphrase changes meaning (`get_failure_modes` P1); only 4/127 tasks come from AOB; queries share vocabulary with the paraphrases (0.307 for V0 vs. 0.325–0.345 for P1–P3); the "tempting" no-tool tasks carry explicit hints.
- **Next:** run `research/prompts/06-codex-phase2-fixes.md` in Codex.

## 2026-11-24: Phase 2 Claude-review fixes completed
- Kept V0, extract_tools.py, SOURCE.md and vendor unchanged; protected pre-revision hashes pass. Rebuilt MG/MS purpose edits with verbatim Args/Returns and ±30% length bounds. MS has 78 conflicting and 25 compatible single-tool labels, with witnesses for all 36 tools.
- Rebuilt P1–P3 inside the original docstring structure, preserving headers, indentation/line layout, backticks and references. Added all 108 author meaning-audit records with agency/constraint/addition checks and description fingerprints; fixed caller-versus-tool normalization and other agency defects.
- Rewrote 103 single-tool tasks into 6–16-word operator queries. Twenty-five adapt nine traceable upstream source anchors (not 25 independent scenarios). Retained 20 easy and 5 out-of-scope no-tool tasks and added 12 genuinely tempting no-tool tasks; total 140.
- Added lexical_overlap.py and 840 covariate rows. Final single-tool means: V0 0.348103, P1 0.352260, P2 0.346935, P3 0.329691; benign max-minus-min 0.022569 <= 0.03. MG 0.328889, MS 0.354964. Query revisions, not description tuning, reduced the overlap imbalance.
- Extended validator passes with zero failures under both normal Python and `python3 -I`, with identical output; 20 mutation cases are rejected. Refreshed NOTES.md, task provenance, audit, report and manifest. The existing tracked __pycache__/ ignore rule was already present and verified.
- Manual review and independent two-way LLM judging remain pending; no independent semantic pass rate is claimed. No model API calls, secrets, dependency installs, commits or pushes. A transient local execution interruption recovered before final validation.

## 2026-11-24: Phase 2 dataset verified by Claude
- Re-ran checks independently: validator 0 failures (also under `python3 -I`); re-extraction byte-identical (V0 untouched); vendor checkout clean at 0d04406.
- Dataset: 36 tools × 6 catalogs; 140 tasks = 103 single-tool + 37 no-tool (20 easy, 12 tempting with no hints, 5 out-of-scope). MS conflicts with 78/103 tasks; every tool has a conflicting task. Length ratios: P1–P3 0.86–1.30, MG 0.79–1.28, MS 0.98–1.25 (MG is no longer truncation). V0 vs. P1–P3 lexical-overlap spread 0.023 (≤0.03).
- Confirmed fixed: `get_failure_modes` P1 agency shift; formatting (Args/Returns) preserved; MS no longer templated.
- **Disclose in the paper:** the 26 AOB-adapted tasks come from only 10 source utterances (up to 8 tasks each); the rest are authored. Paraphrases were authored by an LLM (Codex), and P2 is derived from P1.
- Claude flags for review: MG `cancel_workorder` ("multiple work orders" claims a capability the schema lacks); MG `get_failure_modes` ("potential" overlaps `generate_failure_modes`).
- **Next:** Sridhar's manual review (`research/03-dataset/MANUAL_REVIEW.md`, 18 items) → Phase 3 harness + 20-task pilot (needs API keys).

## 2026-11-24: Sridhar's manual review (items 16–18)
- #16 MG `cancel_workorder`: ❌ "multiple work orders" invented batch cancellation → fixed to "Cancel a maintenance record (-> CAN)." (broader object, still true).
- #17 MG `get_failure_modes`: ❌ "potential failure modes" implied generation → fixed to "READ failure-mode information for an asset class."
- #18 MS `generate_work_order`: ✅ "preventive" is a valid domain narrowing; kept.
- Overlap recomputed (V0/P spread still 0.0226); manifest hashes refreshed; validator 0 failures.
- **Still pending:** items 1–15 (P1–P3 paraphrase equivalence) and the independent LLM equivalence check.

## 2026-11-24: Sridhar's manual review complete
- Paraphrases (items 1–15): **12 meaning-preserving as written, 3 corrected**:
  - #2 P2 `stream_extent`: restored "Reserved metadata identifiers".
  - #3 P3 `history`: "remaining record bookkeeping metadata" → "all other record metadata".
  - #4 P2 `history`: same metadata fix; dedup reworded to "Repeated names are deduplicated, with their original order preserved." (Sridhar's exact wording copied 4+ words from V0, which breaks the paraphrase rule, so it was reworded with the same meaning.)
- MG/MS (items 16–18): 2 corrected, 1 kept.
- Meaning-audit records, hashes and manifest updated; overlap spread still 0.0226; validator 0 failures.
- **Paper wording:** "Of 15 highest-risk paraphrases, 12 were judged meaning-preserving on manual review; 3 were corrected before the experiments."
- **Remaining validation:** independent LLM two-way equivalence check over all 108 paraphrases (needs API; do it in the pilot phase).
- **Next:** Phase 3 harness.

## 2026-11-24: Phase 2 follow-up author review

- Corrected the remaining unsupported batch-operation claim in MG approve_workorder to “Approve a maintenance record (-> APPR).”; updated its scope rationale. This follows the manually accepted cancellation correction but is a new author correction, not an additional human verdict.
- Reconciled NOTES.md and validator review-status output with the completed 18-item manual review recorded above; independent two-way LLM judging remains pending.
- Regenerated overlap CSV and validation report: 0 failures in normal and isolated mode, identical outputs; corruption-test suite passes. Benign overlap spread remains 0.022569; MG mean is 0.334021. Refreshed manifest fingerprints.
- Frozen V0/extractor/SOURCE.md unchanged; vendor clean at the pinned SHA. No network/API calls, secrets, commits or pushes.

## 2026-11-24: Phase 3 offline evaluation harness

- Implemented the standard-library harness under src/semdrift: manifest-verified loading, paired permutations, fixed prompt hashes, eight model adapters, lazy real/fake transports, first-call parsing, resumable JSONL runs, batch build/merge, scoring, usage costs and two-way judge request construction. No industrial tools are executed.
- Added models/pilot/full/judge TOML configs. Pilot deterministically selects 12 single-tool and 8 no-tool tasks meeting the requested strata. Full plan contains 33,600 trials. OpenRouter remains TODO and blocks real runs; fake dry runs explicitly permit it.
- Executed the 1,920-trial fake pilot; saved eight request examples and estimates. Repeating the same run added zero records. Generated fake-only score tables using 10,000 paired task bootstrap draws and 432 unsubmitted judge requests for 108 pairs. These are not model findings or equivalence verdicts.
- No-cache character/4 estimates, assuming 300 output tokens/call: pilot $31.10; full run with OpenAI/Anthropic batch discounts $289.17. OpenRouter uses the documented upper host-price bounds; DeepSeek uses off-peak rates. Actual pilot usage/caching remains necessary. Missing cache prices are explicitly unknown, not fabricated.
- Statistical conventions and online API verification items are recorded in research/04-harness/README.md. Majority ties use lexical labels; ranking tau-b handles ties; Holm covers all model/variant comparisons; incomplete paired results are rejected.
- Offline tests cover requests, parsing, statistics, integrity, resumability, batching, costs, retries, secret redaction and judge aggregation. All sockets are disabled in the harness suite. Dataset/Phase 2 manifest hashes remain intact and vendor status remains clean. No network/API calls, credentials, dependency installations, commits or pushes.

## 2026-11-24: Claude review of the Phase 3 harness
- Independently re-ran: 18 harness tests OK; dataset validator 0 failures; V0 byte-identical.
- Request bodies look right: Claude gets tools + `cache_control` on the last tool, `tool_choice` auto + `disable_parallel_tool_use`, no temperature; Opus/Haiku effort `low`; Sonnet `between_tools` + effort `low`. OpenAI/DeepSeek/OpenRouter use the function-tool format with parallel calls off.
- Anthropic VERIFY-ONLINE item checked against the current Claude API reference: effort `low` (Opus 5.5, Haiku 5.5), `between_tools` (Sonnet 5.5, effort ≤ high) and tool caching are all valid. Still open: OpenAI minimum `reasoning_effort` value, the DeepSeek `thinking: disabled` switch, the OpenRouter host pin, and the batch result envelopes, which will be confirmed by the smoke test.
- Scoring spot-checked: exact McNemar (0,6)→0.03125, (1,9)→0.0215; Kendall τ reversed → −1, one swap of 4 → 0.67. pass^k uses all-k-correct (correct definition).
- **Cost warning:** the catalog is ≈6k input tokens per call. Estimate with no cache: pilot ≈ $31, full ≈ $289. Caching must be measured before scaling → **smoke test first** (1 task × 6 variants × 8 models ≈ 48 calls, ≈ $1–2).
- To add before the pilot: flag or exclude trials with stop_reason `refusal` / `max_tokens` / `length` in scoring.

## 2026-11-24: Budget decision ($20)
- Sridhar's budget: existing OpenAI credit ($10) + OpenRouter top-up ($10). No Anthropic or DeepSeek accounts.
- New lineup (7 models, 6 labs): gpt-6-luna, gpt-6.1-terra (OpenAI direct); claude-haiku-5.5, deepseek-v4.1-flash-1017 (fp8), qwen3.8-27b (fp8), mistral-small-2603, gemini-3.1-flash-lite (OpenRouter, pinned hosts). Details in MODELS.md.
- k = 3 for the full run (pilot k = 1). New configs `configs/budget_*.toml`; Codex's original 8-model configs kept unchanged so its tests still pass (18/18 OK).
- OpenRouter adapter extended with optional `quantizations` and `reasoning.effort` (marked VERIFY-ONLINE).
- Dry run: pilot 840 trials ≈ $1.40. Full ≈ $20 without caching → the smoke test must confirm caching, or apply the fallbacks.
- Needed in `.env`: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`.

## 2026-11-24: Enhanced plan (before any spending)
- Sridhar will fund more credits for a stronger study (no free models). Wrote `research/02-design/ENHANCED_PLAN.md`.
- Pipeline weaknesses found: no placebo noise floor (W1, critical), single rewriter (W2), throwaway pilot (W3), cache-unaware scheduling (W4), no severity tiers (W5), few tempting tasks (W6), unverified API settings (W7), no pre-registration (W8).
- Headline findings designed: wording noise vs. model gap (indistinguishable model pairs), ranking instability vs. placebo, unsafe writes under vagueness, cost per correct decision.
- OpenRouter facts (docs, 2026-11-24): Anthropic/Gemini/Qwen need `cache_control`; DeepSeek and OpenAI cache automatically; batch ≈ −50% but tool support undocumented; 5.5% credit fee.
- Tiers: A ≈ $7–9 (7 cheap models), **B ≈ $27–35 (+3 frontier; recommended)**, C ≈ $65–80 (with caching). Decision pending from Sridhar.

## 2026-11-24: Key discovery: real description drift in AssetOpsBench's history
- Fetched the full AOB git history (1,170 commits; HEAD still 0d04406, working tree unchanged).
- Tool server files changed often since Feb 2026 (iot 57 commits, fmsr 30, utilities 16, wo 11).
- **55 older versions of tool descriptions exist; 43 keep identical parameter names**, spread over 18 of the 36 tools (e.g., `sites` 8 versions, `assets` 10, `stream_extent` 5).
- These are **real, developer-authored description changes**, i.e. genuine "semantic drift" over time. A "historical catalog" condition would test whether real-world documentation evolution changes agent behavior. This is much stronger than LLM-only paraphrases and literally matches the project name.
- Proposed as the paper's centerpiece (pending Sridhar's go-ahead).

## 2026-11-24: Behavior-preserving harness code-quality pass
- Refactored 18 unfrozen Python files: readable layout, typed public functions, named helpers, clearer fixtures, and unchanged serialized output order.
- Preserved four manifest-frozen Phase 2 Python files byte-for-byte at Sridhar's direction; validator cleanup and the dataset-test move were excluded to preserve integrity hashes.
- All baseline outputs and dataset/dry-run hashes matched; the same 18 harness tests and 1 dataset mutation test passed. Additional comparisons matched 90 request/record serializations and six scoring summaries.
- Added minimal Python >=3.11/Ruff configuration; existing Ruff 0.17.2 check and format checks passed. Documented metrics, exceptions, and the unchanged null-tool-calls issue in `research/04-harness/CODE_QUALITY.md`; no network, new dependencies, or commits.

## 2026-11-24: Codex code-quality pass verified
- Verified: tests OK, validator 0 failures, V0 reproduces, the 3 hashed frozen files are unchanged, vendor clean.
- Codex refactored the 18 harness files (now clean), but **also froze `validate_dataset.py`, `lexical_overlap.py` and `test_dataset_checks.py`** (they're hashed in MANIFEST.json), so the messiest file (124 one-space-indented lines in `validate_dataset.py`) is still uncleaned.
- Fixed the bug Codex reported: `runner._called_tools` crashed on `"tool_calls": null` (and Anthropic `content: null`). It now treats them as text-only, consistent with `parse.py`. Tests OK; dry run OK.


## 2026-11-24: Phase 2 script code-quality follow-up
- Refactored validator checks by concern and lexical-overlap helpers; added types, named thresholds, four-space layout, and a 100-character limit while preserving output text and ordering.
- Moved `test_dataset_checks.py` to `tests/`, replacing mutation lambdas with named fixtures. Normal unittest discovery now passes all 19 original tests; all 20 corruption cases match the original validator's output and exit status byte-for-byte.
- Normal and isolated validators both report zero failures with baseline-identical output; lexical stdout and CSV bytes and all dataset files except the authorized manifest update are unchanged. The three protected originals remain frozen.
- Refreshed only the three script entries (including the moved test path) and, with explicit approval, the hashed NOTES entry. Added the required provenance note; no data-file hashes changed.
- Ruff check/format checks pass using the existing installation. Updated `research/04-harness/CODE_QUALITY.md` with metrics and comparison evidence; no network/API calls, new dependencies, or commits.

## 2026-11-24: Stronger study built (pre-spend)
- **Historical drift:** `src/semdrift/extract_history.py` parses every commit of the 4 tool servers (no upstream code executed). **42 earlier, developer-written descriptions across 16 tools** have a schema identical to V0. Catalogs: H1 (earliest), H2 (midpoint, built but not run), H3 (just before V0). Reproducible (byte-identical re-run). Versions in `datasets/history/versions.json`; edit features in `datasets/history/edit_features.json` (median text similarity to V0 0.49; 15/42 older versions have fewer sibling-tool references).
- **Placebo V0R** (byte-identical copy of V0) added to measure run-to-run noise.
- New catalogs are registered in MANIFEST.json and loaded via `data.EXTENDED_FILES`; `tests/test_history.py` checks them (placebo identical; every changed description is a real historical version; names, schemas and access unchanged).
- **+12 tempting no-tool tasks** (T141–T152, no hints) → 152 tasks, 24 tempting. Overlap covariate regenerated (P-spread unchanged 0.0226). Fixed the tempting-count mutation test for the larger set.
- **Harness:** staged runs (`--tasks/--repeats/--models` add to one run), cache-friendly trial order, OpenRouter sticky `session_id`, per-model cache hints (`top_level`/`explicit`), severity tiers and a severity-weighted cost in scoring.
- **Main config** `configs/main.toml`: 10 models (Tier B) × 9 variants (V0, V0R, P1–P3, MG, MS, H1, H3) × 152 tasks × k=3 = **41,040 trials**.
- **Pre-registration** written: `research/PREREG.md` (hypotheses H1–H5, metrics, analysis plan, exclusions, staging and stopping rule, frozen hashes).
- Cost (my estimate; 6k input / 150 output tokens): with warm caches ≈ $35 total (OpenAI ≈ $13, OpenRouter ≈ $22); without caching ≈ $210. **The smoke test must confirm caching before the pilot.** OpenAI's existing $10 is not enough for all 3 OpenAI models: top up ~$10, or route gpt-6.x via OpenRouter.
- Tests: all pass; validator 0 failures.
- TODO (analysis code, before results): excess flip rate vs. placebo, indistinguishable pairs, variance decomposition, historical-subset analysis.

## 2026-11-25: Pre-flight audit before spending (Claude)
- Checked the official OpenAI and OpenRouter docs and OpenRouter's model metadata. **Found 5 problems that would have broken or overpaid the paid run, all fixed:**
  1. gpt-6.1-terra: tool calling only via the **Responses API** → all OpenAI models moved to a new `openai_responses_adapter.py` (`store: false`).
  2. gpt-6-luna: Chat Completions tools only with reasoning `none` → now `none` (its lowest).
  3. OpenRouter responses have **no top-level `provider` field** → the runner would have aborted every OpenRouter call after paying. Attribution now comes from `openrouter_metadata` (header `X-OpenRouter-Metadata: enabled`) and is non-fatal; the pin is enforced by `allow_fallbacks: false`.
  4. The OpenAI SDK path would have rejected OpenRouter-only fields (`reasoning`, `cache_control`, `session_id`) → replaced the SDK transport with a plain stdlib HTTPS client that sends the logged body verbatim (the SDKs weren't installed anyway), with `.env` loading and readable, redacted error messages.
  5. **Default reasoning levels would have multiplied the cost** (Qwen defaults to `xhigh`, DeepSeek to `high`, Sonnet to `high`) → each model now uses its lowest accepted level (see PREREG Deviations, 2026-11-25); mandatory-reasoning models get max_tokens 4096.
- Usage parsing is now None-safe; it records OpenRouter's billed `usage.cost` (used as the cost when present) and cache-write tokens.
- Added `cli probe`: 2 identical real calls per model (≈ $0.05) to verify request acceptance and caching before the smoke stage. Wrote `research/RUNBOOK.md` (steps, commands, pass criteria, cost projection rule).
- Coverage/power: 55 of 103 single-tool tasks have a gold tool whose description changed historically; per-model minimum detectable change ≈ 8 pp (historical subset) / ≈ 6 pp (all single-tool tasks), before pooling across models.
- Tests: 25/25 pass; validator 0 failures; smoke-stage dry run OK (90 trials).
- **Blocker:** the `.env` key values are currently empty.

## 2026-11-25: Recording, safety and analysis plan
- Runner: failures are logged to `errors.jsonl` instead of aborting; a per-model breaker pauses a model after 3 consecutive failures (its trials stay pending); `--max-spend` caps each stage on real spend; one `ledger.jsonl` line per stage (git commit, filters, spend by model, errors); request bodies saved gzip-compressed (~1 GB → a fraction); a progress line every 100 trials. Tests: 27/27 pass.
- Wrote `research/ANALYSIS_PLAN.md` (confirmatory A1–A6 from PREREG; exploratory B1–B6: confusion matrices, tool-level attribution of real edits, edit features vs. effect, noise and position bias, cross-model agreement, severity, cost/latency frontier, robustness checks, qualitative examples; data preservation).
- Started `research/FINDINGS.md` (append-only lab notebook), with the pre-data dataset observations.

## 2026-11-25: Analysis module ready before data
- `src/semdrift/analysis.py` + `cli analyze`: placebo-adjusted (V0R) excess flip rates with task-bootstrap CIs (all tasks and the historical subset), indistinguishable model pairs, per-tool attribution of the real historical edits, confusions, position bias, severity profiles, repeat agreement, billed cost and latency per correct decision. Works on partial stages. Tested on synthetic results (28/28 tests pass).
- PREREG Deviations: clarified (pre-data) that McNemar uses per-task majority decisions and that Holm runs over all model × variant comparisons, matching the scorer.
- `.env` keys still empty: the probe is waiting on them.

## 2026-11-25: Probe done ($0.14 spent)
- Keys in `.env`; balances OpenRouter $35.00, OpenAI $14.55.
- Probe: 9/10 models OK; Gemini 4 Carbon (and Neon) banned for this account → Gemini 4 Argon on the flex tier (PREREG deviation recorded). Caching confirmed on 8 models. Projected full run: **$24.90**. Details in FINDINGS.md.
- Runner: one thread per model (thread-safe progress and errors); 28/28 tests pass.

## 2026-11-25: Smoke stage done
- Committed bf3b9e9 (pre-experiment) before any experiment data. Smoke: 90/90 OK, 0 errors, $0.378. Archived with checksums. Next: pilot (20 tasks × repeat 0, cap $10), pending Sridhar's go.

## 2026-11-25: Pilot done; stopping rule triggered by cost
- Pilot: 1,710 new trials, 0 errors, $5.89 (above estimate). Claude cache placement was wrong (top-level → per-question cache entries); fixed to a system-message breakpoint, verified with 3 calls. Added `--amend` (logged in run.json with the previous fingerprint) for settings that don't change what the model is asked. Gemini 4 Argon caches poorly (~$0.006/call), so the full k=3 is unaffordable for it.
- First observations recorded in FINDINGS.md. Decision on Argon and on the next stage pending from Sridhar.

## 2026-11-25: Data collection complete
- 38,304/38,304 trials; archived with checksums. Total spend ≈ $36.18 (OpenRouter $29.93 + OpenAI ≈ $6.25).
- Confirmatory scoring in two passes (10 models round 1; 9 models × 3 rounds) because Argon has k = 1. Headline: no significant accuracy changes, but model rankings and the top-ranked model change under benign and real-history rewording beyond the placebo; clear placebo-adjusted decision flips for several models, including on real IBM edits; harmful writes concentrated in small models.
- Process notes: the run was interrupted 3 times (2 manual restarts for throughput/rate limits, 1 session end); each interruption is logged in ledger.jsonl and nothing was lost. The Anthropic API key in .env was tested (free models call): invalid (401).
