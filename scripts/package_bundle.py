from __future__ import annotations

import argparse
import hashlib
import shutil
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
    archive.with_suffix(archive.suffix + ".sha256").write_text(
        f"{digest}  {archive.name}\n", encoding="ascii"
    )
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
