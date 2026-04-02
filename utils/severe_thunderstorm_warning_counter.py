# utils/severe_thunderstorm_warning_counter.py

import requests
import time
from datetime import datetime, timezone

IEM_COW_URL = "https://mesonet.agron.iastate.edu/api/1/cow.json"

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/json",
}

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _get_with_retries(params: dict[str, str], timeout: int = 25, attempts: int = 3) -> requests.Response:
    last_error: requests.RequestException | None = None

    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(IEM_COW_URL, params=params, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.HTTPError as exc:
            last_error = exc
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code not in RETRYABLE_STATUS_CODES or attempt == attempts:
                raise
        except requests.RequestException as exc:
            last_error = exc
            if attempt == attempts:
                raise

        time.sleep(min(2 ** (attempt - 1), 4))

    if last_error is not None:
        raise last_error
    raise RuntimeError("Request failed before a response was returned.")


def fetch_svr_warning_count_ytd(year: int) -> int:
    """
    Returns an unofficial national YTD count of Severe Thunderstorm Warnings
    using IEM Cow storm-based warning stats (events_total).
    """
    start = datetime(year, 1, 1, 0, 0, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    params = {
        "phenomena": "SV",     # Severe Thunderstorm Warnings :contentReference[oaicite:3]{index=3}
        "begints": start,      # UTC ISO8601 :contentReference[oaicite:4]{index=4}
        "endts": end,
    }

    r = _get_with_retries(params)
    data = r.json()

    # Cow schema: stats.events_total :contentReference[oaicite:5]{index=5}
    return int(data["stats"]["events_total"])
