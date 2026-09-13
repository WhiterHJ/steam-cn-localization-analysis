from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from steam_cn_insights.snapshot import (
    _load_chart_games,
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


if __name__ == "__main__":
    unittest.main()
