"""Plan, resume, and record selection-only experiment trials."""

import json
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import adapters
from .config import check_pin
from .data import digest, load, validate_arguments
from .parse import parse, usage
from .permute import permutations
from .prompt import PROMPT_SHA256
from .transport import FakeTransport, RealTransport, sanitize

MILLISECONDS_PER_SECOND = 1000


def write_json(path: Path | str, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def plan(
    config: dict[str, Any], dataset: dict[str, Any] | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dataset = dataset or load(config["root"])
    all_tasks = {item["id"]: item for item in dataset["tasks"]}
    ids = config.get("task_ids", list(all_tasks))
    if len(ids) != len(set(ids)) or not set(ids) <= all_tasks.keys():
        raise ValueError("Invalid or duplicate task IDs")
    if (
        config["k"] < 1
        or len(config["models"]) != len(set(config["models"]))
        or len(config["variants"]) != len(set(config["variants"]))
    ):
        raise ValueError("Invalid trial dimensions")
    orders = permutations(
        config["k"], config["seed"], [item["name"] for item in dataset["catalogs"]["V0"]]
    )
    trials = []
    for model in config["models"]:
        for variant in config["variants"]:
            if variant not in dataset["catalogs"]:
                raise ValueError("Unknown variant")
            for task_id in ids:
                for order in orders:
                    trial = {
                        "model": model,
                        "variant": variant,
                        "task_id": task_id,
                        "repeat": order["repeat"],
                        "permutation_id": order["permutation_id"],
                    }
                    trial["trial_id"] = digest([model, variant, task_id, order["repeat"]])
                    trials.append(trial)
    return trials, orders


def request(
    config: dict[str, Any],
    dataset: dict[str, Any],
    trial: dict[str, Any],
    orders: list[dict[str, Any]],
) -> dict[str, Any]:
    lookup = {item["name"]: item for item in dataset["catalogs"][trial["variant"]]}
    catalog = [lookup[name] for name in orders[trial["repeat"]]["tool_order"]]
    task = next(item for item in dataset["tasks"] if item["id"] == trial["task_id"])
    model = config["model_settings"][trial["model"]]
    body = adapters.build(model, catalog, task["query"])
    if model["provider"] == "openrouter":
        # Sticky routing: every request sharing this tool prefix goes to the same host, so the
        # prompt cache stays warm (OpenRouter sessions expire after 60 idle minutes).
        body["session_id"] = digest([trial["model"], trial["variant"], trial["permutation_id"]])[
            :32
        ]
    return body


def cache_friendly_order(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run trials that share a prompt prefix (model, catalog, tool order) back to back.

    Ordering changes cost only: trial identity, requests and records are unaffected.
    """
    return sorted(
        trials, key=lambda t: (t["model"], t["variant"], t["repeat"], t["task_id"])
    )


def select_stage(
    trials: list[dict[str, Any]],
    tasks: list[str] | None = None,
    repeats: list[int] | None = None,
    models: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Restrict one invocation to a slice of the planned run (pilot, first repeat, ...).

    The run's fingerprint is the full plan, so every slice adds to the same final dataset.
    """
    selected = [
        trial
        for trial in trials
        if (tasks is None or trial["task_id"] in tasks)
        and (repeats is None or trial["repeat"] in repeats)
        and (models is None or trial["model"] in models)
    ]
    if not selected:
        raise ValueError("Stage selection matches no planned trials")
    return selected


def make_record(
    config: dict[str, Any],
    dataset: dict[str, Any],
    trial: dict[str, Any],
    body: dict[str, Any],
    raw: dict[str, Any],
    latency_ms: float | None,
    dry_run: bool = False,
    batch: bool = False,
) -> dict[str, Any]:
    model = config["model_settings"][trial["model"]]
    raw = sanitize(raw)
    parsed = parse(raw, model["provider"])
    task = next(item for item in dataset["tasks"] if item["id"] == trial["task_id"])
    lookup = {item["name"]: item for item in dataset["catalogs"]["V0"]}
    selected = lookup.get(parsed["tool_name"])
    valid, invalid = (
        validate_arguments(parsed["arguments"], selected["input_schema"])
        if selected
        else (False, [])
    )
    served = _provider_served(model, raw, dry_run)
    call_names = _called_tools(raw, model)
    unsafe_write = task["gold_access"] in ("read", "none") and any(
        lookup.get(name, {}).get("access") == "write" for name in call_names
    )
    return {
        **_request_metadata(config, dataset, trial, body, served, latency_ms, dry_run),
        **parsed,
        "gold": task["gold"],
        "correct": parsed["tool_name"] == task["gold"],
        "args_valid": valid if parsed["action"] == "tool" else None,
        "invalid_arg_keys": invalid,
        "usage": usage(raw, model["provider"]),
        "stop_reason": parsed["raw_stop_reason"],
        "model_version_returned": raw.get("model"),
        "raw_response": raw,
        "dry_run": dry_run,
        "batch": batch,
        "settings": model,
        **_task_outcome(task, selected, unsafe_write, call_names, dataset, trial),
    }


@contextmanager
def run_lock(directory: Path) -> Iterator[None]:
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".writer.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError(
            "Another writer or stale .writer.lock exists; inspect before removing"
        ) from None
    try:
        os.close(descriptor)
        yield
    finally:
        lock.unlink()


def read_records(directory: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(Path(directory).glob("*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                records.append(json.loads(line))
    ids = [record["trial_id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate trial IDs in results")
    return records


def prepare(
    config: dict[str, Any],
    dataset: dict[str, Any],
    orders: list[dict[str, Any]],
    directory: Path,
    dry_run: bool,
) -> None:
    fingerprint = {
        "config": {k: v for k, v in config.items() if k != "root"},
        "dataset_manifest_sha256": dataset["manifest_sha256"],
        "prompt_sha256": PROMPT_SHA256,
        "permutations": orders,
        "dry_run": dry_run,
    }
    path = directory / "run.json"
    if path.exists() and json.loads(path.read_text()) != fingerprint:
        raise ValueError("Run configuration changed; use a new run_id")
    write_json(path, fingerprint)
    write_json(config["root"] / "results/permutations.json", orders)
    write_json(directory / "permutations.json", orders)


def append_record(directory: Path, record: dict[str, Any]) -> None:
    filename = record["model"].replace("/", "__") + ".jsonl"
    with (directory / filename).open("a") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _called_tools(raw: dict[str, Any], model: dict[str, Any]) -> list[str | None]:
    if model["provider"] == "anthropic":
        call_names = [
            call.get("name") for call in raw.get("content") or [] if call.get("type") == "tool_use"
        ]
    else:
        choice = (raw.get("choices") or [{}])[0]
        # Providers may send an explicit `"tool_calls": null` on text-only replies.
        call_names = [
            (call.get("function") or {}).get("name")
            for call in (choice.get("message") or {}).get("tool_calls") or []
        ]
    return call_names


def _record_estimate(
    config: dict[str, Any],
    trial: dict[str, Any],
    body: dict[str, Any],
    estimates: list[dict[str, Any]],
    examples: set[str],
) -> None:
    estimates.append(
        {
            "model": trial["model"],
            "input": len(json.dumps(body, ensure_ascii=False)) / 4,
            "output": config.get("estimated_output_tokens", 300),
        }
    )
    if trial["model"] not in examples:
        write_json(
            config["root"] / "results/dryrun" / (trial["model"].replace("/", "__") + ".json"),
            body,
        )
        examples.add(trial["model"])


def _execute_trial(
    config: dict[str, Any],
    dataset: dict[str, Any],
    trial: dict[str, Any],
    body: dict[str, Any],
    directory: Path,
    dry_run: bool,
    transport: FakeTransport | RealTransport,
) -> None:
    if not dry_run:
        write_json(directory / "requests" / (digest(body) + ".json"), body)
    start = time.monotonic()
    raw = transport.send(config["model_settings"][trial["model"]], body)
    record = make_record(
        config,
        dataset,
        trial,
        body,
        raw,
        (time.monotonic() - start) * MILLISECONDS_PER_SECOND,
        dry_run,
    )
    append_record(directory, record)


def _run_trials(
    config: dict[str, Any],
    dataset: dict[str, Any],
    trials: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    directory: Path,
    dry_run: bool,
    transport: FakeTransport | RealTransport,
    existing: dict[str, dict[str, Any]],
) -> tuple[int, list[dict[str, Any]]]:
    estimates = []
    examples = set()
    added = 0
    for trial in trials:
        body = request(config, dataset, trial, orders)
        if dry_run:
            _record_estimate(config, trial, body, estimates, examples)
        previous = existing.get(trial["trial_id"])
        if previous:
            if previous["request_sha256"] != digest(body):
                raise ValueError("Request changed on resume; use a new run_id")
            continue
        if not dry_run and config["model_settings"][trial["model"]]["provider"] in config.get(
            "batch_providers", []
        ):
            continue  # Completed through batch-build / external submission / batch-merge.
        _execute_trial(config, dataset, trial, body, directory, dry_run, transport)
        added += 1
    return (added, estimates)


def run(
    config: dict[str, Any],
    dry_run: bool = False,
    transport: FakeTransport | RealTransport | None = None,
    stage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    check_pin(config, dry_run)
    dataset = load(config["root"])
    planned, orders = plan(config, dataset)
    trials = cache_friendly_order(select_stage(planned, **(stage or {})))
    directory = config["root"] / "results/raw" / (config["run_id"] + ("-dryrun" if dry_run else ""))
    transport = transport or (FakeTransport() if dry_run else RealTransport())
    with run_lock(directory):
        prepare(config, dataset, orders, directory, dry_run)
        existing = {record["trial_id"]: record for record in read_records(directory)}
        if not existing.keys() <= {item["trial_id"] for item in planned}:
            raise ValueError("Unplanned records in run")
        added, estimates = _run_trials(
            config, dataset, trials, orders, directory, dry_run, transport, existing
        )
        result = {
            "run_id": directory.name,
            "planned_trials": len(planned),
            "stage_trials": len(trials),
            "new_trials": added,
            "completed_trials": len(existing) + added,
            "pending_trials": len(planned) - len(existing) - added,
            "dry_run": dry_run,
        }
        if dry_run:
            from .cost import estimate

            result["cost_projection"] = estimate(
                config, estimates, len({item["task_id"] for item in trials})
            )
            write_json(config["root"] / "results/dryrun/summary.json", result)
        return result


def _task_outcome(
    task: dict[str, Any],
    selected: dict[str, Any] | None,
    unsafe_write: bool,
    call_names: list[str | None],
    dataset: dict[str, Any],
    trial: dict[str, Any],
) -> dict[str, Any]:
    return {
        "task_type": task["type"],
        "subtype": task.get("subtype"),
        "ms_conflict": task.get("ms_conflict"),
        "source_family": task.get("source"),
        "gold_access": task["gold_access"],
        "selected_access": selected["access"] if selected else None,
        "unsafe_write": unsafe_write,
        "called_tool_names": call_names,
        "lexical_overlap": next(
            (
                record["overlap"]
                for record in dataset["covariates"]
                if record["task_id"] == task["id"] and record["variant"] == trial["variant"]
            ),
            None,
        ),
    }


def _provider_served(model: dict[str, Any], raw: dict[str, Any], dry_run: bool) -> str | None:
    served = raw.get("provider") if model["provider"] == "openrouter" else model["provider"]
    if model["provider"] == "openrouter" and not dry_run and not served:
        raise ValueError(
            "OpenRouter response lacks provider attribution; verify adapter before continuing"
        )
    return served


def _request_metadata(
    config: dict[str, Any],
    dataset: dict[str, Any],
    trial: dict[str, Any],
    body: dict[str, Any],
    served: str | None,
    latency_ms: float | None,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        **trial,
        "run_id": config["run_id"] + ("-dryrun" if dry_run else ""),
        "provider_served": served,
        "dataset_manifest_sha256": dataset["manifest_sha256"],
        "prompt_sha256": PROMPT_SHA256,
        "request_sha256": digest(body),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "latency_ms": latency_ms,
    }
