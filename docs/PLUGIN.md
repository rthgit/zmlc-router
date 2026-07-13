# Codex Plugin

The plugin lives in `plugins/zmlc-router` and contributes:

- a routing skill for choosing deterministic tools before LLM generation;
- an MCP server exposing compact routing, audit, solver, prompt, and metrics tools;
- a self-contained runtime with no repository path dependency.

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
