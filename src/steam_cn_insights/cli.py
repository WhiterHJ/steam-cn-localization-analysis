"""Command-line entry point for project data tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import run_analysis
from .charts import run_chart_collection
from .feasibility import run_feasibility
from .snapshot import run_snapshot_collection


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "task",
        nargs="?",
        choices=("feasibility", "charts", "snapshot", "analyze"),
        default="feasibility",
        help="Data task to run (default: feasibility).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root containing config/ and data/ directories.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore cached responses and request fresh data.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional app limit for snapshot development runs.",
    )
    parser.add_argument(
        "--cache-date",
        help="Optional YYYY-MM-DD cache date to replay for the snapshot task.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.task == "feasibility":
        _, report = run_feasibility(args.project_root.resolve(), refresh=args.refresh)
    elif args.task == "charts":
        _, report = run_chart_collection(args.project_root.resolve(), refresh=args.refresh)
    elif args.task == "snapshot":
        _, report = run_snapshot_collection(
            args.project_root.resolve(),
            refresh=args.refresh,
            limit=args.limit,
            cache_date=args.cache_date,
        )
    else:
        _, report = run_analysis(args.project_root.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
