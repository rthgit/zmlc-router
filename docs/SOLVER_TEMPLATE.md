# Solver Contribution Template

A solver is accepted only when its support predicate is narrower than its execution
logic and its evidence can be recomputed independently.

```python
from dataclasses import dataclass

from zmlc.models import SolverResult, Task


@dataclass
class ExampleSolver:
    name: str = "example"
    priority: int = 50

    def supports(self, task: Task) -> bool:
        return False  # Match only a closed, explicit contract.

    def solve(self, task: Task) -> SolverResult | None:
        return None  # Abstain whenever parsing or proof is incomplete.
```

Add a solver-specific branch to `verify_solver_result` that recomputes the answer from
evidence rather than trusting solver confidence. Include positive, paraphrase,
boundary, malformed, ambiguous, and adversarial tests. Extend the public corpus only
with generated or independently sourced tasks; never add hidden benchmark answers.
