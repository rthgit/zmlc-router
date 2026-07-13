# ZMLC Product Contract

## Mission

Move bounded AI work from probabilistic generation to verified computation while
preserving a safe fallback for genuinely lossy tasks.

## Non-negotiable invariants

- A solver may abstain; it must never guess outside its declared contract.
- Deterministic acceptance requires verification and calibrated confidence.
- Every answer records route and token usage; full traces are exposed only on request.
- Remote fallback receives the original task, not a lossy paraphrase.
- Benchmark-specific IDs, prompts, expected answers, and caches are forbidden in core.
- Secrets are read from runtime configuration and are never stored in profiles or traces.

## Package boundaries

- `zmlc.models`: stable data contracts.
- `zmlc.solvers`: deterministic capabilities.
- `zmlc.registry`: solver discovery and priority.
- `zmlc.verifiers`: answer acceptance.
- `zmlc.providers`: local and remote model adapters.
- `zmlc.router`: policy execution and audit trace.
- `zmlc.mcp_server`: Codex and agent-tool integration.

## Release status

The framework includes opt-in entry-point discovery, bounded batch/async routing,
solver-specific verification, content-free telemetry, prompt compilation, a public
conformance corpus, and signed standalone release automation. Remaining work for 1.0
is a published paired Codex A/B run; see `docs/ROADMAP_PUBLIC.md`.
