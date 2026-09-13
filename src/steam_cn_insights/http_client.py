"""Small cached JSON client used by the data collectors."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


USER_AGENT = (
    "steam-cn-localization-analysis/0.1 "
    "(+https://github.com/WhiterHJ/steam-cn-localization-analysis)"
)


class FetchError(RuntimeError):
    """Raised when a remote JSON resource cannot be fetched or decoded."""


def _request_bytes(
    url: str,
    params: Mapping[str, object],
    *,
    timeout: float,
    retries: int,
) -> bytes:
    request_url = f"{url}?{urlencode(params)}" if params else url
    request = Request(
        request_url,
        headers={
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.8",
            "User-Agent": USER_AGENT,
        },
    )

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
            if attempt >= retries:
                break
            time.sleep(min(2**attempt, 8))

    raise FetchError(f"Failed to fetch {request_url}: {last_error}") from last_error


def fetch_json(
    url: str,
    params: Mapping[str, object],
    cache_path: Path,
    *,
    refresh: bool = False,
    timeout: float = 30.0,
    retries: int = 3,
) -> dict[str, Any]:
    """Fetch JSON with on-disk caching and bounded retry behavior."""

    if cache_path.exists() and not refresh:
        with cache_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    request_url = f"{url}?{urlencode(params)}" if params else url
    try:
        body = _request_bytes(url, params, timeout=timeout, retries=retries).decode("utf-8-sig")
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FetchError(f"Failed to decode JSON from {request_url}: {error}") from error

    if not isinstance(payload, dict):
        raise FetchError(f"Expected a JSON object from {request_url}")
    with cache_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return payload


def fetch_text(
    url: str,
    params: Mapping[str, object],
    cache_path: Path,
    *,
    refresh: bool = False,
    timeout: float = 30.0,
    retries: int = 3,
) -> str:
    """Fetch UTF-8 text with the same cache and retry contract as JSON."""

    if cache_path.exists() and not refresh:
        return cache_path.read_text(encoding="utf-8")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        text = _request_bytes(url, params, timeout=timeout, retries=retries).decode("utf-8")
    except UnicodeDecodeError as error:
        raise FetchError(f"Failed to decode text from {url}: {error}") from error
    cache_path.write_text(text, encoding="utf-8", newline="\n")
    return text
