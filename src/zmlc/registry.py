from __future__ import annotations

from collections.abc import Iterable
from importlib.metadata import entry_points

from zmlc.solvers.base import Solver, validate_solver_contract
from zmlc.solvers.builtin import default_solvers


class SolverRegistry:
    def __init__(self, solvers: Iterable[Solver] | None = None) -> None:
        self._solvers: dict[str, Solver] = {}
        for solver in solvers if solvers is not None else default_solvers():
            self.register(solver)

    def register(self, solver: Solver, *, replace: bool = False) -> None:
        validate_solver_contract(solver)
        if solver.name in self._solvers and not replace:
            raise ValueError(f"solver already registered: {solver.name}")
        self._solvers[solver.name] = solver

    def unregister(self, name: str) -> None:
        self._solvers.pop(name, None)

    def candidates(self) -> list[Solver]:
        return sorted(self._solvers.values(), key=lambda item: item.priority, reverse=True)

    def names(self) -> list[str]:
        return [solver.name for solver in self.candidates()]

    def load_entry_points(self, group: str = "zmlc.solvers") -> list[str]:
        """Load explicitly requested third-party solvers from Python entry points."""
        loaded: list[str] = []
        for entry_point in entry_points(group=group):
            candidate = entry_point.load()
            solver = candidate() if isinstance(candidate, type) else candidate
            self.register(solver)
            loaded.append(solver.name)
        return loaded
