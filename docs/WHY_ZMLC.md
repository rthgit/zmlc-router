# Why ZMLC

Model generation is useful for ambiguous work. It is unnecessary for bounded work that
ordinary code can solve and independently verify. ZMLC puts a fail-closed preflight in
front of Codex: a verified deterministic result returns immediately; every unsupported
task is delegated to the user's existing Codex installation unchanged.

## What it changes

```text
Without ZMLC: task -> Codex model -> answer
With ZMLC:    task -> verified solver -> answer
                        |
                        +-- abstain -> Codex model -> answer
```

The abstention boundary is the product. A solver may answer only when its output can be
checked independently. ZMLC does not add a second model, API key, local model, hidden
provider, or model cache.

## What is measured

On the checked-in 200-task proxy corpus, the current release records 100% routing and
supported-answer accuracy, zero deterministic false accepts, 52.32% estimated token
savings, and 0.031 ms median routing latency.

In a paired five-task Codex smoke test, answer quality remained 5/5, four Codex calls
were avoided, and measured aggregate tokens fell by 81.56%.

These are proxy results and a deliberately small deterministic smoke test. They are not
a billing claim or a forecast for arbitrary coding workloads. All cases, outputs, and
methodology are checked into the repository.

## MCP versus preflight

The MCP plugin exposes solvers, compact prompt compilation, audits, and metrics inside
an active Codex task. It can reduce work within that task, but the model call has already
started. The standalone `zmlc codex` command runs before Codex and can avoid the entire
call. Unsupported work is passed to Codex without semantic rewriting.
