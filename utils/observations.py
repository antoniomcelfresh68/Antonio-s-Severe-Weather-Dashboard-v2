# utils/observations.py

import streamlit as st
import requests
from typing import Any, Dict, Optional, Tuple
import time
from datetime import datetime, timezone
import math
import streamlit.components.v1 as components
from utils.ai_context import update_page_ai_context
from utils.nws import get_nws_point_properties
from utils.satelite import render_satellite_panel

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/geo+json, application/json",
}
SPC_MESO_BASE = "https://www.spc.noaa.gov/exper/mesoanalysis/new"
DEFAULT_MESO_SECTOR = "19"
DEFAULT_MESO_PARAMETER = "pmsl"

def _get_nearest_radar_id(lat: float, lon: float) -> Optional[str]:
    """
    Uses api.weather.gov points endpoint; returns radarStation like 'KTLX' when available.
    """
    try:
        return get_nws_point_properties(lat, lon).get("radarStation")
    except Exception:
        return None

@st.cache_data(ttl=120, show_spinner=False)
def _get_json(url: str, timeout: int = 20) -> Dict[str, Any]:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _safe(d: Dict[str, Any], *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _build_spc_meso_url(sector: str, parm: str) -> str:
    return f"{SPC_MESO_BASE}/viewsector.php?sector={sector}&parm={parm}"

def _c_to_f(c: Optional[float]) -> Optional[float]:
    if c is None:
        return None
    return c * 9/5 + 32

def _ms_to_mph(ms: Optional[float]) -> Optional[float]:
    if ms is None:
        return None
    return ms * 2.236936

def _deg_to_compass(deg: Optional[float]) -> Optional[str]:
    if deg is None:
        return None
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    i = int((deg % 360) / 22.5 + 0.5) % 16
    return dirs[i]

def _fmt_num(x: Optional[float], suffix: str = "", digits: int = 0) -> str:
    if x is None:
        return "—"
    if digits == 0:
        return f"{int(round(x))}{suffix}"
    return f"{x:.{digits}f}{suffix}"


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        # NWS timestamps often end with Z
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb/2)**2
    return 2 * R * math.asin(math.sqrt(a))

@st.cache_data(ttl=1800, show_spinner=False)
def _get_candidate_observation_stations(lat: float, lon: float) -> list[dict[str, Any]]:
    try:
        stations_url = get_nws_point_properties(lat, lon).get("observationStations")
        if not stations_url:
            return []

        stations = _get_json(stations_url)
        features = stations.get("features", []) or []
        if not features:
            return []
        return features[:10]
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def _candidate_station_ids_by_distance(lat: float, lon: float) -> list[str]:
    candidates: list[tuple[float, str]] = []

    for feat in _get_candidate_observation_stations(lat, lon):
        sid = _safe(feat, "properties", "stationIdentifier")
        if not sid:
            continue

        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates") or None
        dist_m = 9e18
        if isinstance(coords, (list, tuple)) and len(coords) >= 2:
            st_lon, st_lat = coords[0], coords[1]
            dist_m = _haversine_m(lat, lon, st_lat, st_lon)

        candidates.append((dist_m, sid))

    if not candidates:
        return []

    candidates.sort(key=lambda item: item[0])
    return [station_id for _, station_id in candidates]


@st.cache_data(ttl=120, show_spinner=False)
def _get_station_latest_obs(station_id: str) -> Optional[Dict[str, Any]]:
    try:
        latest = _get_json(f"https://api.weather.gov/stations/{station_id}/observations/latest")
        props = latest.get("properties") or {}
        return props or None
    except Exception:
        return None


def _observation_score(props: Dict[str, Any]) -> int:
    want_fields = [
        ("temperature", "value"),
        ("dewpoint", "value"),
        ("relativeHumidity", "value"),
        ("windDirection", "value"),
        ("windSpeed", "value"),
        ("windGust", "value"),
        ("seaLevelPressure", "value"),
        ("visibility", "value"),
    ]

    present = 0
    for k1, k2 in want_fields:
        if _safe(props, k1, k2) is not None:
            present += 1

    ts = _parse_iso(props.get("timestamp"))
    if ts is not None:
        age = datetime.now(timezone.utc) - ts.astimezone(timezone.utc)
        age_min = age.total_seconds() / 60.0
        if age_min <= 90:
            present += 1
        elif age_min >= 240:
            present -= 2

    return present


def _get_nws_latest_obs_near_point(lat: float, lon: float) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Returns (obs_properties, station_id), preferring usable nearby stations.
    """
    station_ids = _candidate_station_ids_by_distance(lat, lon)
    if not station_ids:
        return None, None

    best_station_id: Optional[str] = None
    best_props: Optional[Dict[str, Any]] = None
    best_score: Optional[int] = None

    for station_id in station_ids:
        props = _get_station_latest_obs(station_id)
        if not props:
            continue

        score = _observation_score(props)
        if best_score is None or score > best_score:
            best_station_id = station_id
            best_props = props
            best_score = score

    if best_props is None:
        return None, station_ids[0]
    return best_props, best_station_id

@st.cache_data(ttl=120, show_spinner=False)
def get_location_temp_dew_f(lat: float, lon: float) -> Tuple[Optional[float], Optional[float]]:
    """
    Return latest temperature/dewpoint (degF) from the same NWS observation workflow
    used by the observations page.
    """
    temp_f, dew_f, _wind, _cond = get_location_glance(lat, lon)
    return temp_f, dew_f

@st.cache_data(ttl=120, show_spinner=False)
def get_location_wind_conditions(lat: float, lon: float) -> Tuple[str, str]:
    """
    Return compact wind (direction + speed) and current conditions text for a location.
    """
    _temp, _dew, wind_str, cond_str = get_location_glance(lat, lon)
    return wind_str, cond_str


@st.cache_data(ttl=120, show_spinner=False)
def get_location_glance(lat: float, lon: float) -> Tuple[Optional[float], Optional[float], str, str]:
    """
    Return temp/dew (degF) and compact wind/conditions from a single cached lookup.
    """
    obs, _ = _get_nws_latest_obs_near_point(lat, lon)
    if not obs:
        return None, None, "--", "--"

    temp_c = _safe(obs, "temperature", "value")
    dew_c = _safe(obs, "dewpoint", "value")
    temp_f = _c_to_f(temp_c)
    dew_f = _c_to_f(dew_c)

    wind_dir = _safe(obs, "windDirection", "value")
    wind_spd_ms = _safe(obs, "windSpeed", "value")
    wind_spd_mph = _ms_to_mph(wind_spd_ms)
    wd_card = _deg_to_compass(wind_dir)

    wind_str = "--"
    if wind_spd_mph is not None:
        if wind_dir is not None and wd_card is not None:
            wind_str = f"{wd_card} ({wind_dir:.0f} deg) {wind_spd_mph:.0f} mph"
        else:
            wind_str = f"{wind_spd_mph:.0f} mph"

    cond_str = (obs.get("textDescription") or "").strip() or "--"
    return temp_f, dew_f, wind_str, cond_str

def render_spc_mesoanalysis() -> None:
    st.markdown(" # SPC Mesoanalysis")
    update_page_ai_context(
        "Observations",
        selected_mesoanalysis_parameter=DEFAULT_MESO_PARAMETER,
    )
    meso_url = _build_spc_meso_url(DEFAULT_MESO_SECTOR, DEFAULT_MESO_PARAMETER)
    components.iframe(meso_url, height=1000, scrolling=True)

def render():
    st.markdown(f" # Observations")
    render_spc_mesoanalysis()
    lat = float(st.session_state.lat)
    lon = float(st.session_state.lon)
    radar_id = _get_nearest_radar_id(lat, lon) or "KTLX"  # fallback for Oklahoma
    obs, station_id = _get_nws_latest_obs_near_point(lat, lon)

    update_page_ai_context(
        "Observations",
        radar_station=radar_id,
        latest_observation={
            "station_id": station_id,
            "timestamp": (obs or {}).get("timestamp") if obs else None,
            "temperature_c": _safe(obs or {}, "temperature", "value"),
            "dewpoint_c": _safe(obs or {}, "dewpoint", "value"),
            "relative_humidity_percent": _safe(obs or {}, "relativeHumidity", "value"),
            "wind_direction_degrees": _safe(obs or {}, "windDirection", "value"),
            "wind_speed_m_s": _safe(obs or {}, "windSpeed", "value"),
            "wind_gust_m_s": _safe(obs or {}, "windGust", "value"),
            "text_description": (obs or {}).get("textDescription") if obs else None,
        },
    )
#    Cache-bust once per minute so the gif actually updates in browsers/CDNs
    bust = int(time.time() // 60)
    st.markdown(f" # Radar for {st.session_state.city_key} ({radar_id})")
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown(f"**Base Reflectivity ({radar_id})**")
        st.image(
        f"https://radar.weather.gov/ridge/standard/{radar_id}_loop.gif?b={bust}",
        width='stretch',
    )

    with col2:
        st.markdown(f"**Base Velocity ({radar_id})**")
        st.image(
        f"https://radar.weather.gov/ridge/standard/base_velocity/{radar_id}_loop.gif?b={bust}",
        width='stretch',
    )

    st.caption("Radar imagery: NOAA/NWS RIDGE (loop GIFs).")
    render_satellite_panel()

   

    

    

    
