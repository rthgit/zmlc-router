# Token-Efficient Prompt Policy

## Task capsule

Use only sections that change execution:

```text
TASK
<one concrete objective>

CONTEXT
- @only/relevant/path

CONSTRAINTS
- <behavioral or compatibility requirement>

OUTPUT
<exact artifact or response contract>

DONE WHEN
- <targeted verification>
```

## Remove

- role-play titles and years of experience;
- praise, greetings, motivational language, and closing offers;
- repeated descriptions of the same objective;
- universal ToT/GoT/SoT instructions;
- requests to print chain-of-thought;
- entire files when a path, symbol, diff, or line reference is sufficient;
- examples that merely restate an already precise schema.

## Keep

- irreversible constraints;
- target paths and symbols;
- input/output schemas;
- acceptance tests;
- security, compatibility, and performance boundaries;
- ambiguity that materially changes implementation.

## Codex coding workflow

1. Search narrowly using filenames and symbols.
2. Read only the implementation, call sites, and targeted tests.
3. Reuse repository conventions.
4. Edit the smallest coherent surface.
5. Run targeted checks before broad suites.
6. Report changed behavior and verification, not a transcript of tool use.

## Host-model fallback

Codex itself is the model fallback. Never start a local model or request another API key from this
plugin. If no deterministic solver applies, continue the original task directly in the active
Codex session. Do not inspect the plugin implementation or invoke its Python entrypoint manually.

## Reasoning policy

Request the final answer, decision, evidence, or patch. Do not request hidden reasoning.
For high-risk decisions, request alternatives and evaluation criteria as concise output artifacts,
not an internal thought transcript.
