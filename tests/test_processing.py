from __future__ import annotations

import unittest

from steam_cn_insights.processing import _parse_boolean


class ProcessingTests(unittest.TestCase):
    def test_parse_boolean_accepts_csv_spellings(self) -> None:
        self.assertTrue(_parse_boolean("True"))
        self.assertFalse(_parse_boolean("false"))
        self.assertTrue(_parse_boolean(1))

    def test_parse_boolean_rejects_ambiguous_values(self) -> None:
        with self.assertRaises(ValueError):
            _parse_boolean("unknown")


if __name__ == "__main__":
    unittest.main()
