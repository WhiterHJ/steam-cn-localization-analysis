-- Observational comparison by Steam's Simplified Chinese support label.

SELECT
    supports_simplified_chinese,
    COUNT(*) AS game_count,
    MEDIAN(chinese_review_share) AS median_chinese_review_share,
    MEDIAN(chinese_positive_rate) AS median_chinese_positive_rate,
    MEDIAN(non_chinese_positive_rate) AS median_non_chinese_positive_rate,
    MEDIAN(chinese_vs_non_chinese_gap) AS median_chinese_vs_non_chinese_gap
FROM analysis_games
GROUP BY supports_simplified_chinese
ORDER BY supports_simplified_chinese DESC;

-- Games with the highest Chinese-language review participation.
SELECT
    appid,
    name,
    chinese_review_count,
    chinese_review_share,
    chinese_vs_non_chinese_gap,
    best_chart_rank
FROM analysis_games
ORDER BY chinese_review_share DESC
LIMIT 20;

-- Games with the largest negative Chinese vs non-Chinese rating gaps.
SELECT
    appid,
    name,
    chinese_positive_rate,
    non_chinese_positive_rate,
    chinese_vs_non_chinese_gap,
    chinese_review_count
FROM analysis_games
ORDER BY chinese_vs_non_chinese_gap
LIMIT 20;
