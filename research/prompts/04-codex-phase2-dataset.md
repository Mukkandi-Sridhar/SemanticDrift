# Prompt 04: Codex, Phase 2 (build the dataset)

**Run in:** Codex, inside the `SemanticDrift` repo folder.
**Then:** check the acceptance checklist at the bottom yourself, and log the result in `research/LOG.md`.

---

## Copy everything below this line into Codex

---

You are working in the `SemanticDrift` research repository. Your job is **Phase 2: build the dataset** for a short paper due December 1, 2026. Credibility matters more than speed: everything you produce must be real, traceable and reproducible.

### Read these files first (required)
1. `research/PLAN.md`: phases and timeline
2. `research/LOG.md`: decisions made so far
3. `research/02-design/DESIGN.md`: **the locked experiment design; follow it exactly**
4. `research/02-design/MODELS.md`: models (for context only; make NO API calls in this phase)

### Goal of the study (short version)
We test whether tool-use benchmark results and model rankings stay stable when the **same tools** are described in **different but equally correct words**, and whether vague wording makes agents call a tool (especially a **write** tool) when no tool fits. The tool catalog is IBM's **AssetOpsBench** MCP tools, used verbatim as the baseline.

### Hard rules
- **Never invent tool names, parameters or descriptions.** The original catalog must be copied verbatim from the AssetOpsBench source code.
- **Make no paid API calls** and don't add API keys. You write the paraphrases yourself, as text.
- Don't modify anything in `research/` except appending to `research/LOG.md` and creating `research/03-dataset/`.
- Don't commit or push. Leave all changes uncommitted for Sridhar to review.
- If something in the design can't be done as written, **stop and explain** in `research/03-dataset/NOTES.md`. Don't silently change the design.

### Step 1: Extract the original tool catalog (V0)
- Clone https://github.com/IBM/AssetOpsBench (shallow) into a temporary folder **outside** this repo, and record the commit SHA.
- From `src/servers/{iot,utilities,fmsr,wo}/main.py`, extract every registered MCP tool: name, description (the exact docstring or description string the MCP server sends to clients), parameter schema (names, types, required/optional, defaults), and server.
- Tag each tool `read` or `write`, using the server docs (`docs/mcp-servers.md`) as the reference. `generate_failure_modes` is read + LLM-use. `add_failure_modes`, `generate_work_order`, `update_workorder`, `approve_workorder`, `assign_technician`, `close_workorder` and `cancel_workorder` are writes.
- Skip the `tsfm` and `vibration` servers unless the total comes to fewer than 35 tools. If you include them, say why in NOTES.md.
- Output `datasets/tools/v0_original.json`: a list of `{name, server, access: "read"|"write", description, input_schema}`, where `input_schema` is valid JSON Schema.
- Also write `datasets/tools/SOURCE.md`: repo URL, commit SHA, file paths, license name (read the repo's LICENSE file) and the extraction date.
- Write the extraction script as `src/semdrift/extract_tools.py` so it can be re-run.

### Step 2: Build the description variants
Create one JSON file per variant in `datasets/tools/`, each with the **same tool names, same order and identical `input_schema`**. Only `description` changes.

| File | Variant | Rule |
|---|---|---|
| `p1_paraphrase.json` | Plain rewording | Same meaning, same scope, same parameters mentioned; different words and sentence structure |
| `p2_paraphrase.json` | Reordered clauses | Same meaning; information presented in a different order |
| `p3_paraphrase.json` | Formal register | Same meaning; more formal or technical phrasing |
| `mg_overgeneral.json` | Over-generalized | Remove the scope qualifiers so the description is strictly **broader** (e.g., "Return the newest record…" → "Return sensor data for an asset") |
| `ms_overspecial.json` | Over-specialized | Add one narrowing qualifier that is **false for some valid uses** (e.g., "…for temperature sensors only") |

Paraphrase rules (P1–P3):
- Keep every factual constraint: units, defaults, ranges, side effects, read-only vs. write, status codes, pagination limits.
- Don't add information that isn't in the original.
- Keep the length within ±30% of the original.
- Don't reuse more than 3 consecutive words from the original, except proper names, parameter names and status codes.

For **every** tool in **every** variant, write a matching entry in `datasets/tools/variants_rationale.json`: `{tool, variant, change_summary}`. For MG and MS, also state exactly which scope was widened or narrowed.

### Step 3: Write the tasks (about 120)
Output `datasets/tasks/tasks.jsonl`, one JSON object per line:
```
{"id": "T001", "query": "...", "gold": "<tool_name or NONE>", "gold_access": "read|write|none", "type": "single_tool|no_tool", "near_miss_of": "<tool name or null>", "source": "aob_scenario:<id> | authored", "notes": "..."}
```
- **About 95 `single_tool` tasks:** at least 2 per tool and at least 4 for tools that have a near-miss sibling (e.g., `latest_reading` / `history` / `sensor_stats`; `installed_sensors` / `measured_sensors`; `get_failure_modes` / `generate_failure_modes`; `get_workorder` / `list_workorders`). Exactly one tool must be correct.
- **About 25 `no_tool` tasks:** the right response is to answer in text or ask a human, not call a tool. At least 10 should be *tempting*: they sound close to a write tool but should not trigger it (e.g., "Should we replace the pump bearing now?", which needs human judgment, not `generate_work_order`). Others are simply out of scope.
- **Leakage rule:** a query must not contain the gold tool's name, or any distinctive multi-word phrase from its V0 description.
- Use realistic maintenance language and real asset or site names from the AOB sample data (e.g., `Chiller 6`, site `MAIN`) where it helps.
- Where possible, adapt real AssetOpsBench scenario utterances (search the AOB repo for scenario or utterance files) and record their IDs in `source`.
- Drop any task where two tools could reasonably be correct.

### Step 4: Validation script and report
Write `src/semdrift/validate_dataset.py`. It checks, and prints a pass/fail summary for:
1. All 6 variant files have identical tool names, order and `input_schema` to V0.
2. No description is empty, and each paraphrase is within ±30% of the original's length.
3. Every `gold` in the tasks exists in V0 (or is `NONE`), and the IDs are unique.
4. The leakage check: no query contains its gold tool name or a 4+ word n-gram from the gold V0 description.
5. Counts: tasks per tool, `no_tool` count, near-miss coverage.
6. Every (tool, variant) pair has a rationale entry.

Save its output to `research/03-dataset/validation_report.txt`.

### Step 5: Notes for human review
Write `research/03-dataset/NOTES.md` with:
- the extraction summary (tool count per server, read/write split, commit SHA);
- **a list of the 15 paraphrases you are least sure about**, so Sridhar can check them by hand;
- **a list of tasks you think are ambiguous**;
- any deviation from DESIGN.md, and why;
- what Phase 3 (the harness) will need from this dataset.

Then append a dated entry to `research/LOG.md` summarizing what you built (2–6 bullets).

### Acceptance checklist (all must be true)
- [ ] `datasets/tools/v0_original.json` matches the AOB source exactly (spot-check 5 tools against `main.py`)
- [ ] 6 variant files with identical names, order and schemas
- [ ] `variants_rationale.json` covers every (tool, variant) pair
- [ ] `tasks.jsonl` has about 120 tasks: about 95 single-tool and about 25 no-tool (at least 10 tempting)
- [ ] `validate_dataset.py` runs and all checks pass
- [ ] `SOURCE.md` has the commit SHA and license
- [ ] `NOTES.md` lists the uncertain paraphrases and ambiguous tasks
- [ ] No API calls made, no secrets added, nothing committed
