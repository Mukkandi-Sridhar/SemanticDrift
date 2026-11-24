# AssetOpsBench source provenance

- Upstream: https://github.com/IBM/AssetOpsBench
- Verified checkout HEAD: `0d044061ab3ffd4b213ddf6a0868c360d7e9667c`
- Extraction date: 2026-11-23 (Asia/Calcutta)
- License: Apache License 2.0, read from upstream `LICENSE`; an unchanged copy is included as `LICENSE.AssetOpsBench`.
- Source checkout: `vendor/AssetOpsBench/`, read-only for this work. No network access or server execution.

## Method

Descriptions are exact function docstrings cleaned with `ast.get_docstring(clean=True)` (inspect.cleandoc semantics); explicit decorator `name=`/`description=` override defaults. Order is iot, utilities, fmsr, wo; source declaration order for decorators, then the central registration list order for wo. The default WO surface includes both `_READ_TOOLS` and `_WRITE_TOOLS` (`AOB_READONLY` is not set to `1`). Its registered functions are wrappers defined in `wo/main.py`; backend functions in `wo/workorders.py` are not the client surface.

**Schemas were reconstructed from source by static analysis, not captured from a running server.** Parameter types, nullability and defaults are mapped to JSON Schema. Optional/nullable annotations are not required, as specified in the Phase 2 resume instructions. `PAGE_SIZE` resolves to the source literal 1000. `Dict[str, Any]` maps to an object with unconstrained additional properties. No unsupported custom input annotations were encountered. Return annotations are not inputs. FastMCP-generated titles and other runtime presentation metadata are not asserted to be reproduced.

Read/write labels follow `docs/mcp-servers.md`: 29 read, 7 write. `generate_failure_modes` is read + LLM-use and has not been executed. The selected four servers supply 36 tools; tsfm and vibration are excluded.

## Reproduce

```sh
git -C vendor/AssetOpsBench rev-parse HEAD
python3 src/semdrift/extract_tools.py --source vendor/AssetOpsBench --output /tmp/semdrift-v0-reproduced.json
cmp datasets/tools/v0_original.json /tmp/semdrift-v0-reproduced.json
python3 src/semdrift/validate_dataset.py
```

The extractor uses Python standard-library modules only, imports no upstream modules, and rejects a mismatched commit. The validator checks the emitted JSON Schema vocabulary with standard-library code; it is not an arbitrary JSON Schema implementation.

## Attribution and modifications

V0 descriptions are reproduced from IBM AssetOpsBench under Apache-2.0. P1/P2/P3/MG/MS contain descriptions modified by the SemanticDrift dataset author on 2026-11-23; they are experimental descriptions, not upstream descriptions or supported new capabilities. Schemas, names, access tags and ordering are unchanged across all six files. See `variants_rationale.json` for all 216 pairs. No root-level upstream NOTICE file was present.

## Source file hashes

Paths below are relative to the pinned upstream checkout.

| Path | SHA-256 |
|---|---|
| `src/servers/iot/main.py` | `b45d7072e4f3207f18392c7a127760cbb8ad22d8b78166f25f246b0b337d7801` |
| `src/servers/utilities/main.py` | `99b49ef7b904aad200faeec0da821a14f50713efa94abfd46594d4d2ca4ad969` |
| `src/servers/fmsr/main.py` | `fe447faf3ea6f0d90b22afce13f88f898f3652015c70a372c5eb2dd3562db231` |
| `src/servers/wo/main.py` | `ca7069240501922a1c95204c17656cc32ed500f8764c0b2c11498e90760ccc8a` |
| `src/servers/wo/workorders.py` | `8d78a7f751fc0b3ef364383e9f8809580d9d56da40b4b396cd9f482832f4795c` |
| `docs/mcp-servers.md` | `c49e1b6e429a087e75217683f9ffe5f84f32135f6606ffd23c17e8490755b903` |
| `LICENSE` | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |
| `docs/guideline/utterance_design_guideline.md` | `c57209e763579e93be18a316f3d69ecbf29053df21185b393c694c95e7b636c6` |
| `benchmarks/scenario_suite/scenarios.txt` | `6f587e7c7101737db00af7366fa795af144bb51587642563a99656d24b991d47` |
| `src/couchdb/scenarios_data/scenario_1/question.txt` | `604f1cb3deb924c1e21865a0e580bb7c1fe61e39f0df3993d755b2000ffa066c` |
| `src/couchdb/scenarios_data/scenario_3/question.txt` | `ab0147071bed7eedfa76659f1f4ee807c006b84e2b5e58d43c77aeb062e70e98` |
| `src/scenarios/local/vibration_utterance.json` | `e0fc9ea84df260be0360f8a1d88b1be4798e9b12ce1d34953b9e656848be58fa` |
| `src/couchdb/scenarios_data/shared/iot/asset_profile_sample.json` | `59affb7ff4e3f23592da059aa33f2da533b0d928b2e37796f9cfa8f3d4f813eb` |
| `src/couchdb/scenarios_data/shared/work_order/workorders.csv` | `86ea1dd775361fa42e3a568479b7303525fcec9db21f8237d93cc1cef881c4c1` |
| `src/couchdb/scenarios_data/shared/catalog/sensors.csv` | `c7303e70a7fa0d87c44787028402c7fd9559e63454570c3e5850d77151f33ad2` |
| `src/couchdb/scenarios_data/shared/catalog/assets.csv` | `37a81e3ceb6b791c9977e67c4cea8ec569882aff3842883559d70e971b01c583` |
