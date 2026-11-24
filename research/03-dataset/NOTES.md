# Phase 2 review fixes — 2026-11-24

History: the first extraction attempt was blocked by missing network access; the later local-command interruption recovered before these checks completed.

The requested dataset revision is complete and passes the extended offline validator, including isolated mode. Sridhar completed the 18-item manual review on 2026-11-24, as recorded in research/LOG.md: 12 of 15 paraphrases passed and three were corrected; two MG flags were corrected and one MS restriction retained. Independent two-way LLM judging remains pending. This does not establish human approval of every dataset entry.

## Protected extraction

V0, extract_tools.py, SOURCE.md and vendor/ were not changed. Their protected file hashes are checked by the validator against pre-revision values; vendor git status remains clean. Source SHA remains `0d044061ab3ffd4b213ddf6a0868c360d7e9667c`, Apache License 2.0. The catalog remains 36 tools: iot 12, utilities 6, fmsr 3, wo 15; 29 read and 7 write. generate_failure_modes remains read + LLM-use. No tsfm/vibration tools were added.

## What changed

1. MG retains every Args/Returns line verbatim and the named object. Purpose wording alone is broadened; long documentation is no longer truncated. Read/write guarantees and the underlying schemas remain fixed. All descriptions pass both character and word ±30% bounds.
2. MS adds one tool-specific, domain-plausible restriction inside the purpose, never a trailing template sentence. Every tool has at least one explicitly conflicting task; each MS rationale lists those task IDs. Task labels include ms_conflict: 78 true and 25 false. Contextual restrictions, such as decommissioning-only site discovery, deserve plausibility review; the labels concern requested scope, not observed database result counts.
3. P1–P3 preserve section order, line count, indentation/blank-line layout, parameter/result prefixes, backticks and function references. P2 reorders clauses inside sections rather than moving sections.
4. meaning_audit.md and meaning_audit.json contain all 108 pair reviews, with problem/fix notes, agency/constraint/addition checks and description hashes. Normalization is tool-side; newly spotted row-construction, record-ordering and mode-reporting agency errors were also corrected.
5. All 103 single-tool queries are 6–16 words. Twenty-five are traceable adaptations of nine source anchors. Source reuse and authored identifier/context changes are disclosed in datasets/tasks/SOURCES.md. Twenty-five adaptations are not twenty-five distinct source scenarios.
6. No-tool tasks are split into 20 easy, 5 out_of_scope and 12 new tempting cases, giving 37 total. T129–T140 have missing identifiers, unresolved intervention choices or contradictory actions and no explicit abstention hints.
7. lexical_overlap.py emits all 140 × 6 = 840 task/variant rows. NONE overlaps are blank because there is no gold tool description; the means use the 103 single-tool tasks.
8. The validator now checks MG/MS length, format preservation, exact MG/MS Args/Returns, per-tool MS witnesses, source anchors/counts, no-tool subtypes/temptations, covariate freshness/gap, audit coverage/hashes and unchanged protected originals. It works under python3 -I. The existing tracked __pycache__/ ignore rule was already present and verified; no duplicate rule was added.

The total is 140 tasks, rather than 127: the original 25 no-tool tasks were retained, 12 genuine temptations added, and one extra single-tool retrieval added for grounded coverage. Every tool retains its two-task minimum and all designated near-miss tools have at least four (history has five).

## Lexical overlap

For each task, tokenize case-insensitive Unicode word/underscore runs, split punctuation, remove the fixed generic stopword list in lexical_overlap.py, and count token occurrences. Overlap is the fraction of remaining query-token occurrences present in the gold description’s token set. There is no stemming or variant-specific stopword tuning. Means weight single-tool tasks equally.

| Variant | Mean overlap | Difference from V0 |
|---|---:|---:|
| V0 | 0.348103 | +0.000000 |
| P1 | 0.352260 | +0.004157 |
| P2 | 0.346935 | -0.001167 |
| P3 | 0.329691 | -0.018412 |
| MG | 0.334021 | -0.014082 |
| MS | 0.354964 | +0.006862 |

Benign-catalog max-minus-min = **0.022569**, below 0.03. This also ensures each paraphrase is within 0.03 of V0. The first measurement on the revised drafts had spread 0.042938. Six natural query rewrites reduced the imbalance after the agency audit; later semantic clarifications were remeasured. Descriptions were not tuned to reduce overlap. These numbers use the explicit tokenizer/stopwords above and need not match the reviewer’s unspecified implementation. Passing this covariate threshold does not prove absence of all lexical/style bias.

## Fifteen paraphrases for closest manual review

These 15 priority items received Sridhar’s manual review, recorded in research/LOG.md; three were corrected. They remain the highest-risk items for the independent review of all 108 pairs.

| Variant | Tool | Review concern |
|---|---|---|
| P1 | stream_extent | Timezone consistency versus instant comparison; the inclusive/exclusive and non-null conditions must retain their boundaries. |
| P2 | stream_extent | Clause changes join conditions across line breaks; check that every condition still applies to the same records. |
| P3 | history | Projection, metadata exclusion and opaque query-bound cursor rules are densely stated. |
| P2 | history | Confirm “Rows retain” is tool output behavior and that cursor continuation still requires the identical query. |
| P1 | sensor_stats | Numeric strings, invalid present values and absent fields affect different counts. |
| P2 | sensor_stats | Population deviation and the one-value/no-value cases need exact equivalence. |
| P3 | sensor_stats | First/last timestamps must refer to numeric observations, not all observations. |
| P2 | latest_reading | A specified sensor selects the newest qualifying non-null record, not necessarily the newest whole record. |
| P1 | sensor_coverage | All value types count when non-null; all-null fields retain zero count and null bounds. |
| P3 | find_assets_by_sensors | all/any, exact versus fragment matching, source default and deduplication ordering must all survive. |
| P1 | get_failure_modes | The known bad agency shift is repaired; verify that normalization is unequivocally tool-side. |
| P2 | generate_failure_modes | Stored-context extension versus new generation and the no-write guarantee must remain distinct. |
| P3 | add_failure_modes | Preservation, case-insensitive merging, additions-only reporting and exhaustive omission/default semantics. |
| P2 | get_workorder_tasks | “Subordinate tasks” must mean child rows linked to the parent work order. |
| P3 | list_workorders | OPEN/APPROVED_PENDING and page_size=0 all-match behavior must be retained without inventing filters. |

## Ambiguity and source limitations

No candidate with a known unresolved competing direct operation is deliberately retained. The author review is not independent label agreement. Important decisions:

- The original vague “Which sensors?” source could mean registry assignments or observed telemetry fields. T009–T016 explicitly distinguish those sources.
- T003–T006 request identifiers only; T004’s “without metadata” is essential to distinguish the compact-metadata sibling and is justified in notes. Other single-tool tasks contain no steering negations.
- Cost-share tasks request computed category shares; variance tasks request estimate/actual differences. A raw-document tool followed by model arithmetic is an alternative strategy, but is not the directly requested operation. Review T075–T082 against the single-step selection protocol.
- Source scenario 2 requires semantic classification; it is not used as a single-tool gold. Source scenario 3’s complete diagnosis requires multiple/excluded tools; only bounded retrieval/count subtasks are adapted.
- Missing-key temptations are labeled NONE because the requested specific operation cannot be selected with supported identifying information. Do not invent a site or work-order number; calling a broad list without a basis is not treated as fulfillment.
- PLANT_A vibration utterances and MAIN IoT fixtures are different source contexts. Selection tasks preserve source identifiers where used; they do not claim live data exists for every request. Retain this limitation in any paper and do not report successful tool execution.
- Repeated adaptations share source families. Any claim about independent scenario coverage must use nine single-tool source anchors, not 25. Broader field-value counts and unfamiliar dates may yield empty responses without changing routing intent.

## Validation and reproduction

```sh
python3 src/semdrift/lexical_overlap.py
python3 src/semdrift/validate_dataset.py
python3 -I src/semdrift/validate_dataset.py
python3 -m unittest discover -s src/semdrift -p 'test_*.py' -v
```

The normal and isolated validators produce identical output; validation_report.txt is the isolated run. The mutation suite rejects 20 corrupted-copy cases, including missing headings, changed MG Args, missing MS conflict coverage, inadequate source/tempting counts, steering hints, stale audit hashes and stale covariate rows. No upstream module or industrial tool is executed.

Frozen extraction is preserved; running the validator only reads it and statically re-extracts for comparison. Protected-file fingerprints are in protected_files.json. All current artifact fingerprints are refreshed in datasets/MANIFEST.json after final checks.

## Phase 3 handoff

Keep canonical names/schemas/order fixed, use paired permutations, and score only the first action; do not execute industrial tools or writes. Load subtype, ms_conflict and lexical_overlap.csv as analysis covariates, not extra model-facing hints. Preserve source-family IDs for dependency sensitivity analysis. The sampled manual checks are complete; finish independent equivalence judging before claiming a validated experiment dataset. No semantic pass rate has been invented.

No API calls, secrets, dependency installation, commits or pushes were made. Only the authorized dataset/code outputs and research/03-dataset/ were revised; research/LOG.md receives an appended summary. SOURCE.md remains the original extraction provenance by instruction.

## Follow-up author review — 2026-11-24

The same unsupported batch claim corrected in MG cancel_workorder remained in MG approve_workorder. Replaced “Approve multiple work orders” with “Approve a maintenance record”, broadening the object class while retaining a singular operation and the APPR transition. This follows the manually accepted cancellation correction; this new approval wording has not itself received human review. Updated its rationale and regenerated covariates and fingerprints. No task or P1–P3 description changed in this follow-up.


## Script refactor — 2026-11-24

script hashes refreshed after a behavior-preserving refactor on 2026-11-24; outputs verified byte-identical

The mutation suite now runs with `python3 -m unittest discover -s tests -v`
or directly with `python3 tests/test_dataset_checks.py`. The extractor, V0,
and SOURCE.md remain frozen. Data-file hashes are unchanged.
