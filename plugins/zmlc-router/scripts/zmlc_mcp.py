from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ARCHIVE = PLUGIN_ROOT / "runtime" / "zmlc_router.pyz"
SOURCE_ROOT = PLUGIN_ROOT.parent.parent / "src"

for candidate in (RUNTIME_ARCHIVE, SOURCE_ROOT):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from zmlc.mcp_server import main  # noqa: E402


if __name__ == "__main__":
    main()
