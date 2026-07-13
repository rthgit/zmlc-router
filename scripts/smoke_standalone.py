from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def executable(root: Path, name: str) -> Path:
    suffix = ".exe" if sys.platform == "win32" else ""
    path = root / "plugins" / "zmlc-router" / "bin" / f"{name}{suffix}"
    if not path.is_file():
        raise SystemExit(f"missing standalone executable: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a standalone ZMLC bundle")
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    cli = executable(root, "zmlc")
    mcp = executable(root, "zmlc-mcp")

    with tempfile.TemporaryDirectory() as temporary:
        unrelated_cwd = Path(temporary)
        completed = subprocess.run(
            [str(cli), "codex", "--json", "What is 17 + 25?"],
            cwd=unrelated_cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(f"standalone preflight failed: {completed.stderr}")
        result = json.loads(completed.stdout)
        if result.get("answer") != "42" or result.get("codex_invoked") is not False:
            raise SystemExit(f"unexpected preflight result: {result}")

        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "solve_math", "arguments": {"prompt": "144 / 12"}},
            },
        ]
        payload = "\n".join(json.dumps(request) for request in requests) + "\n"
        completed = subprocess.run(
            [str(mcp)],
            cwd=unrelated_cwd,
            input=payload,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(f"standalone MCP failed: {completed.stderr}")
        responses = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
        if len(responses) != 3:
            raise SystemExit(f"expected three MCP responses, received {len(responses)}")
        tool_names = {
            tool["name"] for tool in responses[1].get("result", {}).get("tools", [])
        }
        if not {"route_task", "solve_math", "compile_prompt"}.issubset(tool_names):
            raise SystemExit(f"missing MCP tools: {sorted(tool_names)}")
        content = responses[2]["result"]["content"][0]["text"]
        solved = json.loads(content)
        if solved.get("answer") != "12" or solved.get("route") != "deterministic":
            raise SystemExit(f"unexpected MCP solve result: {solved}")

    print("STANDALONE SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
