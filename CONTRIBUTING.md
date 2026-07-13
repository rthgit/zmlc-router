# Contributing

New solvers must include:

1. a narrow `supports` predicate;
2. explicit input and output assumptions;
3. deterministic execution or independently verifiable evidence;
4. positive, negative, ambiguity, and adversarial tests;
5. abstention when the contract cannot be proven.

Solver pull requests must also demonstrate solver-specific verification. A generic
format check is not sufficient. Rules tied to benchmark IDs, hidden-task wording, or
memorized expected answers are rejected.

Run before opening a change:

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
python benchmarks/generate_public_corpus.py
python -m zmlc.cli benchmark benchmarks/public_mixed_200.jsonl --report build/benchmark/report.json
python scripts/build_plugin_runtime.py
python scripts/check_release.py
```

Do not add benchmark-specific expected answers to the framework package.
