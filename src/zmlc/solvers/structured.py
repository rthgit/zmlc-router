from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date

from zmlc.models import SolverResult, Task


def _number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.10g}"


_UNIT_ALIASES = {
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "m": "m",
    "meter": "m",
    "meters": "m",
    "km": "km",
    "kilometer": "km",
    "kilometers": "km",
    "mg": "mg",
    "milligram": "mg",
    "milligrams": "mg",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
}
_UNIT_FACTORS = {
    "mm": ("length", 0.001),
    "cm": ("length", 0.01),
    "m": ("length", 1.0),
    "km": ("length", 1000.0),
    "mg": ("mass", 0.001),
    "g": ("mass", 1.0),
    "kg": ("mass", 1000.0),
}


@dataclass
class UnitConversionSolver:
    name: str = "unit_conversion"
    priority: int = 98

    def supports(self, task: Task) -> bool:
        low = task.prompt.lower()
        return "convert" in low and (" to " in low or " into " in low)

    def solve(self, task: Task) -> SolverResult | None:
        match = re.search(
            r"(?i)convert\s+([-+]?\d+(?:\.\d+)?)\s*([a-z]+)\s+(?:to|into)\s+([a-z]+)",
            task.prompt,
        )
        if not match:
            return None
        value = float(match.group(1))
        source = _UNIT_ALIASES.get(match.group(2).lower())
        target = _UNIT_ALIASES.get(match.group(3).lower())
        if source not in _UNIT_FACTORS or target not in _UNIT_FACTORS:
            return None
        source_dimension, source_factor = _UNIT_FACTORS[source]
        target_dimension, target_factor = _UNIT_FACTORS[target]
        if source_dimension != target_dimension:
            return None
        converted = value * source_factor / target_factor
        return SolverResult(
            _number(converted),
            self.name,
            1.0,
            {"value": value, "source_factor": source_factor, "target_factor": target_factor},
        )


@dataclass
class FinanceSolver:
    name: str = "bounded_finance"
    priority: int = 97

    def supports(self, task: Task) -> bool:
        low = task.prompt.lower()
        return "simple interest" in low or "percentage change" in low

    def solve(self, task: Task) -> SolverResult | None:
        low = task.prompt.lower()
        if "simple interest" in low:
            match = re.search(
                r"(?i)(?:principal(?:\s+of)?|on)\s*[$]?\s*([-+]?\d+(?:\.\d+)?)"
                r".*?([-+]?\d+(?:\.\d+)?)\s*%.*?([-+]?\d+(?:\.\d+)?)\s*years?",
                task.prompt,
            )
            if not match:
                return None
            principal, rate, years = map(float, match.groups())
            answer = principal * rate / 100 * years
            return SolverResult(
                _number(answer),
                self.name,
                1.0,
                {"operation": "simple_interest", "principal": principal, "rate": rate, "years": years},
            )
        match = re.search(
            r"(?i)percentage change\s+from\s+([-+]?\d+(?:\.\d+)?)\s+to\s+([-+]?\d+(?:\.\d+)?)",
            task.prompt,
        )
        if not match:
            return None
        old, new = map(float, match.groups())
        if old == 0:
            return None
        answer = (new - old) / abs(old) * 100
        return SolverResult(
            _number(answer),
            self.name,
            1.0,
            {"operation": "percentage_change", "old": old, "new": new},
        )


@dataclass
class SetOperationSolver:
    name: str = "set_operation"
    priority: int = 94

    def supports(self, task: Task) -> bool:
        low = task.prompt.lower()
        return sum(1 for char in task.prompt if char == "[") >= 2 and any(
            cue in low for cue in ("union", "intersection", "set difference")
        )

    def solve(self, task: Task) -> SolverResult | None:
        arrays = re.findall(r"\[[^\[\]]*\]", task.prompt)
        if len(arrays) < 2:
            return None
        try:
            left, right = json.loads(arrays[0]), json.loads(arrays[1])
            left_set, right_set = set(left), set(right)
        except (json.JSONDecodeError, TypeError):
            return None
        low = task.prompt.lower()
        if "intersection" in low:
            result, operation = left_set & right_set, "intersection"
        elif "set difference" in low:
            result, operation = left_set - right_set, "difference"
        elif "union" in low:
            result, operation = left_set | right_set, "union"
        else:
            return None
        try:
            answer_values = sorted(result)
        except TypeError:
            return None
        return SolverResult(
            json.dumps(answer_values, separators=(",", ":")),
            self.name,
            1.0,
            {"operation": operation, "left": left, "right": right},
        )


@dataclass
class DateDifferenceSolver:
    name: str = "date_difference"
    priority: int = 105

    def supports(self, task: Task) -> bool:
        low = task.prompt.lower()
        return "days between" in low and len(re.findall(r"\d{4}-\d{2}-\d{2}", task.prompt)) == 2

    def solve(self, task: Task) -> SolverResult | None:
        values = re.findall(r"\d{4}-\d{2}-\d{2}", task.prompt)
        try:
            start, end = (date.fromisoformat(value) for value in values)
        except ValueError:
            return None
        answer = abs((end - start).days)
        return SolverResult(
            str(answer), self.name, 1.0, {"start": start.isoformat(), "end": end.isoformat()}
        )
