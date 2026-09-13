"""Descriptive and inferential analysis for the Steam Chinese review snapshot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from .processing import MIN_ALL_REVIEWS, MIN_CHINESE_REVIEWS, build_data_model


def bootstrap_median_difference(
    first: np.ndarray,
    second: np.ndarray,
    *,
    iterations: int = 10_000,
    seed: int = 20260913,
) -> tuple[float, float, float]:
    """Return median(first)-median(second) and a percentile bootstrap interval."""

    if len(first) < 2 or len(second) < 2:
        raise ValueError("Each bootstrap group needs at least two observations")
    generator = np.random.default_rng(seed)
    differences = np.empty(iterations)
    for index in range(iterations):
        sample_first = generator.choice(first, size=len(first), replace=True)
        sample_second = generator.choice(second, size=len(second), replace=True)
        differences[index] = np.median(sample_first) - np.median(sample_second)
    estimate = float(np.median(first) - np.median(second))
    lower, upper = np.percentile(differences, [2.5, 97.5])
    return estimate, float(lower), float(upper)


def _optional_number(value: Any, *, digits: int = 6) -> float | int | None:
    if pd.isna(value):
        return None
    if isinstance(value, (int, np.integer)):
        return int(value)
    return round(float(value), digits)


def _public_game_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    fields = [
        "appid",
        "name",
        "available_in_cn",
        "supports_simplified_chinese",
        "localization_status",
        "is_free",
        "genres",
        "all_review_count",
        "chinese_review_count",
        "chinese_review_share",
        "chinese_positive_rate",
        "non_chinese_positive_rate",
        "chinese_vs_non_chinese_gap",
        "mostplayed_rank",
        "topselling_rank",
        "best_chart_rank",
        "chart_membership",
        "sample_origin",
        "sample_origin_label",
        "curated_reason",
        "review_threshold_eligible",
        "analysis_eligible",
    ]
    records: list[dict[str, Any]] = []
    for row in frame[fields].itertuples(index=False, name=None):
        item = {
            field: _optional_number(value) if field not in {
                "name",
                "localization_status",
                "genres",
                "chart_membership",
                "sample_origin",
                "sample_origin_label",
                "curated_reason",
            } and not isinstance(value, (bool, np.bool_)) else value
            for field, value in zip(fields, row, strict=True)
        }
        item["available_in_cn"] = bool(item["available_in_cn"])
        item["supports_simplified_chinese"] = bool(
            item["supports_simplified_chinese"]
        )
        item["is_free"] = bool(item["is_free"])
        item["review_threshold_eligible"] = bool(item["review_threshold_eligible"])
        item["analysis_eligible"] = bool(item["analysis_eligible"])
        records.append(item)
    return records


def analyze_snapshot(frame: pd.DataFrame) -> dict[str, Any]:
    chart_frame = frame.loc[frame["sample_origin"].eq("chart")].copy()
    curated_frame = frame.loc[frame["sample_origin"].eq("curated_contrast")].copy()
    eligible = chart_frame.loc[chart_frame["analysis_eligible"]].copy()
    supported = eligible.loc[eligible["supports_simplified_chinese"]]
    unsupported = eligible.loc[~eligible["supports_simplified_chinese"]]

    support_rate = float(chart_frame["supports_simplified_chinese"].mean())
    cn_review_coverage = float((chart_frame["chinese_review_count"] > 0).mean())
    median_cn_share = float(eligible["chinese_review_share"].median())
    median_gap = float(eligible["chinese_vs_non_chinese_gap"].median())

    inferential: dict[str, Any] = {
        "status": "insufficient_group_size",
        "supported_count": int(len(supported)),
        "unsupported_count": int(len(unsupported)),
    }
    if len(supported) >= 3 and len(unsupported) >= 3:
        first = supported["chinese_review_share"].dropna().to_numpy(dtype=float)
        second = unsupported["chinese_review_share"].dropna().to_numpy(dtype=float)
        estimate, lower, upper = bootstrap_median_difference(first, second)
        test = mannwhitneyu(first, second, alternative="two-sided")
        inferential = {
            "status": "computed",
            "supported_count": int(len(first)),
            "unsupported_count": int(len(second)),
            "median_difference": round(estimate, 6),
            "bootstrap_ci_95": [round(lower, 6), round(upper, 6)],
            "mann_whitney_u": round(float(test.statistic), 3),
            "p_value": round(float(test.pvalue), 6),
            "interpretation_guardrail": (
                "This is an observational group comparison, not a causal estimate."
            ),
        }

    support_comparison = []
    for supported_flag, group in eligible.groupby(
        "supports_simplified_chinese", observed=True
    ):
        support_comparison.append(
            {
                "supports_simplified_chinese": bool(supported_flag),
                "label": "支持简体中文" if supported_flag else "未标注简体中文",
                "game_count": int(len(group)),
                "median_chinese_review_share": round(
                    float(group["chinese_review_share"].median()), 6
                ),
                "median_chinese_positive_rate": round(
                    float(group["chinese_positive_rate"].median()), 6
                ),
                "median_chinese_vs_non_chinese_gap": round(
                    float(group["chinese_vs_non_chinese_gap"].median()), 6
                ),
            }
        )

    top_share = eligible.nlargest(12, "chinese_review_share")
    lowest_gap = eligible.nsmallest(12, "chinese_vs_non_chinese_gap")
    latest_date = frame["snapshot_date"].max().strftime("%Y-%m-%d")
    collected_at = frame["collected_at_utc"].max().isoformat()

    return {
        "metadata": {
            "snapshot_date": latest_date,
            "collected_at_utc": collected_at,
            "scope": "Union of Steam global Top Sellers and Most Played top 100 charts",
            "explorer_scope": (
                "Chart sample plus a purposively selected comparison pool; "
                "curated cases are excluded from aggregate and inferential results"
            ),
            "minimum_all_reviews": MIN_ALL_REVIEWS,
            "minimum_chinese_reviews": MIN_CHINESE_REVIEWS,
            "primary_gap_definition": (
                "Simplified-Chinese positive rate minus non-Chinese positive rate"
            ),
        },
        "kpis": {
            "game_count": int(len(chart_frame)),
            "total_browsable_count": int(len(frame)),
            "curated_case_count": int(len(curated_frame)),
            "analysis_eligible_count": int(len(eligible)),
            "simplified_chinese_support_count": int(
                chart_frame["supports_simplified_chinese"].sum()
            ),
            "simplified_chinese_support_rate": round(support_rate, 6),
            "games_with_chinese_reviews": int(
                (chart_frame["chinese_review_count"] > 0).sum()
            ),
            "chinese_review_coverage_rate": round(cn_review_coverage, 6),
            "median_chinese_review_share": round(median_cn_share, 6),
            "median_chinese_vs_non_chinese_gap": round(median_gap, 6),
        },
        "support_comparison": support_comparison,
        "inferential_comparison": inferential,
        "top_chinese_review_share": _public_game_records(top_share),
        "largest_negative_gaps": _public_game_records(lowest_gap),
        "games": _public_game_records(frame),
        "limitations": [
            "中文评论指评论所选语言，不代表玩家国籍或所在地。",
            "评论数不等于销量、收入或活跃玩家数。",
            "样本只覆盖采集时点进入两个 Steam 全球榜单前100名的游戏。",
            "精选对照池是有意挑选的案例，只用于检索与个案观察，不进入任何总体比例、排行榜或组间检验。",
            "评价差异是描述性关联，不能证明本地化造成了评价变化。",
            "全语言汇总包含中文评论；主差值因此改用中文与非中文评价比较。",
        ],
    }


def run_analysis(project_root: Path) -> tuple[dict[str, Any], dict[str, object]]:
    """Build the data model and materialize analysis results for reports and site."""

    frame, model_report = build_data_model(project_root)
    results = analyze_snapshot(frame)

    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    report_path = processed_dir / "analysis_summary.json"
    with report_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    site_data_dir = project_root / "site" / "assets" / "data"
    site_data_dir.mkdir(parents=True, exist_ok=True)
    site_data_path = site_data_dir / "latest.json"
    with site_data_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(results, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")

    report: dict[str, object] = {
        **model_report,
        "analysis_status": "passed",
        "site_data_path": str(site_data_path.relative_to(project_root)),
        "analysis_summary_path": str(report_path.relative_to(project_root)),
    }
    return results, report
