"""Metric calculations shared by collectors, analysis, and tests."""

from __future__ import annotations

from typing import Any, Mapping


def safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def calculate_game_metrics(
    all_reviews: Mapping[str, Any],
    chinese_reviews: Mapping[str, Any],
) -> dict[str, float | int | None]:
    """Calculate transparent cross-language review metrics for one game."""

    all_total = int(all_reviews["total_reviews"])
    all_positive = int(all_reviews["total_positive"])
    chinese_total = int(chinese_reviews["total_reviews"])
    chinese_positive = int(chinese_reviews["total_positive"])
    non_chinese_total = all_total - chinese_total
    non_chinese_positive = all_positive - chinese_positive

    all_positive_rate = safe_rate(all_positive, all_total)
    chinese_positive_rate = safe_rate(chinese_positive, chinese_total)
    positive_rate_gap = (
        chinese_positive_rate - all_positive_rate
        if chinese_positive_rate is not None and all_positive_rate is not None
        else None
    )
    non_chinese_positive_rate = safe_rate(non_chinese_positive, non_chinese_total)
    chinese_vs_non_chinese_gap = (
        chinese_positive_rate - non_chinese_positive_rate
        if chinese_positive_rate is not None and non_chinese_positive_rate is not None
        else None
    )

    return {
        "all_review_count": all_total,
        "all_positive_count": all_positive,
        "all_negative_count": int(all_reviews["total_negative"]),
        "chinese_review_count": chinese_total,
        "chinese_positive_count": chinese_positive,
        "chinese_negative_count": int(chinese_reviews["total_negative"]),
        "non_chinese_review_count": non_chinese_total,
        "non_chinese_positive_count": non_chinese_positive,
        "chinese_review_share": safe_rate(chinese_total, all_total),
        "all_positive_rate": all_positive_rate,
        "chinese_positive_rate": chinese_positive_rate,
        "non_chinese_positive_rate": non_chinese_positive_rate,
        "positive_rate_gap": positive_rate_gap,
        "chinese_vs_non_chinese_gap": chinese_vs_non_chinese_gap,
    }
