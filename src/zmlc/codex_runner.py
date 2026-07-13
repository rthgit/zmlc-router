from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Callable, Sequence

from zmlc.models import Route, Task
from zmlc.policy import RoutingPolicy
from zmlc.prompting import estimate_tokens
from zmlc.router import Router


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class CodexUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class CodexPreflightResult:
    answer: str
    route: Route
    codex_invoked: bool
    exit_code: int
    usage: CodexUsage = CodexUsage()
    solver: str | None = None
    stderr: str = ""


def find_codex_binary(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    configured = os.environ.get("CODEX_BIN")
    if configured:
        return configured
    candidates: list[Path] = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        direct_desktop_cli = Path(local_app_data) / "OpenAI" / "Codex" / "bin" / "codex.exe"
        if direct_desktop_cli.is_file():
            candidates.append(direct_desktop_cli)
        candidates.extend(Path(local_app_data).glob("OpenAI/Codex/bin/*/codex.exe"))
    if candidates:
        return str(max(candidates, key=lambda path: path.stat().st_mtime))
    discovered = shutil.which("codex")
    if discovered:
        return discovered
    candidates.extend(
        path
        for path in (
            Path.home() / ".local" / "bin" / "codex",
            Path("/usr/local/bin/codex"),
            Path("/Applications/Codex.app/Contents/Resources/codex"),
        )
        if path.is_file()
    )
    if candidates:
        return str(max(candidates, key=lambda path: path.stat().st_mtime))
    raise FileNotFoundError("Codex CLI was not found; set CODEX_BIN or pass --codex-bin")


def parse_codex_jsonl(payload: str) -> tuple[str, CodexUsage]:
    answer = ""
    usage = CodexUsage()
    for line in payload.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") if isinstance(event, dict) else None
        if isinstance(item, dict) and item.get("type") == "agent_message":
            text = item.get("text")
            if isinstance(text, str):
                answer = text
        event_usage = event.get("usage") if isinstance(event, dict) else None
        if isinstance(event_usage, dict):
            usage = CodexUsage(
                input_tokens=int(event_usage.get("input_tokens") or 0),
                cached_input_tokens=int(event_usage.get("cached_input_tokens") or 0),
                output_tokens=int(event_usage.get("output_tokens") or 0),
                reasoning_output_tokens=int(event_usage.get("reasoning_output_tokens") or 0),
            )
    return answer, usage


def invoke_codex(
    prompt: str,
    *,
    codex_binary: str | None = None,
    model: str | None = None,
    reasoning_effort: str | None = None,
    sandbox: str | None = None,
    cwd: str | Path | None = None,
    configs: Sequence[str] = (),
    ephemeral: bool = True,
    runner: Runner = subprocess.run,
) -> CodexPreflightResult:
    command = [
        find_codex_binary(codex_binary),
        "exec",
        "--json",
        "--skip-git-repo-check",
    ]
    if ephemeral:
        command.append("--ephemeral")
    if model:
        command.extend(("--model", model))
    if reasoning_effort:
        command.extend(("--config", f'model_reasoning_effort="{reasoning_effort}"'))
    if sandbox:
        command.extend(("--sandbox", sandbox))
    if cwd:
        command.extend(("--cd", str(cwd)))
    for config in configs:
        command.extend(("--config", config))
    command.append(prompt)
    completed = runner(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    answer, usage = parse_codex_jsonl(completed.stdout)
    return CodexPreflightResult(
        answer=answer,
        route=Route.HOST_MODEL,
        codex_invoked=True,
        exit_code=completed.returncode,
        usage=usage,
        stderr=completed.stderr,
    )


def run_codex_preflight(
    prompt: str,
    *,
    task_type: str = "auto",
    codex_binary: str | None = None,
    model: str | None = None,
    reasoning_effort: str | None = None,
    sandbox: str | None = None,
    cwd: str | Path | None = None,
    configs: Sequence[str] = (),
    ephemeral: bool = True,
    runner: Runner = subprocess.run,
) -> CodexPreflightResult:
    router = Router(
        policy=RoutingPolicy(
            delegate_to_host=True,
            allow_local_model=False,
            allow_remote_model=False,
        )
    )
    routed = router.solve(
        Task(
            prompt=prompt,
            task_type=task_type,
            metadata={"baseline_tokens": max(1, estimate_tokens(prompt))},
        )
    )
    if routed.route == Route.DETERMINISTIC:
        return CodexPreflightResult(
            answer=routed.answer,
            route=routed.route,
            codex_invoked=False,
            exit_code=0,
            solver=routed.solver,
        )
    return invoke_codex(
        prompt,
        codex_binary=codex_binary,
        model=model,
        reasoning_effort=reasoning_effort,
        sandbox=sandbox,
        cwd=cwd,
        configs=configs,
        ephemeral=ephemeral,
        runner=runner,
    )
