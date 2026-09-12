from __future__ import annotations

import unittest

from steam_cn_insights.quality import QualityError, validate_review_summary
from steam_cn_insights.steam import supports_simplified_chinese


class ParsingTests(unittest.TestCase):
    def test_detects_simplified_chinese_in_html(self) -> None:
        value = "English, <strong>Simplified Chinese</strong>, French"
        self.assertTrue(supports_simplified_chinese(value))

    def test_does_not_confuse_traditional_chinese(self) -> None:
        self.assertFalse(supports_simplified_chinese("English, Traditional Chinese"))


class QualityTests(unittest.TestCase):
    def test_review_counts_must_reconcile(self) -> None:
        with self.assertRaises(QualityError):
            validate_review_summary(
                {
                    "appid": 1,
                    "language": "all",
                    "total_reviews": 10,
                    "total_positive": 8,
                    "total_negative": 1,
                }
            )


if __name__ == "__main__":
    unittest.main()
