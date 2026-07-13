# Architecture

The framework separates five contracts:

1. `Task` describes input and output constraints.
2. `Solver` handles closed, verifiable operations and may abstain.
3. `Verifier` checks structural correctness before acceptance.
4. `Host delegation` returns unsupported work to the active Codex model without a
   second model call.
5. Optional `Provider` adapters support non-Codex deployments.
6. `Router` applies policy and emits a compact result or an on-demand audit trace.

Solver confidence is not a substitute for verification. Every accepted solver attaches
recomputable evidence and passes its solver-specific verifier. Any ambiguity delegates.

```text
                         +-> verified deterministic answer
Task -> candidates -> verifier
                         +-> host_model / delegate_to_codex
```

Default telemetry is in-memory and content-free. It records route, status, latency,
estimated token savings, and avoided model calls, but never prompt or answer text.

Competition-specific rules belong in separate profile packages, never in `zmlc-core`.
