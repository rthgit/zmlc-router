from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Route(str, Enum):
    DETERMINISTIC = "deterministic"
    HOST_MODEL = "host_model"
    LOCAL_MODEL = "local_model"
    REMOTE_MODEL = "remote_model"
    FAILED = "failed"


@dataclass(frozen=True)
class Task:
    prompt: str
    task_id: str = "task"
    task_type: str = "auto"
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SolverResult:
    answer: str
    solver: str
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderResult:
    answer: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class TraceEvent:
    stage: str
    status: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SolveResult:
    task_id: str
    answer: str
    route: Route
    confidence: float
    solver: str | None = None
    provider: str | None = None
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    estimated_tokens_saved: int = 0
    trace: tuple[TraceEvent, ...] = ()
