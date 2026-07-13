from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path


def add(rows: list[dict[str, object]], **payload: object) -> None:
    rows.append(payload)


def build_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(40):
        left, right = index + 3, index % 9 + 2
        add(
            rows,
            task_id=f"arithmetic-{index:03d}",
            prompt=f"Calculate {left} + {right}.",
            task_type="math",
            expected_route="deterministic",
            expected_answer=str(left + right),
            baseline_tokens=80,
        )
    for index in range(20):
        values = [index + 1, index + 3, index + 5]
        add(
            rows,
            task_id=f"aggregate-{index:03d}",
            prompt=f"Return the sum of {values}.",
            task_type="math",
            expected_route="deterministic",
            expected_answer=str(sum(values)),
            baseline_tokens=80,
        )
    for index in range(15):
        source = f"Token Route {index}"
        add(
            rows,
            task_id=f"transform-{index:03d}",
            prompt=f'Return uppercase for "{source}".',
            task_type="format_strict",
            expected_route="deterministic",
            expected_answer=source.upper(),
            baseline_tokens=70,
        )
    for index in range(20):
        value = index + 1
        add(
            rows,
            task_id=f"unit-{index:03d}",
            prompt=f"Convert {value} km to m.",
            task_type="math",
            expected_route="deterministic",
            expected_answer=str(value * 1000),
            baseline_tokens=90,
        )
    for index in range(15):
        old, new = 100 + index * 10, 110 + index * 11
        expected = (new - old) / old * 100
        rendered = str(int(expected)) if expected.is_integer() else f"{expected:.10g}"
        add(
            rows,
            task_id=f"finance-{index:03d}",
            prompt=f"Calculate the percentage change from {old} to {new}.",
            task_type="math",
            expected_route="deterministic",
            expected_answer=rendered,
            baseline_tokens=100,
        )
    for index in range(15):
        left, right = [index, index + 1], [index + 1, index + 2]
        add(
            rows,
            task_id=f"set-{index:03d}",
            prompt=f"Return the union of {left} and {right} as JSON.",
            task_type="format_strict",
            expected_route="deterministic",
            expected_answer=json.dumps(sorted(set(left) | set(right)), separators=(",", ":")),
            baseline_tokens=90,
        )
    start = date(2026, 1, 1)
    for index in range(15):
        end = start + timedelta(days=index + 1)
        add(
            rows,
            task_id=f"date-{index:03d}",
            prompt=f"How many days between {start.isoformat()} and {end.isoformat()}?",
            task_type="math",
            expected_route="deterministic",
            expected_answer=str(index + 1),
            baseline_tokens=90,
        )
    open_prompts = (
        "Review the architecture and recommend one improvement.",
        "Write a concise explanation of routing tradeoffs.",
        "Summarize the supplied design without losing caveats.",
        "Debug an unfamiliar integration failure.",
        "Compare two deployment strategies and justify the decision.",
        "Draft a migration plan for a production service.",
    )
    for index in range(60):
        add(
            rows,
            task_id=f"host-{index:03d}",
            prompt=f"{open_prompts[index % len(open_prompts)]} Case {index}.",
            task_type="qa",
            expected_route="host_model",
            expected_answer=None,
            baseline_tokens=180,
        )
    return rows


def main() -> int:
    destination = Path(__file__).with_name("public_mixed_200.jsonl")
    rows = build_rows()
    if len(rows) != 200:
        raise SystemExit(f"expected 200 rows, got {len(rows)}")
    destination.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
