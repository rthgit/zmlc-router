from __future__ import annotations

from typing import Protocol

from zmlc.models import SolverResult, Task


class Solver(Protocol):
    name: str
    priority: int

    def supports(self, task: Task) -> bool: ...

    def solve(self, task: Task) -> SolverResult | None: ...


def validate_solver_contract(solver: object) -> None:
    name = getattr(solver, "name", None)
    priority = getattr(solver, "priority", None)
    if not isinstance(name, str) or not name.strip():
        raise TypeError("solver name must be a non-empty string")
    if not isinstance(priority, int):
        raise TypeError(f"solver {name!r} priority must be an integer")
    if not callable(getattr(solver, "supports", None)):
        raise TypeError(f"solver {name!r} must define supports(task)")
    if not callable(getattr(solver, "solve", None)):
        raise TypeError(f"solver {name!r} must define solve(task)")
