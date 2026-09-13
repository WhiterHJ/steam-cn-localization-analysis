from __future__ import annotations

import unittest

from steam_cn_insights.metrics import calculate_game_metrics, safe_rate


class MetricTests(unittest.TestCase):
    def test_safe_rate_handles_zero_denominator(self) -> None:
        self.assertIsNone(safe_rate(0, 0))

    def test_calculate_game_metrics(self) -> None:
        metrics = calculate_game_metrics(
            {"total_reviews": 1_000, "total_positive": 800, "total_negative": 200},
            {"total_reviews": 200, "total_positive": 140, "total_negative": 60},
        )
        self.assertEqual(metrics["all_review_count"], 1_000)
        self.assertEqual(metrics["all_positive_count"], 800)
        self.assertEqual(metrics["all_negative_count"], 200)
        self.assertEqual(metrics["chinese_review_count"], 200)
        self.assertEqual(metrics["chinese_positive_count"], 140)
        self.assertEqual(metrics["chinese_negative_count"], 60)
        self.assertEqual(metrics["non_chinese_review_count"], 800)
        self.assertEqual(metrics["non_chinese_positive_count"], 660)
        self.assertAlmostEqual(metrics["chinese_review_share"], 0.2)
        self.assertAlmostEqual(metrics["all_positive_rate"], 0.8)
        self.assertAlmostEqual(metrics["chinese_positive_rate"], 0.7)
        self.assertAlmostEqual(metrics["non_chinese_positive_rate"], 0.825)
        self.assertAlmostEqual(metrics["positive_rate_gap"], -0.1)
        self.assertAlmostEqual(metrics["chinese_vs_non_chinese_gap"], -0.125)


if __name__ == "__main__":
    unittest.main()
