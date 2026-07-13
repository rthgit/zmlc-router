from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys

from zmlc.codex_runner import find_codex_binary, run_codex_preflight


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    passed: bool
    detail: str


def _plugin_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parents[2] / "plugins" / "zmlc-router"


def run_doctor(*, plugin_root: Path | None = None) -> dict[str, object]:
    checks: list[DoctorCheck] = []
    try:
        codex = find_codex_binary()
        checks.append(DoctorCheck("codex", True, codex))
    except FileNotFoundError as error:
        checks.append(DoctorCheck("codex", False, str(error)))

    root = (plugin_root or _plugin_root()).resolve()
    manifest = root / ".codex-plugin" / "plugin.json"
    checks.append(
        DoctorCheck(
            "plugin_manifest",
            manifest.is_file(),
            str(manifest) if manifest.is_file() else f"missing: {manifest}",
        )
    )
    mcp_config = root / ".mcp.json"
    checks.append(
        DoctorCheck(
            "mcp_config",
            mcp_config.is_file(),
            str(mcp_config) if mcp_config.is_file() else f"missing: {mcp_config}",
        )
    )
    mcp_candidates = tuple((root / "bin").glob("zmlc-mcp*")) + (
        root / "runtime" / "zmlc_router.pyz",
    )
    mcp_runtime = next((path for path in mcp_candidates if path.is_file()), None)
    checks.append(
        DoctorCheck(
            "mcp_runtime",
            mcp_runtime is not None,
            str(mcp_runtime) if mcp_runtime else "standalone binary or source zipapp not found",
        )
    )

    result = run_codex_preflight("What is 17 + 25?")
    deterministic_ok = result.answer == "42" and not result.codex_invoked
    checks.append(
        DoctorCheck(
            "deterministic_preflight",
            deterministic_ok,
            f"answer={result.answer!r}, codex_invoked={result.codex_invoked}",
        )
    )
    return {
        "ok": all(check.passed for check in checks),
        "plugin_root": str(root),
        "checks": [asdict(check) for check in checks],
    }


def format_doctor(report: dict[str, object]) -> str:
    lines = ["ZMLC doctor"]
    for check in report["checks"]:  # type: ignore[index]
        mark = "PASS" if check["passed"] else "FAIL"  # type: ignore[index]
        lines.append(f"[{mark}] {check['name']}: {check['detail']}")  # type: ignore[index]
    lines.append("READY" if report["ok"] else "NOT READY")
    return "\n".join(lines)


def json_doctor(report: dict[str, object]) -> str:
    return json.dumps(report, indent=2)
