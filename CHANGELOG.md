# Changelog

## Unreleased

## 1.0.1

- Added a dedicated ZMLC routing icon for the composer and plugin catalog.
- Added a reproducible renderer and transparent 64 px and 512 px PNG assets.

## 1.0.0

- Added `zmlc codex`, a fail-closed preflight that avoids Codex calls for verified tasks.
- Added automatic discovery of installed Codex CLI and Codex Desktop runtimes.
- Added a real paired `codex exec` A/B gate and published task-level smoke results.
- Added a standalone `zmlc` executable to every platform release bundle.
- Fixed MCP startup from cached plugin directories and approved the local read-only tool set.
- Documented the distinction between in-task MCP assistance and actual call avoidance.

## 0.9.1

- Removed the unused Python zipapp from native standalone plugin bundles.
- Added a release gate that rejects absolute build-machine paths in standalone artifacts.
- Fixed duplicate package version metadata.

## 0.9.0

- Added a host-model delegation route for Codex without a second model.
- Added solver-specific verification, telemetry, compact MCP responses, and audit tools.
- Added unit, finance, set, and date solvers with fail-closed behavior.
- Added a 200-task public proxy benchmark and hard release gate.
- Added self-contained zipapp and signed cross-platform standalone release workflows.
