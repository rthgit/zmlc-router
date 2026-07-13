from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a checksummed standalone plugin archive")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    archive = Path(shutil.make_archive(str(output.with_suffix("")), "zip", source.parent, source.name))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(
        f"{digest}  {archive.name}\n", encoding="ascii"
    )
    manifest = json.loads(
        (source / "plugins" / "zmlc-router" / ".codex-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        )
    )
    expected_version = str(manifest["version"]).split("+", 1)[0]
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("smoke_release_archive.py")),
            "--archive",
            str(archive),
            "--sha256",
            str(checksum),
            "--expected-version",
            expected_version,
        ],
        check=True,
    )
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
