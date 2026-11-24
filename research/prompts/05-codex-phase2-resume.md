# Prompt 05: Codex, resume Phase 2 (source is now available offline)

**Why:** Codex's sandbox has no internet access, so the clone failed (see `research/03-dataset/NOTES.md`). Claude cloned AssetOpsBench into the repo instead, in a git-ignored folder.

---

## Copy everything below this line into Codex

---

Resume Phase 2 using `research/prompts/04-codex-phase2-dataset.md`. Follow it exactly, with these changes only:

**1. The source checkout already exists. Don't clone.**
- Path: `vendor/AssetOpsBench/` (inside this repo, git-ignored; don't modify anything in it)
- Upstream: https://github.com/IBM/AssetOpsBench
- Commit SHA: `0d044061ab3ffd4b213ddf6a0868c360d7e9667c` (2026-11-14, "Merge pull request #683")
- License: Apache License 2.0 (`vendor/AssetOpsBench/LICENSE`)
- Verify the SHA yourself with `git -C vendor/AssetOpsBench rev-parse HEAD` and record it in `datasets/tools/SOURCE.md`.

**2. How the tools are registered (checked by Claude):**
- `src/servers/iot/main.py`, `utilities/main.py` and `fmsr/main.py` use `@mcp.tool(...)` decorators.
- `src/servers/wo/main.py` registers tools **centrally in a loop** (around line 417: `mcp.tool(title=_title, annotations=...)(_fn)`) over functions defined in `src/servers/wo/workorders.py`. Follow that loop to get the exact list. Respect `AOB_READONLY` semantics: the default surface is 15 tools (9 read + 6 write); we use the **default** surface.

**3. Extraction method (no network, no dependency install):**
- Preferred: parse the source with Python's `ast` module. FastMCP builds the client-visible **description from the function docstring** (unless `description=` is passed to `mcp.tool`) and the **input schema from the function signature and type hints/defaults**. Reproduce that: take the docstring verbatim (`inspect.cleandoc`-style), and build the JSON Schema from the parameter names, annotations (`str` → string, `int` → integer, `float` → number, `bool` → boolean, `list[str]` → array of strings, `X | None` / `Optional[X]` → not required) and defaults.
- If a decorator passes an explicit `description=` or `name=`, that value wins.
- If an annotation is a custom type you can't map faithfully, record it as-is in an `x_source_annotation` field, and list it in NOTES.md. Don't guess.
- Mark in `SOURCE.md` that schemas were reconstructed from source by static analysis, not captured from a running server.

**4. Scenario utterances for seeding tasks** (use for `source: aob_scenario:<id>`):
- `vendor/AssetOpsBench/src/scenarios/`
- `vendor/AssetOpsBench/benchmarks/scenario_suite/scenarios.txt`
- `vendor/AssetOpsBench/src/couchdb/scenarios_data/`
- `vendor/AssetOpsBench/docs/guideline/utterance_design_guideline.md` (style guide for realistic queries)

**5. Everything else is unchanged:** no API calls, no secrets, no commits, don't modify `vendor/`, and follow the same acceptance checklist. Overwrite the "blocked" note in `research/03-dataset/NOTES.md` with the real results, keeping a one-line history entry saying the first attempt was blocked by missing network access.
