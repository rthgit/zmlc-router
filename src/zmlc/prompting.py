from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PromptSpec:
    objective: str
    context: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    output: str = "Return only the requested result."
    verification: tuple[str, ...] = ()
    mode: str = "auto"


@dataclass(frozen=True)
class CompiledPrompt:
    text: str
    estimated_tokens: int
    source_tokens: int = 0

    @property
    def estimated_savings(self) -> int:
        return max(0, self.source_tokens - self.estimated_tokens)

    def is_smaller_by(self, minimum_tokens: int = 1) -> bool:
        return self.source_tokens - self.estimated_tokens >= minimum_tokens


def estimate_tokens(text: str) -> int:
    """Dependency-free estimate suitable for comparing prompt variants."""
    if not text.strip():
        return 0
    words = len(re.findall(r"\S+", text))
    characters = len(text)
    return max(words, (characters + 3) // 4)


def compact_request(text: str) -> str:
    """Remove transport noise while preserving task semantics and code blocks."""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    compacted: list[str] = []
    previous = None
    in_fence = False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        normalized = line if in_fence else re.sub(r"[ \t]+", " ", line).strip()
        if not normalized and (not compacted or compacted[-1] == ""):
            continue
        key = normalized.casefold()
        if normalized and key == previous and not in_fence:
            continue
        compacted.append(normalized)
        previous = key if normalized else None
    return "\n".join(compacted).strip()


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = compact_request(str(value))
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return tuple(result)


def compile_prompt(spec: PromptSpec, *, source: str = "") -> CompiledPrompt:
    objective = compact_request(spec.objective)
    if not objective:
        raise ValueError("objective is required")
    context = _dedupe(spec.context)
    constraints = _dedupe(spec.constraints)
    verification = _dedupe(spec.verification)

    sections = [f"TASK\n{objective}"]
    if context:
        sections.append("CONTEXT\n" + "\n".join(f"- {item}" for item in context))
    if constraints:
        sections.append("CONSTRAINTS\n" + "\n".join(f"- {item}" for item in constraints))
    sections.append("OUTPUT\n" + compact_request(spec.output))
    if verification:
        sections.append("DONE WHEN\n" + "\n".join(f"- {item}" for item in verification))

    execution = {
        "coding": "Inspect narrowly, implement the smallest coherent change, then run targeted checks.",
        "debug": "Identify the root cause before editing. Verify the failing path after the fix.",
        "review": "Lead with actionable findings ordered by severity and cite exact locations.",
        "extraction": "Return only schema-valid extracted values. Mark missing values explicitly.",
        "planning": "Map dependencies and acceptance criteria before sequencing actions.",
    }.get(spec.mode, "Use tools and deterministic checks first.")
    sections.append(f"EXECUTION\n{execution} Do not narrate internal reasoning.")
    text = "\n\n".join(sections)
    return CompiledPrompt(
        text=text,
        estimated_tokens=estimate_tokens(text),
        source_tokens=estimate_tokens(source),
    )


def compact_host_prompt(source: str, *, minimum_savings: int = 8) -> CompiledPrompt:
    """Compact transport noise, but keep the original when compaction is not worthwhile."""
    compacted = compact_request(source)
    source_tokens = estimate_tokens(source)
    compacted_tokens = estimate_tokens(compacted)
    if source_tokens - compacted_tokens < minimum_savings:
        return CompiledPrompt(source, source_tokens, source_tokens)
    return CompiledPrompt(compacted, compacted_tokens, source_tokens)


def codex_coding_prompt(
    objective: str,
    *,
    paths: Iterable[str] = (),
    constraints: Iterable[str] = (),
    checks: Iterable[str] = (),
) -> CompiledPrompt:
    defaults = (
        "Inspect only files relevant to the requested behavior.",
        "Preserve existing project conventions and unrelated user changes.",
        "Prefer targeted edits and existing abstractions.",
    )
    return compile_prompt(
        PromptSpec(
            objective=objective,
            context=tuple(f"@{path}" for path in paths),
            constraints=(*defaults, *tuple(constraints)),
            output="Implement the change. Return a concise change summary and verification results.",
            verification=tuple(checks),
            mode="coding",
        )
    )
