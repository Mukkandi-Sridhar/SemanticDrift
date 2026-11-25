"""Command-line planning, offline checks, and experiment reporting."""

import argparse
import json
from typing import Any

from . import analysis, batch, cost, judge, probe, runner, score
from .config import load_config
from .transport import load_env_file


def _summarize_run(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    run_id = config["run_id"] + ("-dryrun" if args.dry_run else "")
    records = runner.read_records(config["root"] / "results/raw" / run_id)
    expected, _ = runner.plan(config)
    if {r["trial_id"] for r in records} != {t["trial_id"] for t in expected}:
        raise ValueError("Incomplete or unexpected results; finish the configured run first")
    if args.command == "score":
        result = score.summarize(
            records,
            config["k"],
            config.get("bootstrap_resamples", score.DEFAULT_BOOTSTRAP_RESAMPLES),
            config["seed"],
        )
        score.save(result, config["root"] / "results/scores" / run_id)
        result = {
            "saved": str(config["root"] / "results/scores" / run_id / "summary.json"),
            "dry_run": args.dry_run,
        }
    else:
        result = cost.report(records, config)
        runner.write_json(config["root"] / "results/scores" / run_id / "cost.json", result)
    return result


def _stage(args: argparse.Namespace) -> dict[str, Any] | None:
    stage = {
        "tasks": args.tasks.split(",") if args.tasks else None,
        "repeats": [int(r) for r in args.repeats.split(",")] if args.repeats else None,
        "models": args.models.split(",") if args.models else None,
    }
    return stage if any(value is not None for value in stage.values()) else None


def _dispatch(
    config: dict[str, Any], args: argparse.Namespace, parser: argparse.ArgumentParser
) -> dict[str, Any]:
    if args.command == "plan":
        trials, orders = runner.plan(config)
        runner.write_json(config["root"] / "results/permutations.json", orders)
        result = {
            "trials": len(trials),
            "tasks": len({t["task_id"] for t in trials}),
            "models": len(config["models"]),
            "variants": len(config["variants"]),
            "repeats": config["k"],
        }
    elif args.command == "run":
        result = runner.run(
            config, args.dry_run, stage=_stage(args), max_spend=args.max_spend, amend=args.amend
        )
    elif args.command == "batch-build":
        result = batch.build(config, args.dry_run)
    elif args.command == "batch-merge":
        if not args.input:
            parser.error("--input is required for batch-merge")
        result = batch.merge(config, args.input, args.dry_run)
    elif args.command == "analyze":
        run_dir = config["root"] / "results/raw" / (
            config["run_id"] + ("-dryrun" if args.dry_run else "")
        )
        output = analysis.analyze(runner.read_records(run_dir), config["root"], run_dir)
        path = config["root"] / "results/analysis" / run_dir.name / "analysis.json"
        runner.write_json(path, output)
        result = {"saved": str(path), "records": output["n_records"]}
    elif args.command == "probe":
        result = probe.run_probe(config, args.models.split(",") if args.models else None)
    elif args.command == "judge":
        result = judge.build(config, args.dry_run)
    else:
        result = _summarize_run(config, args)
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Tool selection only; never executes tools.")
    parser.add_argument(
        "command",
        choices=[
            "plan", "run", "probe", "analyze", "batch-build", "batch-merge", "score", "cost",
            "judge",
        ],
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--input", help="Provider batch output JSONL for batch-merge")
    parser.add_argument("--tasks", help="run: comma-separated task IDs (one stage of the run)")
    parser.add_argument("--repeats", help="run: comma-separated repeat indices, e.g. 0")
    parser.add_argument("--models", help="run: comma-separated model keys")
    parser.add_argument(
        "--amend", help="run: reason for a logged settings amendment (cache placement etc.)"
    )
    parser.add_argument(
        "--max-spend", type=float, help="run: stop this stage once its spend reaches this many USD"
    )
    args = parser.parse_args(argv)
    config = load_config(args.config)
    load_env_file(config["root"] / ".env")
    try:
        result = _dispatch(config, args, parser)
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
