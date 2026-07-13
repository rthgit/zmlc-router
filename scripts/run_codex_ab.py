from __future__ import annotations

import argparse
import json

from zmlc.codex_ab import load_codex_ab_cases, run_codex_ab, write_codex_ab_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a paired plain-Codex versus ZMLC preflight A/B")
    parser.add_argument("tasks")
    parser.add_argument("--report", required=True)
    parser.add_argument("--codex-bin")
    parser.add_argument("--model")
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--sandbox", default="read-only")
    parser.add_argument("--cd")
    parser.add_argument("--config", action="append", default=[])
    parser.add_argument("--minimum-savings", type=float, default=35.0)
    parser.add_argument("--maximum-quality-loss", type=float, default=0.01)
    args = parser.parse_args()
    report = run_codex_ab(
        load_codex_ab_cases(args.tasks),
        codex_binary=args.codex_bin,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        sandbox=args.sandbox,
        cwd=args.cd,
        configs=args.config,
        minimum_savings_pct=args.minimum_savings,
        maximum_quality_loss=args.maximum_quality_loss,
        progress=lambda message: print(message, flush=True),
    )
    write_codex_ab_report(report, args.report)
    print(json.dumps(report, indent=2))
    return 0 if report["gate"]["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
