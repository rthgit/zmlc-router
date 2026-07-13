# Benchmarking

Run the public release gate with:

```bash
python benchmarks/generate_public_corpus.py
python -m zmlc.cli benchmark benchmarks/public_mixed_200.jsonl \
  --report build/benchmark/report.json
```

The corpus contains 200 generated, inspectable tasks across arithmetic, aggregates,
string transforms, units, bounded finance, sets, dates, and open-ended delegation.
It contains no competition-private questions or hidden expected answers.

The report is a proxy measurement. A deterministic route counts as zero model tokens;
a delegated route retains the supplied baseline estimate. Therefore the savings value
measures routing opportunity, not actual Codex billing. Real model A/B measurements
must use the same host model, settings, task set, and judge, and must report confidence
intervals and task-level results.

For a real paired A/B run, store one JSONL row per task with `task_id`,
`baseline_tokens`, `candidate_tokens`, `baseline_score`, and `candidate_score`, then run:

```bash
zmlc compare paired-results.jsonl --report build/benchmark/paired.json
```

This report computes per-task token savings, mean and median savings, quality delta,
and reproducible 95% bootstrap intervals. The paired gate permits at most one
percentage point of mean quality loss.

Release is blocked when deterministic false accepts are non-zero, deterministic answer
accuracy or route accuracy falls below 99%, or estimated savings falls below 35%.
