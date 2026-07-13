import tempfile
import unittest
from pathlib import Path

from zmlc import MemoryTelemetry, Route, Router, Task
from zmlc.benchmark import BenchmarkCase, run_benchmark, write_report


class TelemetryBenchmarkTests(unittest.TestCase):
    def test_memory_telemetry_counts_avoided_calls(self) -> None:
        telemetry = MemoryTelemetry()
        router = Router(telemetry=telemetry)
        result = router.solve(
            Task(prompt="Calculate 17+25", metadata={"baseline_tokens": 80})
        )
        self.assertEqual(result.route, Route.DETERMINISTIC)
        summary = telemetry.summary()
        self.assertEqual(summary["model_calls_avoided"], 1)
        self.assertEqual(summary["estimated_tokens_saved"], 80)

    def test_release_gate_detects_savings_and_quality(self) -> None:
        report = run_benchmark(
            [
                BenchmarkCase("math", "Calculate 17+25", "math", "deterministic", "42", 100),
                BenchmarkCase("host", "Write an essay", "qa", "host_model", None, 100),
            ],
            minimum_savings_pct=40,
        )
        self.assertTrue(report.gate_passed)
        self.assertEqual(report.false_accepts, 0)
        self.assertEqual(report.token_savings_pct, 50.0)

    def test_release_gate_rejects_low_route_accuracy(self) -> None:
        report = run_benchmark(
            [
                BenchmarkCase(
                    "unsupported",
                    "Return uppercase without an explicit source.",
                    "format_strict",
                    "deterministic",
                    "VALUE",
                    100,
                )
            ],
            minimum_savings_pct=0,
        )
        self.assertFalse(report.gate_passed)
        self.assertTrue(any("route accuracy" in item for item in report.gate_failures))

    def test_report_round_trip(self) -> None:
        report = run_benchmark(
            [BenchmarkCase("math", "Calculate 2+2", "math", "deterministic", "4", 20)],
            minimum_savings_pct=0,
        )
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "report.json"
            write_report(report, destination)
            self.assertIn('"gate_passed": true', destination.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
