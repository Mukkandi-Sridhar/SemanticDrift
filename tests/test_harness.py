"""Offline regression checks for requests, execution records, and study statistics."""

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from semdrift import adapters, analysis, batch, cost, judge, runner, score
from semdrift.config import load_config
from semdrift.data import ROOT, load, validate_arguments
from semdrift.parse import parse, usage
from semdrift.transport import FakeTransport, RealTransport, TransportError, sanitize


# Every test is network-denied, including future tests added to this module.
def setUpModule() -> None:
    global deny_socket, deny_connection
    deny_socket = patch("socket.socket", side_effect=AssertionError("Network forbidden"))
    deny_connection = patch(
        "socket.create_connection", side_effect=AssertionError("Network forbidden")
    )
    deny_socket.start()
    deny_connection.start()


def tearDownModule() -> None:
    deny_socket.stop()
    deny_connection.stop()


def response(name: str | None = None, args: str = "{}", count: int = 1) -> dict[str, Any]:
    message = {"content": "answer"}
    if name:
        message["tool_calls"] = [
            {"type": "function", "function": {"name": name, "arguments": args}}
            for _ in range(count)
        ]
    return {
        "model": "fixture",
        "choices": [{"message": message, "finish_reason": "tool_calls" if name else "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 2},
    }


def responses_reply(name: str) -> dict[str, Any]:
    """An OpenAI Responses API result calling one tool (OpenAI models use this API)."""
    return {
        "model": "fixture",
        "status": "completed",
        "output": [{"type": "function_call", "name": name, "arguments": "{}"}],
        "usage": {"input_tokens": 10, "output_tokens": 2},
    }


class HarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = load()
        cls.config = load_config(ROOT / "configs/pilot.toml")

    def sandbox(self, folder: str) -> dict[str, Any]:
        config = copy.deepcopy(self.config)
        config.update(
            root=Path(folder), models=["gpt-6-luna"], variants=["V0", "P1"], task_ids=["T001"], k=2
        )
        config["model_settings"] = {
            model: config["model_settings"][model] for model in config["models"]
        }
        return config

    def test_pilot_strata(self) -> None:
        selected = [task for task in self.dataset["tasks"] if task["id"] in self.config["task_ids"]]
        self.assertEqual(len(selected), 20)
        singles = [task for task in selected if task["type"] == "single_tool"]
        self.assertEqual(len(singles), 12)
        self.assertGreaterEqual(sum(bool(task["near_miss_of"]) for task in singles), 6)
        self.assertGreaterEqual(sum(task["ms_conflict"] for task in singles), 4)
        for subtype, count in [("tempting", 4), ("easy", 2), ("out_of_scope", 1)]:
            self.assertGreaterEqual(sum(task.get("subtype") == subtype for task in selected), count)

    def test_permutations(self) -> None:
        trials, orders = runner.plan(self.config, self.dataset)
        self.assertEqual(len(trials), 1920)
        self.assertNotEqual(orders[0]["tool_order"], orders[1]["tool_order"])
        for repeat in range(2):
            self.assertEqual(
                len({task["permutation_id"] for task in trials if task["repeat"] == repeat}),
                1,
            )
        self.assertEqual(orders, runner.plan(self.config, self.dataset)[1])

    def test_goldens(self) -> None:
        tools = self.dataset["catalogs"]["V0"]
        for name, model in self.config["model_settings"].items():
            expected = json.loads(
                (ROOT / "tests/golden" / (name.replace("/", "__") + ".json")).read_text()
            )
            self.assertEqual(adapters.build(model, tools, "List available facilities."), expected)
            self.assertNotIn("temperature", expected)
            if model["provider"] == "anthropic":
                self.assertIn("cache_control", expected["tools"][-1])
                self.assertFalse(any("cache_control" in task for task in expected["tools"][:-1]))
                self.assertEqual(expected["max_tokens"], 1024)

    def test_parse_edge_cases(self) -> None:
        for count in (1, 3):
            parsed = parse(response("sites", count=count), "openrouter")
            self.assertEqual(parsed["n_tool_calls"], count)
            self.assertEqual(parsed["tool_name"], "sites")
            self.assertEqual(parsed["arguments"], {})
        for raw in (response(), {}, {"choices": []}, {"choices": [{"message": {"content": None}}]}):
            self.assertEqual(parse(raw, "openrouter")["tool_name"], "NONE")
        self.assertEqual(parse(response("sites", "{bad"), "openrouter")["arguments"], "{bad")
        for content, count in [
            ([], 0),
            ([{"type": "text", "text": "x"}], 0),
            ([{"type": "tool_use", "name": "sites", "input": {}}], 1),
            ([{"type": "tool_use", "name": "sites", "input": {}}] * 2, 2),
        ]:
            self.assertEqual(parse({"content": content}, "anthropic")["n_tool_calls"], count)

    def test_invalid_tool_name_is_not_abstention(self) -> None:
        parsed = parse(response("NONE"), "openrouter")
        self.assertEqual(parsed["action"], "tool")
        self.assertNotEqual(parsed["tool_name"], "NONE")

    def test_schema(self) -> None:
        schema = {"type": "object", "properties": {"a": {"type": "integer"}}, "required": ["a"]}
        self.assertEqual(validate_arguments({"a": 1}, schema), (True, []))
        for args in ({"a": True}, {}, {"a": "1"}, "{bad"):
            self.assertFalse(validate_arguments(args, schema)[0])
        self.assertEqual(validate_arguments({"a": 1, "extra": 2}, schema), (False, ["extra"]))

    def test_resume_and_change_detection(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            patch("semdrift.runner.load", return_value=self.dataset),
        ):
            config = self.sandbox(temp)
            fake = FakeTransport([response("sites")] * 4)
            self.assertEqual(runner.run(config, True, fake)["new_trials"], 4)
            self.assertEqual(runner.run(config, True, fake)["new_trials"], 0)
            self.assertEqual(fake.calls, 4)
            self.assertEqual(len(runner.read_records(Path(temp) / "results/raw/pilot-dryrun")), 4)
            config["seed"] += 1
            with self.assertRaisesRegex(ValueError, "configuration changed"):
                runner.run(config, True, fake)

    def test_full_run_defers_batch_providers(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            patch("semdrift.runner.load", return_value=self.dataset),
        ):
            config = self.sandbox(temp)
            config["batch_providers"] = ["openai"]
            fake = FakeTransport()
            result = runner.run(config, False, fake)
            self.assertEqual(fake.calls, 0)
            self.assertEqual(result["pending_trials"], 4)

    def test_rpm_limit(self) -> None:
        now = [0.0]
        waits = []

        def sleep(seconds: float) -> None:
            waits.append(seconds)
            now[0] += seconds

        def clock() -> float:
            return now[0]

        transport = RealTransport(sleep=sleep, clock=clock)
        model = {**self.config["model_settings"]["gpt-6-luna"], "rpm": 1}
        with patch.object(transport, "_request", return_value=response()):
            transport.send(model, {})
            transport.send(model, {})
        self.assertEqual(waits, [60.0])

    def test_pin_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "provider_pin"):
            runner.run(self.config, False, FakeTransport())
        with self.assertRaisesRegex(ValueError, "provider_pin"):
            batch.build(self.config)

    def test_integrity_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = json.loads((ROOT / "datasets/MANIFEST.json").read_text())
            for rel in ["datasets/MANIFEST.json", *manifest["sha256"]]:
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, root / rel)
            (root / "datasets/tools/p1_paraphrase.json").write_text("[]")
            config = self.sandbox(temp)
            with self.assertRaisesRegex(ValueError, "integrity mismatch"):
                runner.run(config, True, FakeTransport())

    def test_batch_roundtrip(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            patch("semdrift.batch.load", return_value=self.dataset),
        ):
            config = self.sandbox(temp)
            config["models"] = ["gpt-6-luna", "claude-sonnet-5-5"]
            config["model_settings"] = {
                model: self.config["model_settings"][model] for model in config["models"]
            }
            built = batch.build(config, True)
            self.assertEqual(built["trials"], 8)
            index = json.loads((Path(temp) / "results/batch/pilot-dryrun/index.json").read_text())
            items = batch_responses(index)
            target = Path(temp) / "responses.jsonl"
            target.write_text("".join(json.dumps(x) + "\n" for x in reversed(items)))
            self.assertEqual(batch.merge(config, target, True)["merged"], 8)
            self.assertEqual(batch.merge(config, target, True)["merged"], 0)
            items[0] = {"custom_id": items[0]["custom_id"], "error": {"code": "cancelled"}}
            target.write_text(json.dumps(items[0]) + "\n")
            self.assertEqual(batch.merge(config, target, True)["failed_unfinished"], 1)

    def test_usage_cost(self) -> None:
        token_usage = usage(
            {
                "usage": {
                    "input_tokens": 10,
                    "cache_read_input_tokens": 20,
                    "cache_creation_input_tokens": 30,
                    "output_tokens": 5,
                }
            },
            "anthropic",
        )
        self.assertEqual(token_usage["input"], 60)
        prices = {
            "input": 1,
            "cached_input": 0.1,
            "cache_write": 2,
            "output": 3,
            "batch_discount": 0.5,
        }
        self.assertAlmostEqual(cost.charge(token_usage, prices, True), 43.5 / 1e6)
        with self.assertRaises(ValueError):
            cost.charge(token_usage, {**prices, "cache_write": -1})
        self.assertEqual(
            usage({"usage": {"prompt_tokens": 100, "prompt_cache_hit_tokens": 40}}, "deepseek")[
                "cached_input"
            ],
            40,
        )

    def test_failures_are_logged_and_runs_continue(self) -> None:
        class Failing:
            calls = 0

            def send(self, model: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
                self.calls += 1
                raise RuntimeError("Transport failed for gpt-6-luna: HTTP 400: bad field")

        with (
            tempfile.TemporaryDirectory() as temp,
            patch("semdrift.runner.load", return_value=self.dataset),
        ):
            config = self.sandbox(temp)
            failing = Failing()
            result = runner.run(config, True, failing)
            directory = Path(temp) / "results/raw/pilot-dryrun"
            errors = (directory / "errors.jsonl").read_text().splitlines()
            # Three consecutive failures stop that model; the rest stays pending, nothing is lost.
            self.assertEqual((failing.calls, len(errors)), (3, 3))
            self.assertEqual(result["models_stopped_after_repeated_errors"], ["gpt-6-luna"])
            self.assertEqual(result["pending_trials"], 4)
            ledger = (directory / "ledger.jsonl").read_text().splitlines()
            self.assertEqual(len(ledger), 1)
            self.assertEqual(runner.read_records(directory), [])

    def test_spend_cap_stops_a_stage(self) -> None:
        priced = response("sites")
        priced["usage"]["cost"] = 1.0
        with (
            tempfile.TemporaryDirectory() as temp,
            patch("semdrift.runner.load", return_value=self.dataset),
        ):
            config = self.sandbox(temp)
            config["model_settings"]["gpt-6-luna"] = {
                **config["model_settings"]["gpt-6-luna"],
                "provider": "openrouter",
                "provider_pin": "test",
            }
            result = runner.run(config, True, FakeTransport([priced] * 4), max_spend=2.0)
            self.assertTrue(result["stopped_for_budget"])
            self.assertEqual(result["new_trials"], 2)
            self.assertEqual(result["stage_spend_usd"], 2.0)

    def test_analysis_runs_on_partial_results(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            patch("semdrift.runner.load", return_value=self.dataset),
            patch("semdrift.analysis.load", return_value=self.dataset),
        ):
            config = self.sandbox(temp)
            config.update(variants=["V0", "V0R", "H1"], task_ids=["T001", "T002"])
            # Dry runs execute streams in order (model, repeat, catalog), tasks within a stream.
            # H1 differs from V0 on T001 in both repeats; V0 and V0R agree.
            replies = [responses_reply("assets"), responses_reply("sites")] * 2  # H1 r0, r1
            replies += [responses_reply("sites")] * 8  # V0 and V0R, both repeats
            runner.run(config, True, FakeTransport(replies))
            run_dir = Path(temp) / "results/raw/pilot-dryrun"
            output = analysis.analyze(runner.read_records(run_dir), Path(temp), run_dir)
            h1 = next(
                row for row in output["excess_flip_rates_all_tasks"] if row["variant"] == "H1"
            )
            self.assertEqual((h1["placebo_flip_rate"], h1["flip_rate"]), (0.0, 0.5))
            self.assertEqual(h1["excess_flip_rate"], 0.5)
            self.assertEqual(output["indistinguishable_pairs"]["n_pairs"], 0)
            self.assertTrue(output["severity_profile"])

    def test_model_can_run_fewer_repeats(self) -> None:
        config = copy.deepcopy(self.config)
        config.update(variants=["V0"], task_ids=["T001", "T002"], k=3)
        first = config["models"][0]
        config["model_settings"][first] = {**config["model_settings"][first], "k": 1}
        trials, _ = runner.plan(config, self.dataset)
        repeats = {t["repeat"] for t in trials if t["model"] == first}
        others = {t["repeat"] for t in trials if t["model"] != first}
        self.assertEqual((repeats, others), ({0}, {0, 1, 2}))

    def test_retry(self) -> None:
        transport = RealTransport(sleep=skip_sleep)
        model = self.config["model_settings"]["gpt-6-luna"]
        with patch.object(
            transport, "_request", side_effect=[TransportError("busy", 429), response()]
        ) as mock:
            self.assertEqual(transport.send(model, {}), response())
            self.assertEqual(mock.call_count, 2)
        with patch.object(
            transport, "_request", side_effect=TransportError("HTTP 400: bad field", 400)
        ) as mock:
            with self.assertRaisesRegex(RuntimeError, "Transport failed.*HTTP 400"):
                transport.send(model, {})
            self.assertEqual(mock.call_count, 1)  # client errors are not retried

    def test_responses_api_parsing(self) -> None:
        raw = {
            "status": "completed",
            "output": [
                {"type": "reasoning", "summary": []},
                {"type": "function_call", "name": "sites", "arguments": "{}"},
            ],
            "usage": {
                "input_tokens": 6000,
                "input_tokens_details": {"cached_tokens": 5800},
                "output_tokens": 40,
                "output_tokens_details": None,
            },
        }
        parsed = parse(raw, "openai")
        self.assertEqual((parsed["action"], parsed["tool_name"]), ("tool", "sites"))
        self.assertEqual(parsed["arguments"], {})
        text_only = {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}}
        self.assertEqual(parse(text_only, "openai")["tool_name"], "NONE")
        self.assertEqual(parse(text_only, "openai")["raw_stop_reason"], "max_output_tokens")
        counts = usage(raw, "openai")
        self.assertEqual((counts["cached_input"], counts["reasoning"]), (5800, 0))

    def test_openrouter_usage_reports_billed_cost(self) -> None:
        raw = response("sites")
        raw["usage"] = {
            "prompt_tokens": 6000,
            "completion_tokens": 30,
            "prompt_tokens_details": {"cached_tokens": 5800, "cache_write_tokens": 0},
            "completion_tokens_details": None,
            "cost": 0.00042,
        }
        counts = usage(raw, "openrouter")
        self.assertEqual((counts["cached_input"], counts["cost"]), (5800, 0.00042))

    def test_judge(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp,
            patch("semdrift.judge.load", return_value=self.dataset),
        ):
            config = load_config(ROOT / "configs/judge.toml")
            config["root"] = Path(temp)
            result = judge.build(config, True)
            self.assertEqual(result["requests"], 432)
            entries = json.loads(Path(result["path"]).read_text())["requests"]
            answers = {e["judge_id"]: "EQUIVALENT. Same behavior." for e in entries}
            self.assertEqual(
                sum(verdict["status"] == "pass" for verdict in judge.verdicts(entries, answers)),
                108,
            )
            answers[entries[0]["judge_id"]] = "NOT_EQUIVALENT. Changed scope."
            self.assertEqual(
                sum(verdict["status"] == "fail" for verdict in judge.verdicts(entries, answers)), 1
            )
            self.assertEqual(
                sum(verdict["status"] == "pending" for verdict in judge.verdicts(entries, {})), 108
            )

    def test_secret_redaction_and_extra_write(self) -> None:
        with patch.dict("os.environ", {"OPENAI_API_KEY": "dummy-secret-value"}):
            self.assertEqual(
                sanitize({"x": "dummy-secret-value", "headers": {"a": "b"}}),
                {"x": "[REDACTED]", "headers": "[REDACTED]"},
            )
        trials, orders = runner.plan(self.config, self.dataset)
        trial = next(
            task
            for task in trials
            if self.config["model_settings"][task["model"]]["provider"] == "openrouter"
        )
        body = runner.request(self.config, self.dataset, trial, orders)
        raw = response("sites")
        raw["choices"][0]["message"]["tool_calls"] += response("generate_work_order")["choices"][0][
            "message"
        ]["tool_calls"]
        record = runner.make_record(self.config, self.dataset, trial, body, raw, 1, True)
        self.assertEqual(record["n_tool_calls"], 2)
        self.assertTrue(record["unsafe_write"])


class ScoreTests(unittest.TestCase):
    def fixture(self) -> list[dict[str, Any]]:
        # Four tasks, two repeats. B reverses A's ranking after editing.
        decisions = {
            ("A", "V0"): [["read"] * 2, ["read"] * 2, ["NONE"] * 2, ["write"] * 2],
            ("A", "P1"): [["read", "write"], ["write"] * 2, ["write"] * 2, ["write"] * 2],
            ("B", "V0"): [["read"] * 2, ["write"] * 2, ["write"] * 2, ["write"] * 2],
            ("B", "P1"): [["read"] * 2, ["read"] * 2, ["NONE"] * 2, ["write"] * 2],
        }
        rows = []
        for (model, variant), tasks in decisions.items():
            for task_index, choices in enumerate(tasks):
                gold = "read" if task_index < 2 else "NONE"
                for repeat, name in enumerate(choices):
                    rows.append(
                        {
                            "trial_id": f"{model}{variant}{task_index}{repeat}",
                            "model": model,
                            "variant": variant,
                            "task_id": str(task_index),
                            "repeat": repeat,
                            "gold": gold,
                            "tool_name": name,
                            "n_tool_calls": int(name != "NONE"),
                            "args_valid": True,
                            "selected_access": name if name in ("read", "write") else None,
                            "gold_access": "read" if task_index < 2 else "none",
                            "subtype": "easy" if task_index == 2 else "tempting",
                            "ms_conflict": task_index == 0,
                            "dry_run": True,
                        }
                    )
        return rows

    def test_hand_computed(self) -> None:
        summary = score.summarize(self.fixture(), 2, 100, 42)
        rows = {(metric["model"], metric["variant"]): metric for metric in summary["metrics"]}
        self.assertEqual(rows[("A", "V0")]["accuracy"], 0.75)
        self.assertEqual(rows[("A", "V0")]["pass^k"], 0.75)
        self.assertEqual(rows[("A", "P1")]["accuracy"], 0.125)
        self.assertEqual(rows[("A", "P1")]["pass^k"], 0)
        self.assertEqual(rows[("A", "V0")]["false_action_rate"], 0.5)
        self.assertEqual(rows[("A", "P1")]["false_action_rate"], 1)
        self.assertEqual(rows[("A", "V0")]["false_action_easy"], 0)
        self.assertEqual(summary["rankings"][0]["kendall_tau_b"], -1)
        self.assertEqual(summary["rankings"][0]["pairwise_rank_flip_share"], 1)
        row = next(metric for metric in summary["comparisons"] if metric["model"] == "A")
        self.assertEqual(row["flip_rate"], 0.5)
        self.assertEqual(row["mcnemar_p"], 0.5)
        self.assertEqual(score.mcnemar(6, 0), 0.03125)
        self.assertEqual(score.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
        self.assertEqual(summary, score.summarize(self.fixture(), 2, 100, 42))
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            score.summarize(self.fixture()[:-1], 2, 10)

    def test_ties(self) -> None:
        self.assertIsNone(score.kendall([1, 1], [2, 2]))
        self.assertAlmostEqual(score.kendall([1, 1, 2], [1, 2, 3]), 2 / (6**0.5))
        self.assertEqual(score.mcnemar(0, 0), 1)


def skip_sleep(seconds: float) -> None:
    return None


def batch_responses(index: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for custom_id, entry in index["entries"].items():
        if entry["trial"]["model"] == "claude-sonnet-5-5":
            items.append(
                {
                    "custom_id": custom_id,
                    "result": {
                        "type": "succeeded",
                        "message": {"content": [], "stop_reason": "end_turn"},
                    },
                }
            )
        else:
            items.append(
                {
                    "custom_id": custom_id,
                    "response": {"status_code": 200, "body": response("sites")},
                }
            )
    return items
