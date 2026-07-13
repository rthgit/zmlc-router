import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from zmlc.codex_runner import find_codex_binary, parse_codex_jsonl, run_codex_preflight
from zmlc.models import Route


class CodexRunnerTests(unittest.TestCase):
    def test_deterministic_preflight_never_invokes_codex(self) -> None:
        def forbidden_runner(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("Codex must not run for deterministic tasks")

        result = run_codex_preflight("What is 17 + 25?", runner=forbidden_runner)
        self.assertEqual(result.answer, "42")
        self.assertEqual(result.route, Route.DETERMINISTIC)
        self.assertFalse(result.codex_invoked)
        self.assertEqual(result.usage.total_tokens, 0)

    def test_lossy_task_uses_existing_codex_cli(self) -> None:
        seen: list[list[str]] = []

        def fake_runner(command, **kwargs):  # type: ignore[no-untyped-def]
            seen.append(command)
            events = [
                {"type": "item.completed", "item": {"type": "agent_message", "text": "blue"}},
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 100,
                        "cached_input_tokens": 20,
                        "output_tokens": 5,
                        "reasoning_output_tokens": 1,
                    },
                },
            ]
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="\n".join(json.dumps(event) for event in events),
                stderr="",
            )

        result = run_codex_preflight(
            "Return only the word blue.",
            codex_binary="codex-test",
            model="model-test",
            reasoning_effort="low",
            runner=fake_runner,
        )
        self.assertTrue(result.codex_invoked)
        self.assertEqual(result.answer, "blue")
        self.assertEqual(result.usage.total_tokens, 105)
        self.assertEqual(
            seen[0][0:4],
            ["codex-test", "exec", "--json", "--skip-git-repo-check"],
        )

    def test_parser_uses_last_agent_message_and_usage(self) -> None:
        payload = "\n".join(
            [
                json.dumps(
                    {"type": "item.completed", "item": {"type": "agent_message", "text": "a"}}
                ),
                json.dumps(
                    {"type": "item.completed", "item": {"type": "agent_message", "text": "b"}}
                ),
                json.dumps(
                    {"type": "turn.completed", "usage": {"input_tokens": 7, "output_tokens": 2}}
                ),
            ]
        )
        answer, usage = parse_codex_jsonl(payload)
        self.assertEqual(answer, "b")
        self.assertEqual(usage.total_tokens, 9)

    def test_finds_codex_desktop_runtime_without_fixed_version_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            local_app_data = Path(temporary)
            older = local_app_data / "OpenAI" / "Codex" / "bin" / "old" / "codex.exe"
            newer = local_app_data / "OpenAI" / "Codex" / "bin" / "new" / "codex.exe"
            older.parent.mkdir(parents=True)
            newer.parent.mkdir(parents=True)
            older.write_bytes(b"old")
            newer.write_bytes(b"new")
            os.utime(older, (1, 1))
            os.utime(newer, (2, 2))
            with (
                patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}, clear=False),
                patch(
                    "zmlc.codex_runner.shutil.which",
                    return_value="C:/WindowsApps/codex.exe",
                ),
            ):
                self.assertEqual(find_codex_binary(), str(newer))


if __name__ == "__main__":
    unittest.main()
