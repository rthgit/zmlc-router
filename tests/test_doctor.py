import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from zmlc.doctor import format_doctor, run_doctor


class DoctorTests(unittest.TestCase):
    def test_doctor_passes_with_codex_and_plugin_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plugin = Path(temporary)
            (plugin / ".codex-plugin").mkdir()
            (plugin / ".codex-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
            (plugin / ".mcp.json").write_text("{}", encoding="utf-8")
            (plugin / "bin").mkdir()
            (plugin / "bin" / "zmlc-mcp.exe").write_bytes(b"binary")
            with patch("zmlc.doctor.find_codex_binary", return_value="codex-test"):
                report = run_doctor(plugin_root=plugin)
        self.assertTrue(report["ok"])
        self.assertIn("[PASS] codex", format_doctor(report))
        self.assertIn("READY", format_doctor(report))

    def test_doctor_fails_closed_when_installation_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch(
                "zmlc.doctor.find_codex_binary",
                side_effect=FileNotFoundError("missing codex"),
            ):
                report = run_doctor(plugin_root=Path(temporary))
        self.assertFalse(report["ok"])
        self.assertIn("[FAIL] codex", format_doctor(report))
        self.assertIn("NOT READY", format_doctor(report))


if __name__ == "__main__":
    unittest.main()
