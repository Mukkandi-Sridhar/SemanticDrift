"""Reject controlled dataset corruptions without modifying the study artifacts."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
Rows = list[dict[str, Any]]
MIN_TEMPTING_TASKS = 12  # mirrors src/semdrift/validate_dataset.py


def copy_dataset(root: Path) -> None:
    shutil.copytree(ROOT / "datasets", root / "datasets")
    (root / "research").mkdir()
    shutil.copytree(ROOT / "research/03-dataset", root / "research/03-dataset")
    (root / "src/semdrift").mkdir(parents=True)
    shutil.copyfile(ROOT / "src/semdrift/extract_tools.py", root / "src/semdrift/extract_tools.py")
    (root / "vendor").mkdir()
    (root / "vendor/AssetOpsBench").symlink_to(
        ROOT / "vendor/AssetOpsBench", target_is_directory=True
    )


def run_validator(root: Path, isolated: bool = False) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if isolated:
        command.append("-I")
    command.extend([str(ROOT / "src/semdrift/validate_dataset.py"), "--root", str(root)])
    return subprocess.run(command, capture_output=True, text=True)


def reverse_tools(rows: Rows) -> None:
    rows.reverse()


def add_schema_property(rows: Rows) -> None:
    rows[0]["input_schema"]["properties"].update(invented={"type": "string"})


def empty_description(rows: Rows) -> None:
    rows[0]["description"] = ""


def copy_original_description(rows: Rows) -> None:
    original = json.loads((ROOT / "datasets/tools/v0_original.json").read_text())
    rows[0]["description"] = original[0]["description"]


def duplicate_task_id(rows: Rows) -> None:
    rows[1]["id"] = rows[0]["id"]


def unknown_gold(rows: Rows) -> None:
    rows[0]["gold"] = "fabricated_tool"


def leak_tool_name(rows: Rows) -> None:
    rows[0]["query"] = "Please call " + rows[0]["gold"]


def wrong_access(rows: Rows) -> None:
    rows[0]["gold_access"] = "write"


def remove_rationale(rows: Rows) -> None:
    rows.pop()


def shorten_description(rows: Rows) -> None:
    rows[0]["description"] = "Sites."


def lengthen_description(rows: Rows) -> None:
    rows[0]["description"] = " ".join(["sites"] * 100)


def replace_section_header(rows: Rows) -> None:
    rows[1]["description"] = rows[1]["description"].replace("Args:", "Parameters:")


def change_argument_wording(rows: Rows) -> None:
    rows[1]["description"] = rows[1]["description"].replace("Exact site id", "Approximate site id")


def remove_conflict_flag(rows: Rows) -> None:
    rows[0].pop("ms_conflict")


def remove_site_conflicts(rows: Rows) -> None:
    for row in rows:
        if row["gold"] == "sites":
            row["ms_conflict"] = False


def remove_source_adaptations(rows: Rows) -> None:
    for row in rows:
        if row["type"] == "single_tool":
            row["source"] = "authored"


def reduce_tempting_count(rows: Rows) -> None:
    # Relabel all but MIN_TEMPTING_TASKS - 1 tempting tasks so the count falls below the minimum.
    tempting = [row for row in rows if row.get("subtype") == "tempting"]
    for task in tempting[MIN_TEMPTING_TASKS - 1 :]:
        task["subtype"] = "easy"


def add_steering_hint(rows: Rows) -> None:
    task = next(row for row in rows if row.get("subtype") == "tempting")
    task["query"] = "Do not save this; give general guidance."


def stale_audit_hash(rows: Rows) -> None:
    rows[0]["variant_description_sha256"] = "0" * 64


class DatasetChecks(unittest.TestCase):
    def _assert_mutation_rejected(
        self,
        root: Path,
        path: Path,
        modify: Callable[[Rows], None],
        expected: str = "",
        jsonl: bool = False,
    ) -> None:
        saved = path.read_text()
        rows = [json.loads(line) for line in saved.splitlines()] if jsonl else json.loads(saved)
        modify(rows)
        changed = "".join(json.dumps(row) + "\n" for row in rows) if jsonl else json.dumps(rows)
        try:
            path.write_text(changed)
            result = run_validator(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "FAIL" + (" " + expected if expected else ""), result.stdout, result.stdout
            )
        finally:
            path.write_text(saved)

    def _check_catalog_mutations(self, root: Path) -> None:
        path = root / "datasets/tools/p1_paraphrase.json"
        for label, modify in [
            ("reordered tools", reverse_tools),
            ("changed schema", add_schema_property),
            ("empty description", empty_description),
            ("copied original wording", copy_original_description),
        ]:
            with self.subTest(label=label):
                self._assert_mutation_rejected(root, path, modify)

    def _check_task_mutations(self, root: Path) -> None:
        path = root / "datasets/tasks/tasks.jsonl"
        for label, modify in [
            ("duplicate ID", duplicate_task_id),
            ("unknown gold", unknown_gold),
            ("query leakage", leak_tool_name),
            ("wrong access", wrong_access),
        ]:
            with self.subTest(label=label):
                self._assert_mutation_rejected(root, path, modify, jsonl=True)

    def _check_variant_review_mutations(self, root: Path) -> None:
        # Review-specific regressions must fail their own check, not just
        # a collateral fingerprint or lexical-freshness check.
        for filename, modify, expected in [
            ("mg_overgeneral.json", shorten_description, "MG word length"),
            ("ms_overspecial.json", lengthen_description, "MS word length"),
            ("p1_paraphrase.json", replace_section_header, "P1 required section headers"),
            ("mg_overgeneral.json", change_argument_wording, "MG verbatim Args/Returns"),
        ]:
            self._assert_mutation_rejected(
                root, root / "datasets/tools" / filename, modify, expected
            )

    def _check_task_review_mutations(self, root: Path) -> None:
        path = root / "datasets/tasks/tasks.jsonl"
        for modify, expected in [
            (remove_conflict_flag, "single-tool ms_conflict booleans"),
            (remove_site_conflicts, "MS conflict for every tool"),
            (remove_source_adaptations, "at least 25 source-adapted single-tool tasks"),
            (reduce_tempting_count, "tempting no-tool count"),
            (add_steering_hint, "tempting queries omit steering hints"),
        ]:
            self._assert_mutation_rejected(root, path, modify, expected, jsonl=True)

    def _check_stale_covariate(self, root: Path) -> None:
        path = root / "datasets/tasks/lexical_overlap.csv"
        saved = path.read_text()
        try:
            path.write_text("task_id,variant,overlap\nT001,V0,1.0\n")
            result = run_validator(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FAIL lexical covariate freshness and exact coverage", result.stdout)
        finally:
            path.write_text(saved)

    def test_valid_and_corrupted_copies(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semdrift-validation-") as temporary:
            root = Path(temporary)
            copy_dataset(root)

            self.assertEqual(run_validator(root).returncode, 0)
            isolated = run_validator(root, isolated=True)
            self.assertEqual(isolated.returncode, 0, isolated.stdout + isolated.stderr)
            self.assertEqual(run_validator(root).stdout, isolated.stdout)
            self._check_catalog_mutations(root)
            self._check_task_mutations(root)
            self._assert_mutation_rejected(
                root, root / "datasets/tools/variants_rationale.json", remove_rationale
            )
            self._check_variant_review_mutations(root)
            self._check_task_review_mutations(root)
            self._assert_mutation_rejected(
                root,
                root / "research/03-dataset/meaning_audit.json",
                stale_audit_hash,
                "meaning audit description hashes current",
            )
            self._check_stale_covariate(root)
            self.assertEqual(run_validator(root).returncode, 0)


if __name__ == "__main__":
    unittest.main()
