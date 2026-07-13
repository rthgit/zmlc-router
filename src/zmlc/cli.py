from __future__ import annotations

import argparse
import json
import sys

from zmlc.benchmark import load_cases, run_benchmark, write_report
from zmlc.experiments import compare_observations, load_observations, write_paired_report
from zmlc.models import Task
from zmlc.prompting import PromptSpec, compile_prompt
from zmlc.router import Router


def _result_dict(result: object) -> dict[str, object]:
    value = result.__dict__.copy()
    value["route"] = value["route"].value
    value["trace"] = [event.__dict__ for event in value["trace"]]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="zmlc")
    sub = parser.add_subparsers(dest="command", required=True)
    solve = sub.add_parser("solve", help="Route and solve one task")
    solve.add_argument("prompt", nargs="?")
    solve.add_argument("--type", default="auto", dest="task_type")
    solve.add_argument("--json", action="store_true", dest="json_output")
    route = sub.add_parser("route", help="Show the selected route and trace")
    route.add_argument("prompt", nargs="?")
    prompt_cmd = sub.add_parser("prompt", help="Compile a token-efficient Codex task capsule")
    prompt_cmd.add_argument("objective")
    prompt_cmd.add_argument("--context", action="append", default=[])
    prompt_cmd.add_argument("--constraint", action="append", default=[])
    prompt_cmd.add_argument("--check", action="append", default=[])
    prompt_cmd.add_argument("--output", default="Return only the requested result.")
    prompt_cmd.add_argument(
        "--mode",
        choices=("auto", "coding", "debug", "review", "extraction", "planning"),
        default="auto",
    )
    benchmark_cmd = sub.add_parser("benchmark", help="Run the public routing release gate")
    benchmark_cmd.add_argument("tasks")
    benchmark_cmd.add_argument("--report")
    benchmark_cmd.add_argument("--minimum-savings", type=float, default=35.0)
    benchmark_cmd.add_argument("--minimum-route-accuracy", type=float, default=0.99)
    benchmark_cmd.add_argument("--minimum-answer-accuracy", type=float, default=0.99)
    compare_cmd = sub.add_parser("compare", help="Analyze paired baseline and candidate runs")
    compare_cmd.add_argument("observations")
    compare_cmd.add_argument("--report")
    compare_cmd.add_argument("--minimum-savings", type=float, default=35.0)
    compare_cmd.add_argument("--maximum-quality-loss", type=float, default=0.01)
    args = parser.parse_args(argv)
    if args.command == "prompt":
        compiled = compile_prompt(
            PromptSpec(
                objective=args.objective,
                context=tuple(args.context),
                constraints=tuple(args.constraint),
                verification=tuple(args.check),
                output=args.output,
                mode=args.mode,
            )
        )
        print(compiled.text)
        return 0
    if args.command == "benchmark":
        report = run_benchmark(
            load_cases(args.tasks),
            minimum_savings_pct=args.minimum_savings,
            minimum_route_accuracy=args.minimum_route_accuracy,
            minimum_answer_accuracy=args.minimum_answer_accuracy,
        )
        if args.report:
            write_report(report, args.report)
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.gate_passed else 3
    if args.command == "compare":
        report = compare_observations(
            load_observations(args.observations),
            minimum_median_savings_pct=args.minimum_savings,
            maximum_quality_loss=args.maximum_quality_loss,
        )
        if args.report:
            write_paired_report(report, args.report)
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.gate_passed else 3
    prompt = args.prompt or sys.stdin.read().strip()
    if not prompt:
        parser.error("a prompt is required")
    result = Router().solve(Task(prompt=prompt, task_type=getattr(args, "task_type", "auto")))
    if args.command == "route" or getattr(args, "json_output", False):
        print(json.dumps(_result_dict(result), indent=2, default=str))
    else:
        print(result.answer)
    return 0 if result.answer else 2


if __name__ == "__main__":
    raise SystemExit(main())
