# Prompt 10: Codex, clean up the 3 remaining Phase 2 scripts

**Why:** in prompt 09, Codex froze all four Phase 2 scripts. Sridhar's decision was to freeze **only `extract_tools.py`** (it produced the dataset). The other three are validation and analysis helpers, and `validate_dataset.py` is the least readable file in the repo (124 one-space-indented lines).

---

## Copy everything below this line into Codex

---

Follow-up to `research/prompts/09-codex-code-quality.md` and `research/04-harness/CODE_QUALITY.md`.

**Clarified decision:** only `src/semdrift/extract_tools.py`, `datasets/tools/v0_original.json` and `datasets/tools/SOURCE.md` stay frozen (`research/03-dataset/protected_files.json`). Apply the same refactoring standards from prompt 09 to:
- `src/semdrift/validate_dataset.py`: split into functions by concern (catalog / variants / tasks / provenance / covariate), with one `main()`; 4-space indentation; no `;`; lines ≤100; named constants for 0.7/1.3, 0.03, etc.
- `src/semdrift/lexical_overlap.py`
- `src/semdrift/test_dataset_checks.py`: move it to `tests/test_dataset_checks.py` and make it discoverable by `python3 -m unittest discover -s tests`.

Rules:
1. **Baseline first**: validator output (normal and `-I`), the `lexical_overlap.py` output, the SHA-256 of `datasets/tasks/lexical_overlap.csv` and of every file in `datasets/`, and the test results.
2. **Outputs must be byte-identical afterwards.** Same check names, order and messages in the validation report, same CSV bytes.
3. Keep `python3 src/semdrift/validate_dataset.py` and `python3 -I src/semdrift/validate_dataset.py` working.
4. If `datasets/MANIFEST.json` (or the validator) hashes these script files, update **only those script hashes**, and record in `research/03-dataset/NOTES.md`: "script hashes refreshed after a behavior-preserving refactor on <date>; outputs verified byte-identical". Never change data-file hashes.
5. Remove these three files from the ruff exclude list in `pyproject.toml`. `ruff check` and `ruff format --check` must pass (if ruff is available).
6. No behavior changes, no new dependencies, no commits. Update `research/04-harness/CODE_QUALITY.md` (before/after table for these files) and append to `research/LOG.md`.

**Done when** all tests pass, the validator shows 0 failures in both modes, every baseline output is identical, and the three files have no `;` joins, 1-space indents or lines >100.
