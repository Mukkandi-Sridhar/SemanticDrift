"""Offline checks for catalogs, tasks, provenance, and study covariates."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Explicit trusted sibling path also works in Python isolated mode (-I).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_tools import PIN, extract
from lexical_overlap import compute as compute_overlap

CLI_DESCRIPTION = """Offline structural validation; semantic equivalence still needs human review.

Run from repo root: python3 src/semdrift/validate_dataset.py
Word length and overlap use Unicode word tokens (underscores retained),
casefolded for overlap. Hyphens/slashes/punctuation are word boundaries.
"""

MIN_LENGTH_RATIO = 0.7
MAX_LENGTH_RATIO = 1.3
MAX_OVERLAP_GAP = 0.03

NGRAM_SIZE = 4
EXPECTED_CATALOGS = 6
NEAR_MIN_TASKS = 4
DEFAULT_MIN_TASKS = 2
MIN_SINGLE_TASKS = 90
MAX_SINGLE_TASKS = 110
MIN_NO_TOOL_TASKS = 37
MIN_TEMPTING_TASKS = 12
MIN_SOURCE_TASKS = 25
MIN_QUERY_WORDS = 6
MAX_QUERY_WORDS = 20
OVERLAP_TOLERANCE = 1e-10
EXPECTED_AUDIT_RECORDS = 108
SCHEMA_KEYWORDS = {
    "type",
    "properties",
    "required",
    "items",
    "anyOf",
    "additionalProperties",
    "default",
    "x_source_annotation",
}
SCHEMA_TYPES = {"null", "string", "integer", "number", "boolean", "array", "object"}

FILES = {
    "V0": "v0_original.json",
    "P1": "p1_paraphrase.json",
    "P2": "p2_paraphrase.json",
    "P3": "p3_paraphrase.json",
    "MG": "mg_overgeneral.json",
    "MS": "ms_overspecial.json",
}
# Explicitly paired near-miss groups. More than the examples in prompt 04.
NEAR_GROUPS = [
    ["latest_reading", "history", "sensor_stats"],
    ["installed_sensors", "measured_sensors"],
    ["get_failure_modes", "generate_failure_modes"],
    ["get_workorder", "list_workorders"],
    ["asset_ids", "assets"],
    ["stream_extent", "sensor_coverage"],
    ["get_workorder_costs", "get_workorder_actuals_vs_planned"],
]
NEAR = {n for group in NEAR_GROUPS for n in group}
# Proper names only; no exemptions for generic maintenance language.
PROPER = [
    "Chiller 6",
    "ISO 8601",
    "MAIN",
    "PUMP",
    "COMPRESSOR",
    "UTC",
    "JSON",
    "LLM",
    "FCC",
    "CouchDB",
    "APPR",
    "WAPPR",
    "CAN",
    "COMP",
    "OPEN",
    "APPROVED_PENDING",
    "FC001",
]


def words(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold())


def ngrams(text: str, n: int = NGRAM_SIZE) -> set[tuple[str, ...]]:
    tokens = words(text)
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def overlaps(text: str, original: str) -> list[tuple[str, ...]]:
    return sorted(ngrams(text) & ngrams(original))


def overlap_exempt(gram: tuple[str, ...], row: dict[str, Any]) -> bool:
    # A matching run is exempt only if every token belongs to a proper name,
    # parameter identifier, or status code. Do not exempt entire sentences.
    allowed = set(row["input_schema"]["properties"])
    # Fixed section markers and result type names cannot be rewritten.
    allowed.update(["args", "returns"])
    allowed.update(
        m.casefold()
        for m in re.findall(r"^    ([A-Za-z]+):", row["description"], re.M)
        if m[:1].isupper()
    )
    for p in PROPER:
        allowed.update(words(p))
    return all(w in allowed for w in gram)


def structure(text: str) -> list[tuple[int, bool, str | None]]:
    """Positions, indentation and blank lines, plus immutable section headings."""
    return [
        (
            len(line) - len(line.lstrip()),
            not bool(line.strip()),
            line.strip() if line.strip() in {"Args:", "Returns:"} else None,
        )
        for line in text.splitlines()
    ]


def code_spans(text: str) -> Counter[str]:
    return Counter(m.group(0) for m in re.finditer(r"(`+)([^`]*?)\1", text))


def sections(text: str) -> str:
    positions = [text.index(h) for h in ("Args:", "Returns:") if h in text]
    return text[min(positions) :] if positions else ""


def prefixes(text: str) -> list[str]:
    return re.findall(r"^    ([A-Za-z_][A-Za-z_0-9]*):", text, re.M)


def accepts(value: Any, schema: dict[str, Any]) -> bool:
    if "anyOf" in schema:
        return any(accepts(value, branch) for branch in schema["anyOf"])
    schema_type = schema.get("type")
    valid = {
        "null": value is None,
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
    }
    if schema_type and not valid[schema_type]:
        return False
    if schema_type == "array":
        return all(accepts(v, schema.get("items", {})) for v in value)
    if schema_type == "object":
        if any(k not in value for k in schema.get("required", [])):
            return False
        return all(
            accepts(v, schema.get("properties", {}).get(k, schema.get("additionalProperties", {})))
            for k, v in value.items()
        )
    return True


def validate_schema(schema: dict[str, Any]) -> None:
    if not isinstance(schema, dict):
        raise ValueError("Schema must be an object")
    if set(schema) - SCHEMA_KEYWORDS:
        raise ValueError("Unsupported schema vocabulary")
    if "type" in schema and schema["type"] not in SCHEMA_TYPES:
        raise ValueError("Invalid type")
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise ValueError("Invalid properties")
        for key, v in schema["properties"].items():
            if not isinstance(key, str):
                raise ValueError("Property name must be a string")
            validate_schema(v)
    _validate_required(schema)
    for key in ("items", "additionalProperties"):
        if key in schema:
            validate_schema(schema[key])
    if "anyOf" in schema:
        if not isinstance(schema["anyOf"], list) or not schema["anyOf"]:
            raise ValueError("Invalid anyOf")
        for branch in schema["anyOf"]:
            validate_schema(branch)
    if "x_source_annotation" in schema and not isinstance(schema["x_source_annotation"], str):
        raise ValueError("Invalid source annotation")
    if "default" in schema and not accepts(schema["default"], schema):
        raise ValueError("Default does not match schema")


def _load_catalogs(root: Path, check: Callable[..., None]) -> dict[str, list[dict[str, Any]]]:
    catalogs = {}
    for variant, file in FILES.items():
        try:
            catalogs[variant] = json.loads((root / "datasets/tools" / file).read_text())
        except (OSError, ValueError) as error:
            check("load " + variant, False, str(error))
    return catalogs


def _check_catalogs(
    root: Path,
    catalogs: dict[str, list[dict[str, Any]]],
    base: list[dict[str, Any]],
    names: list[str],
    check: Callable[..., None],
) -> None:
    check(
        "upstream commit pin",
        subprocess.check_output(
            ["git", "-C", str(root / "vendor/AssetOpsBench"), "rev-parse", "HEAD"], text=True
        ).strip()
        == PIN,
    )
    check("V0 source reconstruction", base == extract(root / "vendor/AssetOpsBench"))
    check("unique tool names", len(names) == len(set(names)))
    check("six catalogs", len(catalogs) == EXPECTED_CATALOGS)


def _check_catalog_variants(
    catalogs: dict[str, list[dict[str, Any]]],
    base: list[dict[str, Any]],
    names: list[str],
    check: Callable[..., None],
) -> None:
    for variant, catalog in catalogs.items():
        check(variant + " ordered names", [tool["name"] for tool in catalog] == names)
        check(
            variant + " identical non-description fields",
            [{k: v for k, v in tool.items() if k != "description"} for tool in catalog]
            == [{k: v for k, v in tool.items() if k != "description"} for tool in base],
        )
        check(
            variant + " nonempty descriptions",
            all(
                isinstance(tool["description"], str) and tool["description"].strip()
                for tool in catalog
            ),
        )
        if variant != "V0":
            _check_variant(variant, catalog, base, check)
            check(
                variant + " descriptions changed",
                all(
                    tool["description"] != original["description"]
                    for tool, original in zip(catalog, base)
                ),
            )


def _check_variant(
    variant: str,
    catalog: list[dict[str, Any]],
    base: list[dict[str, Any]],
    check: Callable[..., None],
) -> None:
    lengths, characters, reused = _variant_differences(catalog, base)
    check(variant + " word length ±30%", not lengths, "; ".join(lengths))
    check(variant + " character length ±30%", not characters, "; ".join(characters))
    if variant.startswith("P"):
        _check_paraphrase(variant, catalog, base, reused, check)
    check(
        variant + " required section headers",
        all(
            all(
                h not in original["description"] or h in tool["description"]
                for h in ("Args:", "Returns:")
            )
            for tool, original in zip(catalog, base)
        ),
    )
    if variant in ("MG", "MS"):
        check(
            variant + " verbatim Args/Returns",
            all(
                sections(tool["description"]) == sections(original["description"])
                for tool, original in zip(catalog, base)
            ),
        )


def _check_catalog_schemas(base: list[dict[str, Any]], check: Callable[..., None]) -> None:
    # Validate the exact emitted JSON Schema vocabulary, with no dependencies.
    # Reject unsupported keywords instead of claiming full arbitrary-schema support.
    errors = []
    for tool in base:
        try:
            validate_schema(tool["input_schema"])
        except (ValueError, TypeError) as error:
            errors.append(tool["name"] + ": " + str(error))
    check(
        "JSON Schema emitted-vocabulary validity and default types", not errors, "; ".join(errors)
    )


def _load_rationales(
    root: Path, names: list[str], check: Callable[..., None]
) -> list[dict[str, Any]] | None:
    rationales = None
    try:
        rationales = json.loads((root / "datasets/tools/variants_rationale.json").read_text())
        pairs = [(r["tool"], r["variant"]) for r in rationales]
        check(
            "rationale exact coverage",
            len(pairs) == len(set(pairs))
            and set(pairs) == {(n, v) for n in names for v in FILES}
            and all(r["change_summary"].strip() for r in rationales),
        )
    except (OSError, ValueError) as error:
        check("rationales", False, str(error))
    return rationales


def _load_tasks(root: Path, check: Callable[..., None]) -> list[dict[str, Any]]:
    try:
        tasks = [
            json.loads(line)
            for line in (root / "datasets/tasks/tasks.jsonl").read_text().splitlines()
        ]
    except (OSError, ValueError) as error:
        check("tasks available", False, str(error))
        tasks = []
    return tasks


def _check_provenance(root: Path, tasks: list[dict[str, Any]], check: Callable[..., None]) -> None:
    try:
        index = json.loads((root / "datasets/tasks/source_index.json").read_text())
        source_errors = []
        for key, entry in index.items():
            raw = (root / "vendor/AssetOpsBench" / entry["path"]).read_bytes()
            text = raw.decode()
            if entry["record_id"] is not None:
                text = next(r["text"] for r in json.loads(text) if r["id"] == entry["record_id"])
            else:
                text = text.splitlines()[entry["line"] - 1]
            anchor = entry["record_id"] if entry["record_id"] is not None else entry["line"]
            if key != entry["path"] + "#" + str(anchor) or not text.strip():
                source_errors.append(key)
            if hashlib.sha256(raw).hexdigest() != entry["sha256"] or text != entry["original_text"]:
                source_errors.append(key)
        source_errors += [
            task["id"]
            for task in tasks
            if task["source"].startswith("aob_scenario:")
            and task["source"].split(":", 1)[1] not in index
        ]
        check(
            "scenario source traceability",
            not source_errors,
            repr(source_errors) if source_errors else "",
        )
    except (OSError, ValueError, KeyError, StopIteration, IndexError) as error:
        check("scenario source traceability", False, str(error))


def _check_task_labels(
    tasks: list[dict[str, Any]], lookup: dict[str, dict[str, Any]], check: Callable[..., None]
) -> None:
    check("unique task IDs", bool(tasks) and len({task["id"] for task in tasks}) == len(tasks))
    invalid = []
    leaks = []
    for task in tasks:
        gold = task["gold"]
        valid = gold == "NONE" or gold in lookup
        if not valid:
            invalid.append(task["id"])
            continue
        expected = "none" if gold == "NONE" else lookup[gold]["access"]
        if task["gold_access"] != expected or task["type"] != (
            "no_tool" if gold == "NONE" else "single_tool"
        ):
            invalid.append(task["id"])
        if task["near_miss_of"] is not None and task["near_miss_of"] not in lookup:
            invalid.append(task["id"])
        if not re.fullmatch(r"T\d{3}", task["id"]) or not task["query"].strip():
            invalid.append(task["id"])
        if not (task["source"] == "authored" or task["source"].startswith("aob_scenario:")):
            invalid.append(task["id"])
        if gold != "NONE":
            if gold.casefold() in task["query"].casefold():
                leaks.append(task["id"] + " tool name")
            shared = overlaps(task["query"], lookup[gold]["description"])
            if shared:
                leaks.append(task["id"] + " " + repr(shared))
    check("task labels, access, type, references", not invalid, repr(invalid) if invalid else "")
    check("task leakage", not leaks, "; ".join(leaks))


def _has_near_miss(tasks: list[dict[str, Any]], name: str) -> bool:
    for task in tasks:
        if task["gold"] != name:
            continue
        siblings = next(group for group in NEAR_GROUPS if name in group)
        if task["near_miss_of"] in siblings and task["near_miss_of"] != name:
            return True
    return False


def _conflicting_task_ids(tasks: list[dict[str, Any]], name: str) -> set[str]:
    return {
        task["id"] for task in tasks if task["gold"] == name and task.get("ms_conflict") is True
    }


def _check_task_coverage(
    tasks: list[dict[str, Any]], names: list[str], check: Callable[..., None]
) -> None:
    counts = Counter(task["gold"] for task in tasks)
    for n in names:
        minimum = NEAR_MIN_TASKS if n in NEAR else DEFAULT_MIN_TASKS
        print(f"COUNT {n}: {counts[n]} (minimum {minimum})")
    check(
        "per-tool minimum coverage",
        all(counts[n] >= (NEAR_MIN_TASKS if n in NEAR else DEFAULT_MIN_TASKS) for n in names),
    )
    check(
        "near-miss sibling annotations",
        all(_has_near_miss(tasks, name) for name in NEAR),
    )
    no_tool_count = counts["NONE"]
    single_count = len(tasks) - no_tool_count
    # "About" is disclosed, not disguised as an exact 120 requirement.
    check(
        "task counts",
        MIN_SINGLE_TASKS <= single_count <= MAX_SINGLE_TASKS and no_tool_count >= MIN_NO_TOOL_TASKS,
        f"{single_count} single_tool + {no_tool_count} no_tool = {len(tasks)}; target ≈95 + 25",
    )


def _check_task_conflicts(
    tasks: list[dict[str, Any]],
    names: list[str],
    rationales: list[dict[str, Any]] | None,
    check: Callable[..., None],
) -> None:
    single_tasks = [task for task in tasks if task["type"] == "single_tool"]
    check(
        "single-tool ms_conflict booleans",
        all(type(task.get("ms_conflict")) is bool for task in single_tasks),
    )
    check(
        "MS conflict for every tool",
        all(
            any(task["gold"] == n and task.get("ms_conflict") is True for task in single_tasks)
            for n in names
        ),
    )
    if rationales is not None:
        check(
            "MS rationale conflict witnesses",
            all(
                set(r.get("conflicting_task_ids", []))
                == _conflicting_task_ids(single_tasks, r["tool"])
                for r in rationales
                if r["variant"] == "MS"
            ),
        )


def _check_no_tool_tasks(tasks: list[dict[str, Any]], check: Callable[..., None]) -> None:
    no_tasks = [task for task in tasks if task["type"] == "no_tool"]
    check(
        "no-tool subtypes",
        all(
            task.get("subtype") in {"easy", "tempting", "out_of_scope"} and task["notes"].strip()
            for task in no_tasks
        ),
    )
    tempting = [task for task in no_tasks if task.get("subtype") == "tempting"]
    check("tempting no-tool count", len(tempting) >= MIN_TEMPTING_TASKS, str(len(tempting)))
    hint = re.compile(
        r"\b(do not|don.t|without|rather than|general guidance|plain text|"
        r"do nothing|ask a human)\b",
        re.I,
    )
    check(
        "tempting queries omit steering hints",
        not any(hint.search(task["query"]) for task in tempting),
    )


def _check_task_sources(tasks: list[dict[str, Any]], check: Callable[..., None]) -> None:
    single_tasks = [task for task in tasks if task["type"] == "single_tool"]
    seeded = [task for task in single_tasks if task["source"].startswith("aob_scenario:")]
    check(
        "at least 25 source-adapted single-tool tasks",
        len(seeded) >= MIN_SOURCE_TASKS,
        str(len(seeded)),
    )
    check(
        "source anchor syntax",
        all(
            re.fullmatch(r"aob_scenario:[^#]+#\d+", task["source"])
            for task in tasks
            if task["source"] != "authored"
        ),
    )
    lengths = [len(task["query"].split()) for task in single_tasks]
    print(
        f"QUERY LENGTH whitespace words: min={min(lengths, default=0)} "
        f"max={max(lengths, default=0)}; "
        f"6–20={sum(MIN_QUERY_WORDS <= n <= MAX_QUERY_WORDS for n in lengths)}/{len(lengths)}"
    )


def _check_lexical_covariate(root: Path, check: Callable[..., None]) -> None:
    try:
        calculated, means = compute_overlap(root)
        with (root / "datasets/tasks/lexical_overlap.csv").open(newline="") as stream:
            stored = list(csv.DictReader(stream))
        expected = {(r["task_id"], r["variant"]): r["overlap"] for r in calculated}
        actual = {
            (r["task_id"], r["variant"]): (float(r["overlap"]) if r["overlap"] else None)
            for r in stored
        }
        fresh = len(actual) == len(stored) == len(expected) and set(actual) == set(expected)
        if fresh:
            fresh = all(
                (
                    actual[k] is None
                    if v is None
                    else actual[k] is not None and abs(actual[k] - v) < OVERLAP_TOLERANCE
                )
                for k, v in expected.items()
            )
        check("lexical covariate freshness and exact coverage", fresh)
        for variant, value in means.items():
            print(f"OVERLAP {variant}: {value:.6f}")
        gap = max(means[v] for v in ("V0", "P1", "P2", "P3")) - min(
            means[v] for v in ("V0", "P1", "P2", "P3")
        )
        check("benign-catalog overlap spread <=0.03", gap <= MAX_OVERLAP_GAP, f"{gap:.6f}")
    except (OSError, ValueError, KeyError) as error:
        check("lexical covariate", False, str(error))


def _check_review_provenance(
    root: Path,
    catalogs: dict[str, list[dict[str, Any]]],
    names: list[str],
    lookup: dict[str, dict[str, Any]],
    check: Callable[..., None],
) -> None:
    try:
        audit = json.loads((root / "research/03-dataset/meaning_audit.json").read_text())
        pairs = [(r["tool"], r["variant"]) for r in audit]
        check(
            "108 meaning-audit records",
            len(pairs) == EXPECTED_AUDIT_RECORDS
            and len(set(pairs)) == EXPECTED_AUDIT_RECORDS
            and set(pairs) == {(n, v) for n in names for v in ("P1", "P2", "P3")}
            and all(
                r["problem"]
                and r["fix"]
                and all(
                    r[k] == "author_checked" for k in ("agency", "constraints", "nothing_added")
                )
                for r in audit
            ),
        )
        _check_audit_hashes(audit, catalogs, lookup, check)
        check(
            "meaning audit Markdown exists",
            (root / "research/03-dataset/meaning_audit.md").is_file(),
        )
        protected = json.loads((root / "research/03-dataset/protected_files.json").read_text())
        check(
            "protected originals unchanged",
            all(
                hashlib.sha256((root / p).read_bytes()).hexdigest() == sha
                for p, sha in protected.items()
            ),
        )
    except (OSError, ValueError, KeyError) as error:
        check("review records", False, str(error))


def _variant_differences(
    catalog: list[dict[str, Any]], base: list[dict[str, Any]]
) -> tuple[list[str], list[str], list[str]]:
    lengths = []
    characters = []
    reused = []
    for tool, original in zip(catalog, base):
        ratio = len(words(tool["description"])) / len(words(original["description"]))
        if not MIN_LENGTH_RATIO <= ratio <= MAX_LENGTH_RATIO:
            lengths.append(f"{tool['name']}={ratio:.3f}")
        char_ratio = len(tool["description"]) / len(original["description"])
        if not MIN_LENGTH_RATIO <= char_ratio <= MAX_LENGTH_RATIO:
            characters.append(f"{tool['name']}={char_ratio:.3f}")
        bad = [
            g
            for g in overlaps(tool["description"], original["description"])
            if not overlap_exempt(g, original)
        ]
        if bad:
            reused.append(tool["name"] + ": " + repr(bad))
    return lengths, characters, reused


def _check_paraphrase(
    variant: str,
    catalog: list[dict[str, Any]],
    base: list[dict[str, Any]],
    reused: list[str],
    check: Callable[..., None],
) -> None:
    check(variant + " no unexempted 4-word reuse", not reused, "; ".join(reused))
    check(
        variant + " line/indent/section layout",
        all(
            structure(tool["description"]) == structure(original["description"])
            for tool, original in zip(catalog, base)
        ),
    )
    check(
        variant + " protected backticks/references",
        all(
            code_spans(tool["description"]) == code_spans(original["description"])
            for tool, original in zip(catalog, base)
        ),
    )
    check(
        variant + " parameter/result prefixes",
        all(
            prefixes(tool["description"]) == prefixes(original["description"])
            for tool, original in zip(catalog, base)
        ),
    )


def _check_audit_hashes(
    audit: list[dict[str, Any]],
    catalogs: dict[str, list[dict[str, Any]]],
    lookup: dict[str, dict[str, Any]],
    check: Callable[..., None],
) -> None:
    audit_fresh = True
    for record in audit:
        n, v = record["tool"], record["variant"]
        current = next(tool["description"] for tool in catalogs[v] if tool["name"] == n)
        audit_fresh &= (
            hashlib.sha256(current.encode()).hexdigest() == record["variant_description_sha256"]
        )
        audit_fresh &= (
            hashlib.sha256(lookup[n]["description"].encode()).hexdigest()
            == record["v0_description_sha256"]
        )
    check("meaning audit description hashes current", audit_fresh)


def _validate_required(schema: dict[str, Any]) -> None:
    if "required" in schema:
        required = schema["required"]
        if not isinstance(required, list) or any(not isinstance(x, str) for x in required):
            raise ValueError("Invalid required")
        if len(required) != len(set(required)) or not set(required) <= set(
            schema.get("properties", {})
        ):
            raise ValueError("Invalid required names")


def main() -> int | bool:
    parser = argparse.ArgumentParser(description=CLI_DESCRIPTION)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root
    fails = []

    def check(label: str, condition: Any, detail: str = "") -> None:
        print(("PASS" if condition else "FAIL") + " " + label + (" — " + detail if detail else ""))
        if not condition:
            fails.append(label)

    catalogs = _load_catalogs(root, check)
    if "V0" not in catalogs:
        return 1
    base = catalogs["V0"]
    names = [tool["name"] for tool in base]
    lookup = {tool["name"]: tool for tool in base}
    _check_catalogs(root, catalogs, base, names, check)
    _check_catalog_variants(catalogs, base, names, check)
    _check_catalog_schemas(base, check)
    rationales = _load_rationales(root, names, check)
    tasks = _load_tasks(root, check)
    _check_provenance(root, tasks, check)
    _check_task_labels(tasks, lookup, check)
    _check_task_coverage(tasks, names, check)
    _check_task_conflicts(tasks, names, rationales, check)
    _check_no_tool_tasks(tasks, check)
    _check_task_sources(tasks, check)
    _check_lexical_covariate(root, check)
    _check_review_provenance(root, catalogs, names, lookup, check)
    print(
        (
            "SEMANTIC REVIEW: Sridhar completed the 18-item manual review on "
            "2026-11-24 (research/LOG.md); independent two-way equivalence "
            "judging remains pending. Later author corrections are not human "
            "approval; structural PASS is not semantic approval."
        )
    )
    print(f"SUMMARY: {len(fails)} failed checks")
    return bool(fails)


if __name__ == "__main__":
    sys.exit(main())
