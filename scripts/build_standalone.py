from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a platform-specific standalone plugin")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    plugin_source = project_root / "plugins" / "zmlc-router"
    bundle = args.output.resolve()
    if bundle.exists():
        shutil.rmtree(bundle)
    plugin_bundle = bundle / "plugins" / "zmlc-router"
    shutil.copytree(plugin_source, plugin_bundle)
    # The standalone bundle uses the native MCP executable built below. Keeping
    # the development zipapp would duplicate the runtime and retain bytecode
    # source filenames from the build machine.
    shutil.rmtree(plugin_bundle / "runtime", ignore_errors=True)
    marketplace_path = bundle / ".agents" / "plugins" / "marketplace.json"
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)
    marketplace_path.write_text(
        json.dumps(
            {
                "name": "zmlc-public",
                "interface": {"displayName": "ZMLC Public"},
                "plugins": [
                    {
                        "name": "zmlc-router",
                        "source": {
                            "source": "local",
                            "path": "./plugins/zmlc-router",
                        },
                        "policy": {
                            "installation": "AVAILABLE",
                            "authentication": "ON_INSTALL",
                        },
                        "category": "Productivity",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    dist_dir = project_root / "build" / "standalone"
    work_dir = project_root / "build" / "pyinstaller"
    executables = (
        ("zmlc-mcp", project_root / "scripts" / "standalone_entry.py"),
        ("zmlc", project_root / "scripts" / "standalone_cli_entry.py"),
    )
    for name, entrypoint in executables:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--onefile",
                "--clean",
                "--name",
                name,
                "--distpath",
                str(dist_dir),
                "--workpath",
                str(work_dir / name),
                "--specpath",
                str(work_dir),
                "--paths",
                str(project_root / "src"),
                str(entrypoint),
            ],
            check=True,
            cwd=project_root,
        )
    bin_dir = plugin_bundle / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".exe" if sys.platform == "win32" else ""
    for name, _ in executables:
        shutil.copy2(dist_dir / f"{name}{suffix}", bin_dir / f"{name}{suffix}")
    mcp_executable_name = f"zmlc-mcp{suffix}"
    (plugin_bundle / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "zmlc-router": {
                        "command": f"./bin/{mcp_executable_name}",
                        "args": [],
                        "cwd": ".",
                        "required": True,
                        "startup_timeout_sec": 15,
                        "tool_timeout_sec": 10,
                        "supports_parallel_tool_calls": True,
                        "default_tools_approval_mode": "approve",
                        "enabled_tools": [
                            "route_task",
                            "audit_task",
                            "solve_math",
                            "validate_json",
                            "list_solvers",
                            "compile_prompt",
                            "estimate_tokens",
                            "session_metrics",
                        ],
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    developer_path = str(project_root)
    needles = {
        developer_path.encode("utf-8"),
        developer_path.encode("utf-16-le"),
    }
    for path in plugin_bundle.rglob("*"):
        if path.is_file():
            payload = path.read_bytes()
            if any(needle in payload for needle in needles):
                raise SystemExit(f"standalone bundle contains developer path: {path}")
    subprocess.run(
        [
            sys.executable,
            str(project_root / "scripts" / "smoke_standalone.py"),
            "--root",
            str(bundle),
        ],
        check=True,
        cwd=project_root,
    )
    print(bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
