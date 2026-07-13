# ZMLC Router: Public 1.0 Roadmap

## Implementation status

The `0.9.1` public-beta implementation now includes the portable runtime builders,
solver-specific verification, public proxy corpus, content-free telemetry, host-model
delegation, compact prompt compiler, paired A/B analyzer, hard release checks,
cross-platform CI, signed release workflows, privacy/security policies, and clean
artifact smoke tests described below.

One 1.0 exit criterion remains intentionally open: publish a paired A/B run against
plain Codex using the same model and settings, demonstrating median real token savings
of at least 35% with no more than one percentage point mean quality loss. The current
52.32% result is a transparent proxy and cannot satisfy that criterion by itself.

## Product target

Turn ZMLC Router into a portable Codex plugin and general MCP service that reduces
model-token use without lowering task quality. The active host model remains the
fallback. A local model or external API must never be required for the default path.

"10/10" means all of the following are measured, not claimed:

- at least 35% median token reduction on the public mixed-workload benchmark;
- no more than 1 percentage point quality loss against the no-router baseline;
- zero false deterministic accepts in the release-gate corpus;
- less than 50 ms median routing overhead for deterministic tasks;
- clean installation on Windows, macOS, and Linux with no absolute paths;
- no API key, local model, or manual Python configuration for the Codex fallback;
- an auditable decision trace available on request but silent by default.

## Phase 0 - Freeze and measure

Goal: establish a reproducible baseline before changing routing behavior.

- Freeze the current plugin as `0.1.x`.
- Build paired A/B fixtures: plain Codex versus Codex with ZMLC.
- Record input tokens, output tokens, latency, route, solver, verification result,
  task quality, and failures.
- Separate deterministic, structured, coding, retrieval, and open-ended workloads.
- Add at least 200 public tasks with no competition-private or memorized answers.

Exit criteria:

- one command produces a versioned JSON and Markdown benchmark report;
- repeated runs report confidence intervals and per-task deltas;
- the current 6.5/10 estimate is replaced by measured numbers.

## Phase 1 - Portable runtime

Goal: install and run from a clean machine without machine-specific paths.

- Remove the absolute Python and repository paths from `.mcp.json`.
- Make the MCP server self-contained inside the plugin package.
- Select and validate one distribution strategy:
  - preferred: signed standalone executables for Windows, macOS, and Linux;
  - fallback: a published package with a generated launcher and explicit runtime check.
- Keep the stdio protocol dependency-free at runtime.
- Resolve resources relative to the installed plugin root.
- Add clean-machine installation tests in disposable CI runners.

Exit criteria:

- clone/install/start succeeds on all three operating systems;
- no path contains a developer username, drive letter, or repository checkout;
- `tools/list`, deterministic solve, and host-model delegation pass after installation.

## Phase 2 - Safe solver platform

Goal: expand zero-model coverage without dataset-specific matching.

- Define a strict solver contract: support detection, solve, verify, evidence, abstain.
- Add property-based tests and adversarial negatives for every solver.
- Expand high-value general solvers:
  - arithmetic, percentages, unit conversion, dates, and bounded finance;
  - JSON Schema, CSV, XML, and exact output normalization;
  - statistics, set/list operations, and table aggregation;
  - regex extraction, deterministic text transforms, and code format checks;
  - repository facts available through structured local tools.
- Require solver-specific verification before accepting an answer.
- Track false accepts separately from ordinary wrong answers.

Exit criteria:

- at least 95% precision for each enabled solver family;
- zero release-gate false accepts;
- unsupported or ambiguous tasks always delegate to the host model.

## Phase 3 - Host-model routing and prompt compiler

Goal: reduce model context when deterministic resolution is not possible.

- Keep `host_model` as a first-class route, never as a failure.
- Compile minimal task capsules from objective, relevant context references,
  constraints, output contract, and verification contract.
- Deduplicate repeated instructions and omit conversational filler.
- Use repository symbols, paths, diffs, and schemas instead of whole-file copies.
- Never request hidden chain-of-thought or universal ToT/GoT/SoT procedures.
- Add task-specific profiles for coding, debugging, review, extraction, and planning.
- Add a token budget that can bypass routing when middleware would cost more.

Exit criteria:

- prompt compaction preserves every executable constraint in the test corpus;
- open-ended tasks are completed by the active Codex model with no second model call;
- middleware overhead is lower than the estimated savings for every routed request.

## Phase 4 - Policy engine and observability

Goal: make decisions explainable without adding noise to normal Codex use.

- Add policies for confidence, risk, maximum overhead, privacy, and fail-closed behavior.
- Emit structured events for candidate, abstain, verify, accept, and delegate.
- Keep traces local and disabled in normal user-facing responses.
- Add per-session counters for model calls avoided and estimated tokens saved.
- Provide `zmlc audit` and an MCP audit tool for explicit inspection.
- Never log prompt content or secrets unless the user opts in.

Exit criteria:

- every accepted deterministic result has verifier evidence;
- every delegation has a stable reason code;
- telemetry can be disabled completely.

## Phase 5 - Quality and token benchmark gate

Goal: prevent optimistic local tests from becoming release claims.

- Run deterministic tests on every commit.
- Run multi-seed model evaluations before release.
- Include unseen paraphrases and adversarial formatting.
- Compare against plain Codex using the same model, task, and settings.
- Publish task-level data, aggregate metrics, and known limitations.
- Block release if quality drops by more than 1 point or false accepts are non-zero.

Exit criteria:

- median token savings >=35%;
- quality delta >=-1 percentage point;
- deterministic false accepts = 0;
- crash-free and parser-pass rates = 100% in the release suite.

## Phase 6 - Public distribution

Goal: make installation and contribution credible for external users.

- Publish the framework and plugin in a dedicated public GitHub repository.
- Keep Apache-2.0 licensing and add security, privacy, and support policies.
- Publish checksums and signed release artifacts.
- Provide a public Codex marketplace manifest with semantic versions.
- Document install, update, uninstall, troubleshooting, and offline behavior.
- Add a five-minute quick start and solver contribution template.
- Verify installation from the public release, not from a working tree.

Exit criteria:

- a new user installs and completes the smoke test without local edits;
- the public artifact contains no secrets, private datasets, absolute paths, or caches;
- release provenance and checksums are reproducible.

## Phase 7 - 1.0 release and maintenance

Goal: ship a stable public contract rather than a one-off prototype.

- Freeze MCP tool schemas and solver interfaces for 1.x.
- Add deprecation and migration policy.
- Publish benchmark results for every release.
- Triage solver requests by expected token value and verification strength.
- Reject rules that depend on benchmark IDs or exact hidden-task wording.

Exit criteria:

- all 10/10 product targets pass in CI and on clean-machine release tests;
- documentation and benchmark results match the released binaries;
- rollback to the previous release is documented and tested.

## Recommended delivery order

1. Baseline telemetry and A/B benchmark.
2. Portable self-contained MCP runtime.
3. Safe solver expansion with adversarial tests.
4. Host-model prompt compaction and budget policy.
5. Cross-platform CI, security audit, and public beta.
6. Measured 1.0 release.

Do not optimize for the number of solvers. Optimize for verified model calls avoided
per unit of routing overhead, with quality protected as a hard constraint.
