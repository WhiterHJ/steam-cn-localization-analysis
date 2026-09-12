"""Command-line entry point for project data tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .feasibility import run_feasibility


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    _, report = run_feasibility(args.project_root.resolve(), refresh=args.refresh)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
