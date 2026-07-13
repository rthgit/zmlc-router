import unittest

from zmlc.codex_ab import CodexAbCase, answer_matches, build_codex_ab_report
from zmlc.codex_runner import CodexPreflightResult, CodexUsage
from zmlc.models import Route


def _result(answer: str, tokens: int, route: Route, invoked: bool) -> CodexPreflightResult:
    return CodexPreflightResult(
        answer=answer,
        route=route,
        codex_invoked=invoked,
        exit_code=0,
        usage=CodexUsage(input_tokens=tokens),
    )


class CodexAbTests(unittest.TestCase):
    def test_json_comparison_is_semantic(self) -> None:
        self.assertTrue(answer_matches('{"x": 1}', '{"x":1}', "json"))

    def test_report_uses_real_usage_and_quality_gate(self) -> None:
        cases = [
            CodexAbCase("a", "What is 2+2?", "4"),
            CodexAbCase("b", "Return blue", "blue"),
        ]
        baseline = [
            _result("4", 100, Route.HOST_MODEL, True),
            _result("blue", 100, Route.HOST_MODEL, True),
        ]
        candidate = [
            _result("4", 0, Route.DETERMINISTIC, False),
            _result("blue", 100, Route.HOST_MODEL, True),
        ]
        report = build_codex_ab_report(cases, baseline, candidate)
        self.assertEqual(report["aggregate_savings_pct"], 50.0)
        self.assertEqual(report["codex_calls_avoided"], 1)
        self.assertTrue(report["gate"]["passed"])


if __name__ == "__main__":
    unittest.main()
