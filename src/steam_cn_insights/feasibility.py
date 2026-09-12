"""End-to-end feasibility collection for a small fixed app sample."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .metrics import calculate_game_metrics
from .quality import validate_game_record, validate_review_summary, validate_unique_appids
from .steam import fetch_app_details, fetch_review_summary


def _serialize_cell(value: Any) -> Any:
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return value


def run_feasibility(
    project_root: Path,
    *,
    refresh: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collect ten known games, calculate metrics, validate, and write outputs."""

    collected_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    snapshot_date = collected_at[:10]
    config_path = project_root / "config" / "feasibility_apps.json"
    cache_dir = project_root / "data" / "raw" / "feasibility" / snapshot_date
    output_dir = project_root / "data" / "interim"
    output_dir.mkdir(parents=True, exist_ok=True)

    with config_path.open("r", encoding="utf-8") as handle:
        apps = json.load(handle)

    records: list[dict[str, Any]] = []
    for position, app in enumerate(apps, start=1):
        appid = int(app["appid"])
        print(f"[{position:02d}/{len(apps):02d}] Collecting appid={appid}...")
        details = fetch_app_details(appid, cache_dir, refresh=refresh)
        all_reviews = fetch_review_summary(appid, "all", cache_dir, refresh=refresh)
        chinese_reviews = fetch_review_summary(
            appid, "schinese", cache_dir, refresh=refresh
        )

        validate_review_summary(all_reviews)
        validate_review_summary(chinese_reviews)
        record = {
            **details,
            **calculate_game_metrics(all_reviews, chinese_reviews),
            "collected_at_utc": collected_at,
        }
        validate_game_record(record)
        records.append(record)

    validate_unique_appids(records)

    csv_path = output_dir / "feasibility_games.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(
            {key: _serialize_cell(value) for key, value in record.items()}
            for record in records
        )

    report = {
        "status": "passed",
        "collected_at_utc": collected_at,
        "game_count": len(records),
        "games_with_simplified_chinese": sum(
            bool(record["supports_simplified_chinese"]) for record in records
        ),
        "games_with_chinese_reviews": sum(
            int(record["chinese_review_count"]) > 0 for record in records
        ),
        "output_csv": str(csv_path.relative_to(project_root)),
        "raw_cache_directory": str(cache_dir.relative_to(project_root)),
    }
    report_path = output_dir / "feasibility_report.json"
    with report_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    return records, report
