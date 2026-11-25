# One request, ten catalogs: a worked example

A single case from the main run, chosen by a fixed rule: the model is correct in every repeat
under the original catalog and the placebo, and wrong in every repeat under the earliest
historical catalog (H1). Two (model, task) pairs met that rule; this is the one with three
repeats.

**Request (task T034):**

> Read Chiller 6's most recent Condenser Water Flow measurement at MAIN.

**Gold tool:** `latest_reading`. **Model:** Claude Haiku 5.5.

## What the model chose

| Catalog | Repeat 1 | Repeat 2 | Repeat 3 |
|---|---|---|---|
| Original (V0) | `latest_reading` ✓ | `latest_reading` ✓ | `latest_reading` ✓ |
| Placebo (V0R) | `latest_reading` ✓ | `latest_reading` ✓ | `latest_reading` ✓ |
| Paraphrases P1–P3, vaguer, narrower | `latest_reading` ✓ (all 15 trials) | | |
| Historical, previous (H3) | `latest_reading` ✓ | `latest_reading` ✓ | `latest_reading` ✓ |
| **Historical, earliest (H1)** | **`measured_sensors` ✗** | **`measured_sensors` ✗** | **`measured_sensors` ✗** |

Every correct call used the same arguments
(`site_name: "MAIN"`, `asset_id: "Chiller 6"`, `sensor: "Condenser Water Flow"`).

## What changed between V0 and H1

Both descriptions come from the AssetOpsBench repository (H1 from July 2026 commits, V0 from
the pinned November commit). The tools, parameters and everything else are the same.

`measured_sensors`:

| H1 (earlier) | V0 (current) |
|---|---|
| List measured sensor fields for one asset at one site. | List measurement fields observed in an asset's telemetry stream. Returns the sorted union across the full stream, excluding record metadata. Use `installed_sensors()` for assigned sensors, which may differ. |

`latest_reading` (opening paragraph):

| H1 (earlier) | V0 (current) |
|---|---|
| Omit `sensor` to return every measured field present in the newest record. Provide an exact field name from `measured_sensors()` to return the newest record where that field is present and non-null. … | Omit `sensor` for all measured fields in the newest record. When a sensor is provided, returns the newest record where that field is present and non-null. … |

## Reading it carefully

The earlier `measured_sensors` description is one short line built around the word "measured",
and the earlier `latest_reading` description points to `measured_sensors()` by name. The current
wording says what `measured_sensors` returns (a list of field names, not values). That may be
why the model followed a different path, but **this is one case, not evidence on its own**: the
study's claims rest on the aggregate, placebo-adjusted analysis in `research/FINDINGS.md`. The
example shows what a wording-induced change looks like in practice: the same request, the same
tools and the same model, a consistent change of decision, and nothing that an accuracy average
would show.
