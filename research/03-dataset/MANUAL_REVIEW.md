# Manual paraphrase review: Sridhar

> **Status 2026-11-24 (complete):** Paraphrases 1–15: **12 ✅ as written; 3 corrected** (#2, #3, #4). MG/MS flags: #16 ❌ fixed, #17 ❌ fixed, #18 ✅ kept.

**How to review (about 30 minutes):** for each item, read ORIGINAL vs. VARIANT. For P1–P3, ask: *would a developer reading either one call the tool in exactly the same situations, with the same arguments?* Mark ✅ (same meaning) or ❌ (different) and write a short note if ❌.
For MG/MS items: MG should be *broader but still true*; MS should be *narrower* (that's intended).

When you're done, tell Claude which items are ❌. Claude will fix them and record the pass rate (e.g., 14/15) for the paper.

## 1. P1 · `stream_extent`

**Check:** Timezone handling, inclusive/exclusive bounds and non-null conditions unchanged?

**ORIGINAL (V0)**
```text
Inspect the size and timestamp span of an asset's telemetry stream.

Optionally filter by one measured sensor and a half-open ISO 8601 window:
`start` is inclusive and `end` is exclusive. Sensor-filtered records count
only when the field is present and non-null. Bounds and record timestamps
must consistently include or omit timezone offsets; aware timestamps are
compared by instant even when their offsets differ.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    asset_id: Exact asset id from `asset_ids()`, such as `Chiller 6`.
    sensor: Optional exact field name from `measured_sensors()`.
        Reserved metadata fields such as `asset_id` and `timestamp` are not
        valid sensor names.
    start: Optional inclusive ISO 8601 date or datetime lower bound.
    end: Optional exclusive ISO 8601 date or datetime upper bound.

Returns:
    StreamExtentResult: Earliest and latest matching timestamps, record
    count, whether the count exceeds one 1000-record page, and average
    interval implied by the span and count.
```

**VARIANT (P1)**
```text
Check asset telemetry record count and timestamp extent.

Optional filters select a measured sensor plus a ISO 8601 half-open interval:
`start` is included, whereas `end` is excluded. Sensor-filtered records qualify
only with that field non-null and present. Bounds and observation timestamps
must uniformly carry timezone offsets or uniformly omit them; aware timestamps undergo
comparison as instants, even with differing offsets.

Args:
    site_name: Supply an exact site identifier, e.g. `MAIN`; `sites()` can
        show which identifiers are valid.
    asset_id: Supply the exact identifier from `asset_ids()`, e.g. `Chiller 6`.
    sensor: An optional precise field name obtained through `measured_sensors()`.
        Reserved metadata names, including `asset_id` and `timestamp`, cannot be
        used as sensor identifiers.
    start: Optional lower boundary, included, as an date or datetime formatted using ISO 8601.
    end: Optional upper boundary, excluded, as an date or datetime formatted using ISO 8601.

Returns:
    StreamExtentResult: First and last qualifying timestamps, record
    count, an indication of whether it exceeds a page of 1000 records, and average
    spacing derived from the count and temporal extent.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 2. P2 · `stream_extent`

**Check:** Do all conditions still apply to the same records?

**ORIGINAL (V0)**
```text
Inspect the size and timestamp span of an asset's telemetry stream.

Optionally filter by one measured sensor and a half-open ISO 8601 window:
`start` is inclusive and `end` is exclusive. Sensor-filtered records count
only when the field is present and non-null. Bounds and record timestamps
must consistently include or omit timezone offsets; aware timestamps are
compared by instant even when their offsets differ.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    asset_id: Exact asset id from `asset_ids()`, such as `Chiller 6`.
    sensor: Optional exact field name from `measured_sensors()`.
        Reserved metadata fields such as `asset_id` and `timestamp` are not
        valid sensor names.
    start: Optional inclusive ISO 8601 date or datetime lower bound.
    end: Optional exclusive ISO 8601 date or datetime upper bound.

Returns:
    StreamExtentResult: Earliest and latest matching timestamps, record
    count, whether the count exceeds one 1000-record page, and average
    interval implied by the span and count.
```

**VARIANT (P2)**
```text
For asset telemetry, inspect the record count and timestamp extent.

A measured sensor and ISO 8601 half-open interval can optionally filter results:
Include `start`, exclude `end`. Records filtered by sensor qualify
only with a present, non-null field. Observation timestamps and bounds
must uniformly omit or include timezone offsets; offset-aware timestamps undergo
instant-based comparison even with differing offsets.

Args:
    site_name: For an exact identifier such as `MAIN`, `sites()` can
        show the valid site identifiers.
    asset_id: From `asset_ids()`, take an exact identifier, e.g. `Chiller 6`.
    sensor: From `measured_sensors()`, an optional exact field identifier.
        Metadata identifiers, including `asset_id` and `timestamp`, cannot be
        used as sensor identifiers.
    start: As an date or datetime formatted using ISO 8601, an optional included lower boundary.
    end: As an date or datetime formatted using ISO 8601, an optional excluded upper boundary.

Returns:
    StreamExtentResult: Qualifying first/last timestamps, plus record
    count, an indication of exceeding a page of 1000 records, and average
    spacing derived from the temporal extent and count.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 3. P3 · `history`

**Check:** Projection, metadata exclusion and cursor rules unchanged?

**ORIGINAL (V0)**
```text
Return one chronological page of telemetry observations for an asset.

Optional bounds form a half-open ISO 8601 window. Use `sensors` to project
exact measured fields; omit it to return all measured fields present in each
row. Every row includes `asset_id` and `timestamp` and excludes other record
metadata.

Leave `cursor` unset for the first page. When `has_more` is true, repeat the
same query with `next_cursor`. Cursors are opaque and query-bound. Timestamp
offset rules match `stream_extent()`.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    asset_id: Exact asset id from `asset_ids()`, such as `Chiller 6`.
    start: Optional inclusive ISO 8601 lower bound.
    end: Optional exclusive ISO 8601 upper bound.
    sensors: Optional non-empty list of exact measured field names. Duplicate
        names are removed while preserving order.
    limit: Maximum observations in this page, from 1 to 1000.
    cursor: Opaque `next_cursor` from the previous page of the same query.

Returns:
    HistoryResult: Projected observations, returned count, echoed bounds,
    and cursor fields for the next page.
```

**VARIANT (P3)**
```text
Retrieve a chronological telemetry page for an individual asset.

Optional bounds define a ISO 8601 half-open interval. Projection via `sensors` selects
exact measured fields; omission includes every present measured field in each
row. Rows retain `asset_id` and `timestamp` while omitting remaining record
bookkeeping metadata.

The initial page leaves `cursor` unset. A true `has_more` requires resubmitting the
identical query using `next_cursor`. Each cursor is opaque and query-specific. Timestamp
offsets are governed by `stream_extent()`.

Args:
    site_name: The requested site’s exact identifier, e.g. `MAIN`; invoke `sites()` to
        obtain the valid site identifiers.
    asset_id: Exact asset identifier obtained through `asset_ids()`, e.g. `Chiller 6`.
    start: An optional included lower boundary expressed in ISO 8601.
    end: Optional excluded upper boundary expressed in ISO 8601.
    sensors: Optional nonempty list specifying exact measured identifiers. Duplicate
        names are eliminated without reordering.
    limit: Per-page observation ceiling within 1–1000.
    cursor: The opaque `next_cursor` obtained from this query’s preceding page.

Returns:
    HistoryResult: Observations after projection, returned quantity, echoed boundaries,
    and subsequent-page cursor fields.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 4. P2 · `history`

**Check:** Cursor continuation still requires the identical query?

**ORIGINAL (V0)**
```text
Return one chronological page of telemetry observations for an asset.

Optional bounds form a half-open ISO 8601 window. Use `sensors` to project
exact measured fields; omit it to return all measured fields present in each
row. Every row includes `asset_id` and `timestamp` and excludes other record
metadata.

Leave `cursor` unset for the first page. When `has_more` is true, repeat the
same query with `next_cursor`. Cursors are opaque and query-bound. Timestamp
offset rules match `stream_extent()`.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    asset_id: Exact asset id from `asset_ids()`, such as `Chiller 6`.
    start: Optional inclusive ISO 8601 lower bound.
    end: Optional exclusive ISO 8601 upper bound.
    sensors: Optional non-empty list of exact measured field names. Duplicate
        names are removed while preserving order.
    limit: Maximum observations in this page, from 1 to 1000.
    cursor: Opaque `next_cursor` from the previous page of the same query.

Returns:
    HistoryResult: Projected observations, returned count, echoed bounds,
    and cursor fields for the next page.
```

**VARIANT (P2)**
```text
For an asset, fetch a chronologically ordered page of telemetry.

A ISO 8601 half-open interval optionally bounds results. Through `sensors`, select
precise measured fields; omission includes every measured field present per
row. Rows retain `asset_id` and `timestamp`, excluding remaining record
bookkeeping metadata.

On the initial page, omit `cursor`; a true `has_more` requires resubmitting the
identical query using `next_cursor`; each cursor is opaque, query-specific. Timestamp
offsets follow the rules of `stream_extent()`.

Args:
    site_name: For an exact identifier such as `MAIN`, `sites()` can
        show the valid site identifiers.
    asset_id: From `asset_ids()`, take an exact identifier, e.g. `Chiller 6`.
    start: An included lower boundary in ISO 8601, optionally supplied.
    end: An excluded upper boundary in ISO 8601, optionally supplied.
    sensors: Exact measured names in an optional nonempty list. Duplicate
        names are discarded in their original order.
    limit: Between 1 and 1000 observations at most per page.
    cursor: From this identical query’s preceding page, its opaque `next_cursor`.

Returns:
    HistoryResult: Observations after projection with their count and echoed boundaries,
    plus cursor fields to access the subsequent page.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 5. P1 · `sensor_stats`

**Check:** Numeric strings / invalid values / absent fields counted the same way?

**ORIGINAL (V0)**
```text
Compute numeric statistics for one or all measured sensors.

Omit `sensor` to summarize every measured field. Optional bounds form a
half-open ISO 8601 window. Timestamp offset rules match `stream_extent()`.

Finite numbers and numeric strings contribute to the numeric statistics.
Present null, boolean, non-numeric, and non-finite values contribute to
`null_count`; missing fields contribute to neither count. `stddev` is the
population standard deviation: `0.0` for one numeric value and null for none.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    asset_id: Exact asset id from `asset_ids()`, such as `Chiller 6`.
    sensor: Optional exact field name from `measured_sensors()`. Omit it to
        summarize all measured fields.
    start: Optional inclusive ISO 8601 lower bound.
    end: Optional exclusive ISO 8601 upper bound.

Returns:
    SensorStatsResult: Per-field numeric and null counts, range, mean,
    population standard deviation, and earliest/latest numeric timestamps.
```

**VARIANT (P1)**
```text
Calculate numerical summaries for one measured sensor or every measured sensor.

Leave `sensor` out to summarize each measured field. The optional bounds define a
ISO 8601 half-open interval. Timestamp offsets follow `stream_extent()`.

Finite numbers, including numeric strings, enter the numerical summaries.
Present booleans, nulls, non-finite and non-numeric values enter
`null_count`; absent fields enter neither count. Here, `stddev` denotes
population standard deviation: one numeric observation yields `0.0`; none yields null.

Args:
    site_name: Supply an exact site identifier, e.g. `MAIN`; `sites()` can
        show which identifiers are valid.
    asset_id: Supply the exact identifier from `asset_ids()`, e.g. `Chiller 6`.
    sensor: An optional precise field name obtained through `measured_sensors()`. Leave it out to
        summarize each measured field.
    start: Optional ISO 8601 lower boundary, included.
    end: Optional ISO 8601 upper boundary, excluded.

Returns:
    SensorStatsResult: Counts of numeric/null values per field, mean, range,
    population standard deviation, with first/last timestamps of numeric observations.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 6. P2 · `sensor_stats`

**Check:** Population std-dev and the one-value / no-value cases identical?

**ORIGINAL (V0)**
```text
Compute numeric statistics for one or all measured sensors.

Omit `sensor` to summarize every measured field. Optional bounds form a
half-open ISO 8601 window. Timestamp offset rules match `stream_extent()`.

Finite numbers and numeric strings contribute to the numeric statistics.
Present null, boolean, non-numeric, and non-finite values contribute to
`null_count`; missing fields contribute to neither count. `stddev` is the
population standard deviation: `0.0` for one numeric value and null for none.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    asset_id: Exact asset id from `asset_ids()`, such as `Chiller 6`.
    sensor: Optional exact field name from `measured_sensors()`. Omit it to
        summarize all measured fields.
    start: Optional inclusive ISO 8601 lower bound.
    end: Optional exclusive ISO 8601 upper bound.

Returns:
    SensorStatsResult: Per-field numeric and null counts, range, mean,
    population standard deviation, and earliest/latest numeric timestamps.
```

**VARIANT (P2)**
```text
For all measured sensors or one, calculate numerical summaries.

Without `sensor`, each measured field is summarized. Optional bounds define a
ISO 8601 half-open interval; offset treatment follows `stream_extent()`.

The numerical summaries include finite numbers and strings representing numbers.
Present non-finite, non-numeric, boolean and null values enter
`null_count`; neither count includes absent fields. Here, `stddev` denotes
population standard deviation, yielding `0.0` with a single numeric observation, null with none.

Args:
    site_name: For an exact identifier such as `MAIN`, `sites()` can
        show the valid site identifiers.
    asset_id: From `asset_ids()`, take an exact identifier, e.g. `Chiller 6`.
    sensor: From `measured_sensors()`, an optional exact field identifier; omission will
        summarize each measured field.
    start: An included lower boundary in ISO 8601, optionally supplied.
    end: An excluded upper boundary in ISO 8601, optionally supplied.

Returns:
    SensorStatsResult: Field-specific range and mean, counts of numeric/null values,
    population standard deviation, plus first/last timestamps of numeric observations.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 7. P3 · `sensor_stats`

**Check:** First/last timestamps still refer to numeric observations only?

**ORIGINAL (V0)**
```text
Compute numeric statistics for one or all measured sensors.

Omit `sensor` to summarize every measured field. Optional bounds form a
half-open ISO 8601 window. Timestamp offset rules match `stream_extent()`.

Finite numbers and numeric strings contribute to the numeric statistics.
Present null, boolean, non-numeric, and non-finite values contribute to
`null_count`; missing fields contribute to neither count. `stddev` is the
population standard deviation: `0.0` for one numeric value and null for none.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    asset_id: Exact asset id from `asset_ids()`, such as `Chiller 6`.
    sensor: Optional exact field name from `measured_sensors()`. Omit it to
        summarize all measured fields.
    start: Optional inclusive ISO 8601 lower bound.
    end: Optional exclusive ISO 8601 upper bound.

Returns:
    SensorStatsResult: Per-field numeric and null counts, range, mean,
    population standard deviation, and earliest/latest numeric timestamps.
```

**VARIANT (P3)**
```text
Compute numerical summaries over one measured sensor or every measured sensor.

Omission of `sensor` selects each measured field. Optional boundaries define a
ISO 8601 half-open interval. Timestamp offsets follow `stream_extent()`.

Numerical summaries include numeric strings as well as finite numbers.
Present non-numeric values, booleans, nulls and values that are non-finite enter
`null_count`; absent fields enter neither count. Here, `stddev` denotes
population standard deviation, yielding `0.0` with a single numeric observation; none yields null.

Args:
    site_name: The requested site’s exact identifier, e.g. `MAIN`; invoke `sites()` to
        obtain the valid site identifiers.
    asset_id: Exact asset identifier obtained through `asset_ids()`, e.g. `Chiller 6`.
    sensor: An optional exact field identifier obtained through `measured_sensors()`. Omission will
        summarize each measured field.
    start: Optional included lower boundary expressed in ISO 8601.
    end: Optional excluded upper boundary expressed in ISO 8601.

Returns:
    SensorStatsResult: Field-specific numeric/null counts, mean, range,
    population standard deviation, with first/last timestamps of numeric observations.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 8. P2 · `latest_reading`

**Check:** With a sensor given: newest non-null record for that sensor (not the newest whole record)?

**ORIGINAL (V0)**
```text
Return the newest telemetry observation for an asset.

Omit `sensor` for all measured fields in the newest record. When a sensor is
provided, returns the newest record where that field is present and non-null.
Records are compared by parsed timestamp using the `stream_extent()` rules.

`age_seconds` is the difference between the current UTC time and the reading
timestamp. Offset-free timestamps are interpreted as UTC; a negative value
indicates a timestamp in the future.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    asset_id: Exact asset id from `asset_ids()`, such as `Chiller 6`.
    sensor: Optional exact field name from `measured_sensors()`. Reserved
        metadata fields are not valid sensor names.

Returns:
    LatestReadingResult: Selected timestamp, values, and age in seconds.
```

**VARIANT (P2)**
```text
For an asset, fetch its most recent telemetry observation.

Without `sensor`, include every measured field of the latest record. If a sensor is
specified, its field must be non-null and present in the most recent qualifying record.
The tool orders records by parsed timestamps, following `stream_extent()`.

`age_seconds` expresses current UTC time minus the observation
timestamp. Timestamps lacking offsets are treated as UTC; negative age
signifies that the timestamp lies ahead of now.

Args:
    site_name: For an exact identifier such as `MAIN`, `sites()` can
        show the valid site identifiers.
    asset_id: From `asset_ids()`, take an exact identifier, e.g. `Chiller 6`.
    sensor: From `measured_sensors()`, an optional exact field identifier. Reserved
        metadata identifiers cannot serve as sensors.

Returns:
    LatestReadingResult: Chosen values and timestamp, with age measured in seconds.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 9. P1 · `sensor_coverage`

**Check:** Non-null of any type counts; all-null fields keep zero count and null bounds?

**ORIGINAL (V0)**
```text
Summarize non-null observation coverage for every measured sensor.

Scans the full timestamped stream. `non_null_count` includes present,
non-null values of any type. Fields observed only with null values have zero
count and null bounds. Timestamp offset rules match `stream_extent()`.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    asset_id: Exact asset id from `asset_ids()`, such as `Chiller 6`.

Returns:
    SensorCoverageResult: Timestamped records scanned and per-sensor counts
    and chronological bounds, sorted by field name.
```

**VARIANT (P1)**
```text
Summarize every measured sensor’s coverage of observations that are not null.

Scans the entire timestamped stream. `non_null_count` counts any present,
values that are non-null, irrespective of type. Exclusively null-valued fields receive zero
count with null boundaries. Timestamp offsets follow `stream_extent()`.

Args:
    site_name: Supply an exact site identifier, e.g. `MAIN`; `sites()` can
        show which identifiers are valid.
    asset_id: Supply the exact identifier from `asset_ids()`, e.g. `Chiller 6`.

Returns:
    SensorCoverageResult: Scanned timestamped-record total and counts per sensor
    with chronological boundaries, ordered by field name.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 10. P3 · `find_assets_by_sensors`

**Check:** all/any, exact vs. fragment, source default, dedup order unchanged?

**ORIGINAL (V0)**
```text
Find site assets by installed or measured sensor names.

Searches only assets registered at `site_name`. Duplicate queries are
removed while preserving first occurrence order.

Args:
    site_name: Exact site id to query, such as `MAIN`. Use `sites()` to
        discover valid site ids.
    sensors: Sensor names, or fragments when `substring` is true.
    match: `all` requires every query; `any` requires at least one.
    substring: Use case-insensitive fragment matching instead of exact,
        case-sensitive matching.
    source: `measured` searches observed fields; `installed` searches
        registry assignments. Defaults to `measured`.

Returns:
    FindAssetsResult: Query settings and matching assets with the concrete
    sensor names found.
```

**VARIANT (P3)**
```text
Identify site assets through assigned or observed sensor names.

Search excludes assets not registered under `site_name`. Repeated queries are
eliminated while retaining the order of initial occurrence.

Args:
    site_name: The requested site’s exact identifier, e.g. `MAIN`; invoke `sites()` to
        obtain the valid site identifiers.
    sensors: Sensor identifiers, or fragments if `substring` is enabled.
    match: `all` requires each query to match; `any` requires one or more matches.
    substring: Select case-insensitive fragment comparison rather than exact,
        case-sensitive equality.
    source: `measured` targets observed fields; `installed` targets
        registry sensor assignments; the default is `measured`.

Returns:
    FindAssetsResult: Search configuration and matched assets with the specific
    matched sensor identifiers.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 11. P1 · `get_failure_modes`

**Check:** Is normalization clearly done BY THE TOOL (not an instruction to the caller)?

**ORIGINAL (V0)**
```text
READ the known failure modes for an asset class.

Args:
    asset_class: Asset class to look up, such as "pump". Case, whitespace,
        digits, underscores, and hyphens are normalized before querying.
```

**VARIANT (P1)**
```text
READ known failure modes associated with the specified class of assets.

Args:
    asset_class: Requested class, e.g. "pump". The tool normalizes case, whitespace,
        digits, hyphens and underscores before the lookup.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 12. P2 · `generate_failure_modes`

**Check:** Still says it extends stored modes and does NOT write to the database?

**ORIGINAL (V0)**
```text
GENERATE a new or extended failure-mode list for an asset class.

This tool does not write to the database. If the normalized `asset_class`
exists in the database, the current stored failure modes are used as context
and the LLM generates additional modes. If no stored modes exist, the LLM
generates a new list from scratch.

Args:
    asset_class: Asset class to reason about, such as "pump". Case,
        whitespace, digits, underscores, and hyphens are normalized before
        prompting the LLM.
    max_modes: Maximum number of new failure modes to request from the LLM.
```

**VARIANT (P2)**
```text
For a specified asset class, GENERATE a failure-mode list, fresh or expanded.

No database writes occur. If normalized `asset_class`
is already stored, the saved modes provide context
for additional modes from the LLM. Without stored modes, the LLM
produces a fresh list.

Args:
    asset_class: Requested class for reasoning, e.g. "pump". Letter case,
        whitespace, digits, hyphens and underscores are normalized before
        sending the LLM prompt.
    max_modes: From the LLM, the maximum requested quantity of newly generated failure modes.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 13. P3 · `add_failure_modes`

**Check:** Merge, case-insensitive dedup, additions-only report, exhaustive default unchanged?

**ORIGINAL (V0)**
```text
WRITE failure modes for an asset class to the database.

Existing modes are preserved, incoming modes are merged case-insensitively,
and only newly added modes are reported. Use this after curated or generated
modes should become available to future `get_failure_modes` calls.

Args:
    asset_class: Asset class to update, such as "pump". Case, whitespace,
        digits, underscores, and hyphens are normalized before writing.
    failure_modes: Failure modes to add for the asset class.
    exhaustive: Set true only when the stored list is believed complete. If
        omitted, the existing value is preserved; new records default false.
    source: Optional provenance for the stored list.
```

**VARIANT (P3)**
```text
WRITE failure modes associated with an asset class into database storage.

Retains existing modes and merges supplied modes without case sensitivity,
reporting exclusively added modes. Use when generated or curated
modes should become retrievable through subsequent `get_failure_modes` retrieval.

Args:
    asset_class: Class being modified, e.g. "pump". The tool normalizes case, whitespace,
        digits, hyphens and underscores prior to persistence.
    failure_modes: Modes to append for the specified asset class.
    exhaustive: Specify true exclusively for a stored set believed complete. When
        omitted, the tool retains the prior value; newly created records default to false.
    source: Provenance, optionally associated with the persisted set.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 14. P2 · `get_workorder_tasks`

**Check:** "Subordinate tasks" = child tasks of the parent work order?

**ORIGINAL (V0)**
```text
List the child tasks of a parent work order.
```

**VARIANT (P2)**
```text
Show a work-order’s subordinate tasks.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 15. P3 · `list_workorders`

**Check:** OPEN / APPROVED_PENDING and page_size=0 behavior kept, no invented filters?

**ORIGINAL (V0)**
```text
List work orders with optional filters (site, status, asset, priority, dates).
status accepts OPEN / APPROVED_PENDING; page_size=0 returns all matches in one call.
```

**VARIANT (P3)**
```text
Enumerate work orders, optionally restricted by site, asset, status, priority or dates.
status permits OPEN / APPROVED_PENDING; setting page_size=0 retrieves every match together.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 16. MG · `cancel_workorder`

**Check:** CLAUDE FLAG: "multiple work orders" claims a capability the schema lacks (one wonum). Is that "broader scope" or a false claim? If false, reword (e.g., "Cancel work").

**ORIGINAL (V0)**
```text
Cancel a work order (-> CAN).
```

**VARIANT (MG)**
```text
Cancel multiple work orders (-> CAN).
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 17. MG · `get_failure_modes`

**Check:** "potential" failure modes now overlaps generate_failure_modes. Acceptable as over-generalization?

**ORIGINAL (V0)**
```text
READ the known failure modes for an asset class.

Args:
    asset_class: Asset class to look up, such as "pump". Case, whitespace,
        digits, underscores, and hyphens are normalized before querying.
```

**VARIANT (MG)**
```text
READ the potential failure modes for an asset class.

Args:
    asset_class: Asset class to look up, such as "pump". Case, whitespace,
        digits, underscores, and hyphens are normalized before querying.
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______

## 18. MS · `generate_work_order`

**Check:** "preventive" work order: plausible narrowing? (conflicts with corrective repair tasks)

**ORIGINAL (V0)**
```text
Create a work order (status WAPPR). Attach aob_source provenance (agent/trigger/evidence).
```

**VARIANT (MS)**
```text
Create a preventive work order (status WAPPR). Attach aob_source provenance (agent/trigger/evidence).
```

Verdict: ☐ ✅ same  ☐ ❌ different · Note: ______
