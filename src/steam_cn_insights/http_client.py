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
    request_url = f"{url}?{urlencode(params)}"
    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.8",
            "User-Agent": USER_AGENT,
        },
    )

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8-sig")
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise FetchError(f"Expected a JSON object from {request_url}")
            with cache_path.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            return payload
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            if attempt >= retries:
                break
            time.sleep(min(2**attempt, 8))

    raise FetchError(f"Failed to fetch {request_url}: {last_error}") from last_error
