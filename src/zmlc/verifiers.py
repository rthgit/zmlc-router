from __future__ import annotations

import ast
import json
import re
import statistics
from datetime import date

from zmlc.models import SolverResult, Task


def _number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.10g}"


def verify_answer(task: Task, answer: str) -> bool:
    text = answer.strip()
    if not text:
        return False
    expected_type = str(task.constraints.get("type") or "").lower()
    expects_json = expected_type == "json" or (
        task.task_type == "format_strict" and "json" in task.prompt.lower()
    )
    if expects_json:
        try:
            json.loads(text)
        except json.JSONDecodeError:
            return False
    if expected_type == "number":
        try:
            float(text.rstrip("%"))
        except ValueError:
            return False
    if task.task_type == "code" and task.metadata.get("language", "python") == "python":
        try:
            ast.parse(text)
        except SyntaxError:
            return False
    return True


def verify_solver_result(task: Task, result: SolverResult) -> bool:
    """Recompute deterministic evidence before accepting a solver result."""
    if not verify_answer(task, result.answer):
        return False
    evidence = result.evidence
    try:
        if result.solver == "arithmetic":
            if evidence.get("operation") == "percent_of":
                expected = float(evidence["percent"]) * float(evidence["value"]) / 100
            else:
                from zmlc.solvers.builtin import _safe_eval

                expected = _safe_eval(str(evidence["expression"]))
            return result.answer == _number(expected)
        if result.solver == "list_aggregate":
            values = [float(value) for value in evidence["values"]]
            operation = evidence["operation"]
            functions = {
                "median": statistics.median,
                "mean": statistics.mean,
                "minimum": min,
                "maximum": max,
                "count": lambda items: len(items),
                "sum": sum,
            }
            return result.answer == _number(float(functions[operation](values)))
        if result.solver == "exact_json":
            return json.loads(result.answer) == evidence["value"]
        if result.solver == "string_transform":
            source, operation = str(evidence["source"]), evidence["operation"]
            transformations = {
                "uppercase": lambda value: value.upper(),
                "lowercase": lambda value: value.lower(),
                "reverse": lambda value: value[::-1],
                "remove spaces": lambda value: value.replace(" ", ""),
                "count words": lambda value: str(len(re.findall(r"\b\w+\b", value))),
            }
            return result.answer == transformations[operation](source)
        if result.solver == "regex_extract":
            matches = re.findall(str(evidence["pattern"]), task.prompt)
            return bool(matches) and result.answer == str(matches[-1]).rstrip(".,)")
        if result.solver == "unit_conversion":
            expected = (
                float(evidence["value"])
                * float(evidence["source_factor"])
                / float(evidence["target_factor"])
            )
            return result.answer == _number(expected)
        if result.solver == "bounded_finance":
            if evidence["operation"] == "simple_interest":
                expected = (
                    float(evidence["principal"])
                    * float(evidence["rate"])
                    / 100
                    * float(evidence["years"])
                )
            else:
                old, new = float(evidence["old"]), float(evidence["new"])
                expected = (new - old) / abs(old) * 100
            return result.answer == _number(expected)
        if result.solver == "set_operation":
            left, right = set(evidence["left"]), set(evidence["right"])
            operation = evidence["operation"]
            if operation == "union":
                expected_set = left | right
            elif operation == "intersection":
                expected_set = left & right
            else:
                expected_set = left - right
            expected = json.dumps(sorted(expected_set), separators=(",", ":"))
            return result.answer == expected
        if result.solver == "date_difference":
            start = date.fromisoformat(str(evidence["start"]))
            end = date.fromisoformat(str(evidence["end"]))
            return result.answer == str(abs((end - start).days))
    except (KeyError, TypeError, ValueError, ZeroDivisionError, SyntaxError):
        return False
    return False
