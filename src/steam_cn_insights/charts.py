"""Collectors and parsers for the server-rendered Steam Charts tables."""

from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .http_client import FetchError, fetch_text
from .quality import validate_chart_entries


CHART_URLS = {
    "mostplayed": "https://store.steampowered.com/charts/mostplayed",
    "topselling": "https://store.steampowered.com/charts/topselling/global",
}

_TBODY_PATTERN = re.compile(r"<tbody[^>]*>(.*?)</tbody>", re.IGNORECASE | re.DOTALL)
_ROW_PATTERN = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_CELL_PATTERN = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
_APP_PATTERN = re.compile(r'href="https://store\.steampowered\.com/app/(\d+)/')
_TAG_PATTERN = re.compile(r"<[^>]+>")


def _clean_text(fragment: str) -> str:
    return " ".join(html.unescape(_TAG_PATTERN.sub(" ", fragment)).split())


def _parse_int(value: str) -> int | None:
    normalized = value.replace(",", "").strip()
    return int(normalized) if normalized.isdigit() else None


def parse_chart_html(chart_type: str, page: str) -> list[dict[str, Any]]:
    """Parse one Steam chart without depending on generated CSS class names."""

    if chart_type not in CHART_URLS:
        raise ValueError(f"Unsupported chart type: {chart_type}")
    tbody_match = _TBODY_PATTERN.search(page)
    if not tbody_match:
        raise FetchError(f"Steam {chart_type} page did not contain a table body")

    entries: list[dict[str, Any]] = []
    for row_html in _ROW_PATTERN.findall(tbody_match.group(1)):
        app_match = _APP_PATTERN.search(row_html)
        cells = _CELL_PATTERN.findall(row_html)
        if not app_match or len(cells) < 4:
            continue

        rank = _parse_int(_clean_text(cells[1]))
        if rank is None:
            continue
        entry: dict[str, Any] = {
            "chart_type": chart_type,
            "rank": rank,
            "appid": int(app_match.group(1)),
            "name": _clean_text(cells[2]),
            "chart_price_text": _clean_text(cells[3]),
            "current_players": None,
            "peak_today": None,
            "rank_change_text": None,
            "weeks_on_chart": None,
        }
        if chart_type == "mostplayed" and len(cells) >= 6:
            entry["current_players"] = _parse_int(_clean_text(cells[4]))
            entry["peak_today"] = _parse_int(_clean_text(cells[5]))
        elif chart_type == "topselling" and len(cells) >= 6:
            entry["rank_change_text"] = _clean_text(cells[4])
            entry["weeks_on_chart"] = _parse_int(_clean_text(cells[5]))
        entries.append(entry)

    return entries


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def run_chart_collection(
    project_root: Path,
    *,
    refresh: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collect current top-selling and most-played chart snapshots."""

    collected_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    snapshot_date = collected_at[:10]
    cache_dir = project_root / "data" / "raw" / "charts" / snapshot_date
    output_dir = project_root / "data" / "interim"
    all_entries: list[dict[str, Any]] = []

    for chart_type, url in CHART_URLS.items():
        print(f"Collecting Steam chart: {chart_type}...")
        page = fetch_text(
            url,
            {"cc": "cn", "l": "english"},
            cache_dir / f"{chart_type}.html",
            refresh=refresh,
        )
        entries = parse_chart_html(chart_type, page)
        validate_chart_entries(entries, expected_count=100)
        for entry in entries:
            entry["snapshot_date"] = snapshot_date
            entry["collected_at_utc"] = collected_at
            entry["market"] = "global"
        all_entries.extend(entries)

    _write_csv(output_dir / "chart_entries.csv", all_entries)

    games: dict[int, dict[str, Any]] = {}
    for entry in all_entries:
        appid = int(entry["appid"])
        game = games.setdefault(
            appid,
            {
                "appid": appid,
                "name": entry["name"],
                "mostplayed_rank": None,
                "topselling_rank": None,
                "chart_count": 0,
                "snapshot_date": snapshot_date,
                "collected_at_utc": collected_at,
            },
        )
        game[f"{entry['chart_type']}_rank"] = entry["rank"]
        game["chart_count"] = int(game["chart_count"]) + 1

    game_records = sorted(
        games.values(),
        key=lambda item: (
            min(
                rank
                for rank in (item["mostplayed_rank"], item["topselling_rank"])
                if rank is not None
            ),
            item["appid"],
        ),
    )
    _write_csv(output_dir / "chart_games.csv", game_records)

    report = {
        "status": "passed",
        "collected_at_utc": collected_at,
        "snapshot_date": snapshot_date,
        "chart_entry_count": len(all_entries),
        "unique_app_count": len(game_records),
        "overlap_app_count": sum(int(item["chart_count"]) == 2 for item in game_records),
        "charts": {chart: 100 for chart in CHART_URLS},
    }
    report_path = output_dir / "chart_collection_report.json"
    with report_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    return all_entries, report
