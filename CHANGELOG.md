# Changelog

## Unreleased

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
