"""Data-quality checks for the feasibility and production datasets."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class QualityError(ValueError):
    """Raised when collected data violates a required invariant."""


def validate_review_summary(summary: Mapping[str, Any]) -> None:
    total = int(summary["total_reviews"])
    positive = int(summary["total_positive"])
    negative = int(summary["total_negative"])
    if min(total, positive, negative) < 0:
        raise QualityError(f"Negative review count in {summary}")
    if positive + negative != total:
        raise QualityError(
            f"Review totals do not reconcile for appid={summary.get('appid')}, "
            f"language={summary.get('language')}: {positive} + {negative} != {total}"
        )


def validate_game_record(record: Mapping[str, Any]) -> None:
    if not record.get("name"):
        raise QualityError(f"Missing game name for appid={record.get('appid')}")
    if record.get("type") != "game":
        raise QualityError(
            f"Expected type=game for appid={record.get('appid')}, got {record.get('type')}"
        )

    all_count = int(record["all_review_count"])
    chinese_count = int(record["chinese_review_count"])
    if chinese_count > all_count:
        raise QualityError(
            f"Chinese review count exceeds all-language count for appid={record.get('appid')}"
        )

    for field in ("chinese_review_share", "all_positive_rate", "chinese_positive_rate"):
        value = record.get(field)
        if value is not None and not 0 <= float(value) <= 1:
            raise QualityError(f"{field} is outside [0, 1] for appid={record.get('appid')}")


def validate_unique_appids(records: Iterable[Mapping[str, Any]]) -> None:
    appids = [int(record["appid"]) for record in records]
    if len(appids) != len(set(appids)):
        raise QualityError("Duplicate appid values found in collected records")
