# SemanticDrift dataset

A tool-selection test set built on the MCP tools of
[IBM AssetOpsBench](https://github.com/IBM/AssetOpsBench) (industrial asset operations and
maintenance). It holds one set of tools, nine versions of their descriptions and 152 labelled
requests, so that the same request can be asked under different wordings of the same tools.

Every file is fingerprinted in [`MANIFEST.json`](MANIFEST.json) (SHA-256). Run
`python3 src/semdrift/validate_dataset.py` to check the files against it.

## Contents

| File | What it is |
|---|---|
| `tools/v0_original.json` | The 36 tools as published upstream (commit `0d04406`) |
| `tools/v0r_placebo.json` | Byte-identical copy of V0, used to measure run-to-run noise |
| `tools/p1_paraphrase.json`, `p2_…`, `p3_…` | Meaning-preserving rewrites of every description |
| `tools/mg_overgeneral.json` | Each purpose sentence widened; parameter docs unchanged |
| `tools/ms_overspecial.json` | One plausible narrowing per tool |
| `tools/h1_earliest.json`, `h2_midpoint.json`, `h3_previous.json` | Real earlier descriptions from the AssetOpsBench git history |
| `tools/variants_rationale.json` | For every tool and rewritten catalog, what was changed |
| `tools/SOURCE.md`, `tools/LICENSE.AssetOpsBench` | Provenance and upstream license (Apache-2.0) |
| `history/versions.json` | Every distinct description of each tool found in the git history, with commit and date |
| `history/edit_features.json` | Simple features of each historical edit (length ratio, similarity, sibling references) |
| `tasks/tasks.jsonl` | The 152 requests and their gold labels |
| `tasks/SOURCES.md`, `tasks/source_index.json` | Where requests adapted from AssetOpsBench scenarios come from |
| `tasks/lexical_overlap.csv` | Word overlap between each request and its gold description, per catalog |

## Tools

36 tools from four servers. The schema, name, order and read/write access are identical in every
catalog; only `description` differs.

| Server | Read tools | Write tools |
|---|---|---|
| `iot` (asset registry and telemetry) | 12 | 0 |
| `utilities` (catalogs, time) | 6 | 0 |
| `fmsr` (failure modes) | 2 | 1 |
| `wo` (work orders) | 9 | 6 |
| **Total** | **29** | **7** |

A tool record:

```json
{"name": "sites", "server": "iot", "access": "read",
 "description": "List sorted site identifiers available in the asset registry. ...",
 "input_schema": {"type": "object", "properties": {}}}
```

Schemas were reconstructed from the upstream source by static analysis, not captured from a
running server.

## Historical catalogs

`extract_history.py` parses every commit that touched the four server files. An earlier
description is used only if the tool's schema at that commit is **identical** to today's, so the
wording is the only difference. That leaves 42 earlier descriptions across 16 of the 36 tools;
tools without one keep their V0 text. H1 takes each tool's oldest eligible description, H3 the
one just before V0, and H2 the middle one (H2 was built but not run in the main study).

## Tasks

| Type | Count | Gold label |
|---|---|---|
| Single tool | 103 | Exactly one correct tool (89 read tasks, 14 write tasks) |
| No tool: tempting | 24 | `NONE`: the request resembles a write action but needs a human decision (for example, a missing work-order number, or two conflicting instructions) |
| No tool: easy | 20 | `NONE`: clearly a question for a person or a text answer |
| No tool: out of scope | 5 | `NONE`: nothing in the catalog applies |

A task record:

```json
{"id": "T001", "query": "Which facilities are available in the MAIN registry for commissioning?",
 "gold": "sites", "gold_access": "read", "type": "single_tool", "near_miss_of": null,
 "source": "aob_scenario:src/couchdb/scenarios_data/default/question.txt#1",
 "notes": "...", "ms_conflict": true}
```

- `near_miss_of`: a sibling tool that is easy to confuse with the gold tool, when one exists.
- `ms_conflict`: whether the narrowed catalog (MS) wrongly excludes the gold tool for this request
  (true for 78 of 103 single-tool tasks).
- `source`: 26 requests are adapted from 10 AssetOpsBench scenario utterances; the other 126
  were written for this study.
- Requests never contain the gold tool's name or a 4-word phrase from its V0 description.

## How it was checked

- The tool extraction is reproducible byte for byte from the pinned upstream commit.
- Paraphrases keep section layout, parameter names and code references. The 15 riskiest were
  reviewed by hand: 12 kept as written, 3 corrected. A meaning audit of all 108 is in
  `research/03-dataset/meaning_audit.md`.
- Word overlap between requests and the gold description differs by at most 0.023 across V0 and
  the three paraphrases, so no catalog is favoured by vocabulary.
- The validator checks schemas, counts, labels, leakage and provenance; tests in
  `tests/test_dataset_checks.py` and `tests/test_history.py` check that it catches broken copies.

## Intended use and limits

Use it to measure how sensitive LLM tool selection is to wording, for single-step selection
in one domain. It isn't a test of full agent workflows, and the tools are never executed. The
paraphrased, vaguer and narrower catalogs were written with a language model; the historical
catalogs were written by the AssetOpsBench developers.
