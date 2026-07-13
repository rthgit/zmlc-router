from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median
from typing import Iterable

from zmlc.models import Route, Task
from zmlc.policy import RoutingPolicy
from zmlc.router import Router


@dataclass(frozen=True)
class BenchmarkCase:
    task_id: str
    prompt: str
    task_type: str
    expected_route: str
    expected_answer: str | None = None
    baseline_tokens: int = 0


@dataclass(frozen=True)
class BenchmarkReport:
    mode: str
    task_count: int
    deterministic_count: int
    host_model_count: int
    route_accuracy: float
    answer_accuracy: float
    deterministic_precision: float
    false_accepts: int
    baseline_tokens: int
    candidate_tokens: int
    token_savings_pct: float
    median_latency_ms: float
    gate_passed: bool
    gate_failures: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["gate_failures"] = list(self.gate_failures)
        return payload

    def to_markdown(self) -> str:
        status = "PASS" if self.gate_passed else "FAIL"
        rows = (
            ("Mode", self.mode),
            ("Tasks", self.task_count),
            ("Deterministic", self.deterministic_count),
            ("Delegated to host", self.host_model_count),
            ("Route accuracy", f"{self.route_accuracy:.2%}"),
            ("Deterministic answer accuracy", f"{self.answer_accuracy:.2%}"),
            ("Deterministic precision", f"{self.deterministic_precision:.2%}"),
            ("False accepts", self.false_accepts),
            ("Estimated token savings", f"{self.token_savings_pct:.2f}%"),
            ("Median router latency", f"{self.median_latency_ms:.3f} ms"),
            ("Release gate", status),
        )
        table = "\n".join(f"| {label} | {value} |" for label, value in rows)
        failures = ""
        if self.gate_failures:
            failures = "\n\n## Gate failures\n\n" + "\n".join(
                f"- {failure}" for failure in self.gate_failures
            )
        return (
            "# ZMLC Public Benchmark\n\n"
            "> Proxy benchmark: deterministic routes use zero model tokens; delegated "
            "routes retain the baseline estimate. This is not a measured Codex billing claim.\n\n"
            "| Metric | Result |\n|---|---|\n"
            f"{table}{failures}\n"
        )


def load_cases(path: str | Path) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                cases.append(BenchmarkCase(**payload))
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValueError(f"invalid benchmark row {line_number}: {exc}") from exc
    return cases


def run_benchmark(
    cases: Iterable[BenchmarkCase],
    *,
    minimum_savings_pct: float = 35.0,
    minimum_answer_accuracy: float = 0.99,
    minimum_route_accuracy: float = 0.99,
) -> BenchmarkReport:
    router = Router(
        policy=RoutingPolicy(
            delegate_to_host=True,
            allow_local_model=False,
            allow_remote_model=False,
        )
    )
    rows = []
    for case in cases:
        result = router.solve(
            Task(
                task_id=case.task_id,
                prompt=case.prompt,
                task_type=case.task_type,
                metadata={"baseline_tokens": case.baseline_tokens},
            )
        )
        answer_correct = _answer_matches(result.answer, case.expected_answer)
        route_correct = result.route.value == case.expected_route
        false_accept = result.route == Route.DETERMINISTIC and (
            case.expected_route != Route.DETERMINISTIC.value or not answer_correct
        )
        candidate_tokens = 0 if result.route == Route.DETERMINISTIC else case.baseline_tokens
        rows.append(
            {
                "result": result,
                "route_correct": route_correct,
                "answer_correct": answer_correct,
                "false_accept": false_accept,
                "baseline_tokens": case.baseline_tokens,
                "candidate_tokens": candidate_tokens,
            }
        )

    count = len(rows)
    deterministic_rows = [row for row in rows if row["result"].route == Route.DETERMINISTIC]
    answer_rows = [row for row in rows if row["result"].route == Route.DETERMINISTIC]
    false_accepts = sum(bool(row["false_accept"]) for row in rows)
    baseline_tokens = sum(int(row["baseline_tokens"]) for row in rows)
    candidate_tokens = sum(int(row["candidate_tokens"]) for row in rows)
    savings = (
        (baseline_tokens - candidate_tokens) / baseline_tokens * 100 if baseline_tokens else 0.0
    )
    answer_accuracy = (
        sum(bool(row["answer_correct"]) for row in answer_rows) / len(answer_rows)
        if answer_rows
        else 1.0
    )
    precision = (
        (len(deterministic_rows) - false_accepts) / len(deterministic_rows)
        if deterministic_rows
        else 1.0
    )
    route_accuracy = _ratio(sum(bool(row["route_correct"]) for row in rows), count)
    failures = []
    if false_accepts:
        failures.append(f"deterministic false accepts: {false_accepts}")
    if answer_accuracy < minimum_answer_accuracy:
        failures.append(
            f"answer accuracy {answer_accuracy:.4f} below {minimum_answer_accuracy:.4f}"
        )
    if route_accuracy < minimum_route_accuracy:
        failures.append(
            f"route accuracy {route_accuracy:.4f} below {minimum_route_accuracy:.4f}"
        )
    if savings < minimum_savings_pct:
        failures.append(f"token savings {savings:.2f}% below {minimum_savings_pct:.2f}%")

    return BenchmarkReport(
        mode="proxy",
        task_count=count,
        deterministic_count=len(deterministic_rows),
        host_model_count=count - len(deterministic_rows),
        route_accuracy=route_accuracy,
        answer_accuracy=round(answer_accuracy, 4),
        deterministic_precision=round(precision, 4),
        false_accepts=false_accepts,
        baseline_tokens=baseline_tokens,
        candidate_tokens=candidate_tokens,
        token_savings_pct=round(savings, 2),
        median_latency_ms=round(
            median(row["result"].latency_ms for row in rows) if rows else 0.0, 3
        ),
        gate_passed=not failures,
        gate_failures=tuple(failures),
    )


def write_report(report: BenchmarkReport, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    destination.with_suffix(".md").write_text(report.to_markdown(), encoding="utf-8")


def _answer_matches(actual: str, expected: str | None) -> bool:
    if expected is None:
        return True
    if actual.strip() == expected.strip():
        return True
    try:
        return json.loads(actual) == json.loads(expected)
    except (json.JSONDecodeError, TypeError):
        return False


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 1.0
