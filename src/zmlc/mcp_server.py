from __future__ import annotations

import json
import sys
from typing import Any

from zmlc import __version__
from zmlc.models import Task
from zmlc.policy import RoutingPolicy
from zmlc.prompting import (
    PromptSpec,
    compile_prompt as build_prompt,
    estimate_tokens as estimate_token_count,
)
from zmlc.router import Router
from zmlc.telemetry import MemoryTelemetry


def _payload(result: Any, *, audit: bool = True) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": result.task_id,
        "answer": result.answer,
        "route": result.route.value,
        "confidence": result.confidence,
        "tokens": result.input_tokens + result.output_tokens,
    }
    if result.solver:
        payload["solver"] = result.solver
    if audit:
        payload.update(
            {
                "provider": result.provider,
                "model": result.model,
                "latency_ms": result.latency_ms,
                "estimated_tokens_saved": result.estimated_tokens_saved,
                "trace": [event.__dict__ for event in result.trace],
            }
        )
    if result.route.value == "host_model":
        payload["action"] = "delegate_to_codex"
    return payload


def _tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "route_task",
            "description": "Route a task through verified deterministic solvers or delegate it to Codex.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "task_type": {"type": "string", "default": "auto"},
                    "audit": {"type": "boolean", "default": False},
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "audit_task",
            "description": "Route a task and return the complete local decision trace.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "task_type": {"type": "string", "default": "auto"},
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "solve_math",
            "description": "Solve a bounded arithmetic task without an LLM when possible.",
            "inputSchema": {
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        },
        {
            "name": "validate_json",
            "description": "Validate a JSON value without model inference.",
            "inputSchema": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
            },
        },
        {
            "name": "list_solvers",
            "description": "List deterministic solvers in execution priority order.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "compile_prompt",
            "description": "Compile a compact Codex task capsule with explicit output and verification contracts.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "objective": {"type": "string"},
                    "context": {"type": "array", "items": {"type": "string"}},
                    "constraints": {"type": "array", "items": {"type": "string"}},
                    "output": {"type": "string"},
                    "verification": {"type": "array", "items": {"type": "string"}},
                    "mode": {"type": "string", "default": "auto"},
                    "source": {"type": "string", "default": ""},
                },
                "required": ["objective"],
            },
        },
        {
            "name": "estimate_tokens",
            "description": "Estimate prompt tokens for comparing compact prompt variants.",
            "inputSchema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
        {
            "name": "session_metrics",
            "description": "Return aggregate local routing metrics without prompt contents.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def _call_tool(router: Router, name: str, arguments: dict[str, Any]) -> str:
    if name == "route_task":
        prompt = str(arguments.get("prompt") or "")
        task = Task(
            prompt=prompt,
            task_type=str(arguments.get("task_type") or "auto"),
            metadata={"baseline_tokens": estimate_token_count(prompt)},
        )
        result = router.solve(task)
        payload = _payload(result, audit=bool(arguments.get("audit", False)))
        return json.dumps(payload)
    if name == "audit_task":
        return _call_tool(router, "route_task", {**arguments, "audit": True})
    if name == "solve_math":
        return json.dumps(
            _payload(
                router.solve(Task(prompt=str(arguments.get("prompt") or ""), task_type="math")),
                audit=False,
            )
        )
    if name == "validate_json":
        try:
            parsed = json.loads(str(arguments.get("value") or ""))
        except json.JSONDecodeError as exc:
            return json.dumps({"valid": False, "error": str(exc)})
        return json.dumps({"valid": True, "value": parsed})
    if name == "list_solvers":
        return json.dumps(router.registry.names())
    if name == "compile_prompt":
        compiled = build_prompt(
            PromptSpec(
                objective=str(arguments.get("objective") or ""),
                context=tuple(arguments.get("context") or ()),
                constraints=tuple(arguments.get("constraints") or ()),
                output=str(arguments.get("output") or "Return only the requested result."),
                verification=tuple(arguments.get("verification") or ()),
                mode=str(arguments.get("mode") or "auto"),
            ),
            source=str(arguments.get("source") or ""),
        )
        return json.dumps(
            {
                "prompt": compiled.text,
                "estimated_tokens": compiled.estimated_tokens,
                "source_tokens": compiled.source_tokens,
                "estimated_savings": compiled.estimated_savings,
            }
        )
    if name == "estimate_tokens":
        text = str(arguments.get("text") or "")
        return json.dumps({"estimated_tokens": estimate_token_count(text), "characters": len(text)})
    if name == "session_metrics":
        telemetry = getattr(router, "telemetry", None)
        summary = telemetry.summary() if hasattr(telemetry, "summary") else {}
        return json.dumps(summary)
    raise ValueError(f"unknown tool: {name}")


def _fallback_stdio_server() -> None:
    """Small MCP JSON-RPC server for installations without the optional SDK."""
    router = Router(
        policy=RoutingPolicy(
            delegate_to_host=True,
            allow_local_model=False,
            allow_remote_model=False,
        ),
        telemetry=MemoryTelemetry(),
    )
    for line in sys.stdin:
        request: dict[str, Any] = {}
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "zmlc-router", "version": __version__},
                }
            elif method == "tools/list":
                result = {"tools": _tools()}
            elif method == "tools/call":
                params = request.get("params") or {}
                output = _call_tool(router, str(params.get("name") or ""), params.get("arguments") or {})
                result = {"content": [{"type": "text", "text": output}], "isError": False}
            elif method == "ping":
                result = {}
            elif method and method.startswith("notifications/"):
                continue
            else:
                raise ValueError(f"unsupported method: {method}")
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if isinstance(request, dict) else None,
                "error": {"code": -32603, "message": str(exc)},
            }
        print(json.dumps(response, separators=(",", ":")), flush=True)


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        _fallback_stdio_server()
        return

    server = FastMCP("zmlc-router")
    router = Router(
        policy=RoutingPolicy(
            delegate_to_host=True,
            allow_local_model=False,
            allow_remote_model=False,
        ),
        telemetry=MemoryTelemetry(),
    )

    @server.tool()
    def route_task(prompt: str, task_type: str = "auto", audit: bool = False) -> str:
        """Route a task through deterministic solvers or delegate it to Codex."""
        return _call_tool(
            router,
            "route_task",
            {"prompt": prompt, "task_type": task_type, "audit": audit},
        )

    @server.tool()
    def audit_task(prompt: str, task_type: str = "auto") -> str:
        """Route a task and return the complete local decision trace."""
        return _call_tool(router, "audit_task", {"prompt": prompt, "task_type": task_type})

    @server.tool()
    def solve_math(prompt: str) -> str:
        """Solve a bounded arithmetic task without an LLM when possible."""
        return _call_tool(router, "solve_math", {"prompt": prompt})

    @server.tool()
    def validate_json(value: str) -> str:
        """Validate and normalize a JSON value without model inference."""
        return _call_tool(router, "validate_json", {"value": value})

    @server.tool()
    def list_solvers() -> str:
        """List deterministic solver names in execution priority order."""
        return _call_tool(router, "list_solvers", {})

    @server.tool()
    def compile_prompt(
        objective: str,
        context: list[str] | None = None,
        constraints: list[str] | None = None,
        output: str = "Return only the requested result.",
        verification: list[str] | None = None,
        mode: str = "auto",
        source: str = "",
    ) -> str:
        """Compile a compact task capsule for Codex."""
        return _call_tool(
            router,
            "compile_prompt",
            {
                "objective": objective,
                "context": context or [],
                "constraints": constraints or [],
                "output": output,
                "verification": verification or [],
                "mode": mode,
                "source": source,
            },
        )

    @server.tool()
    def estimate_tokens(text: str) -> str:
        """Estimate prompt tokens without sending text to a model."""
        return _call_tool(router, "estimate_tokens", {"text": text})

    @server.tool()
    def session_metrics() -> str:
        """Return aggregate local routing metrics without prompt contents."""
        return _call_tool(router, "session_metrics", {})

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
