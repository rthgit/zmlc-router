from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {".git", ".venv", "_wheel_smoke", "build", "dist", "__pycache__"}
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:\\(?:Users|workspace|tmp)\\", re.IGNORECASE),
    re.compile(r"/(?:home|Users|workspace)/[^\s\"']+", re.IGNORECASE),
)
SECRET_PATTERNS = (
    re.compile(r"\bfw_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)(?:api[_-]?key|token)\s*[:=]\s*[\"'][^\"']{12,}[\"']"),
)


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a public ZMLC release tree")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    failures: list[str] = []
    developer_path_needles = {
        str(root).encode("utf-8"),
        str(root).replace("\\", "/").encode("utf-8"),
        str(root).encode("utf-16-le"),
    }

    required = (
        "LICENSE",
        "README.md",
        "SECURITY.md",
        "docs/INSTALL.md",
        "docs/PRIVACY.md",
        "benchmarks/public_mixed_200.jsonl",
        "benchmarks/results/codex_ab_smoke_gpt-5.5.json",
        "build/benchmark/report.json",
        "plugins/zmlc-router/.codex-plugin/plugin.json",
        "plugins/zmlc-router/.mcp.json",
        "plugins/zmlc-router/runtime/zmlc_router.pyz",
    )
    for relative in required:
        if not (root / relative).is_file():
            fail(f"missing required file: {relative}", failures)

    corpus = root / "benchmarks/public_mixed_200.jsonl"
    if corpus.is_file():
        rows = [line for line in corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) != 200:
            fail(f"public corpus must contain 200 rows, found {len(rows)}", failures)

    report_path = root / "build/benchmark/report.json"
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if not report.get("gate_passed"):
            fail("public benchmark release gate failed", failures)
        if report.get("false_accepts") != 0:
            fail("public benchmark contains deterministic false accepts", failures)

    codex_report_path = root / "benchmarks/results/codex_ab_smoke_gpt-5.5.json"
    if codex_report_path.is_file():
        codex_report = json.loads(codex_report_path.read_text(encoding="utf-8"))
        if not (codex_report.get("gate") or {}).get("passed"):
            fail("real Codex A/B gate failed", failures)
        if codex_report.get("quality_delta", -1) < -0.01:
            fail("real Codex A/B quality loss exceeds one percentage point", failures)

    plugin_path = root / "plugins/zmlc-router/.codex-plugin/plugin.json"
    if plugin_path.is_file():
        plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
        if plugin.get("name") != "zmlc-router":
            fail("plugin name must be zmlc-router", failures)
        if plugin.get("repository") != "https://github.com/rthgit/zmlc-router":
            fail("plugin repository must point to the public framework repository", failures)

    mcp_path = root / "plugins/zmlc-router/.mcp.json"
    if mcp_path.is_file():
        mcp_document = json.loads(mcp_path.read_text(encoding="utf-8"))
        servers = mcp_document.get("mcpServers") or mcp_document.get("mcp_servers") or {}
        server = servers.get("zmlc-router") or {}
        if server.get("cwd") != ".":
            fail("plugin MCP server must resolve its command from plugin-root cwd", failures)
        if server.get("default_tools_approval_mode") != "approve":
            fail("local read-only MCP tools must be non-interactive in codex exec", failures)

    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        if "plugins" in path.parts:
            payload = path.read_bytes()
            if any(needle in payload for needle in developer_path_needles):
                fail(f"absolute build path in plugin artifact: {path.relative_to(root)}", failures)
                continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(root)
        for pattern in ABSOLUTE_PATH_PATTERNS:
            if pattern.search(text):
                fail(f"absolute developer path in {relative}", failures)
                break
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"possible secret in {relative}", failures)
                break

    if failures:
        print("RELEASE CHECK FAILED", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1
    print("RELEASE CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
