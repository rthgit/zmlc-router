from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from statistics import median
from typing import Callable, Sequence

from zmlc.codex_runner import CodexPreflightResult, invoke_codex, run_codex_preflight


@dataclass(frozen=True)
class CodexAbCase:
    task_id: str
    prompt: str
    expected: str
    task_type: str = "auto"
    comparison: str = "text"


@dataclass(frozen=True)
class CodexAbObservation:
    task_id: str
    baseline_answer: str
    candidate_answer: str
    baseline_tokens: int
    candidate_tokens: int
    baseline_correct: bool
    candidate_correct: bool
    candidate_route: str
    codex_invoked: bool
    savings_pct: float


def load_codex_ab_cases(path: str | Path) -> list[CodexAbCase]:
    cases: list[CodexAbCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        cases.append(CodexAbCase(**json.loads(line)))
    return cases


def answer_matches(answer: str, expected: str, comparison: str = "text") -> bool:
    if comparison == "json":
        try:
            return json.loads(answer) == json.loads(expected)
        except json.JSONDecodeError:
            return False
    return " ".join(answer.strip().lower().split()) == " ".join(expected.strip().lower().split())


def build_codex_ab_report(
    cases: Sequence[CodexAbCase],
    baseline_results: Sequence[CodexPreflightResult],
    candidate_results: Sequence[CodexPreflightResult],
    *,
    minimum_savings_pct: float = 35.0,
    maximum_quality_loss: float = 0.01,
) -> dict[str, object]:
    if not (len(cases) == len(baseline_results) == len(candidate_results)):
        raise ValueError("cases and result sequences must have equal length")
    observations: list[CodexAbObservation] = []
    for case, baseline, candidate in zip(cases, baseline_results, candidate_results, strict=True):
        baseline_tokens = baseline.usage.total_tokens
        candidate_tokens = candidate.usage.total_tokens
        savings_pct = (
            100.0 * (baseline_tokens - candidate_tokens) / baseline_tokens
            if baseline_tokens
            else 0.0
        )
        observations.append(
            CodexAbObservation(
                task_id=case.task_id,
                baseline_answer=baseline.answer,
                candidate_answer=candidate.answer,
                baseline_tokens=baseline_tokens,
                candidate_tokens=candidate_tokens,
                baseline_correct=answer_matches(baseline.answer, case.expected, case.comparison),
                candidate_correct=answer_matches(candidate.answer, case.expected, case.comparison),
                candidate_route=candidate.route.value,
                codex_invoked=candidate.codex_invoked,
                savings_pct=round(savings_pct, 2),
            )
        )
    count = len(observations)
    baseline_quality = sum(item.baseline_correct for item in observations) / count if count else 0.0
    candidate_quality = sum(item.candidate_correct for item in observations) / count if count else 0.0
    median_savings = median(item.savings_pct for item in observations) if observations else 0.0
    baseline_tokens = sum(item.baseline_tokens for item in observations)
    candidate_tokens = sum(item.candidate_tokens for item in observations)
    aggregate_savings = (
        100.0 * (baseline_tokens - candidate_tokens) / baseline_tokens if baseline_tokens else 0.0
    )
    quality_delta = candidate_quality - baseline_quality
    gate_passed = median_savings >= minimum_savings_pct and quality_delta >= -maximum_quality_loss
    return {
        "measurement": "real_codex_exec_tokens",
        "task_count": count,
        "baseline_quality": round(baseline_quality, 4),
        "candidate_quality": round(candidate_quality, 4),
        "quality_delta": round(quality_delta, 4),
        "baseline_tokens": baseline_tokens,
        "candidate_tokens": candidate_tokens,
        "median_savings_pct": round(median_savings, 2),
        "aggregate_savings_pct": round(aggregate_savings, 2),
        "codex_calls_avoided": sum(not item.codex_invoked for item in observations),
        "gate": {
            "minimum_median_savings_pct": minimum_savings_pct,
            "maximum_quality_loss": maximum_quality_loss,
            "passed": gate_passed,
        },
        "observations": [asdict(item) for item in observations],
    }


def run_codex_ab(
    cases: Sequence[CodexAbCase],
    *,
    codex_binary: str | None = None,
    model: str | None = None,
    reasoning_effort: str | None = None,
    sandbox: str | None = None,
    cwd: str | Path | None = None,
    configs: Sequence[str] = (),
    minimum_savings_pct: float = 35.0,
    maximum_quality_loss: float = 0.01,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    baseline_results: list[CodexPreflightResult] = []
    candidate_results: list[CodexPreflightResult] = []
    for index, case in enumerate(cases, start=1):
        if progress:
            progress(f"[{index}/{len(cases)}] baseline {case.task_id}")
        baseline_results.append(
            invoke_codex(
                case.prompt,
                codex_binary=codex_binary,
                model=model,
                reasoning_effort=reasoning_effort,
                sandbox=sandbox,
                cwd=cwd,
                configs=configs,
            )
        )
        if progress:
            progress(f"[{index}/{len(cases)}] candidate {case.task_id}")
        candidate_results.append(
            run_codex_preflight(
                case.prompt,
                task_type=case.task_type,
                codex_binary=codex_binary,
                model=model,
                reasoning_effort=reasoning_effort,
                sandbox=sandbox,
                cwd=cwd,
                configs=configs,
            )
        )
    return build_codex_ab_report(
        cases,
        baseline_results,
        candidate_results,
        minimum_savings_pct=minimum_savings_pct,
        maximum_quality_loss=maximum_quality_loss,
    )


def write_codex_ab_report(report: dict[str, object], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
