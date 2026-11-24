"""Local batch files only. No submission method exists."""

import json
from pathlib import Path
from typing import Any

from .config import check_pin
from .data import digest, load
from .runner import (
    append_record,
    make_record,
    plan,
    prepare,
    read_records,
    request,
    run_lock,
    write_json,
)


def _batch_entry(
    model: dict[str, Any], trial: dict[str, Any], body: dict[str, Any], index: dict[str, Any]
) -> dict[str, Any]:
    # Provider custom IDs are kept short enough for Anthropic's 64-character limit.
    custom_id = trial["trial_id"]
    index["entries"][custom_id] = {"trial": trial, "request_sha256": digest(body)}
    if model["provider"] == "anthropic":
        return {"custom_id": custom_id, "params": body}
    elif model["provider"] == "openai":
        return {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": body,
        }
    else:
        # Local queue for sequential APIs; NOT a provider batch submission format.
        return {"custom_id": custom_id, "body": body, "local_queue_only": True}


def _batch_response(model: dict[str, Any], item: dict[str, Any]) -> dict[str, Any] | None:
    # VERIFY-ONLINE: Confirm OpenAI Batch and Anthropic Message Batches result envelopes
    # with real smoke-test outputs.
    if model["provider"] == "anthropic":
        result = item.get("result", {})
        raw = result.get("message") if result.get("type") == "succeeded" else None
    else:
        result = item.get("response") or {}
        raw = (
            result.get("body")
            if result.get("status_code") == 200 and not item.get("error")
            else None
        )
    return raw


def _validate_item(
    config: dict[str, Any],
    dataset: dict[str, Any],
    orders: list[dict[str, Any]],
    item: dict[str, Any],
    index: dict[str, Any],
    expected: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    custom_id = item["custom_id"]
    if custom_id not in index["entries"] or custom_id not in expected:
        raise ValueError("Unknown batch custom_id")
    trial = expected[custom_id]
    if index["entries"][custom_id]["trial"] != trial:
        raise ValueError("Batch plan changed")
    body = request(config, dataset, trial, orders)
    if digest(body) != index["entries"][custom_id]["request_sha256"]:
        raise ValueError("Batch request changed")
    model = config["model_settings"][trial["model"]]
    raw = _batch_response(model, item)
    return (custom_id, trial, body, model, raw)


def build(config: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    check_pin(config, dry_run)
    dataset = load(config["root"])
    trials, orders = plan(config, dataset)
    directory = (
        config["root"] / "results/batch" / (config["run_id"] + ("-dryrun" if dry_run else ""))
    )
    directory.mkdir(parents=True, exist_ok=True)
    index = {"manifest_sha256": dataset["manifest_sha256"], "dry_run": dry_run, "entries": {}}
    files = {}
    for name in config["models"]:
        model = config["model_settings"][name]
        entries = []
        for trial in (trial for trial in trials if trial["model"] == name):
            body = request(config, dataset, trial, orders)
            entries.append(_batch_entry(model, trial, body, index))
        filename = name.replace("/", "__") + (
            ".json" if model["provider"] == "anthropic" else ".jsonl"
        )
        if model["provider"] == "anthropic":
            write_json(directory / filename, {"requests": entries})
        else:
            (directory / filename).write_text(
                "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries)
            )
        files[name] = str(directory / filename)
    write_json(directory / "index.json", index)
    return {"trials": len(trials), "files": files, "submitted": False}


def merge(config: dict[str, Any], input_path: Path | str, dry_run: bool = False) -> dict[str, Any]:
    check_pin(config, dry_run)
    dataset = load(config["root"])
    trials, orders = plan(config, dataset)
    run_id = config["run_id"] + ("-dryrun" if dry_run else "")
    index = json.loads((config["root"] / "results/batch" / run_id / "index.json").read_text())
    if index["manifest_sha256"] != dataset["manifest_sha256"] or index["dry_run"] != dry_run:
        raise ValueError("Batch dataset or mode changed")
    expected = {trial["trial_id"]: trial for trial in trials}
    directory = config["root"] / "results/raw" / run_id
    merged = failed = skipped = 0
    with run_lock(directory):
        prepare(config, dataset, orders, directory, dry_run)
        done = {record["trial_id"]: record for record in read_records(directory)}
        for line in Path(input_path).read_text().splitlines():
            item = json.loads(line)
            custom_id, trial, body, model, raw = _validate_item(
                config, dataset, orders, item, index, expected
            )
            if raw is None:
                failed += 1
                continue  # Failed/cancelled/expired trials remain unfinished and resumable.
            if custom_id in done:
                from .transport import sanitize

                if done[custom_id]["raw_response"] != sanitize(raw):
                    raise ValueError("Conflicting duplicate batch response")
                skipped += 1
                continue
            record = make_record(
                config,
                dataset,
                trial,
                body,
                raw,
                None,
                dry_run,
                batch=model["provider"] in ("openai", "anthropic"),
            )
            write_json(directory / "requests" / (digest(body) + ".json"), body)
            append_record(directory, record)
            done[custom_id] = record
            merged += 1
    return {"merged": merged, "failed_unfinished": failed, "skipped": skipped}
