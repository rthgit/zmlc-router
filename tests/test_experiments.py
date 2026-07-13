import tempfile
import unittest
from pathlib import Path

from zmlc.experiments import (
    PairedObservation,
    compare_observations,
    load_observations,
    write_paired_report,
)


class PairedExperimentTests(unittest.TestCase):
    def test_paired_gate_passes_measured_savings_without_quality_loss(self) -> None:
        rows = [
            PairedObservation(str(index), 100, 50, 1.0, 1.0) for index in range(20)
        ]
        report = compare_observations(rows, bootstrap_samples=200)
        self.assertTrue(report.gate_passed)
        self.assertEqual(report.median_token_savings_pct, 50.0)
        self.assertEqual(report.quality_delta, 0.0)

    def test_paired_gate_rejects_quality_regression(self) -> None:
        rows = [PairedObservation("task", 100, 10, 1.0, 0.5)]
        report = compare_observations(rows)
        self.assertFalse(report.gate_passed)
        self.assertTrue(any("quality delta" in item for item in report.gate_failures))

    def test_paired_report_round_trip(self) -> None:
        report = compare_observations([PairedObservation("task", 100, 50, 1.0, 1.0)])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "paired.json"
            write_paired_report(report, path)
            loaded = load_observations(
                self._write_observations(Path(directory) / "rows.jsonl")
            )
            self.assertTrue(path.is_file())
            self.assertEqual(loaded[0].task_id, "task")

    @staticmethod
    def _write_observations(path: Path) -> Path:
        path.write_text(
            '{"task_id":"task","baseline_tokens":100,"candidate_tokens":50,'
            '"baseline_score":1.0,"candidate_score":1.0}\n',
            encoding="utf-8",
        )
        return path


if __name__ == "__main__":
    unittest.main()
