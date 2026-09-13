from __future__ import annotations

import unittest

from steam_cn_insights.charts import parse_chart_html
from steam_cn_insights.quality import QualityError, validate_chart_entries


MOST_PLAYED_HTML = """
<html><body><table><tbody>
<tr><td><a href="https://store.steampowered.com/app/730/Test"></a></td>
<td>1</td><td><a><img alt=""/><div>Counter-Strike 2</div></a></td>
<td><div>Free To Play</div></td><td>1,083,782</td><td>1,355,646</td></tr>
</tbody></table></body></html>
"""

TOP_SELLING_HTML = """
<html><body><table><tbody>
<tr><td><a href="https://store.steampowered.com/app/570/Test"></a></td>
<td>1</td><td><a><div>Dota 2</div></a></td><td>¥ 0</td>
<td><div>↑ 2</div></td><td><div>735</div></td></tr>
</tbody></table></body></html>
"""


class ChartParserTests(unittest.TestCase):
    def test_parses_most_played_row(self) -> None:
        rows = parse_chart_html("mostplayed", MOST_PLAYED_HTML)
        self.assertEqual(rows[0]["appid"], 730)
        self.assertEqual(rows[0]["name"], "Counter-Strike 2")
        self.assertEqual(rows[0]["current_players"], 1_083_782)
        self.assertEqual(rows[0]["peak_today"], 1_355_646)

    def test_parses_top_selling_row(self) -> None:
        rows = parse_chart_html("topselling", TOP_SELLING_HTML)
        self.assertEqual(rows[0]["appid"], 570)
        self.assertEqual(rows[0]["weeks_on_chart"], 735)

    def test_quality_rejects_incomplete_chart(self) -> None:
        rows = parse_chart_html("mostplayed", MOST_PLAYED_HTML)
        with self.assertRaises(QualityError):
            validate_chart_entries(rows, expected_count=2)


if __name__ == "__main__":
    unittest.main()
