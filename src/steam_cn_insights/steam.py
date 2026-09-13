"""Steam store metadata and review-summary collectors."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from .http_client import FetchError, fetch_json


APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
APP_REVIEWS_URL = "https://store.steampowered.com/appreviews/{appid}"


def _money_from_minor_units(value: Any) -> float | None:
    if value is None:
        return None
    return round(int(value) / 100, 2)


def supports_simplified_chinese(supported_languages: str | None) -> bool:
    """Return whether the Steam language string lists Simplified Chinese."""

    if not supported_languages:
        return False
    plain_text = re.sub(r"<[^>]+>", " ", html.unescape(supported_languages))
    return "simplified chinese" in plain_text.casefold()


def fetch_app_details(
    appid: int,
    cache_dir: Path,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    """Fetch store details, preferring China and falling back to the US catalog."""

    app_payload: dict[str, Any] | None = None
    market_used: str | None = None
    errors: list[str] = []
    for market in ("cn", "us"):
        cache_name = (
            f"appdetails_{appid}.json" if market == "cn" else f"appdetails_{appid}_{market}.json"
        )
        payload = fetch_json(
            APP_DETAILS_URL,
            {"appids": appid, "cc": market, "l": "english"},
            cache_dir / cache_name,
            refresh=refresh,
        )
        candidate = payload.get(str(appid))
        if isinstance(candidate, dict) and candidate.get("success"):
            app_payload = candidate
            market_used = market
            break
        errors.append(f"{market}: unsuccessful response")

    if app_payload is None or market_used is None:
        raise FetchError(
            f"Steam appdetails returned no successful record for appid={appid} "
            f"({'; '.join(errors)})"
        )

    data = app_payload.get("data")
    if not isinstance(data, dict):
        raise FetchError(f"Steam appdetails returned no data object for appid={appid}")

    price = data.get("price_overview") or {}
    release = data.get("release_date") or {}
    genres = data.get("genres") or []
    supported_languages = data.get("supported_languages")

    return {
        "appid": appid,
        "store_market": market_used,
        "available_in_cn": market_used == "cn",
        "name": data.get("name"),
        "type": data.get("type"),
        "is_free": bool(data.get("is_free", False)),
        "release_date_text": release.get("date"),
        "coming_soon": bool(release.get("coming_soon", False)),
        "currency": price.get("currency"),
        "initial_price": _money_from_minor_units(price.get("initial")),
        "final_price": _money_from_minor_units(price.get("final")),
        "discount_percent": price.get("discount_percent"),
        "developers": data.get("developers") or [],
        "publishers": data.get("publishers") or [],
        "genres": [item.get("description") for item in genres if item.get("description")],
        "supported_languages_raw": supported_languages,
        "supports_simplified_chinese": supports_simplified_chinese(supported_languages),
    }


def fetch_review_summary(
    appid: int,
    language: str,
    cache_dir: Path,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    """Fetch the aggregate review summary for one application and language."""

    payload = fetch_json(
        APP_REVIEWS_URL.format(appid=appid),
        {
            "json": 1,
            "filter": "updated",
            "language": language,
            "purchase_type": "all",
            "num_per_page": 1,
            "filter_offtopic_activity": 1,
        },
        cache_dir / f"reviews_{appid}_{language}.json",
        refresh=refresh,
    )
    if payload.get("success") != 1:
        raise FetchError(
            f"Steam reviews returned success={payload.get('success')} "
            f"for appid={appid}, language={language}"
        )

    summary = payload.get("query_summary")
    if not isinstance(summary, dict):
        raise FetchError(
            f"Steam reviews returned no query_summary for appid={appid}, language={language}"
        )

    return {
        "appid": appid,
        "language": language,
        "review_score": summary.get("review_score"),
        "review_score_desc": summary.get("review_score_desc"),
        "total_positive": int(summary.get("total_positive", 0)),
        "total_negative": int(summary.get("total_negative", 0)),
        "total_reviews": int(summary.get("total_reviews", 0)),
    }
