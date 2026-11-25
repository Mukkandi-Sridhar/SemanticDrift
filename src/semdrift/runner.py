"""Plan, resume, and record selection-only experiment trials."""

import gzip
import json
import os
import subprocess
import sys
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
        # A model may run fewer repeats than the study default (e.g. for budget: PREREG §8).
        model_k = config["model_settings"].get(model, {}).get("k", config["k"])
        for variant in config["variants"]:
            if variant not in dataset["catalogs"]:
                raise ValueError("Unknown variant")
            for task_id in ids:
                for order in orders[:model_k]:
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


# Run-level logs that live next to the per-model trial files but are not trial records.
BOOKKEEPING_FILES = {"ledger.jsonl", "errors.jsonl"}


def read_records(directory: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(Path(directory).glob("*.jsonl")):
        if path.name in BOOKKEEPING_FILES:
            continue
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
    amend: str | None = None,
) -> None:
    """Freeze the run's configuration; a later change needs an explicit, logged amendment.

    Amendments are for settings that cannot change what the model is asked (for example where
    the prompt-cache breakpoint sits). Every amendment keeps the previous fingerprint.
    """
    fingerprint = {
        "config": {k: v for k, v in config.items() if k != "root"},
        "dataset_manifest_sha256": dataset["manifest_sha256"],
        "prompt_sha256": PROMPT_SHA256,
        "permutations": orders,
        "dry_run": dry_run,
    }
    path = directory / "run.json"
    amendments = []
    if path.exists():
        stored = json.loads(path.read_text())
        amendments = stored.pop("amendments", [])
        if stored != fingerprint:
            if not amend:
                raise ValueError("Run configuration changed; use a new run_id or --amend")
            if stored["permutations"] != orders or stored["prompt_sha256"] != PROMPT_SHA256:
                raise ValueError("Tool orders or prompt changed; an amendment cannot cover this")
            amendments.append(
                {
                    "utc": datetime.now(timezone.utc).isoformat(),
                    "reason": amend,
                    "previous_fingerprint": stored,
                }
            )
    write_json(path, {**fingerprint, "amendments": amendments} if amendments else fingerprint)
    write_json(config["root"] / "results/permutations.json", orders)
    write_json(directory / "permutations.json", orders)


def append_record(directory: Path, record: dict[str, Any]) -> None:
    filename = record["model"].replace("/", "__") + ".jsonl"
    with (directory / filename).open("a") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _called_tools(raw: dict[str, Any], model: dict[str, Any]) -> list[str | None]:
    if model["provider"] == "openai":
        call_names = [
            item.get("name")
            for item in raw.get("output") or []
            if item.get("type") == "function_call"
        ]
    elif model["provider"] == "anthropic":
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


MAX_CONSECUTIVE_FAILURES = 3


def _save_request(directory: Path, body: dict[str, Any]) -> None:
    """Keep every request body (compressed: each repeats the ~24 KB tool catalog)."""
    path = directory / "requests" / (digest(body) + ".json.gz")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(json.dumps(body, ensure_ascii=False).encode(), mtime=0))


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _trial_cost(record: dict[str, Any], model: dict[str, Any]) -> float:
    from .cost import charge

    try:
        return charge(record["usage"], model["prices"])
    except ValueError:
        return 0.0  # unpriced token category; the provider-reported cost is logged separately


def _execute_trial(
    config: dict[str, Any],
    dataset: dict[str, Any],
    trial: dict[str, Any],
    body: dict[str, Any],
    directory: Path,
    dry_run: bool,
    transport: FakeTransport | RealTransport,
) -> dict[str, Any]:
    if not dry_run:
        _save_request(directory, body)
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
    return record


class _Progress:
    """Spend, errors and per-model failure streaks for one invocation (thread-safe)."""

    def __init__(self, max_spend: float | None) -> None:
        import threading

        self.max_spend = max_spend
        self.spend: dict[str, float] = {}
        self.errors: dict[str, int] = {}
        self.streaks: dict[str, int] = {}
        self.disabled: set[str] = set()
        self.stopped_for_budget = False
        self.completed = 0
        self.lock = threading.Lock()

    @property
    def total(self) -> float:
        with self.lock:
            return sum(self.spend.values())

    def over_budget(self) -> bool:
        return self.max_spend is not None and self.total >= self.max_spend

    def mark_budget_stop(self) -> None:
        with self.lock:
            self.stopped_for_budget = True

    def succeeded(self, model: str, cost: float) -> None:
        with self.lock:
            self.spend[model] = self.spend.get(model, 0.0) + cost
            self.streaks[model] = 0
            self.completed += 1
            report = self.completed % PROGRESS_EVERY == 0
            total, errors = sum(self.spend.values()), sum(self.errors.values())
        if report:
            print(
                f"[{self.completed} new trials] spend ${total:.4f}; errors {errors}",
                file=sys.stderr,
                flush=True,
            )

    def log_error(self, directory: Path, trial: dict[str, Any], exc: Exception) -> None:
        with self.lock:
            _append_jsonl(
                directory / "errors.jsonl",
                {
                    "trial_id": trial["trial_id"],
                    "model": trial["model"],
                    "variant": trial["variant"],
                    "task_id": trial["task_id"],
                    "repeat": trial["repeat"],
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                },
            )
            model = trial["model"]
            self.errors[model] = self.errors.get(model, 0) + 1
            self.streaks[model] = self.streaks.get(model, 0) + 1
            if self.streaks[model] >= MAX_CONSECUTIVE_FAILURES:
                self.disabled.add(model)


def _run_trials(
    config: dict[str, Any],
    dataset: dict[str, Any],
    trials: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    directory: Path,
    dry_run: bool,
    transport: FakeTransport | RealTransport,
    existing: dict[str, dict[str, Any]],
    progress: _Progress,
) -> tuple[int, list[dict[str, Any]]]:
    """Run each model's trials in its own thread, in cache-friendly order within the model.

    Models are independent (separate providers and caches), so running them side by side cuts
    wall-clock time roughly by the number of models. Dry runs stay sequential (deterministic).
    """
    estimates: list[dict[str, Any]] = []
    examples: set = set()
    pending_by_model: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for trial in trials:
        body = request(config, dataset, trial, orders)
        if dry_run:
            _record_estimate(config, trial, body, estimates, examples)
        previous = existing.get(trial["trial_id"])
        if previous:
            if previous["request_sha256"] != digest(body) and not config.get("_amended"):
                raise ValueError("Request changed on resume; use a new run_id or --amend")
            continue
        model = config["model_settings"][trial["model"]]
        if not dry_run and model["provider"] in config.get("batch_providers", []):
            continue  # Completed through batch-build / external submission / batch-merge.
        pending_by_model.setdefault(trial["model"], []).append((trial, body))

    # One stream per prompt prefix (model, repeat, catalog): each has its own tool order and
    # descriptions, so its cache is independent; within a stream, tasks run back to back so the
    # cache stays warm. Per-model concurrency/rpm limits still apply in the transport.
    streams: dict[tuple[str, int, str], list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for model_key, items in pending_by_model.items():
        for trial, body in items:
            key = (model_key, trial["repeat"], trial["variant"])
            streams.setdefault(key, []).append((trial, body))

    def work(stream_key: tuple[str, int, str]) -> int:
        model_key = stream_key[0]
        model = config["model_settings"][model_key]
        done = 0
        for trial, body in streams[stream_key]:
            if model_key in progress.disabled:
                break  # remaining trials stay pending; rerun after fixing the cause
            if progress.over_budget():
                progress.mark_budget_stop()
                break
            try:
                record = _execute_trial(
                    config, dataset, trial, body, directory, dry_run, transport
                )
            except (RuntimeError, ValueError) as exc:
                # Never lose a failure: log it (messages are redacted) and keep going.
                progress.log_error(directory, trial, exc)
                continue
            progress.succeeded(model_key, _trial_cost(record, model))
            done += 1
        return done

    if dry_run or len(streams) <= 1:
        added = sum(work(stream_key) for stream_key in streams)
    else:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=len(streams)) as pool:
            added = sum(pool.map(work, list(streams)))
    return (added, estimates)


PROGRESS_EVERY = 100


def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run(
    config: dict[str, Any],
    dry_run: bool = False,
    transport: FakeTransport | RealTransport | None = None,
    stage: dict[str, Any] | None = None,
    max_spend: float | None = None,
    amend: str | None = None,
) -> dict[str, Any]:
    check_pin(config, dry_run)
    dataset = load(config["root"])
    planned, orders = plan(config, dataset)
    trials = cache_friendly_order(select_stage(planned, **(stage or {})))
    directory = config["root"] / "results/raw" / (config["run_id"] + ("-dryrun" if dry_run else ""))
    transport = transport or (FakeTransport() if dry_run else RealTransport())
    started = datetime.now(timezone.utc).isoformat()
    progress = _Progress(max_spend)
    with run_lock(directory):
        prepare(config, dataset, orders, directory, dry_run, amend)
        config = {**config, "_amended": bool(amend)}
        existing = {record["trial_id"]: record for record in read_records(directory)}
        if not existing.keys() <= {item["trial_id"] for item in planned}:
            raise ValueError("Unplanned records in run")
        added, estimates = _run_trials(
            config, dataset, trials, orders, directory, dry_run, transport, existing, progress
        )
        result = {
            "run_id": directory.name,
            "planned_trials": len(planned),
            "stage_trials": len(trials),
            "new_trials": added,
            "completed_trials": len(existing) + added,
            "pending_trials": len(planned) - len(existing) - added,
            "dry_run": dry_run,
            "stage_spend_usd": round(progress.total, 6),
            "stage_spend_by_model": {k: round(v, 6) for k, v in progress.spend.items()},
            "errors_by_model": progress.errors,
            "models_stopped_after_repeated_errors": sorted(progress.disabled),
            "stopped_for_budget": progress.stopped_for_budget,
        }
        # One ledger line per invocation: what ran, from which code, and what it cost.
        _append_jsonl(
            directory / "ledger.jsonl",
            {
                **result,
                "started_utc": started,
                "finished_utc": datetime.now(timezone.utc).isoformat(),
                "git_commit": _git_commit(config["root"]),
                "stage": stage,
                "max_spend_usd": max_spend,
                "amendment": amend,
                "python": sys.version.split()[0],
            },
        )
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


def _provider_served(model: dict[str, Any], raw: dict[str, Any], dry_run: bool) -> Any:
    """Which host actually answered.

    OpenRouter has no top-level `provider` field in its documented response; routing details
    come back under `openrouter_metadata` when the request sends `X-OpenRouter-Metadata:
    enabled` (see transport.py). The pin itself is enforced by `allow_fallbacks: false`, so a
    missing attribution is recorded as None rather than aborting a paid run.
    """
    if model["provider"] != "openrouter":
        return model["provider"]
    return raw.get("provider") or raw.get("openrouter_metadata")


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
