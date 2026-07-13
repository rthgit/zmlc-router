# Codex Preflight

`zmlc codex` is the token-saving execution path. It attempts only bounded,
independently verified solvers before starting Codex. If no solver can safely answer,
it invokes the Codex CLI already installed on the machine with the original prompt.

```bash
zmlc codex "What is 17 + 25?"
zmlc codex "Review this repository" --cd /path/to/repository --sandbox workspace-write
```

The first command returns `42` without a model call. The second delegates to Codex.
Use `--json` or `--audit` to inspect the route and measured Codex usage:

```bash
zmlc codex --json "Return uppercase: token route"
```

The standalone executable discovers `codex` from `CODEX_BIN`, `PATH`, common CLI
locations, or the installed Codex Desktop runtime. It does not contain a model, ask
for another API key, or call a third-party provider.

## Plugin versus preflight

The Codex plugin contributes solver and prompt tools inside an existing Codex task.
That can reduce generated work, but the model is already running when it selects an
MCP tool. Consequently, MCP usage alone cannot claim that the initial model call was
avoided. Run `zmlc codex` outside the task when actual call avoidance is required.

## Fail-closed behavior

- A deterministic answer is returned only after solver-specific verification.
- Ambiguous, subjective, coding, and open-ended work delegates unchanged to Codex.
- A missing Codex executable matters only for a delegated task.
- No prompt, answer, or credential is persisted by the preflight router.

## Reproduce the paired measurement

```bash
python scripts/run_codex_ab.py benchmarks/codex_ab_smoke.jsonl \
  --report build/codex_ab/report.json \
  --model gpt-5.5 --reasoning-effort low --sandbox read-only
```

The published five-task smoke result avoided four Codex calls, preserved 5/5 answer
quality, and reduced measured aggregate input-plus-output tokens by 81.56%. This is a
small deterministic smoke test, not a forecast for arbitrary coding workloads.
