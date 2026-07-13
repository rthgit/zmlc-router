from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingPolicy:
    """Accuracy-first defaults with explicit token and confidence controls."""

    solver_min_confidence: float = 0.99
    require_verification: bool = True
    allow_local_model: bool = True
    allow_remote_model: bool = True
    delegate_to_host: bool = False
    fail_closed: bool = False
    max_solver_candidates: int = 16
    minimum_estimated_savings: int = 1

    def __post_init__(self) -> None:
        if not 0.0 <= self.solver_min_confidence <= 1.0:
            raise ValueError("solver_min_confidence must be between 0 and 1")
        if self.max_solver_candidates < 1:
            raise ValueError("max_solver_candidates must be positive")
        if self.minimum_estimated_savings < 0:
            raise ValueError("minimum_estimated_savings cannot be negative")
