# Privacy

The Codex plugin processes routing inputs in the local MCP process. Default telemetry
stores only route, solver, token estimate, latency, and status counters in memory. It
does not store prompt text, answers, credentials, file contents, or user identifiers.

Full decision traces are returned only through the explicit `audit_task` tool or when
`audit=true` is requested. They are not persisted by the default telemetry sink.

The plugin does not start a local model and does not make remote model calls. When a
task is unsupported, it delegates to the active Codex model already serving the task.
