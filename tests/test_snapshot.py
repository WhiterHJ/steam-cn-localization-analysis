from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from steam_cn_insights.snapshot import (
    _load_chart_games,
    _load_curated_apps,
    _merge_candidates,
    _serialize,
    minimum_required_count,
)


class SnapshotUtilityTests(unittest.TestCase):
    def test_serialize_lists_for_csv(self) -> None:
        self.assertEqual(_serialize(["Action", "RPG"]), "Action | RPG")

    def test_limited_run_uses_proportional_coverage_floor(self) -> None:
        self.assertEqual(minimum_required_count(20, limited_run=True), 15)

    def test_full_run_keeps_absolute_minimum(self) -> None:
        self.assertEqual(minimum_required_count(10, limited_run=False), 20)

    def test_load_chart_games_requires_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(FileNotFoundError):
                _load_chart_games(Path(temporary_directory) / "missing.csv")

    def test_load_chart_games_reads_utf8_bom_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "games.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["appid", "name"])
                writer.writeheader()
                writer.writerow({"appid": 730, "name": "Counter-Strike 2"})
            rows = _load_chart_games(path)
        self.assertEqual(rows[0]["appid"], "730")

    def test_load_curated_apps_validates_and_reads_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "curated.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "appid": 391540,
                            "name_hint": "Undertale",
                            "selection_reason": "comparison case",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            rows = _load_curated_apps(path)
        self.assertEqual(rows[0]["appid"], 391540)

    def test_merge_candidates_keeps_chart_origin_and_deduplicates(self) -> None:
        chart = [
            {
                "appid": "730",
                "name": "Counter-Strike 2",
                "chart_count": "2",
                "mostplayed_rank": "1",
                "topselling_rank": "3",
            }
        ]
        curated = [
            {
                "appid": 730,
                "name_hint": "Counter-Strike 2",
                "selection_reason": "overlap",
            },
            {
                "appid": 391540,
                "name_hint": "Undertale",
                "selection_reason": "comparison case",
            },
        ]
        merged = _merge_candidates(chart, curated)
        self.assertEqual([item["appid"] for item in merged], ["730", 391540])
        self.assertEqual(merged[0]["sample_origin"], "chart")
        self.assertEqual(merged[1]["sample_origin"], "curated_contrast")


class SiteContractTests(unittest.TestCase):
    def test_explorer_exposes_sorting_and_sample_boundaries(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        html = (project_root / "site" / "index.html").read_text(encoding="utf-8")
        javascript = (project_root / "site" / "assets" / "app.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('data-sort-key="name"', html)
        self.assertIn('id="origin-filter"', html)
        self.assertIn("绝不混入总体结论", html)
        self.assertIn("function compareGames", javascript)
        self.assertIn("aria-sort", javascript)


if __name__ == "__main__":
    unittest.main()
