# utils/tornado_warning_counter.py

from __future__ import annotations
import io
import time
import pandas as pd
import requests
from datetime import datetime, timezone
from typing import Optional

IEM_WATCHWARN = "https://mesonet.agron.iastate.edu/cgi-bin/request/gis/watchwarn.py"

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "text/csv",
}

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _get_with_retries(url: str, *, params: dict[str, str], timeout: int, attempts: int = 3) -> requests.Response:
    last_error: requests.RequestException | None = None

    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
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


def _count_events_from_csv(csv_text: str) -> int:
    if not csv_text.strip():
        return 0

    try:
        df = pd.read_csv(io.StringIO(csv_text))
    except pd.errors.EmptyDataError:
        return 0

    if df.empty:
        return 0

    cols = {c.lower(): c for c in df.columns}

    wfo_col = cols.get("wfo") or cols.get("office") or cols.get("wfo_id")
    etn_col = cols.get("etn") or cols.get("eventid") or cols.get("event_id")
    phen_col = cols.get("phenomena") or cols.get("phen")
    sig_col = cols.get("significance") or cols.get("sig")
    year_col = cols.get("year")

    required = [wfo_col, etn_col]
    if any(c is None for c in required):
        raise ValueError(f"Unexpected CSV schema. Columns: {list(df.columns)}")

    key_cols = [wfo_col, etn_col]
    for c in (year_col, phen_col, sig_col):
        if c is not None:
            key_cols.append(c)

    return int(df.drop_duplicates(subset=key_cols).shape[0])


def fetch_tor_warning_count_ytd(year: Optional[int] = None, timeout: int = 45) -> int:
    """
    Returns national YTD count of Tornado Warning *events* (unique by WFO+ETN+year+phenomena+significance),
    using IEM's VTEC archive CSV bulk service.
    """
    if year is None:
        year = datetime.now(timezone.utc).year

    now = datetime.now(timezone.utc)
    sts = f"{year}-01-01T00:00Z"
    if year >= now.year:
        ets = now.strftime("%Y-%m-%dT%H:%MZ")
    else:
        ets = f"{year+1}-01-01T00:00Z"

    params = {
        "accept": "csv",
        "sts": sts,
        "ets": ets,
        "limitps": "yes",
        "phenomena": "TO",
        "significance": "W",
    }

    r = _get_with_retries(IEM_WATCHWARN, params=params, timeout=timeout)
    count = _count_events_from_csv(r.text)

    # The service can occasionally return an empty current-year window even when
    # the broader yearly query has data. Retry once with the full-year end bound
    # before accepting zero as the real answer.
    if count == 0 and year >= now.year and now.timetuple().tm_yday > 7:
        fallback_params = dict(params)
        fallback_params["ets"] = f"{year+1}-01-01T00:00Z"
        fallback_response = _get_with_retries(IEM_WATCHWARN, params=fallback_params, timeout=timeout)
        fallback_count = _count_events_from_csv(fallback_response.text)
        if fallback_count > 0:
            return fallback_count

    return count
