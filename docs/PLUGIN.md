# Codex Plugin

The plugin lives in `plugins/zmlc-router` and contributes:

- a routing skill for choosing deterministic tools before LLM generation;
- an MCP server exposing compact routing, audit, solver, prompt, and metrics tools;
- a self-contained runtime with no repository path dependency;
- a standalone `zmlc codex` preflight command that can avoid starting Codex.

Public release archives contain a native MCP executable for one operating system and
need neither Python nor framework installation. Source development can use the zipapp:

```bash
python scripts/build_plugin_runtime.py
```

`route_task` is silent and compact by default. It returns a verified deterministic
answer or `host_model` plus `delegate_to_codex`. `audit_task` exposes the full trace only
when requested. `session_metrics` returns aggregate counters without prompt contents.

The public marketplace manifest is `.agents/plugins/marketplace.json`. Release bundles
replace `.mcp.json` with a relative native executable path during the build.

The MCP server runs with the plugin directory as its working directory and an explicit
read-only tool allow-list. This is required for cached Codex plugin installations,
where the current shell directory is unrelated to the plugin root.

MCP tools are selected from inside an active model turn. Use them for verified answers,
compact prompts, and audits, but use the standalone preflight command when the metric
is avoided Codex calls or measured zero model tokens.
