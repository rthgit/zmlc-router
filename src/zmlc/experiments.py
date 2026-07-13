from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median
from collections.abc import Callable, Iterable


@dataclass(frozen=True)
class PairedObservation:
    task_id: str
    baseline_tokens: int
    candidate_tokens: int
    baseline_score: float
    candidate_score: float


@dataclass(frozen=True)
class PairedReport:
    mode: str
    task_count: int
    median_token_savings_pct: float
    mean_token_savings_pct: float
    token_savings_ci95: tuple[float, float]
    quality_delta: float
    quality_delta_ci95: tuple[float, float]
    gate_passed: bool
    gate_failures: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["token_savings_ci95"] = list(self.token_savings_ci95)
        payload["quality_delta_ci95"] = list(self.quality_delta_ci95)
        payload["gate_failures"] = list(self.gate_failures)
        return payload


def load_observations(path: str | Path) -> list[PairedObservation]:
    rows: list[PairedObservation] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                observation = PairedObservation(**payload)
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValueError(f"invalid paired row {line_number}: {exc}") from exc
            if observation.baseline_tokens < 0 or observation.candidate_tokens < 0:
                raise ValueError(f"negative token count on paired row {line_number}")
            if not 0 <= observation.baseline_score <= 1:
                raise ValueError(f"invalid baseline score on paired row {line_number}")
            if not 0 <= observation.candidate_score <= 1:
                raise ValueError(f"invalid candidate score on paired row {line_number}")
            rows.append(observation)
    return rows


def compare_observations(
    observations: Iterable[PairedObservation],
    *,
    minimum_median_savings_pct: float = 35.0,
    maximum_quality_loss: float = 0.01,
    bootstrap_samples: int = 2_000,
    bootstrap_seed: int = 20260713,
) -> PairedReport:
    rows = list(observations)
    if not rows:
        raise ValueError("at least one paired observation is required")
    savings = [
        (row.baseline_tokens - row.candidate_tokens) / row.baseline_tokens * 100
        if row.baseline_tokens
        else 0.0
        for row in rows
    ]
    quality_deltas = [row.candidate_score - row.baseline_score for row in rows]
    savings_ci = _bootstrap_interval(
        savings,
        statistic=mean,
        samples=bootstrap_samples,
        seed=bootstrap_seed,
    )
    quality_ci = _bootstrap_interval(
        quality_deltas,
        statistic=mean,
        samples=bootstrap_samples,
        seed=bootstrap_seed + 1,
    )
    median_savings = float(median(savings))
    quality_delta = float(mean(quality_deltas))
    failures: list[str] = []
    if median_savings < minimum_median_savings_pct:
        failures.append(
            f"median savings {median_savings:.2f}% below {minimum_median_savings_pct:.2f}%"
        )
    if quality_delta < -maximum_quality_loss:
        failures.append(
            f"quality delta {quality_delta:.4f} below {-maximum_quality_loss:.4f}"
        )
    return PairedReport(
        mode="paired_ab",
        task_count=len(rows),
        median_token_savings_pct=round(median_savings, 2),
        mean_token_savings_pct=round(float(mean(savings)), 2),
        token_savings_ci95=tuple(round(value, 2) for value in savings_ci),
        quality_delta=round(quality_delta, 4),
        quality_delta_ci95=tuple(round(value, 4) for value in quality_ci),
        gate_passed=not failures,
        gate_failures=tuple(failures),
    )


def write_paired_report(report: PairedReport, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")


def _bootstrap_interval(
    values: list[float],
    *,
    statistic: Callable[[list[float]], float],
    samples: int,
    seed: int,
) -> tuple[float, float]:
    if samples <= 0 or len(values) == 1:
        value = float(statistic(values))
        return value, value
    randomizer = random.Random(seed)
    estimates = []
    for _ in range(samples):
        sample = [values[randomizer.randrange(len(values))] for _ in values]
        estimates.append(float(statistic(sample)))
    estimates.sort()
    low = estimates[int((len(estimates) - 1) * 0.025)]
    high = estimates[int((len(estimates) - 1) * 0.975)]
    return low, high
