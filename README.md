# ZMLC Router

[![CI](https://github.com/rthgit/zmlc-router/actions/workflows/ci.yml/badge.svg)](https://github.com/rthgit/zmlc-router/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

ZMLC Router is a fail-closed token-efficiency layer for Codex and other AI workloads.
It attempts bounded, independently verified solvers before model generation. In the
Codex plugin, unsupported work is delegated to the active Codex model; no second model,
API key, or local model is required.

The standalone `zmlc codex` command is the real preflight path: it returns verified
deterministic answers before Codex starts and otherwise invokes the Codex installation
already present on the machine. The MCP plugin complements this with tools inside an
active task, but does not claim to erase a model call that has already begun.

This repository is the reusable framework extracted from the AMD Track 1 prototype.
It intentionally excludes benchmark IDs, retired questions, cached answers, and
competition-specific scoring logic.

## Measured release gate

The checked-in 200-task public proxy corpus currently reports:

- 100% route accuracy and deterministic answer accuracy;
- zero deterministic false accepts;
- 52.32% estimated model-token savings;
- 0.022 ms median routing latency.

These are proxy routing results, not a Codex billing claim. See
`docs/BENCHMARKING.md` for the exact methodology and limitations.

A paired five-task `codex exec` smoke A/B using the same `gpt-5.5`, low reasoning,
and read-only sandbox settings preserved 5/5 answer quality, avoided 4/5 Codex calls,
and reduced measured aggregate tokens by 81.56%. This deliberately small deterministic
smoke demonstrates call avoidance; it is not a savings forecast for arbitrary coding.

## Install

For Codex, use the signed standalone archive for Windows, macOS, or Linux described in
`docs/INSTALL.md`. The release bundle does not require Python.

For framework development:

```bash
python -m pip install -e .
```

The source MCP server works with the Python standard library. The optional MCP SDK
adds FastMCP integration:

```bash
python -m pip install -e ".[mcp]"
```

## CLI

```bash
zmlc solve "What is 17 + 25?" --type math
zmlc codex "What is 17 + 25?"
zmlc codex "Review this repository" --cd . --sandbox workspace-write
zmlc route "Return JSON only: {\"ok\": true}"
zmlc prompt "Fix the parser" --context @src/parser.py --constraint "Keep API stable" --check "Run parser tests"
zmlc benchmark benchmarks/public_mixed_200.jsonl --report build/benchmark/report.json
```

## Python

```python
from zmlc import Router, Task

router = Router()
result = router.solve(Task(prompt="What is 25% of 80?", task_type="math"))
print(result.answer)       # 20
print(result.route.value) # deterministic
```

## Add a solver

Implement `name`, `priority`, `supports(task)`, and `solve(task)`, then register it:

```python
registry.register(MyDomainSolver())
```

A solver should abstain unless it can produce a high-confidence answer. Routing to a
model is safer than returning an unverified deterministic guess.

## Architecture

```text
Task -> SolverRegistry -> Solver Verifier -> Host Model Delegation -> SolveResult
```

Local and remote providers remain optional framework integrations; they are disabled in
the default Codex plugin. See `docs/ARCHITECTURE.md` and `docs/PLUGIN.md`.
See `docs/CODEX_PREFLIGHT.md` for the model-call avoidance contract.

## Prompt engineering

`zmlc prompt` compiles compact Codex task capsules. It removes duplicate constraints,
keeps context references instead of embedding full files, defines an output contract,
and requests targeted verification without asking the model to expose chain-of-thought.

The Codex plugin exposes the same behavior through `compile_prompt` and
`estimate_tokens` MCP tools.

## Status

`1.0.0` freezes the solver and MCP contracts, ships standalone MCP and preflight CLI
binaries, and publishes both proxy and real paired smoke measurements.
