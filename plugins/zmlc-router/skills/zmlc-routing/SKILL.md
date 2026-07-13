---
name: zmlc-routing
description: Route Codex work through deterministic solvers and compile concise task prompts before using an LLM. Use for arithmetic, JSON, extraction, string transforms, token-cost audits, prompt compression, coding task capsules, context minimization, and local-first workflow design.
---

# ZMLC Routing

Act as silent middleware. Use ZMLC when a task can be solved, validated, or expressed more compactly before model generation. The active Codex model is the fallback; do not configure or start another model.

## Routing procedure

1. Classify the task silently as deterministic, verifiable, or lossy.
2. Call a ZMLC MCP tool only when its contract clearly matches the task.
3. Accept a solver answer only when its route is `deterministic` and verification passes.
4. When `route_task` returns `host_model` or `delegate_to_codex`, immediately solve the task with the current Codex model.
5. If ZMLC MCP tools are unavailable, continue with current Codex; do not inspect plugin files, search for Python, or run the MCP script manually.
6. Mention routing and token counts only when the user explicitly asks for an audit.

Do not announce that this skill is active. Do not narrate routing, tool discovery, or fallback decisions.

## Prompt procedure

1. State one concrete objective; do not restate the conversation.
2. Include only paths, symbols, schemas, and constraints that alter execution.
3. Define the exact output and the smallest sufficient verification.
4. Call `compile_prompt` for reusable or user-requested prompt optimization.
5. Do not request chain-of-thought or add role-play, greetings, praise, or closing offers.
6. For coding, inspect narrowly, edit the smallest coherent surface, and run targeted checks first.

Do not compile the user's request merely because the skill was invoked. For ordinary coding or open-ended work, execute directly with Codex. Compile only when it removes material context or the user requests a reusable prompt.

Read [references/token-policy.md](references/token-policy.md) only when designing or auditing prompts.

## Appropriate deterministic work

- arithmetic and percentages;
- list aggregates;
- exact JSON validation;
- regex extraction;
- case conversion and other explicit string transforms.

Do not force a deterministic route for summaries, recommendations, subjective QA, or unfamiliar domain reasoning. Delegate these tasks to the current Codex model; this is not an error.

## MCP tools

- `route_task`: return a compact deterministic result or `delegate_to_codex`;
- `audit_task`: return the full local routing trace on explicit request;
- `solve_math`: run bounded arithmetic solvers;
- `validate_json`: parse and validate JSON;
- `list_solvers`: inspect available deterministic capabilities.
- `compile_prompt`: build a compact Codex task capsule;
- `estimate_tokens`: compare prompt variants without a model call.
- `session_metrics`: report aggregate calls avoided and estimated tokens saved without prompts.
