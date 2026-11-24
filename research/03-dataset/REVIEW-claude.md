# Claude review of the Codex Phase 2 dataset (2026-11-23)

## ✅ Verified good
- **Extraction is exact.** 36 tools (iot 12, utilities 6, fmsr 3, wo 15: 29 read, 7 write), matching `docs/mcp-servers.md`. I compared 5 descriptions against the source docstrings myself (`latest_reading`, `cancel_workorder`, `generate_failure_modes`, `get_sensor_catalog`, `list_workorders`): all identical.
- **It reproduces.** Re-running `extract_tools.py` gives a byte-identical `v0_original.json`.
- **Provenance is solid:** commit SHA, Apache-2.0 license copied, SHA-256 hashes of every source file.
- The validator runs with 0 structural failures. (Note: it must be run as `python3 src/semdrift/validate_dataset.py`; the `-I` flag breaks its import.)
- Schemas, names and order are identical across all 6 catalogs.

## ❌ Must fix before running experiments

### 1. The "over-generalized" variant (MG) is really *truncation*
Median MG length is **19% of the original** (min 4%). It deletes the Args/Returns documentation, so MG mixes "broader scope" with "less information". A reviewer would rightly say the effect is just missing documentation. Some outputs are broken: `cancel_workorder` → "Cancel (-> CAN)." (doesn't even say *what* is cancelled).
**Fix:** keep every Args/Returns line; broaden **only the purpose sentence** (e.g., "Return the newest telemetry observation" → "Return telemetry observations"). Length within ±30% of the original.

### 2. The "over-specialized" variant (MS) is a template that rarely bites
Codex appended a fixed sentence: **"Only for site MAIN."** on 26 of 36 tools (plus "Only on Mondays", "Only for pump-related requests"…). But **70 of 127 tasks use site MAIN**, so the restriction is true for most tasks and can't cause failures there. "Only on Mondays" isn't a plausible documentation defect.
**Fix:** one domain-plausible narrowing per tool (e.g., `latest_reading` "…for temperature sensors"), chosen so that it **conflicts with at least one of that tool's tasks**. Record per task whether the MS restriction conflicts (`ms_conflict: true/false`), so the analysis can separate the two cases.

### 3. The paraphrases change *formatting*, not just wording
P1–P3 remove the `Args:` / `Returns:` headers and the backticks, turning structured docstrings into prose. A wording effect can then not be separated from a formatting effect.
**Fix:** keep the docstring structure (section headers, parameter names, backticks, line layout) and reword only the prose inside it.

### 4. At least one paraphrase changes the meaning
`get_failure_modes` original: "Case, whitespace… **are normalized** before querying" (the tool does it). P1: "**Normalize** letter case… before the lookup" (an instruction to the caller). That's a change of meaning.
**Fix:** Codex must audit all 108 paraphrases for agency, voice or obligation shifts (tool does X ↔ caller must do X), and for dropped or added constraints, and log each fix.

### 5. Tasks: style bias and little real-world grounding
- Only **4 of 127** tasks are seeded from AssetOpsBench utterances; 123 were written by Codex.
- Queries share vocabulary with Codex's own paraphrases: the share of query words found in the gold description is 0.307 for the original vs. **0.325–0.345 for P1–P3** (the same author wrote both). That gives the paraphrases a small built-in advantage.
- Many queries read like specifications ("do not infer them from observations", "rather than catalog definitions or newly suggested modes"). 16 of 102 contain steering negations. Real operators don't write like that, and it inflates accuracy.
**Fix:** rewrite queries in short, natural operator language; drop steering negations unless they're essential; seed **at least 25** tasks from AOB scenario utterances; store a per-task `lexical_overlap` for each variant so it can be used as a covariate.

### 6. "Tempting" no-tool tasks aren't tempting
Most include explicit hints ("do not save it", "without changing any maintenance records", "give general guidance"). No model will call a write tool for those, so the false-action test would be weak.
**Fix:** add **at least 12 genuinely tempting** no-tool tasks *without* hints, where the right response is to ask a human: missing required identifiers (e.g., "Close out the chiller job." with no work-order number or site), a decision that needs human authority ("The vibration on pump 3 looks bad, deal with it."), or a conflict between two requests. Each needs a one-line rationale for why `NONE` / ask-human is the gold answer. Keep the current hinted ones as a separate `no_tool_easy` subtype.

## Housekeeping
- Add `__pycache__/` to `.gitignore`.
- Lower the `tempting` count claim in NOTES.md until #6 is done.

## Still pending (not Codex's job)
- **Sridhar's manual check of the paraphrases**, after Codex's fixes.
- **The two-way equivalence check by an LLM judge** (needs API access, so it moves to Phase 3 or 4).
