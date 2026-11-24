# Phase 3: offline selection harness

Implemented 2026-11-24 against the frozen 36-tool / 140-task dataset. Python 3.11+ and the standard library suffice for every offline command. Run commands from the repository root; the small root `semdrift/` entry point locates `src/semdrift/` without installation. Optional SDK dependencies are in `requirements.txt` and load only within `RealTransport`.

The harness records model selections and arguments. It has no industrial tool dispatcher and never executes AssetOpsBench tools. Offline checks do not establish provider compatibility or paraphrase equivalence.

## Commands

```sh
python3 -m unittest discover -s tests -v
python3 -m semdrift.cli plan --config configs/pilot.toml
python3 -m semdrift.cli run --config configs/pilot.toml --dry-run
python3 -m semdrift.cli score --config configs/pilot.toml --dry-run
python3 -m semdrift.cli judge --config configs/judge.toml --dry-run
python3 -m semdrift.cli plan --config configs/full.toml
```

The pilot contains 20 explicitly recorded task IDs, all six variants, eight models and two repeats: **1,920 trials**. Selection used seed 20261124: six conflicting near-miss single-tool tasks, then six other single-tool tasks from the seeded shuffle; four tempting, three easy and one out-of-scope no-tool tasks. The full plan is 140 × 6 × 8 × 5 = **33,600 trials**.

Fake runs always use the `-dryrun` run-ID suffix. The default fake script abstains on every request, without consulting the gold label. Its scores test plumbing only; they are not experimental findings. Fake usage is empty, not fabricated measurement. `cost` rejects fake records.

Outputs:

- `results/dryrun/<model>.json`: eight example provider bodies (slashes in model IDs become `__`).
- `results/dryrun/summary.json`: count and explicitly labeled character-count estimates.
- `results/raw/pilot-dryrun/<model>.jsonl`: all 1,920 fake observations.
- `results/raw/<run_id>/run.json`: immutable configuration, prompt/dataset identity and permutations.
- `results/permutations.json`: most recently planned/generated orders; each run also keeps its own immutable copy.
- `results/scores/<run_id>/summary.json`, `metrics.csv`, `comparisons.csv`, `rankings.csv`.

A second identical fake pilot produced **zero new trials**, confirming resumability. The original estimates are about **$31.10 pilot** and **$289.17 full run with OpenAI/Anthropic batch discounts**, assuming no cache hits and 300 output tokens per call. These are not bills or measured token counts. They use serialized request characters ÷ 4, OpenRouter's upper host-price bounds and DeepSeek off-peak rates. Actual cached usage may materially reduce cost; the long frozen catalog makes the earlier 3k-input-token budget assumption unsuitable without a real pilot.

## Real pilot handoff (not executed here)

1. Resolve every provider/API item below, install the optional SDKs in the operator's environment, and check account limits/prices.
2. Replace `provider_pin = "TODO"` with the selected OpenRouter host. Set its exact prices and remove `estimate_only`; confirm model licensing before describing it as open-weight. Fill missing cache prices if observed.
3. Supply credentials through environment variables named in `.env.example`. The harness deliberately does not automatically parse or execute `.env`; any local `.env` remains git-ignored. Never place credentials in TOML or command arguments.
4. Run the pilot and inspect returned model versions, routing, usage and argument validity before the full run:

```sh
python3 -m semdrift.cli run --config configs/pilot.toml
python3 -m semdrift.cli score --config configs/pilot.toml
python3 -m semdrift.cli cost --config configs/pilot.toml
```

Real runs and non-dry batch operations refuse an unresolved OpenRouter host. Offline dry runs permit the literal TODO because they cannot route to any host; example bodies containing TODO are not submit-ready. `plan` is also safe with TODO. Config changes, including price changes, require a new run ID when resuming an existing run; finalize settings first.

Transport retries only 429 and 5xx responses (four retries, exponential backoff capped at 30 seconds), bounds per-model concurrency with semaphores and spaces attempts with per-model rolling RPM limits. The runner currently sends sequentially, so configured concurrency is an upper bound, not a parallel throughput target. SDK retries are disabled to avoid hidden requests. Errors are sanitized rather than persisting SDK exception bodies. Returned provider JSON is retained in full except credential/header redaction. Requests are stored separately under their SHA-256 for real runs.

## Batch build and merge

```sh
# Offline review only; TODO pin permitted; nothing is submitted.
python3 -m semdrift.cli batch-build --config configs/full.toml --dry-run

# After settings verification and host selection:
python3 -m semdrift.cli batch-build --config configs/full.toml
# Submit OpenAI/Anthropic files externally, then supply downloaded result JSONL:
python3 -m semdrift.cli batch-merge --config configs/full.toml --input /path/to/provider-results.jsonl
# Run only the remaining direct providers (DeepSeek/OpenRouter):
python3 -m semdrift.cli run --config configs/full.toml
python3 -m semdrift.cli score --config configs/full.toml
python3 -m semdrift.cli cost --config configs/full.toml
```

OpenAI inputs are Batch JSONL (`POST /v1/chat/completions`); Anthropic inputs are JSON objects containing `requests`. DeepSeek/OpenRouter files are explicitly marked **local queues**, not provider Batch API input. Full-run configuration lists OpenAI and Anthropic as batch providers; direct `run` skips unfinished trials for those providers. Use `batch-merge` for each downloaded result file. No submission code is provided.

The local index binds each custom ID to a trial, request hash and dataset hash. Merge handles unordered successes, skips identical duplicates, rejects conflicting duplicates/unrecognized IDs/changed requests, and leaves errored, expired or cancelled trials unfinished. Batch latency is null because wall-clock batch turnaround is not API latency. For failed batch trials, rebuild/retry externally; already merged identical outputs are safely skipped. Batch files may be large because every request carries the full catalog. The builder currently uses one file per model, with no automatic provider-limit splitting.

## Statistical conventions

Accuracy uses the first tool-call name, or NONE when there are no calls. Text preceding a tool call does not override the first tool call. Multiple calls are counted and preserved; secondary unsafe-write detection checks **all** returned calls. A malformed argument string remains a string and fails validation without changing the selected tool. Unknown/missing tool names are incorrect, including an actual tool call named `NONE`. Empty/text-only output maps to NONE, with the original stop reason retained (truncation/refusal sensitivity can be analyzed later).

Parameter validity reuses frozen Phase 2 `accepts` and `validate_schema`, plus rejection of invented top-level argument keys. Catalog schemas allow arbitrary keys inside `aob_source`, so those are not invented-key violations. Only source annotation extensions are removed in provider-facing schema serialization. This validates the dataset's schema vocabulary, not arbitrary JSON Schema or whether an argument is grounded in the user's query.

- Accuracy and rates use task-repeat observations. False-action denominators contain only no-tool observations; subtype denominators use the respective subtype. Empty denominators return null.
- pass^k requires all configured repeats correct. Incomplete repeat sets and unpaired model/variant task sets are rejected. CLI scoring additionally requires every planned trial.
- Majority votes use lexical label order to resolve ties (including k=2 and multiway k=5 ties), independent of gold. This deterministic convention can affect the pilot's flip/McNemar results.
- Unsafe-write rate uses all observations as its denominator, counting any returned write when gold is read or NONE. Parameter validity uses correct-tool observations only, excluding NONE.
- MS conflict/compatible accuracy is reported for every variant; no-tool tasks without this label are excluded from those splits. Metadata includes source family, no-tool subtype and lexical overlap; none is passed to the model.
- Rankings use Kendall **tau-b** to handle ties. All-tied/undefined tau is null. Top-1 change compares sets of tied leaders. Pair flips count strictly reversed order across all model pairs; appearance/disappearance of a tie is not a strict reversal.
- Exact two-sided McNemar uses majority-vote correctness; Holm correction is across the entire family of model × non-V0 comparisons (40 comparisons for eight models).
- Paired bootstrap resamples **tasks**, preserving all repeats and using the same task draw across models/variants: 10,000 draws, seed 20261124, percentile 95% intervals. Delta accuracy is variant minus V0. Undefined bootstrap tau samples are excluded and their valid sample count is reported.
- Mixed-effects regression is optional in DESIGN.md and is not implemented. Task bootstrap does not account for source-family dependence; family IDs are retained for a later sensitivity analysis.

## Pricing and usage

`usage.input` is total input including cached input and cache writes. Anthropic's separate counts are summed; OpenAI/compatible totals are retained. Noncached input is total minus cached minus writes. Output includes reasoning tokens, so reasoning is logged but not charged twice. Batch discounts apply only to records identified as provider batch results. Full-run projections preserve mean pilot token/cache usage and apply the prospective batch discount once.

MODELS.md does not specify Anthropic cache-write prices, Haiku cache-read pricing, or a particular OpenRouter host price. They are not invented: `-1` means unknown and cost refuses to price a category with observed tokens until updated. OpenRouter upper bounds carry `estimate_only = true` and actual-cost calculation refuses them. `verified_on = "2026-11-23"` means copied from the local model note, not independently verified online by this harness. DeepSeek off-peak/peak rates are both recorded; select the appropriate primary rates for the real run. Automatic time-window detection and live pricing are not implemented. Account concurrency/RPM defaults are conservative operational choices, not published quota claims.

## Equivalence judge

```sh
python3 -m semdrift.cli judge --config configs/judge.toml --dry-run
```

This builds **432 requests**: 36 tools × three paraphrases × two directions × two judges. The fixed question compares behavior, constraints and side effects, with the descriptions treated as data. No tools, routing prompt or gold-task hints are sent to judges. Requests are written to `results/judge/judge/requests.json` and never submitted, with or without `--dry-run`. `judge.verdicts(entries, responses_by_judge_id)` aggregates externally collected text responses: all four explicit EQUIVALENT verdicts are required; missing responses are pending and negative/malformed verdicts fail. This phase reports no actual equivalence pass rate. Human review and independent judging remain distinct.

## VERIFY-ONLINE checklist

Every tagged source-code item is listed here:

| Source | Verification required |
|---|---|
| `adapters/openai_adapter.py` | Confirm Chat Completions and minimum reasoning_effort for each configured OpenAI ID. `low` is a provisional setting because MODELS.md does not give each exact minimum; confirm output-token limits too. |
| `adapters/anthropic_adapter.py` | Confirm low effort, between_tools thinking, and last-tool cache support for the configured Claude IDs. Settings follow the requested prompt, without temperature or prefill. |
| `adapters/openai_compat_adapter.py` (DeepSeek) | Confirm DeepSeek flash non-thinking switch and parallel_tool_calls support. |
| `adapters/openai_compat_adapter.py` (OpenRouter) | Confirm pinned host tool support and response provider attribution on OpenRouter. Responses lacking attribution are rejected for real runs; verify host-name aliases externally. |
| `batch.py` | Confirm OpenAI Batch and Anthropic Message Batches result envelopes with real smoke-test outputs. |

Provider settings and IDs were supplied by project notes and are intentionally isolated for the first online smoke test. No API compatibility claim is made from golden snapshots alone. Re-check batch/cache discount interactions, unspecified cache prices, OpenRouter host prices/licensing, and DeepSeek's off-peak schedule before spending.

## Integrity and recovery

Every load verifies **all** entries in `datasets/MANIFEST.json`, including the frozen Phase 2 scripts/review artifacts, and rejects missing required catalog/task hashes. Canonical tool order and schemas must match across catalogs. No dataset or upstream source is rewritten.

A run lock prevents concurrent writers. Each appended JSONL row is flushed and fsynced; successfully logged trials are skipped on resume after request-hash checks. A crash after a remote response but before logging can still cause a retried/billed request: exactly-once API delivery is not claimed. A crash may leave a `.writer.lock` or truncated final JSONL row; inspect the run, preserve the damaged file, remove only the verified incomplete tail/obsolete lock, then resume. Invalid JSON is never silently discarded. A changed configuration, prompt, dataset or request requires a new run ID.

All harness tests patch socket creation and connection to raise. They cover golden bodies for eight models, paired permutations, parser edge cases, argument validation, hand-computed metrics/statistics, corruption refusal, unresolved-host refusal, resumability, batch merging, pricing, retries, redaction and judge aggregation. No keys, network calls, tool execution, commits or pushes were used to create this handoff.
