from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests
import streamlit as st

NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"
CHICAGO_TZ = ZoneInfo("America/Chicago")

SEVERE_EVENTS = {
    "Tornado Warning",
    "Severe Thunderstorm Warning",
    "Tornado Watch",
    "Severe Thunderstorm Watch",
}

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: your-email@example.com)",
    "Accept": "application/geo+json, application/json",
}


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _format_central_time(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return dt.astimezone(CHICAGO_TZ).strftime("%I:%M %p CT").lstrip("0")


def _short_event_name(event: str) -> str:
    mapping = {
        "Tornado Warning": "TORNADO WARNING",
        "Severe Thunderstorm Warning": "SEVERE TSTM WARNING",
        "Tornado Watch": "TORNADO WATCH",
        "Severe Thunderstorm Watch": "SEVERE TSTM WATCH",
    }
    return mapping.get(event, event.upper())


def _short_area(area_desc: str, max_len: int = 120) -> str:
    text = (area_desc or "").strip()
    if not text:
        return "U.S."
    return text if len(text) <= max_len else f"{text[: max_len - 1].rstrip()}..."


def _build_display_text(event: str, area_desc: str, ends_dt: Optional[datetime]) -> str:
    event_txt = _short_event_name(event)
    area_txt = _short_area(area_desc)
    time_txt = _format_central_time(ends_dt)
    if not time_txt:
        return f"{event_txt} - {area_txt}"
    tail = "Until" if event.endswith("Watch") else "Expires"
    return f"{event_txt} - {area_txt} - {tail} {time_txt}"


def _parse_features(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()

    for feat in features:
        props = (feat or {}).get("properties", {}) or {}
        event = str(props.get("event") or "").strip()
        if event not in SEVERE_EVENTS:
            continue

        status = str(props.get("status") or "").strip()
        if status and status != "Actual":
            continue

        alert_id = str(props.get("id") or props.get("@id") or "").strip()
        if alert_id and alert_id in seen_ids:
            continue
        if alert_id:
            seen_ids.add(alert_id)

        area_desc = str(props.get("areaDesc") or "").strip()
        end_raw = (
            str(props.get("ends") or "").strip()
            or str(props.get("expires") or "").strip()
        )
        ends_dt = _parse_dt(end_raw)

        results.append(
            {
                "event": event,
                "areaDesc": area_desc,
                "ends": ends_dt,
                "ends_dt": ends_dt,
                "id": alert_id,
                "display_text": _build_display_text(event, area_desc, ends_dt),
            }
        )

    return results


def _mock_snapshot(seed_time: datetime, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        event = str(row["event"])
        area = str(row["areaDesc"])
        end_minutes = int(row.get("end_minutes", 60))
        ends_dt = seed_time + timedelta(minutes=end_minutes)
        alert_id = str(row.get("id") or f"mock-ok-{seed_time.strftime('%H%M')}-{i:02d}")
        alerts.append(
            {
                "event": event,
                "areaDesc": area,
                "ends": ends_dt,
                "ends_dt": ends_dt,
                "id": alert_id,
                "display_text": _build_display_text(event, area, ends_dt),
            }
        )
    return alerts


def mock_ok_outbreak_alerts(mode: str, step: int) -> List[Dict[str, Any]]:
    """Generate mock Oklahoma outbreak alerts for ticker testing."""
    base_ct = datetime.now(CHICAGO_TZ).replace(second=0, microsecond=0)

    static_rows = [
        {"event": "Tornado Warning", "areaDesc": "Cleveland County; Norman; Moore", "end_minutes": 38},
        {"event": "Severe Thunderstorm Warning", "areaDesc": "Oklahoma County; Oklahoma City metro", "end_minutes": 44},
        {"event": "Tornado Warning", "areaDesc": "Canadian County; Yukon; Mustang", "end_minutes": 31},
        {"event": "Severe Thunderstorm Warning", "areaDesc": "Pottawatomie County; Shawnee; Tecumseh", "end_minutes": 52},
        {"event": "Tornado Watch", "areaDesc": "Central Oklahoma including OKC metro", "end_minutes": 173},
        {"event": "Severe Thunderstorm Watch", "areaDesc": "Western Oklahoma; Caddo County; Grady County", "end_minutes": 166},
        {"event": "Severe Thunderstorm Warning", "areaDesc": "Logan County; Guthrie; Edmond north side", "end_minutes": 36},
        {"event": "Tornado Warning", "areaDesc": "McClain County; Newcastle; Blanchard", "end_minutes": 28},
        {"event": "Severe Thunderstorm Warning", "areaDesc": "Garvin County; Pauls Valley", "end_minutes": 49},
        {"event": "Severe Thunderstorm Watch", "areaDesc": "South-central Oklahoma; Murray County; Love County", "end_minutes": 182},
        {"event": "Tornado Warning", "areaDesc": "Lincoln County; Chandler; Stroud", "end_minutes": 33},
        {"event": "Severe Thunderstorm Warning", "areaDesc": "Payne County; Stillwater", "end_minutes": 47},
        {"event": "Tornado Watch", "areaDesc": "Eastern Oklahoma; Creek County; Tulsa southwest suburbs", "end_minutes": 189},
        {"event": "Severe Thunderstorm Warning", "areaDesc": "Pontotoc County; Ada", "end_minutes": 42},
    ]

    dynamic_frames: List[List[Dict[str, Any]]] = [
        [
            {"event": "Tornado Warning", "areaDesc": "Cleveland County; Norman; Moore", "end_minutes": 37},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Oklahoma County; Oklahoma City metro", "end_minutes": 44},
            {"event": "Tornado Warning", "areaDesc": "Canadian County; Yukon; Mustang", "end_minutes": 30},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Grady County; Chickasha; Tuttle", "end_minutes": 48},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Logan County; Guthrie; Edmond north side", "end_minutes": 35},
            {"event": "Tornado Watch", "areaDesc": "Central Oklahoma including OKC metro", "end_minutes": 170},
            {"event": "Severe Thunderstorm Watch", "areaDesc": "Western Oklahoma; Caddo County; Grady County", "end_minutes": 165},
            {"event": "Tornado Warning", "areaDesc": "McClain County; Newcastle; Blanchard", "end_minutes": 27},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Pottawatomie County; Shawnee; Tecumseh", "end_minutes": 51},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Payne County; Stillwater", "end_minutes": 46},
            {"event": "Tornado Watch", "areaDesc": "Eastern Oklahoma; Creek County; Tulsa southwest suburbs", "end_minutes": 186},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Garvin County; Pauls Valley", "end_minutes": 48},
        ],
        [
            {"event": "Tornado Warning", "areaDesc": "Oklahoma County east; Midwest City; Choctaw", "end_minutes": 34},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Cleveland County; Norman south; Noble", "end_minutes": 41},
            {"event": "Tornado Warning", "areaDesc": "Pottawatomie County west; Shawnee outskirts", "end_minutes": 29},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Lincoln County; Chandler; Stroud", "end_minutes": 43},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Payne County; Stillwater", "end_minutes": 40},
            {"event": "Tornado Watch", "areaDesc": "Central Oklahoma including OKC metro", "end_minutes": 163},
            {"event": "Severe Thunderstorm Watch", "areaDesc": "South-central Oklahoma; Garvin; Murray", "end_minutes": 172},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Canadian County east; Bethany west edge", "end_minutes": 36},
            {"event": "Tornado Warning", "areaDesc": "Seminole County; Seminole; Wewoka", "end_minutes": 26},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Pontotoc County; Ada", "end_minutes": 39},
            {"event": "Tornado Watch", "areaDesc": "Northeast Oklahoma; Tulsa metro west", "end_minutes": 180},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Okfuskee County; Okemah", "end_minutes": 45},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Creek County; Sapulpa; Kellyville", "end_minutes": 52},
        ],
        [
            {"event": "Tornado Warning", "areaDesc": "Lincoln County east; Davenport; Sparks", "end_minutes": 31},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Oklahoma County; Oklahoma City northeast", "end_minutes": 38},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Pottawatomie County; Shawnee; McLoud", "end_minutes": 44},
            {"event": "Tornado Warning", "areaDesc": "Seminole County north; Little; Wewoka", "end_minutes": 24},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Creek County; Sapulpa; Drumright", "end_minutes": 41},
            {"event": "Severe Thunderstorm Watch", "areaDesc": "East-central Oklahoma; Lincoln to Okmulgee counties", "end_minutes": 162},
            {"event": "Tornado Watch", "areaDesc": "Eastern Oklahoma; Tulsa metro; Muskogee corridor", "end_minutes": 171},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Logan County east; Meridian; Coyle", "end_minutes": 33},
            {"event": "Tornado Warning", "areaDesc": "Okfuskee County west; Castle; Bearden", "end_minutes": 28},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Payne County; Stillwater east", "end_minutes": 36},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Tulsa County south; Bixby; Jenks", "end_minutes": 48},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Osage County southeast; Skiatook", "end_minutes": 55},
        ],
        [
            {"event": "Tornado Warning", "areaDesc": "Okmulgee County; Okmulgee; Henryetta", "end_minutes": 29},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Tulsa County; Tulsa metro core", "end_minutes": 40},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Muskogee County; Muskogee", "end_minutes": 46},
            {"event": "Tornado Warning", "areaDesc": "Wagoner County; Wagoner; Coweta", "end_minutes": 27},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Rogers County; Claremore", "end_minutes": 43},
            {"event": "Severe Thunderstorm Watch", "areaDesc": "Northeast Oklahoma; Tulsa to Miami", "end_minutes": 154},
            {"event": "Tornado Watch", "areaDesc": "Eastern Oklahoma; Muskogee to Fort Smith corridor", "end_minutes": 165},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Creek County east; Sapulpa east side", "end_minutes": 34},
            {"event": "Tornado Warning", "areaDesc": "McIntosh County north; Checotah", "end_minutes": 23},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Mayes County; Pryor Creek", "end_minutes": 38},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Delaware County; Jay", "end_minutes": 51},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Washington County; Bartlesville", "end_minutes": 58},
        ],
        [
            {"event": "Tornado Warning", "areaDesc": "Cherokee County; Tahlequah", "end_minutes": 26},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Adair County; Stilwell", "end_minutes": 39},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Sequoyah County; Sallisaw", "end_minutes": 42},
            {"event": "Tornado Warning", "areaDesc": "Muskogee County east; Warner; Webbers Falls", "end_minutes": 24},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Le Flore County north; Poteau", "end_minutes": 37},
            {"event": "Severe Thunderstorm Watch", "areaDesc": "Far eastern Oklahoma; Arkansas border counties", "end_minutes": 149},
            {"event": "Tornado Watch", "areaDesc": "Eastern Oklahoma into western Arkansas", "end_minutes": 158},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Haskell County; Stigler", "end_minutes": 33},
            {"event": "Tornado Warning", "areaDesc": "Latimer County; Wilburton", "end_minutes": 21},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Pittsburg County; McAlester", "end_minutes": 45},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Pushmataha County; Antlers", "end_minutes": 50},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Choctaw County; Hugo", "end_minutes": 57},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Bryan County; Durant", "end_minutes": 62},
        ],
        [
            {"event": "Severe Thunderstorm Warning", "areaDesc": "McCurtain County; Idabel", "end_minutes": 36},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Choctaw County; Hugo; Sawyer", "end_minutes": 40},
            {"event": "Tornado Warning", "areaDesc": "Pushmataha County south; Rattan", "end_minutes": 22},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Bryan County east; Durant outskirts", "end_minutes": 43},
            {"event": "Tornado Warning", "areaDesc": "Atoka County east; Caney", "end_minutes": 20},
            {"event": "Severe Thunderstorm Watch", "areaDesc": "Southeast Oklahoma through Red River counties", "end_minutes": 138},
            {"event": "Tornado Watch", "areaDesc": "Southeastern Oklahoma into southwest Arkansas", "end_minutes": 146},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Le Flore County south; Heavener", "end_minutes": 35},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Murray County; Sulphur", "end_minutes": 46},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Carter County; Ardmore", "end_minutes": 52},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Love County; Marietta", "end_minutes": 55},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Johnston County; Tishomingo", "end_minutes": 60},
        ],
        [
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Bryan County east; Bokchito; Durant south", "end_minutes": 30},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Choctaw County east; Boswell", "end_minutes": 34},
            {"event": "Tornado Warning", "areaDesc": "McCurtain County southeast; Haworth", "end_minutes": 18},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Pushmataha County southeast; Sobol", "end_minutes": 37},
            {"event": "Severe Thunderstorm Watch", "areaDesc": "Extreme southeast Oklahoma near Arkansas border", "end_minutes": 126},
            {"event": "Tornado Watch", "areaDesc": "Southeast Oklahoma and adjacent Arkansas", "end_minutes": 133},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Le Flore County southeast; Wister", "end_minutes": 33},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Atoka County south; Atoka", "end_minutes": 42},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Pittsburg County south; Kiowa", "end_minutes": 44},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Coal County; Coalgate", "end_minutes": 48},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Hughes County; Holdenville", "end_minutes": 50},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Pontotoc County south; Ada south", "end_minutes": 54},
        ],
        [
            {"event": "Severe Thunderstorm Warning", "areaDesc": "McCurtain County east; Broken Bow east", "end_minutes": 28},
            {"event": "Tornado Warning", "areaDesc": "McCurtain County southeast; Eagletown", "end_minutes": 16},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Choctaw County southeast; Fort Towson", "end_minutes": 31},
            {"event": "Severe Thunderstorm Watch", "areaDesc": "Far southeast Oklahoma near Red River", "end_minutes": 115},
            {"event": "Tornado Watch", "areaDesc": "Lower Red River Valley east", "end_minutes": 121},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Pushmataha County east; Clayton", "end_minutes": 35},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Le Flore County east; Hodgen", "end_minutes": 38},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Bryan County southeast; Bennington", "end_minutes": 40},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Johnston County south; Milburn", "end_minutes": 43},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Carter County east; Springer", "end_minutes": 47},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Murray County east; Dougherty", "end_minutes": 51},
            {"event": "Severe Thunderstorm Warning", "areaDesc": "Garvin County southeast; Elmore City", "end_minutes": 56},
        ],
    ]

    if mode == "dynamic":
        idx = step % len(dynamic_frames)
        frame_rows = dynamic_frames[idx]
        frame_seed = base_ct + timedelta(minutes=idx * 4)
        return _mock_snapshot(frame_seed, frame_rows)

    return _mock_snapshot(base_ct, static_rows)


def get_severe_alerts(source: str, mode: str) -> List[Dict[str, Any]]:
    """Return severe alerts from live NWS or local Oklahoma outbreak simulation."""
    normalized_source = (source or "live").strip().lower()
    normalized_mode = (mode or "static").strip().lower()
    if normalized_source == "mock":
        step = int(st.session_state.get("mock_alert_step", 0))
        return mock_ok_outbreak_alerts(mode=normalized_mode, step=step)
    return fetch_us_severe_alerts()


def fetch_us_severe_alerts(timeout: Tuple[int, int] = (3, 6)) -> List[Dict[str, Any]]:
    """Fetch active nationwide severe watch/warning alerts.

    Keeps only exact event matches:
    - Tornado Warning
    - Severe Thunderstorm Warning
    - Tornado Watch
    - Severe Thunderstorm Watch
    """
    try:
        resp = requests.get(NWS_ALERTS_URL, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        data = resp.json() or {}
        features = data.get("features", []) or []
    except Exception:
        return []

    return _parse_features(features)


@st.cache_data(ttl=90, show_spinner=False)
def get_cached_severe_alerts_payload() -> Tuple[List[Dict[str, Any]], bool]:
    """Return (alerts, had_error)."""
    try:
        resp = requests.get(NWS_ALERTS_URL, headers=HEADERS, timeout=(3, 6))
        resp.raise_for_status()
        data = resp.json() or {}
        features = data.get("features", []) or []
    except Exception:
        return [], True
    return _parse_features(features), False
