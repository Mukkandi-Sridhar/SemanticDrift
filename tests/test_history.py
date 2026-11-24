"""Checks for the placebo (V0R) and historical (H1-H3) catalogs."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "datasets/tools"
HISTORY = json.loads((ROOT / "datasets/history/versions.json").read_text())
V0 = json.loads((TOOLS / "v0_original.json").read_text())
HISTORICAL_CATALOGS = ("h1_earliest.json", "h2_midpoint.json", "h3_previous.json")


def eligible_descriptions(tool_name: str) -> set[str]:
    return {
        entry["description"]
        for entry in HISTORY["versions"][tool_name]
        if entry["schema_matches_v0"] and not entry["is_v0"]
    }


class PlaceboCatalogTest(unittest.TestCase):
    def test_placebo_is_identical_to_v0(self):
        placebo = json.loads((TOOLS / "v0r_placebo.json").read_text())
        self.assertEqual(placebo, V0)


class HistoricalCatalogTest(unittest.TestCase):
    def test_names_order_access_and_schemas_match_v0(self):
        for filename in HISTORICAL_CATALOGS:
            catalog = json.loads((TOOLS / filename).read_text())
            with self.subTest(catalog=filename):
                self.assertEqual(
                    [(t["name"], t["server"], t["access"], t["input_schema"]) for t in catalog],
                    [(t["name"], t["server"], t["access"], t["input_schema"]) for t in V0],
                )

    def test_every_changed_description_is_a_real_historical_version(self):
        for filename in HISTORICAL_CATALOGS:
            catalog = json.loads((TOOLS / filename).read_text())
            for tool, original in zip(catalog, V0):
                if tool["description"] == original["description"]:
                    continue
                with self.subTest(catalog=filename, tool=tool["name"]):
                    self.assertIn(tool["description"], eligible_descriptions(tool["name"]))

    def test_catalogs_change_the_same_tools(self):
        changed = {
            filename: {
                tool["name"]
                for tool, original in zip(json.loads((TOOLS / filename).read_text()), V0)
                if tool["description"] != original["description"]
            }
            for filename in HISTORICAL_CATALOGS
        }
        tools_with_history = {name for name in HISTORY["versions"] if eligible_descriptions(name)}
        for filename, names in changed.items():
            with self.subTest(catalog=filename):
                self.assertEqual(names, tools_with_history)


if __name__ == "__main__":
    unittest.main()
