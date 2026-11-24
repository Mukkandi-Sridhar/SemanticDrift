# Phase 2 code-quality follow-up — 2026-11-24

This follow-up supersedes the earlier four-script freeze. Only
`src/semdrift/extract_tools.py`, `datasets/tools/v0_original.json`, and
`datasets/tools/SOURCE.md` remain frozen by `protected_files.json`; their hashes
are unchanged. No algorithms, thresholds, check names/order/messages, CSV formats,
CLI arguments, or data-file hashes changed. No dependencies, network/API calls,
or commits were made.

## Changes

- Split validation into catalog/schema, variant, task, provenance/review, and
  covariate functions, coordinated by one `main()`. Named the length bounds,
  overlap tolerance/gap, coverage minima, query bounds, and audit/catalog counts.
- Extracted lexical catalog loading and mean computation into named helpers;
  retained tokenization, stopwords, CSV row/key order, and float formatting.
- Moved the mutation suite to `tests/test_dataset_checks.py`, with named mutations
  and shared copy/run/assert helpers. It retains the same test name and 20
  corrupted-copy cases, restores temporary files after assertions, and supports
  both normal discovery and direct execution.
- Added annotations and short module summaries. Preserved the old CLI descriptions
  separately and verified their help text. The three refactored files have no
  semicolon statement joins, one-space block indents, or lines over 100 characters.
- Removed only these three sources from Ruff exclusions. The extractor remains
  excluded. An independently edited `runner.py` needed one comprehension reflow
  for the global format check; its before/after ASTs matched, and its existing
  logic was preserved. No further changes from the earlier harness pass were made.

## Before / after

Physical lines and longest function spans include signatures, blank lines, and
nested definitions. Literal semicolons include punctuation in preserved report
strings and CLI help; separator tokens count only actual joined statements.

| File | Lines | Longest function | Literal `;` | Statement joins | Lines >100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `src/semdrift/validate_dataset.py` | 261 → 724 | 145 → 41 | 22 → 11 | 11 → 0 | 40 → 0 |
| `src/semdrift/lexical_overlap.py` | 61 → 100 | 14 → 19 | 3 → 1 | 2 → 0 | 4 → 0 |
| `src/semdrift/test_dataset_checks.py` → `tests/test_dataset_checks.py` | 85 → 227 | 69 → 24 | 14 → 1 | 13 → 0 | 20 → 0 |

## Baseline and verification

Fresh baseline, captured before this follow-up's edits and never overwritten:
`/var/folders/wf/gdffq11j5417w_1q91m109s40000gn/T/semdrift-phase2-quality-baseline/`.
After-run outputs, hash manifests, Ruff logs, and corruption comparisons:
`/var/folders/wf/gdffq11j5417w_1q91m109s40000gn/T/semdrift-phase2-quality-after/`.

| Check | Result |
| --- | --- |
| Normal validator stdout/stderr/exit | identical ✅; 0 failures |
| Isolated (`-I`) validator stdout/stderr/exit | identical ✅; 0 failures |
| Lexical-overlap stdout/stderr/exit | identical ✅ |
| Lexical CSV bytes / SHA-256 | identical ✅ |
| All 13 dataset files other than the authorized `MANIFEST.json` update | identical ✅ |
| Three frozen files, checked against `protected_files.json` | identical ✅ |
| Validator and overlap CLI help text | identical ✅ |
| 19 test names and outcomes, mapped one-to-one | identical ✅ |
| Validator stdout/stderr/exit for all 20 corruption cases | identical ✅ |
| Every manifest entry resolves and matches its file | passed |
| `ruff check` and `ruff format --check` | passed; 21 Python files formatted |

`python3 -m unittest discover -s tests -v` now discovers all 19 tests without
`PYTHONPATH` or installation. Before this follow-up, the same set required two
commands: 18 tests under `tests/` and 1 under `src/semdrift/`. The moved test retains
`test_dataset_checks.DatasetChecks.test_valid_and_corrupted_copies`; all other
names and results are unchanged. Only discovery ordering and unittest's naturally
variable elapsed-time/count footer differ from the separate baseline suite logs.
`python3 tests/test_dataset_checks.py -v` also passes independently.

CSV SHA-256: `24386b4357f2819d3183e8be1edea58d3fc13caacc46683c6e4d83ebda6999f6`.

## Authorized manifest changes

The manifest itself necessarily has different bytes and a different digest; this
is the explicit hash-refresh exception, not an identical-file claim. Its metadata,
ordering (apart from the in-place path rename), and every other hash are unchanged.
Only these entries were refreshed:

1. `src/semdrift/validate_dataset.py`.
2. `src/semdrift/lexical_overlap.py`.
3. `src/semdrift/test_dataset_checks.py` renamed in place to
   `tests/test_dataset_checks.py`, with the new file's hash.
4. `research/03-dataset/NOTES.md`, with the user's explicit follow-up approval:
   NOTES is itself hashed, so the required provenance note also needs a refreshed
   hash to retain integrity checks. No data-file hash was changed.

NOTES records the required statement: "script hashes refreshed after a
behavior-preserving refactor on 2026-11-24; outputs verified byte-identical".
`research/03-dataset/protected_files.json` was not modified.

## Ruff and unchanged logic

Used the existing local Ruff 0.17.2 executable at
`/Users/sridhar/Projects/SayFlip/backend/.venv/bin/ruff`; nothing was installed.
Both repo-wide checks passed with only the protected extractor excluded.
No additional suspected logic bugs were identified or fixed in these three files.
The issue described in the earlier report below is a historical finding from
that pass, not a claim about independently edited current harness code.

---

# Earlier harness pass (historical)

The following report records the previous pass and its then-approved exclusions.
Its four-file freeze and separate test-discovery limitation are superseded by the
follow-up above; its original baseline evidence remains unchanged.

# Code-quality pass — 2026-11-24

## Scope and approved exceptions

Refactored the 18 unfrozen Python files in `src/semdrift/` (including adapters)
and `tests/`, and added a minimal `pyproject.toml` for Python >=3.11 with Ruff
E/F/I checks and a 100-character limit. No network/API calls, installations,
new runtime dependencies, or commits were made.

The user explicitly chose to preserve all four Phase 2 sources byte-for-byte:
`extract_tools.py`, `lexical_overlap.py`, `validate_dataset.py`, and
`test_dataset_checks.py`. `datasets/MANIFEST.json` hashes all four, and
`research/03-dataset/protected_files.json` also hashes the extractor. Editing or
moving them would invalidate dataset integrity, change the validator or run
outputs, and require changing forbidden dataset/research files.

Consequently, validator decomposition, the dataset-test move, frozen-file type
hints/layout, and naming the frozen length/overlap thresholds are deliberately
excluded. Ruff excludes exactly these four files. Their original long lines,
indentation, and statement separators remain; the original repo-wide style
completion criterion applies only to the revised scope authorized by the user.
The dataset mutation test remains runnable with:

```sh
python3 -m unittest discover -s src/semdrift -p 'test_*.py' -v
```

## Changes

Separated CLI dispatch/reporting, trial execution/record metadata, batch envelope
handling, judge request construction, and scoring/bootstrap stages into named
helpers. Added public function annotations and short module docstrings, expanded
compressed statements, clarified names, replaced test lambdas with named fixtures,
and retained decision comments and VERIFY-ONLINE notes. Malformed argument JSON
is explicitly returned unchanged rather than handled with a silent `pass`.

`DEFAULT_BOOTSTRAP_RESAMPLES` remains 10000 and is shared with the CLI;
`MILLISECONDS_PER_SECOND` names the existing 1000 conversion. There is no
1000-item pagination setting in the unfrozen code. The SDK exception boundary
still catches `Exception` intentionally to preserve credential-safe failure
messages and existing retry behavior; narrowing it would change behavior.

## Before / after metrics

Counts are physical source lines; longest function includes its signature and
body, including nested definitions. The semicolon column counts every literal
`;` character, including output strings, docstrings, and comments. Statement
separator tokens in the 18 unfrozen files decreased from 4 to
0. All 18 have zero lines over 100 characters, four-space block
indentation, multiline compound-statement bodies, short module docstrings, and
annotations on public functions. Frozen rows are shown for completeness.

| File | Lines before → after | Longest function before → after | `;` before → after | Lines >100 before → after |
| --- | ---: | ---: | ---: | ---: |
| `src/semdrift/__init__.py` | 1 → 1 | 0 → 0 | 0 → 0 | 0 → 0 |
| `src/semdrift/adapters/__init__.py` | 12 → 23 | 6 → 10 | 0 → 0 | 1 → 0 |
| `src/semdrift/adapters/anthropic_adapter.py` | 17 → 34 | 15 → 27 | 0 → 0 | 1 → 0 |
| `src/semdrift/adapters/openai_adapter.py` | 12 → 32 | 10 → 25 | 0 → 0 | 4 → 0 |
| `src/semdrift/adapters/openai_compat_adapter.py` | 19 → 26 | 17 → 19 | 1 → 1 | 2 → 0 |
| `src/semdrift/batch.py` | 87 → 152 | 48 → 44 | 1 → 1 | 6 → 0 |
| `src/semdrift/cli.py` | 48 → 81 | 40 → 26 | 2 → 2 | 5 → 0 |
| `src/semdrift/config.py` | 19 → 28 | 9 → 9 | 0 → 0 | 1 → 0 |
| `src/semdrift/cost.py` | 45 → 97 | 18 → 38 | 11 → 11 | 11 → 0 |
| `src/semdrift/data.py` | 42 → 67 | 22 → 39 | 0 → 0 | 4 → 0 |
| `src/semdrift/extract_tools.py (frozen)` | 136 → 136 | 44 → 44 | 6 → 6 | 8 → 8 |
| `src/semdrift/judge.py` | 42 → 104 | 23 → 35 | 2 → 2 | 6 → 0 |
| `src/semdrift/lexical_overlap.py (frozen)` | 61 → 61 | 14 → 14 | 3 → 3 | 4 → 4 |
| `src/semdrift/parse.py` | 35 → 63 | 21 → 23 | 1 → 1 | 1 → 0 |
| `src/semdrift/permute.py` | 11 → 23 | 4 → 9 | 0 → 0 | 0 → 0 |
| `src/semdrift/prompt.py` | 5 → 13 | 0 → 0 | 1 → 1 | 2 → 0 |
| `src/semdrift/runner.py` | 166 → 363 | 43 → 42 | 4 → 4 | 18 → 0 |
| `src/semdrift/score.py` | 161 → 330 | 97 → 39 | 4 → 4 | 12 → 0 |
| `src/semdrift/test_dataset_checks.py (frozen)` | 85 → 85 | 69 → 69 | 14 → 14 | 20 → 20 |
| `src/semdrift/transport.py` | 92 → 141 | 26 → 34 | 2 → 2 | 8 → 0 |
| `src/semdrift/validate_dataset.py (frozen)` | 261 → 261 | 145 → 145 | 22 → 22 | 40 → 40 |
| `tests/test_harness.py` | 259 → 388 | 21 → 32 | 4 → 0 | 19 → 0 |

The longest remaining unfrozen function is 44 lines (`batch.merge`); record
serialization and signatures account for much of the physical line expansion.
Scoring orchestration and execution loops were split without changing operation
order, seeds, key order, or output strings.

## Baseline comparison

The baseline was captured before editing and never updated:
`/var/folders/wf/gdffq11j5417w_1q91m109s40000gn/T/semdrift-baseline/`.
Post-refactor captures and comparison evidence are in `/var/folders/wf/gdffq11j5417w_1q91m109s40000gn/T/semdrift-quality-after/`.
Both contain separate stdout/stderr captures, and each dry-run configuration has
its own complete snapshot and relative-path SHA-256 manifest.

| Check | Result |
| --- | --- |
| `python3 -I src/semdrift/validate_dataset.py` stdout/stderr and exit | identical ✅ |
| Extractor command stdout/stderr and exit; extracted V0 SHA-256 | identical ✅ |
| `python3 src/semdrift/lexical_overlap.py` stdout/stderr and exit | identical ✅ |
| `datasets/tasks/lexical_overlap.csv` SHA-256 | identical ✅ |
| `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 18 names/results | identical ✅ |
| Separate dataset mutation suite: 1 name/result | identical ✅ |
| `run --config configs/budget_pilot.toml --dry-run`: stdout/stderr and exit | identical ✅ |
| Budget pilot `results/dryrun/`: all 15 file hashes and filenames | identical ✅ |
| `run --config configs/pilot.toml --dry-run`: stdout/stderr and exit | identical ✅ |
| Pilot `results/dryrun/`: all 15 file hashes and filenames | identical ✅ |
| `plan --config configs/budget_full.toml`: stdout/stderr and exit | identical ✅ |
| Every file in `datasets/`: 14 SHA-256 hashes, before baseline commands and after refactoring | identical ✅ |
| Four frozen Python source files: original bytes | identical ✅ |
| 90 original/refactored model/variant requests and fixed-clock log records, serialized with original key order | identical ✅ |
| Six original/refactored score summaries, two seeds and 0/1/100 resamples | identical ✅ |

V0 extraction SHA-256: `cfa6192c129b5656fccc518910aac8a6281e16cc8ae45bc16fe5eda2348f3810`.
Lexical CSV SHA-256: `24386b4357f2819d3183e8be1edea58d3fc13caacc46683c6e4d83ebda6999f6`.

No tests were added, removed, renamed, or moved: all 19 tests map one-to-one by
unchanged fully qualified names (18 harness + 1 separately discovered dataset
mutation test). Unittest's elapsed-seconds footer is inherently variable; only
that elapsed value was normalized for stderr comparison. Names, outcomes, test
counts, stdout, and remaining stderr match. Both baseline dry runs were resumes
with zero new trials; their summary bytes and all snapshot hashes match exactly.
Fresh record serialization was additionally checked with a fixed timestamp and
latency against the baseline implementation, without modifying production clocks.

## Suspected pre-existing bug — deliberately unchanged

- `src/semdrift/runner.py:189`: `_called_tools` iterates
  `message.get("tool_calls", [])`. An explicit JSON `null` yields `None`, so
  record creation raises `TypeError`, although `parse()` treats that same response
  as text-only using `... or []`. The original and refactored `make_record` both
  reproduced `'NoneType' object is not iterable` for this input. The analogous
  Anthropic `content: null` path has the same iteration risk. No fix was made.

## Ruff

Used the already-installed Ruff 0.17.2 at
`/Users/sridhar/Projects/SayFlip/backend/.venv/bin/ruff`; nothing was installed.
From the repo root, `ruff check` passed and `ruff format --check` reported
`18 files already formatted`. The explicit scoped commands
`ruff check src/semdrift tests` and `ruff format --check src/semdrift tests`
also passed. The configuration excludes the four user-approved frozen sources.
