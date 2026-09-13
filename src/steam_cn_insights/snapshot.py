"""Build the first production-ready game and review summary snapshot."""

from __future__ import annotations

import csv
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .http_client import FetchError
from .metrics import calculate_game_metrics
from .quality import QualityError, validate_game_record, validate_review_summary, validate_unique_appids
from .steam import fetch_app_details, fetch_review_summary


def _load_chart_games(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run the charts task before building a game snapshot."
        )
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _serialize(value: Any) -> Any:
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return value


def minimum_required_count(candidate_count: int, *, limited_run: bool) -> int:
    """Return the coverage floor without making small development runs impossible."""

    proportional_floor = math.ceil(candidate_count * 0.75)
    return proportional_floor if limited_run else max(20, proportional_floor)


def _write_csv(path: Path, records: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {key: _serialize(record.get(key)) for key in fieldnames}
            for record in records
        )


def run_snapshot_collection(
    project_root: Path,
    *,
    refresh: bool = False,
    limit: int | None = None,
    cache_date: str | None = None,
    delay_seconds: float = 0.15,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Enrich chart apps with metadata and cross-language review summaries."""

    collected_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    snapshot_date = cache_date or collected_at[:10]
    output_dir = project_root / "data" / "interim"
    candidates = _load_chart_games(output_dir / "chart_games.csv")
    if limit is not None:
        candidates = candidates[:limit]

    cache_dir = project_root / "data" / "raw" / "snapshots" / snapshot_date
    records: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []

    for position, candidate in enumerate(candidates, start=1):
        appid = int(candidate["appid"])
        print(f"[{position:03d}/{len(candidates):03d}] Enriching appid={appid}...")
        try:
            details = fetch_app_details(appid, cache_dir, refresh=refresh)
        except FetchError as error:
            exclusions.append(
                {
                    "appid": appid,
                    "chart_name": candidate["name"],
                    "reason": "metadata_fetch_failed",
                    "detail": str(error),
                }
            )
            continue

        if details["type"] != "game":
            exclusions.append(
                {
                    "appid": appid,
                    "chart_name": candidate["name"],
                    "reason": "not_a_game",
                    "detail": f"Steam product type={details['type']}",
                }
            )
            continue

        try:
            all_reviews = fetch_review_summary(appid, "all", cache_dir, refresh=refresh)
            chinese_reviews = fetch_review_summary(
                appid, "schinese", cache_dir, refresh=refresh
            )
            validate_review_summary(all_reviews)
            validate_review_summary(chinese_reviews)
            record = {
                **details,
                **calculate_game_metrics(all_reviews, chinese_reviews),
                "mostplayed_rank": candidate.get("mostplayed_rank") or None,
                "topselling_rank": candidate.get("topselling_rank") or None,
                "chart_count": int(candidate["chart_count"]),
                "snapshot_date": snapshot_date,
                "collected_at_utc": collected_at,
            }
            validate_game_record(record)
        except (FetchError, QualityError, KeyError, TypeError, ValueError) as error:
            exclusions.append(
                {
                    "appid": appid,
                    "chart_name": candidate["name"],
                    "reason": "review_or_quality_failed",
                    "detail": str(error),
                }
            )
            continue

        records.append(record)
        if delay_seconds:
            time.sleep(delay_seconds)

    validate_unique_appids(records)
    minimum_required = minimum_required_count(
        len(candidates), limited_run=limit is not None
    )
    status = "passed" if len(records) >= minimum_required else "failed"

    record_fields = [
        "appid",
        "store_market",
        "available_in_cn",
        "name",
        "type",
        "is_free",
        "release_date_text",
        "coming_soon",
        "currency",
        "initial_price",
        "final_price",
        "discount_percent",
        "developers",
        "publishers",
        "genres",
        "supports_simplified_chinese",
        "all_review_count",
        "all_positive_count",
        "all_negative_count",
        "chinese_review_count",
        "chinese_positive_count",
        "chinese_negative_count",
        "non_chinese_review_count",
        "non_chinese_positive_count",
        "chinese_review_share",
        "all_positive_rate",
        "chinese_positive_rate",
        "non_chinese_positive_rate",
        "positive_rate_gap",
        "chinese_vs_non_chinese_gap",
        "mostplayed_rank",
        "topselling_rank",
        "chart_count",
        "snapshot_date",
        "collected_at_utc",
    ]
    _write_csv(output_dir / "game_snapshot.csv", records, record_fields)
    _write_csv(
        output_dir / "snapshot_exclusions.csv",
        exclusions,
        ["appid", "chart_name", "reason", "detail"],
    )

    report = {
        "status": status,
        "collected_at_utc": collected_at,
        "snapshot_date": snapshot_date,
        "candidate_app_count": len(candidates),
        "valid_game_count": len(records),
        "excluded_count": len(exclusions),
        "minimum_required": minimum_required,
        "simplified_chinese_support_count": sum(
            bool(record["supports_simplified_chinese"]) for record in records
        ),
        "games_with_chinese_reviews": sum(
            int(record["chinese_review_count"]) > 0 for record in records
        ),
        "exclusion_reasons": {
            reason: sum(item["reason"] == reason for item in exclusions)
            for reason in sorted({item["reason"] for item in exclusions})
        },
    }
    report_path = output_dir / "snapshot_collection_report.json"
    with report_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    if status != "passed":
        raise QualityError(
            f"Snapshot coverage failed: {len(records)} valid games, "
            f"minimum required {minimum_required}"
        )
    return records, report
