"""Read-only dataset integrity and frozen Phase 2 schema validation."""

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .validate_dataset import FILES, accepts, validate_schema

ROOT = Path(__file__).resolve().parents[2]

# Catalogs added after Phase 2 (see research/02-design/ENHANCED_PLAN.md). They are produced by
# extract_history.py, not hand-written, so the Phase 2 paraphrase rules in validate_dataset.py
# do not apply to them; tests/test_history.py checks them instead.
EXTENDED_FILES = {
    "V0R": "v0r_placebo.json",  # byte-identical copy of V0: measures run-to-run noise
    "H1": "h1_earliest.json",  # each tool's earliest developer-written description
    "H2": "h2_midpoint.json",  # each tool's middle historical description
    "H3": "h3_previous.json",  # each tool's last description before V0
}


def digest(value: Any) -> str:
    if not isinstance(value, bytes):
        value = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    return hashlib.sha256(value).hexdigest()


def load(root: Path | str = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    manifest_bytes = (root / "datasets/MANIFEST.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    required = {
        "datasets/tasks/tasks.jsonl",
        *(f"datasets/tools/{filename}" for filename in FILES.values()),
    }
    if not required <= manifest["sha256"].keys():
        raise ValueError("Manifest omits required dataset files")
    for relative, expected in manifest["sha256"].items():
        path = (root / relative).resolve()
        if (
            not path.is_relative_to(root)
            or not path.is_file()
            or digest(path.read_bytes()) != expected
        ):
            raise ValueError(f"Dataset integrity mismatch: {relative}")
    catalogs = {
        variant: json.loads((root / "datasets/tools" / filename).read_text())
        for variant, filename in FILES.items()
    }
    for variant, filename in EXTENDED_FILES.items():
        relative = f"datasets/tools/{filename}"
        if relative in manifest["sha256"]:  # only catalogs registered in the manifest are usable
            catalogs[variant] = json.loads((root / relative).read_text())
    base = [(tool["name"], tool["input_schema"]) for tool in catalogs["V0"]]
    for catalog in catalogs.values():
        if [(tool["name"], tool["input_schema"]) for tool in catalog] != base:
            raise ValueError("Catalog names, order or schemas differ")
        for tool in catalog:
            validate_schema(tool["input_schema"])
    tasks = [
        json.loads(line) for line in (root / "datasets/tasks/tasks.jsonl").read_text().splitlines()
    ]
    with (root / "datasets/tasks/lexical_overlap.csv").open() as stream:
        covariates = list(csv.DictReader(stream))
    return {
        "catalogs": catalogs,
        "tasks": tasks,
        "manifest_sha256": digest(manifest_bytes),
        "covariates": covariates,
    }


def validate_arguments(arguments: Any, schema: dict[str, Any]) -> tuple[bool, list[str]]:
    if not isinstance(arguments, dict):
        return False, []
    invalid = sorted(set(arguments) - set(schema.get("properties", {})))
    return accepts(arguments, schema) and not invalid, invalid
