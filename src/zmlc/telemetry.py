from __future__ import annotations

import json
import threading
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from zmlc.models import SolveResult, Task


@dataclass(frozen=True)
class TelemetryRecord:
    task_id: str
    task_type: str
    route: str
    solver: str | None
    provider: str | None
    verified: bool
    latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_tokens_saved: int


class TelemetrySink(Protocol):
    def record(self, task: Task, result: SolveResult) -> None: ...


def record_from_result(task: Task, result: SolveResult) -> TelemetryRecord:
    return TelemetryRecord(
        task_id=task.task_id,
        task_type=task.task_type,
        route=result.route.value,
        solver=result.solver,
        provider=result.provider,
        verified=result.route.value != "failed",
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        estimated_tokens_saved=result.estimated_tokens_saved,
    )


class MemoryTelemetry:
    def __init__(self) -> None:
        self._records: list[TelemetryRecord] = []
        self._lock = threading.Lock()

    def record(self, task: Task, result: SolveResult) -> None:
        with self._lock:
            self._records.append(record_from_result(task, result))

    def records(self) -> tuple[TelemetryRecord, ...]:
        with self._lock:
            return tuple(self._records)

    def summary(self) -> dict[str, object]:
        records = self.records()
        routes: dict[str, int] = {}
        for record in records:
            routes[record.route] = routes.get(record.route, 0) + 1
        return {
            "task_count": len(records),
            "route_counts": routes,
            "model_calls_avoided": sum(record.route == "deterministic" for record in records),
            "estimated_tokens_saved": sum(record.estimated_tokens_saved for record in records),
            "median_latency_ms": _median(record.latency_ms for record in records),
        }


class JsonlTelemetry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def record(self, task: Task, result: SolveResult) -> None:
        payload = json.dumps(asdict(record_from_result(task, result)), separators=(",", ":"))
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(payload + "\n")


def _median(values: Iterable[float]) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2
