from __future__ import annotations

import ast
import json
import operator
import re
import statistics
from dataclasses import dataclass
from typing import Any

from zmlc.models import SolverResult, Task


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.10g}"


def _safe_eval(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            left, right = visit(node.left), visit(node.right)
            if abs(left) > 1e15 or abs(right) > 1e15:
                raise ValueError("operand outside safe range")
            return float(_BIN_OPS[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return float(_UNARY_OPS[type(node.op)](visit(node.operand)))
        raise ValueError("unsupported expression")

    return visit(tree)


@dataclass
class ArithmeticSolver:
    name: str = "arithmetic"
    priority: int = 100

    def supports(self, task: Task) -> bool:
        low = task.prompt.lower()
        return task.task_type == "math" or any(
            cue in low for cue in ("calculate", "compute", "evaluate", "what is")
        )

    def solve(self, task: Task) -> SolverResult | None:
        low = task.prompt.lower()
        if re.search(r"\b\d{4}-\d{2}-\d{2}\b", task.prompt):
            return None
        percent = re.search(r"([-+]?\d+(?:\.\d+)?)\s*%\s+of\s+([-+]?\d+(?:\.\d+)?)", low)
        if percent:
            answer = float(percent.group(1)) * float(percent.group(2)) / 100
            rendered = _number(answer)
            return SolverResult(
                rendered,
                self.name,
                1.0,
                {
                    "operation": "percent_of",
                    "percent": float(percent.group(1)),
                    "value": float(percent.group(2)),
                },
            )

        expression = re.search(r"(?<![\w.])([-+]?\d+(?:\.\d+)?(?:\s*[-+*/%()]\s*[-+]?\d+(?:\.\d+)?)+)", task.prompt)
        if not expression:
            return None
        try:
            value = _safe_eval(expression.group(1))
        except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
            return None
        return SolverResult(
            _number(value),
            self.name,
            1.0,
            {"operation": "expression", "expression": expression.group(1)},
        )


@dataclass
class ListAggregateSolver:
    name: str = "list_aggregate"
    priority: int = 95

    def supports(self, task: Task) -> bool:
        low = task.prompt.lower()
        return "[" in task.prompt and any(
            cue in low for cue in ("sum", "average", "mean", "median", "minimum", "maximum", "count")
        )

    def solve(self, task: Task) -> SolverResult | None:
        match = re.search(r"\[([^\[\]]+)\]", task.prompt)
        if not match:
            return None
        try:
            values = [float(item.strip()) for item in match.group(1).split(",")]
        except ValueError:
            return None
        low = task.prompt.lower()
        if "median" in low:
            value = statistics.median(values)
            operation = "median"
        elif "average" in low or "mean" in low:
            value = statistics.mean(values)
            operation = "mean"
        elif "minimum" in low or "smallest" in low:
            value = min(values)
            operation = "minimum"
        elif "maximum" in low or "largest" in low:
            value = max(values)
            operation = "maximum"
        elif "count" in low:
            value = float(len(values))
            operation = "count"
        elif "sum" in low:
            value = sum(values)
            operation = "sum"
        else:
            return None
        return SolverResult(
            _number(float(value)), self.name, 1.0, {"values": values, "operation": operation}
        )


@dataclass
class ExactJsonSolver:
    name: str = "exact_json"
    priority: int = 110

    def supports(self, task: Task) -> bool:
        low = task.prompt.lower()
        return "json" in low and ("{" in task.prompt or "[" in task.prompt)

    def solve(self, task: Task) -> SolverResult | None:
        values = re.findall(r"(?s)(\{.*\}|\[.*\])", task.prompt)
        if not values:
            return None
        candidate = values[-1].strip()
        try:
            json.loads(candidate)
        except json.JSONDecodeError:
            return None
        return SolverResult(candidate, self.name, 1.0, {"value": json.loads(candidate)})


@dataclass
class StringTransformSolver:
    name: str = "string_transform"
    priority: int = 90

    def supports(self, task: Task) -> bool:
        low = task.prompt.lower()
        return any(cue in low for cue in ("uppercase", "lowercase", "reverse", "remove spaces", "count words"))

    def solve(self, task: Task) -> SolverResult | None:
        match = re.search(r"([\"'`])(.+?)\1", task.prompt, flags=re.DOTALL)
        if not match:
            return None
        value, low = match.group(2), task.prompt.lower()
        if "uppercase" in low:
            answer = value.upper()
        elif "lowercase" in low:
            answer = value.lower()
        elif "reverse" in low:
            answer = value[::-1]
        elif "remove spaces" in low:
            answer = value.replace(" ", "")
        elif "count words" in low:
            answer = str(len(re.findall(r"\b\w+\b", value)))
        else:
            return None
        return SolverResult(
            answer,
            self.name,
            1.0,
            {"source": value, "operation": next(cue for cue in ("uppercase", "lowercase", "reverse", "remove spaces", "count words") if cue in low)},
        )


@dataclass
class RegexExtractionSolver:
    name: str = "regex_extract"
    priority: int = 85

    def supports(self, task: Task) -> bool:
        low = task.prompt.lower()
        return "extract" in low and any(cue in low for cue in ("email", "url", "number"))

    def solve(self, task: Task) -> SolverResult | None:
        low = task.prompt.lower()
        patterns: list[tuple[str, str]] = [
            ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
            ("url", r"https?://[^\s\"'`<>]+"),
            ("number", r"[-+]?\d+(?:\.\d+)?"),
        ]
        for kind, pattern in patterns:
            if kind not in low:
                continue
            matches = re.findall(pattern, task.prompt)
            if matches:
                answer = str(matches[-1]).rstrip(".,)")
                return SolverResult(
                    answer,
                    self.name,
                    1.0,
                    {"kind": kind, "pattern": pattern, "selected": answer},
                )
        return None


@dataclass
class LookupSolver:
    values: dict[str, str]
    name: str = "lookup"
    priority: int = 80

    def supports(self, task: Task) -> bool:
        normalized = task.prompt.strip().lower()
        return any(key.lower() in normalized for key in self.values)

    def solve(self, task: Task) -> SolverResult | None:
        normalized = task.prompt.strip().lower()
        matches = [(key, value) for key, value in self.values.items() if key.lower() in normalized]
        if not matches:
            return None
        key, answer = max(matches, key=lambda item: len(item[0]))
        return SolverResult(answer, self.name, 1.0, {"matched_key": key})


def default_solvers() -> list[Any]:
    from zmlc.solvers.structured import (
        DateDifferenceSolver,
        FinanceSolver,
        SetOperationSolver,
        UnitConversionSolver,
    )

    return [
        ExactJsonSolver(),
        ArithmeticSolver(),
        UnitConversionSolver(),
        FinanceSolver(),
        ListAggregateSolver(),
        SetOperationSolver(),
        DateDifferenceSolver(),
        StringTransformSolver(),
        RegexExtractionSolver(),
    ]
