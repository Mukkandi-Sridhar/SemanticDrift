# Prompt 07: Codex, finish the interrupted Phase 2 fixes

Use this after Codex's usage limit resets. **Copy everything below the line.**

---

Your previous run of `research/prompts/06-codex-phase2-fixes.md` was interrupted by a usage limit. Read `research/03-dataset/REVISION-STATUS.md` and `research/03-dataset/REVIEW-claude.md`, then finish **only the remaining items**:

1. **Agency / meaning audit** of all P1–P3 paraphrases → write `research/03-dataset/meaning_audit.md` (tool, variant, problem, fix), including `get_failure_modes` P1.
2. **Overlap gap:** the last V0/P1–P3 gap was 0.043; the target is ≤0.03. Revise **queries only** (not descriptions). `lexical_overlap.py` currently writes blank overlap values for some rows; give NONE tasks the value `NA` and exclude them from the means.
3. **Source diversity:** the 25 AOB-seeded tasks reuse only 9 source utterances, and some are near-duplicates that only swap the asset name (e.g., T007/T008 "Look up <asset>’s registry profile at MAIN"). Keep at most **2 tasks per source utterance**. Replace the rest with tasks adapted from other utterances, if the checkout has them, or mark them `authored`. Report the final count of distinct source utterances honestly, even if it ends up below 25.
4. **Validator:** fix the failing `scenario source traceability` check (`question.txt#<line>` references must resolve to a real line in the vendor file), update the count check to the new targets (≈95–105 single-tool, ≥25 no-tool with ≥12 `tempting`), add the checks listed in prompt 06 item 8, and make sure the script runs with `python3 -I`.
5. Add `__pycache__/` to `.gitignore`, refresh `datasets/MANIFEST.json`, rewrite `research/03-dataset/NOTES.md` for the new dataset (including the 15 least-certain paraphrases for Sridhar), delete `REVISION-STATUS.md` once everything passes, and append a dated entry to `research/LOG.md`.

Same rules: don't touch V0, the extractor, `SOURCE.md` or `vendor/`; no API calls; no commits. **Done when** the validator shows 0 failures, the overlap gap is ≤0.03 and `meaning_audit.md` exists.
