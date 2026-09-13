"""Normalize collected Steam snapshots into analysis-ready datasets."""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb
import pandas as pd


MIN_ALL_REVIEWS = 1_000
MIN_CHINESE_REVIEWS = 100

BOOLEAN_COLUMNS = (
    "available_in_cn",
    "is_free",
    "coming_soon",
    "supports_simplified_chinese",
)
INTEGER_COLUMNS = (
    "appid",
    "discount_percent",
    "all_review_count",
    "all_positive_count",
    "all_negative_count",
    "chinese_review_count",
    "chinese_positive_count",
    "chinese_negative_count",
    "non_chinese_review_count",
    "non_chinese_positive_count",
    "mostplayed_rank",
    "topselling_rank",
    "chart_count",
)
RATE_COLUMNS = (
    "chinese_review_share",
    "all_positive_rate",
    "chinese_positive_rate",
    "non_chinese_positive_rate",
    "positive_rate_gap",
    "chinese_vs_non_chinese_gap",
)


def _parse_boolean(value: object) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().casefold()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"Unrecognized boolean value: {value!r}")


def load_and_prepare_snapshot(path: Path) -> pd.DataFrame:
    """Load a collector CSV, coerce types, derive flags, and validate invariants."""

    frame = pd.read_csv(path, encoding="utf-8-sig")
    if frame.empty:
        raise ValueError("Snapshot contains no game records")
    if "sample_origin" not in frame:
        frame["sample_origin"] = "chart"
    if "curated_reason" not in frame:
        frame["curated_reason"] = ""
    frame["curated_reason"] = frame["curated_reason"].fillna("")
    allowed_origins = {"chart", "curated_contrast"}
    unexpected_origins = set(frame["sample_origin"].dropna()) - allowed_origins
    if unexpected_origins:
        raise ValueError(f"Unexpected sample origins: {sorted(unexpected_origins)}")

    for column in BOOLEAN_COLUMNS:
        frame[column] = frame[column].map(_parse_boolean).astype("boolean")
    for column in INTEGER_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
    for column in RATE_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["snapshot_date"] = pd.to_datetime(frame["snapshot_date"], errors="raise")
    frame["collected_at_utc"] = pd.to_datetime(
        frame["collected_at_utc"], utc=True, errors="raise"
    )
    frame["best_chart_rank"] = frame[["mostplayed_rank", "topselling_rank"]].min(
        axis=1, skipna=True
    ).astype("Int64")
    frame["chart_membership"] = "Both charts"
    frame.loc[frame["mostplayed_rank"].isna(), "chart_membership"] = "Top sellers only"
    frame.loc[frame["topselling_rank"].isna(), "chart_membership"] = "Most played only"
    curated_mask = frame["sample_origin"].eq("curated_contrast")
    frame.loc[curated_mask, "chart_membership"] = "Curated comparison"
    frame["sample_origin_label"] = frame["sample_origin"].map(
        {"chart": "每日热门榜", "curated_contrast": "精选对照池"}
    )
    frame["review_threshold_eligible"] = (
        (frame["all_review_count"] >= MIN_ALL_REVIEWS)
        & (frame["chinese_review_count"] >= MIN_CHINESE_REVIEWS)
        & (frame["non_chinese_review_count"] > 0)
    )
    frame["analysis_eligible"] = (
        frame["sample_origin"].eq("chart") & frame["review_threshold_eligible"]
    )
    frame["localization_status"] = frame["supports_simplified_chinese"].map(
        {True: "支持简体中文", False: "未标注简体中文"}
    )

    if frame["appid"].isna().any() or frame["appid"].duplicated().any():
        raise ValueError("Snapshot appid values must be present and unique")
    if (frame["chinese_review_count"] > frame["all_review_count"]).any():
        raise ValueError("Chinese review counts cannot exceed all-language counts")
    if (
        frame["all_positive_count"] + frame["all_negative_count"]
        != frame["all_review_count"]
    ).any():
        raise ValueError("All-language positive and negative counts do not reconcile")
    if (
        frame["chinese_positive_count"] + frame["chinese_negative_count"]
        != frame["chinese_review_count"]
    ).any():
        raise ValueError("Chinese positive and negative counts do not reconcile")
    for column in (
        "chinese_review_share",
        "all_positive_rate",
        "chinese_positive_rate",
        "non_chinese_positive_rate",
    ):
        non_null = frame[column].dropna()
        if not non_null.between(0, 1).all():
            raise ValueError(f"{column} contains a value outside [0, 1]")

    frame["_sample_origin_order"] = frame["sample_origin"].map(
        {"chart": 0, "curated_contrast": 1}
    )
    prepared = frame.sort_values(
        ["_sample_origin_order", "best_chart_rank", "appid"],
        ascending=[True, True, True],
        na_position="last",
    ).drop(columns="_sample_origin_order")
    return prepared.reset_index(drop=True)


def build_data_model(project_root: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    """Create Parquet, DuckDB, and a public compact snapshot from interim data."""

    source = project_root / "data" / "interim" / "game_snapshot.csv"
    if not source.exists():
        raise FileNotFoundError(f"Missing {source}. Run the snapshot task first.")

    frame = load_and_prepare_snapshot(source)
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = processed_dir / "game_snapshot.parquet"
    database_path = processed_dir / "steam_cn.duckdb"
    frame.to_parquet(parquet_path, index=False)

    with duckdb.connect(str(database_path)) as connection:
        connection.register("snapshot_frame", frame)
        connection.execute(
            "CREATE OR REPLACE TABLE game_snapshot AS SELECT * FROM snapshot_frame"
        )
        connection.execute(
            """
            CREATE OR REPLACE VIEW analysis_games AS
            SELECT * FROM game_snapshot WHERE analysis_eligible
            """
        )

    snapshot_date = frame["snapshot_date"].max().strftime("%Y-%m-%d")
    published_dir = project_root / "data" / "published" / "snapshots"
    published_dir.mkdir(parents=True, exist_ok=True)
    public_csv = published_dir / f"steam_games_{snapshot_date}.csv"
    shutil.copyfile(source, public_csv)

    report: dict[str, object] = {
        "status": "passed",
        "snapshot_date": snapshot_date,
        "game_count": int(len(frame)),
        "analysis_eligible_count": int(frame["analysis_eligible"].sum()),
        "unique_appid_count": int(frame["appid"].nunique()),
        "parquet_path": str(parquet_path.relative_to(project_root)),
        "duckdb_path": str(database_path.relative_to(project_root)),
        "published_snapshot_path": str(public_csv.relative_to(project_root)),
    }
    return frame, report
