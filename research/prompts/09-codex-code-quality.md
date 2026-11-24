# Prompt 09: Codex, code-quality pass (behavior must not change)

**Why:** the code works and its outputs are verified, but parts of it are hard to read: one-space indentation in `validate_dataset.py`, many `;`-joined statements, 100+ lines over 110 characters, and lambda-heavy tests. Reviewers and IBM researchers will read this repo, so it should look like a careful engineer's code. This is a **pure refactor**: every output must stay byte-identical.

---

## Copy everything below this line into Codex

---

You are doing a **behavior-preserving code-quality pass** on the SemanticDrift repo. The code is correct and its outputs are verified; your job is to make it read like clean, idiomatic Python a careful senior engineer would write. **Nothing it produces may change.**

### Scope
All Python in `src/semdrift/` (including `adapters/`) and `tests/`. Don't touch `datasets/`, `vendor/`, `configs/`, `results/` or `research/` (except one LOG entry at the end).

### Step 0: Capture a baseline BEFORE editing anything
Write `$TMPDIR/semdrift-baseline/` (outside the repo) containing:
1. `python3 -I src/semdrift/validate_dataset.py` output
2. `python3 src/semdrift/extract_tools.py --source vendor/AssetOpsBench --output <tmp>/v0.json`, then its SHA-256
3. `python3 src/semdrift/lexical_overlap.py` output and the SHA-256 of `datasets/tasks/lexical_overlap.csv`
4. `PYTHONPATH=src python3 -m unittest discover -s tests -v` output (test names and results)
5. `PYTHONPATH=src python3 -m semdrift.cli run --config configs/budget_pilot.toml --dry-run`, then copy `results/dryrun/` and SHA-256 every file in it. Also do the same for `configs/pilot.toml`.
6. `PYTHONPATH=src python3 -m semdrift.cli plan --config configs/budget_full.toml` output
7. SHA-256 of every file in `datasets/`

### Step 1: Refactor, following these standards
- **PEP 8 layout:** 4-space indentation everywhere; no `;` statement joining; no one-line `if x: y` bodies; maximum line length **100**; two blank lines between top-level definitions.
- **Readability:** descriptive names (no `t, b, r, g` except in short comprehensions or loops); replace dense nested comprehensions with small named helper functions; no lambdas assigned to names (use `def`).
- **Structure:** split long functions (over ~40 lines) into well-named helpers. In `validate_dataset.py`, group the checks into functions by concern (catalog checks, variant checks, task checks, provenance checks), with one `main()`.
- **Types and docs:** type hints on all public functions. Each module gets a 1–3 line module docstring saying what it does in this study. Use short docstrings only where the *why* isn't obvious. **No comments that restate the code.** Keep the existing comments that explain decisions (e.g., why a JSON Schema subset is used, VERIFY-ONLINE notes).
- **Constants:** magic numbers (0.7/1.3 length bounds, 0.03 overlap gap, 1000 page size, 10000 bootstrap resamples) become named module-level constants.
- **Errors:** specific exceptions with clear messages; no bare `except`; no silent `pass`.
- **Imports:** standard library only for core logic (as now), sorted: stdlib, then local.
- **Tests:** move `src/semdrift/test_dataset_checks.py` into `tests/` (keep a working way to run it). Make tests readable: arrange / act / assert, descriptive test names, no lambda gymnastics, shared fixtures as helper functions.
- **Avoid "AI-generated" tells:** no over-long docstrings, no emoji, no "This function is responsible for…" phrasing, no redundant type comments, no defensive checks for impossible states, no one-time-use wrapper classes. Prefer plain functions and dataclasses where a record type helps (e.g., the parsed action).
- Add a minimal `pyproject.toml` (project name, Python ≥3.11, and `[tool.ruff]` with line-length 100 and sensible rules) so contributors can lint. If `ruff` is installed locally, run `ruff check` and `ruff format --check` and fix what they report. If it isn't installed, say so; don't install anything.

### Hard rules
- **No behavior change.** No change to algorithms, thresholds, random seeds, output formats, JSON key order, file names, CLI commands or arguments, or log record fields.
- Keep these entry points working exactly as documented: `python3 src/semdrift/extract_tools.py …`, `python3 src/semdrift/validate_dataset.py` (also under `-I`), `python3 src/semdrift/lexical_overlap.py`, and `python -m semdrift.cli …`.
- Don't "fix" logic you think is wrong. If you notice a real bug, **don't change it**; list it in the report (file:line, what, why).
- No network, no API calls, no new dependencies, no commits.

### Step 2: Prove nothing changed
Re-run every Step 0 command and compare against the baseline. **Every hash must match**, the validator and plan outputs must match, and all tests must pass with the same test count (plus any tests you only renamed or moved, mapped one-to-one). If anything differs, fix the refactor; never update the baseline.

### Step 3: Report
Write `research/04-harness/CODE_QUALITY.md` with:
- a before/after table per file (line count, longest function, `;` count, lines >100 characters);
- the baseline comparison (each check: identical ✅);
- any suspected bugs you noticed but didn't fix;
- whether ruff was run, and its result.

Append a dated 3–5 bullet entry to `research/LOG.md`.

### Done when
All Step 2 comparisons are identical; no `;`-joined statements or 1-space indentation remain; no line exceeds 100 characters; tests pass; the report exists.
