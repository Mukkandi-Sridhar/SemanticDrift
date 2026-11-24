"""Recover earlier, developer-written versions of the AssetOpsBench tool descriptions.

For every commit that touched a tool server, the server source is parsed statically (nothing
upstream is imported or executed). A historical description is *eligible* only when the tool's
reconstructed input schema at that commit is identical to the pinned (V0) schema, so the only
thing that differs from V0 is the description text.

Run: python3 src/semdrift/extract_history.py --source vendor/AssetOpsBench
"""

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

from extract_tools import PIN, SERVERS, literal, schema

ROOT = Path(__file__).resolve().parents[2]
V0_PATH = ROOT / "datasets/tools/v0_original.json"
HISTORY_PATH = ROOT / "datasets/history/versions.json"
CATALOG_DIR = ROOT / "datasets/tools"


def git(source: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(source), *args], check=True, capture_output=True, text=True
    ).stdout


def module_constants(tree: ast.Module) -> dict:
    constants = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                try:
                    constants[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    pass
    return constants


def tool_definitions(source_text: str, wanted: set[str]) -> dict[str, tuple[str, dict]]:
    """Return {tool name: (description, input schema)} for wanted tools found in one file.

    Decorator `name=`/`description=` overrides are honoured, as in the pinned extractor.
    Functions registered centrally (the work-order server) carry no decorator, so a
    top-level function whose name matches a pinned tool is accepted as well.
    """
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return {}
    constants = module_constants(tree)
    found = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        options = {}
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and ast.unparse(decorator.func) == "mcp.tool":
                options = {
                    keyword.arg: literal(keyword.value, constants)
                    for keyword in decorator.keywords
                    if keyword.arg in ("name", "description")
                }
        name = options.get("name", node.name)
        if name not in wanted:
            continue
        description = options.get("description", ast.get_docstring(node, clean=True))
        if not description:
            continue
        try:
            input_schema = schema(node, constants)
        except (KeyError, ValueError, TypeError):
            continue
        found[name] = (description, input_schema)
    return found


def collect_versions(source: Path, v0: list[dict]) -> dict[str, list[dict]]:
    """Walk each server file's history oldest-first and record every distinct description."""
    pinned = {tool["name"]: tool for tool in v0}
    by_server: dict[str, set[str]] = {}
    for tool in v0:
        by_server.setdefault(tool["server"], set()).add(tool["name"])

    versions: dict[str, list[dict]] = {name: [] for name in pinned}
    for server in SERVERS:
        path = f"src/servers/{server}/main.py"
        log = git(source, "log", "--reverse", "--format=%H %cI", PIN, "--", path)
        for line in log.splitlines():
            commit, committed_at = line.split()
            try:
                text = git(source, "show", f"{commit}:{path}")
            except subprocess.CalledProcessError:
                continue  # the commit deleted or moved the file

            for name, (description, input_schema) in tool_definitions(
                text, by_server[server]
            ).items():
                seen = {entry["description"] for entry in versions[name]}
                if description in seen:
                    continue
                versions[name].append(
                    {
                        "commit": commit,
                        "committed_at": committed_at,
                        "description": description,
                        "description_sha256": hashlib.sha256(description.encode()).hexdigest(),
                        "schema_matches_v0": input_schema == pinned[name]["input_schema"],
                        "is_v0": description == pinned[name]["description"],
                    }
                )
    return versions


def eligible(entries: list[dict]) -> list[dict]:
    """Earlier descriptions whose schema equals V0 and whose text differs from V0."""
    return [entry for entry in entries if entry["schema_matches_v0"] and not entry["is_v0"]]


def build_catalog(v0: list[dict], choose) -> tuple[list[dict], list[str]]:
    catalog, changed = [], []
    for tool in v0:
        replacement = choose(tool["name"])
        entry = dict(tool)
        if replacement is not None:
            entry["description"] = replacement["description"]
            changed.append(tool["name"])
        catalog.append(entry)
    return catalog, changed


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=ROOT / "vendor/AssetOpsBench")
    args = parser.parse_args()

    head = git(args.source, "rev-parse", "HEAD").strip()
    if head != PIN:
        raise SystemExit(f"Checkout is at {head}, expected pinned commit {PIN}")

    v0 = json.loads(V0_PATH.read_text())
    versions = collect_versions(args.source, v0)
    candidates = {name: eligible(entries) for name, entries in versions.items()}

    def earliest(name):
        return candidates[name][0] if candidates[name] else None

    def previous(name):
        return candidates[name][-1] if candidates[name] else None

    def midpoint(name):
        options = candidates[name]
        return options[(len(options) - 1) // 2] if options else None

    selections = {
        "h1_earliest.json": earliest,
        "h2_midpoint.json": midpoint,
        "h3_previous.json": previous,
    }
    summary = {"pinned_commit": PIN, "catalogs": {}}
    for filename, choose in selections.items():
        catalog, changed = build_catalog(v0, choose)
        write_json(CATALOG_DIR / filename, catalog)
        summary["catalogs"][filename] = {"changed_tools": changed, "n_changed": len(changed)}

    write_json(CATALOG_DIR / "v0r_placebo.json", v0)
    write_json(HISTORY_PATH, {"pinned_commit": PIN, "summary": summary, "versions": versions})

    n_versions = sum(len(entries) for entries in candidates.values())
    tools_with = sum(1 for entries in candidates.values() if entries)
    print(f"eligible earlier descriptions: {n_versions} across {tools_with} tools")
    for filename, info in summary["catalogs"].items():
        print(f"{filename}: {info['n_changed']} tools differ from V0")


if __name__ == "__main__":
    main()
