"""Run the pilot evaluation and print a like-for-like comparison report.

Usage:
    uv run python scripts/run_eval.py [--max-entries N]

Compares three ranking modes on the same labeled cases:
similarity-only baseline, outcome-aware without context, and the shipped
outcome-aware ranking with incident context. Prints each report and a
summary table; also writes a machine-readable summary to
``data/eval_report.json`` for notebooks and dashboards.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from solution_intelligence.evaluate import comparison, format_report

REPORT_PATH = Path(__file__).resolve().parents[1] / "data" / "eval_report.json"


def main() -> None:
    """Run all eval modes and print the comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-entries",
        type=int,
        default=78,
        help="Dataset cap (default: 78, the full demo dataset).",
    )
    args = parser.parse_args()

    reports = comparison(max_entries=args.max_entries)
    for report in reports.values():
        print(format_report(report))
        print()

    print("Summary (same cases, three ranking modes):")
    header = (
        f"{'mode':<12} {'top-1':>6} {'top-3':>6} {'MRR':>6} {'abstain':>8} {'trap':>6}"
    )
    print(header)
    print("-" * len(header))
    for label, report in reports.items():
        trap = report.trap_resisted
        print(
            f"{label:<12} {report.top1_rate:>6.1%} {report.topk_rate:>6.1%} "
            f"{report.mrr:>6.3f} {report.abstain_precision:>8.1%} "
            f"{'-' if trap is None else str(trap):>6}"
        )

    REPORT_PATH.write_text(
        json.dumps(
            {label: report.as_dict() for label, report in reports.items()}, indent=2
        ),
        encoding="utf-8",
    )
    print(f"\nMachine-readable summary written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
