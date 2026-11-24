# Task provenance and adaptation — revised 2026-11-24

There are 140 tasks: 103 single-tool and 37 no-tool. Twenty-five single-tool tasks are adapted from nine exact upstream source anchors. One easy no-tool task adapts a tenth anchor. These are **not 25 independent upstream scenarios**: repeated adaptations share a source family. The remaining 114 tasks are authored.

Every source label uses `aob_scenario:<upstream-relative-file>#<record-id-or-line>`. For JSON files the anchor is an actual record ID; for question.txt it is a 1-based line. `source_index.json` records the original text and full-file SHA-256. The validator resolves every anchor against the unchanged pinned checkout. The selectors 39/38 in benchmarks/scenario_suite/scenarios.txt are not utterances and are not used as invented sources.

## Source mapping

| Anchor | Task IDs |
|---|---|
| `src/couchdb/scenarios_data/default/question.txt#1` | T001, T002 |
| `src/couchdb/scenarios_data/scenario_3/question.txt#12` | T007, T008 |
| `src/scenarios/local/vibration_utterance.json#309` | T009, T010, T011, T012, T013, T014, T015, T016 |
| `src/couchdb/scenarios_data/scenario_3/question.txt#21` | T023, T024, T025, T026 |
| `src/scenarios/local/vibration_utterance.json#308` | T027 |
| `src/scenarios/local/vibration_utterance.json#322` | T028, T128 |
| `src/couchdb/scenarios_data/scenario_3/question.txt#13` | T029, T030 |
| `src/couchdb/scenarios_data/scenario_1/question.txt#1` | T065, T067 |
| `src/couchdb/scenarios_data/scenario_3/question.txt#9` | T066, T068 |
| `src/scenarios/local/vibration_utterance.json#303` | T127 |

## Adaptation policy

The core operation of each selected source request is retained. Multi-step source 3 and utterance 322 contribute explicitly isolated retrieval steps; diagnosis, file writing and FFT stages are not relabeled as single-tool retrieval. The task text supplies identifiers and may bound the returned page. Sensor-discovery utterance 309 is clarified as registry-assigned names versus fields observed in telemetry, since its original wording alone is ambiguous in the selected catalog. Asset, site, measurement, window and workflow substitutions are authored adaptations and are identified in task notes.

Examples: T027 retains the Motor_01/Vibration_X/PLANT_A time-window retrieval from utterance 308; T028 and T128 isolate retrieval from 322; T029/T030 isolate one-measurement retrieval from scenario 3 line 13. T023–T026 adapt its observation-count requirement at line 21 together with the first/last timestamp output at lines 31–32. T001/T002 adapt site discovery and add commissioning/decommissioning contexts to test the MS purpose restriction.

PLANT_A and Motor_01 in those utterances are preserved as source identifiers, not asserted to have data in the checked-in MAIN IoT fixture. Empty data does not make a structurally supported selection invalid. These tasks evaluate the first tool choice, not successful live fixture execution. CHILLER6 is the work-order asset number; Chiller 6 is the registry display identifier. Other names and work-order states are checked against sample files; repair actions and prose are hypothetical requests, not claims about real events.

## Labels and wording

All single-tool queries contain 6–16 whitespace-delimited words. Only the identifier-only task group retains essential output restrictions; T004 explicitly says “without metadata” to distinguish the identifier list from the metadata list. This is documented in notes. Other single-tool requests remove the earlier steering negatives. Labels describe the directly requested operation, not every possible strategy involving a broader retrieval followed by model-side filtering/arithmetic.

Every single-tool task has a boolean ms_conflict; 78 are true and 25 false. These are author annotations of whether the requested scope conflicts with the explicit MS narrowing, including requested coverage and workflow. They are not measurements of runtime rows removed, nor a claim that every hypothetical condition exists in sample data. The MS rationale lists its conflicting task IDs.

The original 25 no-tool tasks remain: 20 easy and 5 out_of_scope. T129–T140 add 12 tempting requests without abstention hints. Their notes identify missing required keys, unresolved authority/action choice or contradictory states. Those cases must be clarified before a specific action, rather than filled with invented identifiers.

## Dependence and review

Source sharing, repeated operations and deliberate MS conflict coverage affect task independence. Report source-family counts; do not claim that the 25 adaptations are 25 independently sampled scenarios. Consider a source-family sensitivity analysis in addition to the locked task-level bootstrap, without silently altering that protocol. Sridhar’s manual task/paraphrase review and independent LLM equivalence judging remain pending. No server or model API was called.
