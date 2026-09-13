-- Headline metrics for the latest Steam chart snapshot.
-- Run against data/processed/steam_cn.duckdb after the `analyze` task.

SELECT
    COUNT(*) AS game_count,
    COUNT(*) FILTER (WHERE supports_simplified_chinese) AS chinese_support_count,
    ROUND(100.0 * AVG(supports_simplified_chinese::INTEGER), 2) AS chinese_support_percent,
    COUNT(*) FILTER (WHERE chinese_review_count > 0) AS games_with_chinese_reviews,
    COUNT(*) FILTER (WHERE analysis_eligible) AS analysis_eligible_count
FROM game_snapshot;

SELECT
    MEDIAN(chinese_review_share) AS median_chinese_review_share,
    MEDIAN(chinese_vs_non_chinese_gap) AS median_chinese_vs_non_chinese_gap
FROM analysis_games;
