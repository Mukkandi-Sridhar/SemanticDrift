# Prompt 06: Codex, Phase 2 fixes (after Claude's review)

---

## Copy everything below this line into Codex

---

Read `research/03-dataset/REVIEW-claude.md` in full. It reviews your Phase 2 dataset. The extraction (V0) is verified correct, so **don't change `v0_original.json`, `extract_tools.py`, `SOURCE.md` or anything in `vendor/`.** Fix issues #1–#6 as follows. Same rules as before: no API calls, no secrets, no commits.

1. **Rebuild `mg_overgeneral.json`.** Keep every `Args:` / `Returns:` line exactly as in V0. Broaden only the purpose sentence(s) so the scope is strictly wider. Each description must be within ±30% of V0 length and must still name the object it acts on (e.g., "work order"). Update the MG entries in `variants_rationale.json` to state exactly what was widened.

2. **Rebuild `ms_overspecial.json`.** No fixed template sentences, and no "Only for site MAIN" or "Only on Mondays". Each tool gets **one domain-plausible narrowing** written into the purpose sentence (not appended at the end), which must **conflict with at least one of that tool's tasks**. Add `"ms_conflict": true|false` to every single-tool task in `tasks.jsonl`. Update the rationale entries.

3. **Rebuild P1, P2 and P3, preserving format.** Keep the docstring structure: section headers (`Args:`, `Returns:`), parameter names, backticks, function references like `sites()`, and the line/indent layout. Reword only the prose. P2 reorders clauses *within* sections; it doesn't move sections around. Length within ±30%.

4. **Meaning audit of all paraphrases.** For every (tool, P1/P2/P3), check: (a) agency and voice ("the tool normalizes" must not become "normalize", an instruction to the caller); (b) every constraint kept (defaults, limits, units, statuses, side effects, read vs. write); (c) nothing added. Known bad case: `get_failure_modes` P1. Log every fix in `research/03-dataset/meaning_audit.md` (tool, variant, problem, fix).

5. **Rewrite the single-tool tasks** in short, natural operator language (typically 6–20 words), the way a maintenance engineer would type it. Remove steering negations ("do not…", "rather than…") unless they're essential to make exactly one tool correct; if one is essential, say so in `notes`. Seed **≥25 tasks** from AssetOpsBench utterances (`vendor/AssetOpsBench/src/scenarios/`, `benchmarks/scenario_suite/scenarios.txt`, `src/couchdb/scenarios_data/*/question.txt`), adapted minimally, with `source: aob_scenario:<file>#<id-or-line>`. Keep the near-miss coverage and per-tool minimums. Exactly one gold tool per task; drop any that become ambiguous.

6. **No-tool tasks.** Relabel the current hinted ones as `type: "no_tool"`, `subtype: "easy"`. Add **≥12** `subtype: "tempting"` tasks with **no hints**, where the correct first action is to ask a human or reply in text. Use cases such as: a required identifier is missing (e.g., "Close out the chiller job."), the action needs human authority ("Vibration on pump 3 looks bad, handle it."), or the request is contradictory. Each gets a `notes` rationale explaining why `NONE` is the gold answer. Keep out-of-scope tasks as `subtype: "out_of_scope"`.

7. **Lexical-overlap covariate.** Add `src/semdrift/lexical_overlap.py`, which writes `datasets/tasks/lexical_overlap.csv` (task_id, variant, overlap = share of non-stopword query tokens found in the gold tool's description). Report the mean per variant in NOTES.md. The goal is that V0 and P1–P3 are **within 0.03** of each other. If they aren't, revise queries (not descriptions) until they are, and report the final numbers.

8. **Validator and housekeeping.** Extend `validate_dataset.py` to check: MG/MS length bounds; that the `Args:` / `Returns:` headers are present in P1–P3/MG/MS whenever V0 has them; that every tool has ≥1 task with `ms_conflict: true`; ≥25 `aob_scenario` tasks; ≥12 tempting no-tool tasks; and that the validator also runs correctly when called as `python3 -I src/semdrift/validate_dataset.py`. Add `__pycache__/` to `.gitignore`. Re-run it and save `research/03-dataset/validation_report.txt`.

9. **Update `research/03-dataset/NOTES.md`:** what changed; a new list of the **15 paraphrases you're least sure about** (for Sridhar's manual check); ambiguous tasks; the overlap numbers. Append a dated summary to `research/LOG.md`.

**Done when:** the validator shows 0 failures with the new checks, `meaning_audit.md` exists, and the V0–paraphrase overlap gap is ≤0.03.
