from __future__ import annotations

import argparse
import shutil
import tempfile
import zipapp
from pathlib import Path


def build_runtime(project_root: Path, output: Path) -> None:
    source_package = project_root / "src" / "zmlc"
    if not source_package.is_dir():
        raise SystemExit(f"missing package: {source_package}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="zmlc-runtime-") as temp_dir:
        staging = Path(temp_dir)
        shutil.copytree(source_package, staging / "zmlc")
        (staging / "__main__.py").write_text(
            "from zmlc.mcp_server import main\n\nif __name__ == '__main__':\n    main()\n",
            encoding="utf-8",
        )
        zipapp.create_archive(staging, output, interpreter="/usr/bin/env python3")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the self-contained ZMLC MCP zipapp")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("plugins/zmlc-router/runtime/zmlc_router.pyz"),
    )
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    output = args.output if args.output.is_absolute() else project_root / args.output
    build_runtime(project_root, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
